import streamlit as st
import pandas as pd
import plotly.express as px

from conexao_banco import conectar_banco
from estatisticas import executar_modelo


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Agregador Eleitoral 2026",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>

    /* Nome dos institutos */
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label p {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        font-size: 13px !important;
        line-height: 1.2 !important;
    }

    /* Checkbox selecionado */
    [data-testid="stCheckbox"] input:checked + div {
        background-color: #0066ff !important;
        border-color: #0066ff !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# CONSULTAS SQL
# ============================================================

CONSULTA_2026 = """
SELECT
    te.ano AS ano,
    ti.nome AS instituto,
    tp.amostra AS amostra,
    tc1.nome AS candidato_a,
    tc2.nome AS candidato_b,
    1.0 * tp.percentual_a /
        (tp.percentual_a + tp.percentual_b) AS percentual_a,
    1.0 * tp.percentual_b /
        (tp.percentual_a + tp.percentual_b) AS percentual_b,
    tp.data_inicio AS data_inicio,
    tp.data_fim AS data_fim,
    tp.margem_erro AS margem_erro
FROM pesquisas AS tp
INNER JOIN eleicoes AS te
    ON tp.eleicao_id = te.id
INNER JOIN institutos AS ti
    ON tp.instituto_id = ti.id
INNER JOIN candidatos AS tc1
    ON tp.candidato_a_id = tc1.id
INNER JOIN candidatos AS tc2
    ON tp.candidato_b_id = tc2.id
WHERE te.ano = 2026
ORDER BY tp.data_fim DESC;
"""

CONSULTA_2022 = """
SELECT
    te.ano AS ano,
    ti.nome AS instituto,
    tp.amostra AS amostra,
    tc1.nome AS candidato_a,
    tc2.nome AS candidato_b,

    1.0 * tp.percentual_a /
        (tp.percentual_a + tp.percentual_b) AS percentual_a,

    1.0 * tp.percentual_b /
        (tp.percentual_a + tp.percentual_b) AS percentual_b,

    (
        1.0 * tp.percentual_a /
        (tp.percentual_a + tp.percentual_b)
    ) - 0.491 AS erro_a,

    (
        1.0 * tp.percentual_b /
        (tp.percentual_a + tp.percentual_b)
    ) - 0.509 AS erro_b,

    tp.data_inicio AS data_inicio,
    tp.data_fim AS data_fim,
    tp.margem_erro AS margem_erro

FROM pesquisas AS tp

INNER JOIN eleicoes AS te
    ON tp.eleicao_id = te.id

INNER JOIN institutos AS ti
    ON tp.instituto_id = ti.id

INNER JOIN candidatos AS tc1
    ON tp.candidato_a_id = tc1.id

INNER JOIN candidatos AS tc2
    ON tp.candidato_b_id = tc2.id

WHERE te.ano = 2022

ORDER BY tp.data_fim DESC;
"""

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

@st.cache_data
def carregar_dados():

    conexao = conectar_banco()

    df_2026 = pd.read_sql(
        CONSULTA_2026,
        conexao
    )

    df_2022 = pd.read_sql(
        CONSULTA_2022,
        conexao
    )

    conexao.close()

    return df_2026, df_2022


df_2026, df_2022 = carregar_dados()


# ============================================================
# TÍTULO
# ============================================================

st.title("Agregador de Pesquisas Eleitorais — Presidência 2026")

st.caption(
    "Aqui você pode acompanhar como as pesquisas de segundo turno evoluem "
    "ao longo do tempo. O modelo combina os resultados das pesquisas, dá "
    "mais peso às informações recentes e projeta a tendência até a eleição. "
    "A partir dessa projeção e da incerteza das pesquisas, são simulados "
    "100.000 cenários para estimar a probabilidade de cada candidato "
    "ultrapassar 50% dos votos. Use os filtros ao lado para explorar "
    "diferentes cenários."
)


# ============================================================
# FILTROS
# ============================================================

st.sidebar.header("Configurações do modelo")

st.sidebar.subheader("Pesquisas consideradas")

institutos = sorted(
    df_2026["instituto"].dropna().unique()
)

selecionar_todas = st.sidebar.checkbox(
    "Selecionar todas",
    value=True
)

pesquisas_selecionadas = []

coluna_1, coluna_2 = st.sidebar.columns(2)

for i, instituto in enumerate(institutos):

    coluna = coluna_1 if i % 2 == 0 else coluna_2

    selecionado = coluna.checkbox(
        instituto,
        value=selecionar_todas,
        key=f"instituto_{instituto}"
    )

    if selecionado:
        pesquisas_selecionadas.append(instituto)

st.sidebar.divider()

usar_ajuste = st.sidebar.toggle(
    "Considerar erro histórico de 2022",
    value=False
)

meia_vida = st.sidebar.slider(
    "Meia-vida da recência (dias)",
    min_value=3,
    max_value=60,
    value=27,
    step=1
)

st.sidebar.caption(
    "A meia-vida controla o quanto o modelo prioriza pesquisas recentes. Quanto menor o número de dias, mais rapidamente pesquisas antigas perdem peso. Quanto maior, maior a influência das pesquisas anteriores"
)
# ============================================================
# EXECUÇÃO DO MODELO
# ============================================================

resultado = executar_modelo(
    df_2026,
    df_2022,
    pesquisas_selecionadas=pesquisas_selecionadas,
    usar_ajuste=usar_ajuste,
    meia_vida=meia_vida
)


serie = resultado["serie"]
projecao = resultado["projecao"]

probabilidade_a = resultado["probabilidade_a"]
probabilidade_b = resultado["probabilidade_b"]

simulacoes = resultado["simulacoes"]

pesquisas_consideradas = resultado[
    "pesquisas_consideradas"
]

# ============================================================
# PROBABILIDADE
# ============================================================

st.subheader("Probabilidade do modelo")

col1, col2, col3 = st.columns([1, 2, 1])


with col1:

    html_flavio = f"""
    <div style="
        text-align: center;
        padding-top: 75px;
    ">
        <div style="
            font-size: 20px;
            font-weight: 600;
        ">
            Flávio Bolsonaro
        </div>

        <div style="
            font-size: 42px;
            font-weight: 700;
            margin-top: 8px;
        ">
            {probabilidade_a:.1%}
        </div>
    </div>
    """

    st.html(html_flavio)


with col2:

    blocos_a = round(probabilidade_a * 100)

    html_blocos = """
    <div style="
        display: grid;
        grid-template-columns: repeat(10, 28px);
        grid-template-rows: repeat(10, 28px);
        gap: 4px;
        width: fit-content;
        margin: 0 auto;
    ">
    """

    for i in range(100):

        if i < blocos_a:

            html_blocos += """
            <div style="
                width: 28px;
                height: 28px;
                background-color: #0066ff;
                border-radius: 4px;
            "></div>
            """

        else:

            html_blocos += """
            <div style="
                width: 28px;
                height: 28px;
                background-color: #ff3333;
                border-radius: 4px;
            "></div>
            """

    html_blocos += "</div>"

html_blocos += """
    <div style="
        text-align: center;
        margin-top: 10px;
        font-size: 13px;
        color: #666;
    ">
        Cada bloco representa 1.000 das 100.000 simulações.
    </div>
</div>
"""

st.html(html_blocos)



with col3:

    html_lula = f"""
    <div style="
        text-align: center;
        padding-top: 75px;
    ">
        <div style="
            font-size: 20px;
            font-weight: 600;
        ">
            Lula
        </div>

        <div style="
            font-size: 42px;
            font-weight: 700;
            margin-top: 8px;
        ">
            {probabilidade_b:.1%}
        </div>
    </div>
    """

    st.html(html_lula)



# ============================================================
# GRÁFICO
# ============================================================

st.subheader("Evolução das pesquisas")

historico = serie[
    [
        "data_referencia",
        "percentual_a",
        "percentual_b"
    ]
].copy()

historico["tipo"] = "Histórico"

futuro = projecao[
    [
        "data_referencia",
        "percentual_a",
        "percentual_b"
    ]
].copy()

futuro["tipo"] = "Projeção"


fig = px.line(
    historico,
    x="data_referencia",
    y="percentual_a",
    labels={
        "data_referencia": "Data",
        "percentual_a": "Percentual"
    }
)

fig.update_traces(
    name="Flávio Bolsonaro",
    line=dict(color="blue")
)

fig.add_scatter(
    x=historico["data_referencia"],
    y=historico["percentual_b"],
    mode="lines",
    name="Lula",
    line=dict(color="red")
)

fig.add_scatter(
    x=futuro["data_referencia"],
    y=futuro["percentual_a"],
    mode="lines",
    name="Projeção Flávio",
    line=dict(
        color="blue",
        dash="dash"
    )
)

fig.add_scatter(
    x=futuro["data_referencia"],
    y=futuro["percentual_b"],
    mode="lines",
    name="Projeção Lula",
    line=dict(
        color="red",
        dash="dash"
    )
)

# Linha de 50%
fig.add_hline(
    y=0.50,
    line_dash="dot",
    annotation_text="50%"
)

fig.update_yaxes(
    tickformat=".0%",
    range=[0, 1]
)

fig.update_layout(
    height=600,
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# TABELA DE PESQUISAS
# ============================================================

st.subheader("Pesquisas consideradas no modelo")

colunas_tabela = [
    "instituto",
    "data_fim",
    "amostra",
    "percentual_a",
    "percentual_b",
    "margem_erro"
]

tabela = pesquisas_consideradas[
    colunas_tabela
].copy()

tabela["percentual_a"] = (
    tabela["percentual_a"]
    .map(lambda x: f"{x:.1%}")
)

tabela["percentual_b"] = (
    tabela["percentual_b"]
    .map(lambda x: f"{x:.1%}")
)

tabela["data_fim"] = pd.to_datetime(
    tabela["data_fim"]
)

tabela = tabela.sort_values(
    "data_fim",
    ascending=False
)

tabela["data_fim"] = tabela["data_fim"].dt.strftime(
    "%d/%m/%Y"
)

tabela = tabela.rename(
    columns={
        "instituto": "Instituto",
        "data_fim": "Data",
        "amostra": "Amostra",
        "percentual_a": "% FLÁVIO (2T)",
        "percentual_b": "% LULA (2T)",
        "margem_erro": "Margem de erro"
    }
)

st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True
)