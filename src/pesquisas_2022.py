# %%
import pandas as pd
import requests
import re
from calendar import monthrange
from io import StringIO

url = "https://pt.wikipedia.org/wiki/Pesquisas_de_opini%C3%A3o_para_a_elei%C3%A7%C3%A3o_presidencial_no_Brasil_em_2022"

html = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
).text

tabelas = pd.read_html(StringIO(html))

tabelas[18]
df= tabelas[18]

nome_coluna = []

for colunas_df in df.columns.tolist():
    nome_coluna.append(colunas_df[0])
df.columns = nome_coluna

df.drop(columns=['Indecisos e Absentos', 'Vantagem'],
        inplace=True

        )

df['Instituto de Pesquisa'] = df['Instituto de Pesquisa'].str.replace(r'\[.*?\]', '', regex=True)
df["Tamanho da Amostra"] = df["Tamanho da Amostra"] *1000
for coluna in ["Bolsonaro PL", "Lula PT"]:
    df[coluna] = df[coluna].str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df[coluna] = pd.to_numeric(df[coluna])
    df[coluna] = df[coluna] / 100  
# %%
extracao = df['Data(s) de Pesquisa'].str.extract(r'(?P<dia_ini>\d+)[–-](?P<dia_fim>\d+)\s+(?P<mes>\w+)\s+(?P<ano>\d{4})')# %%
df['Data_Inicio'] = extracao['dia_ini'] + '-' + extracao['mes'] + '-' + extracao['ano']
df['Data_Fim'] = extracao['dia_fim'] + '-' + extracao['mes'] + '-' + extracao['ano']

# %%


meses_map = {
    'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6,
    'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12
}

def converter_periodo_inteligente(texto):
    if pd.isna(texto):
        return pd.NaT, pd.NaT
    
    texto = str(texto).strip()
    
    try:
        # 1. Caso: Apenas Meses (ex: "Mai–Jun 2021")
        m_mes_mes = re.match(r'^(\w+)[–-](\w+)\s+(\d{4})$', texto)
        if m_mes_mes:
            m1, m2, ano = m_mes_mes.groups()
            num_m1, num_m2, ano_int = meses_map[m1], meses_map[m2], int(ano)
            
            inicio = pd.Timestamp(year=ano_int, month=num_m1, day=1)
            _, ultimo_dia = monthrange(ano_int, num_m2)
            fim = pd.Timestamp(year=ano_int, month=num_m2, day=ultimo_dia)
            return inicio, fim

        # 2. Caso: Data única (ex: "30 Set 2022")
        m_unica = re.match(r'^(\d+)\s+(\w+)\s+(\d{4})$', texto)
        if m_unica:
            d, m, ano = m_unica.groups()
            data = pd.Timestamp(year=int(ano), month=meses_map[m], day=int(d))
            return data, data

        # 3. Caso: Intervalo com meses diferentes ou iguais
        m_intervalo = re.match(r'^(\d+)(?:\s+(\w+))?[–-](\d+)\s+(\w+)\s+(\d{4})$', texto)
        if m_intervalo:
            d1, m1, d2, m2, ano = m_intervalo.groups()
            ano_int = int(ano)
            num_m2 = meses_map[m2]
            d1_int, d2_int = int(d1), int(d2)
            
            if m1 is None:
                # Se o dia inicial for maior, cruza para o mês anterior (ex: 31-5 Abr)
                if d1_int > d2_int:
                    num_m1 = num_m2 - 1 if num_m2 > 1 else 12
                    if num_m1 == 12: 
                        ano_int -= 1
                else:
                    # Se for menor/igual, é do mesmo mês (ex: 29-31 Mar)
                    num_m1 = num_m2
            else:
                num_m1 = meses_map[m1]
                
            inicio = pd.Timestamp(year=ano_int if m1 is None and d1_int > d2_int else int(ano), month=num_m1, day=d1_int)
            fim = pd.Timestamp(year=int(ano), month=num_m2, day=d2_int)
            return inicio, fim

    except ValueError as e:
        print(f"Aviso: Data inválida encontrada no texto: '{texto}' -> {e}")
        return pd.NaT, pd.NaT

    return pd.NaT, pd.NaT

# Aplica a função no DataFrame
df[['Data_Inicio', 'Data_Fim']] = pd.DataFrame(
    df['Data(s) de Pesquisa'].apply(converter_periodo_inteligente).tolist(), 
    index=df.index
)
# %%
df.drop(
    columns=['Data(s) de Pesquisa'],
        inplace=True


)


df.to_csv(
    "data/pesquisa_2022_segundo_turno_lula_bolsonaro.csv",
    index=False,
    encoding='utf-8-sig'
)
