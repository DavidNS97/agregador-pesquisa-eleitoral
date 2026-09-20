# %%
import pandas as pd
import requests

url = "https://pt.wikipedia.org/wiki/Pesquisas_de_opini%C3%A3o_para_a_elei%C3%A7%C3%A3o_presidencial_no_Brasil_em_2026"


html = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
).text

tabelas = pd.read_html(html)

# %%
tabelas[5].columns.tolist()
# %%
df = tabelas[5]
df.columns[4][1]
# %%
nome_coluna = []
for colunas_df in df.columns.tolist():
     nome_coluna.append(colunas_df[1])

df.columns = nome_coluna
#
# %%
df.drop(columns=['Indecisos e Absentos', 'Vantagem'],
        inplace=True

        )

# %%
print(df.info()) 

# %%
df['Margem de erro (pontos percentuais)'].unique()# %%

# %%
pd.to_numeric(
    df['Margem de erro (pontos percentuais)'],
    errors='coerce'
)

# %%
df['Tamanho da Amostra'] = df['Tamanho da Amostra'].str.replace(r'\s+', '', regex=True)
df['Lula PT'] = df['Lula PT'].str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
df['Flávio PL'] = df['Flávio PL'].str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
df['Contratante / Pesquisa Número de identificação'] = df['Contratante / Pesquisa Número de identificação'].str.replace(r'\[.*?\]', '', regex=True)

df.head
# %%
#filtrando valores nao numericos ( rodapes entre linhas)
valido = pd.to_numeric(
    df['Tamanho da Amostra'],
    errors='coerce'
).notna()
df = df[valido].copy()
# %%
#transformando valores para numerico
colunas_numericas = [
    'Tamanho da Amostra',
    'Margem de erro (pontos percentuais)',
    'Lula PT',
    'Flávio PL'
]

df[colunas_numericas] = df[colunas_numericas].apply(pd.to_numeric)

df['Margem de erro (pontos percentuais)'] = df['Margem de erro (pontos percentuais)'] / 10
df['Lula PT'] = df['Lula PT'] / 100
df['Flávio PL'] = df['Flávio PL'] / 100
# %%
meses = {
    'Jan': '01',
    'Fev': '02',
    'Mar': '03',
    'Abr': '04',
    'Mai': '05',
    'Jun': '06',
    'Jul': '07',
    'Ago': '08',
    'Set': '09',
    'Out': '10',
    'Nov': '11',
    'Dez': '12'
}
for mes, numero in meses.items():
    df['Data(s) de Pesquisa'] = df['Data(s) de Pesquisa'].str.replace(mes, numero)

df['data_inicio_pesquisa'] = df['Data(s) de Pesquisa'].str.split(r'[-–]').str[0].str.strip()
df['data_fim_pesquisa'] = df['Data(s) de Pesquisa'].str.split(r'[-–]').str[1].str.strip()

for coluna in ['data_inicio_pesquisa', 'data_fim_pesquisa']:
    df[coluna] = df[coluna] + ' 2026'
    df[coluna] = df[coluna].str.replace(' ', '-', regex=False)
    df[coluna] = pd.to_datetime(
        df[coluna],
        format='%d-%m-%Y')


# %%
df.drop(
    columns=['Data(s) de Pesquisa'],
    inplace=True
)
df.head()

# %%
df.to_csv("C:/Users/david/OneDrive/Desktop/Portifolio/agregador-pesquisa-eleitoral/data/_pesquisa_2026_segundo_turno_lula_flavio.csv",
          index= False)
# %%

# %%
df.head()
# %%
