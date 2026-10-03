import pandas as pd
import numpy as np
from scipy.stats import t



# ============================================================
# CÁLCULO DO VIÉS HISTÓRICO
# ============================================================

def calcular_vies(df, df_2022):

    vies_a_global = (
        df_2022["erro_a"].mean()
    )

    vies_b_global = (
        df_2022["erro_b"].mean()
    )

    resultados_vies = []

    for _, linha in df.iterrows():

        instituto = linha["instituto"]
        data_referencia = linha["data_fim"]

        historico_pesquisa = df_2022[
            df_2022["instituto"] == instituto
        ].copy()

        if not historico_pesquisa.empty:

            historico_pesquisa["distancia"] = abs(
                historico_pesquisa["data_fim"]
                - data_referencia
            )

            historico_pesquisa = (
                historico_pesquisa
                .sort_values("distancia")
            )

            proximos = (
                historico_pesquisa
                .head(3)
            )

            vies_a = (
                proximos["erro_a"].mean()
            )

            vies_b = (
                proximos["erro_b"].mean()
            )

        else:

            vies_a = vies_a_global
            vies_b = vies_b_global

        resultados_vies.append({

            "data_fim": data_referencia,

            "instituto": instituto,

            "vies_a": vies_a,

            "vies_b": vies_b
        })

    return pd.DataFrame(
        resultados_vies
    )


# ============================================================
# AGREGAÇÃO MÓVEL DE 7 DIAS
# ============================================================

def agregar_data(
    df,
    data_referencia,
    coluna_a,
    coluna_b
):

    data_referencia = pd.Timestamp(
        data_referencia
    )

    # Janela móvel de 7 dias
    inicio = (
        data_referencia
        - pd.Timedelta(days=6)
    )

    pesquisas = df[
        (df["data_fim"] >= inicio) &
        (df["data_fim"] <= data_referencia)
    ].copy()

    if pesquisas.empty:
        return None

    # Dias de distância da referência
    pesquisas["dias_atras"] = (
        data_referencia
        - pesquisas["data_fim"]
    ).dt.days

    # Peso de recência
    pesquisas["peso_recencia"] = (
        1
        - pesquisas["dias_atras"] / 8
    )

    # Peso da amostra
    pesquisas["peso_amostra"] = np.sqrt(
        pesquisas["amostra"]
    )

    # Peso final
    pesquisas["peso"] = (
        pesquisas["peso_recencia"]
        * pesquisas["peso_amostra"]
    )

    # Normalização dos pesos
    pesquisas["peso_normalizado"] = (
        pesquisas["peso"]
        / pesquisas["peso"].sum()
    )

    # Contribuição de cada pesquisa
    pesquisas["contribuicao_a"] = (
        pesquisas["peso_normalizado"]
        * pesquisas[coluna_a]
    )

    pesquisas["contribuicao_b"] = (
        pesquisas["peso_normalizado"]
        * pesquisas[coluna_b]
    )

    # Sigma individual
    pesquisas["sigma"] = (
        pesquisas["margem_erro"]
        / 100
        / 1.96
    )

    # Resultado agregado
    resultado_a = (
        pesquisas["contribuicao_a"].sum()
    )

    resultado_b = (
        pesquisas["contribuicao_b"].sum()
    )

    # Variância da margem de erro agregada
    variancia_agregacao = (
        (
            pesquisas["peso_normalizado"] ** 2
            * pesquisas["sigma"] ** 2
        ).sum()
    )

    sigma_margem_erro_agregado = np.sqrt(
        variancia_agregacao
    )

    # Dispersão dos vieses históricos
    sigma_vies_agregado = (
        pesquisas["vies_a"].std()
    )

    # Sigma total
    sigma_agregado = np.sqrt(
        sigma_margem_erro_agregado ** 2
        + sigma_vies_agregado ** 2
    )

    return {

        "data_referencia": data_referencia,

        "percentual_a": resultado_a,

        "percentual_b": resultado_b,

        "sigma_agregado": sigma_agregado
    }


# ============================================================
# GERA SÉRIE AGREGADA
# ============================================================

def gerar_serie(
    df,
    coluna_a,
    coluna_b
):

    datas = pd.date_range(
        df["data_fim"].min(),
        df["data_fim"].max(),
        freq="D"
    )

    resultados = []

    for data in datas:

        resultado = agregar_data(
            df,
            data,
            coluna_a,
            coluna_b
        )

        if resultado is not None:

            resultados.append(
                resultado
            )

    serie = pd.DataFrame(
        resultados
    )

    if serie.empty:

        raise ValueError(
            "Não foi possível gerar a série agregada."
        )

    return serie


# ============================================================
# REGRESSÃO + PROJEÇÃO
# ============================================================

def gerar_projecao(
    serie,
    meia_vida,
    data_final
):

    # --------------------------------------------------------
    # PESOS DA REGRESSÃO
    # --------------------------------------------------------

    serie["dias_atras"] = (
        serie["data_referencia"].max()
        - serie["data_referencia"]
    ).dt.days

    serie["peso_regressao"] = (
        0.5 ** (
            serie["dias_atras"]
            / meia_vida
        )
    )

    # --------------------------------------------------------
    # REGRESSÃO PONDERADA
    # --------------------------------------------------------

    serie["X"] = (
        serie["data_referencia"]
        - serie["data_referencia"].min()
    ).dt.days

    serie["Y_candidatoa"] = (
        serie["percentual_a"]
    )

    coef_inclinacao, coef_intercep = np.polyfit(
        serie["X"],
        serie["Y_candidatoa"],
        1,
        w=serie["peso_regressao"]
    )

    # --------------------------------------------------------
    # VALORES ESTIMADOS
    # --------------------------------------------------------

    serie["Y_estimado"] = (
        serie["X"]
        * coef_inclinacao
        + coef_intercep
    )

    # --------------------------------------------------------
    # RESÍDUOS
    # --------------------------------------------------------

    serie["residuo"] = (
        serie["Y_candidatoa"]
        - serie["Y_estimado"]
    )

    # --------------------------------------------------------
    # PROJEÇÃO
    # --------------------------------------------------------

    dias_ate_eleicao = (
        data_final
        - serie["data_referencia"].max()
    ).days

    X_futuro = range(
        serie["X"].max() + 1,
        serie["X"].max()
        + dias_ate_eleicao
        + 1
    )

    datas_futuras = pd.date_range(
        start=(
            serie["data_referencia"].max()
            + pd.Timedelta(days=1)
        ),
        end=data_final,
        freq="D"
    )

    X_futuro = np.array(
        list(X_futuro)
    )

    projecao_a = (
        X_futuro
        * coef_inclinacao
        + coef_intercep
    )

    projecao = pd.DataFrame({

        "data_referencia": datas_futuras,

        "X": X_futuro,

        "percentual_a": projecao_a,

        "percentual_b": (
            1 - projecao_a
        ),

        "tipo": "Projeção"
    })

    # --------------------------------------------------------
    # FAIXA DE INCERTEZA
    # --------------------------------------------------------

    graus_liberdade = (
        len(serie) - 2
    )

    variancia_residual = (
        (
            serie["peso_regressao"]
            * serie["residuo"] ** 2
        ).sum()
        /
        (
            serie["peso_regressao"].sum()
            - 2
        )
    )

    erro_residual = np.sqrt(
        variancia_residual
    )

    valor_t = t.ppf(
        0.975,
        graus_liberdade
    )

    margem = (
        valor_t
        * erro_residual
    )

    projecao["limite_inferior"] = (
        projecao["percentual_a"]
        - margem
    )

    projecao["limite_superior"] = (
        projecao["percentual_a"]
        + margem
    )

    return serie, projecao


# ============================================================
# MONTE CARLO
# ============================================================

def executar_monte_carlo(
    serie,
    projecao,
    numero_simulacoes=100000
):

    sigma_atual = (
        serie["sigma_agregado"].iloc[-1]
    )

    projecao_a = (
        projecao["percentual_a"].iloc[-1]
    )

    simulacoes = np.random.normal(
        loc=projecao_a,
        scale=sigma_atual,
        size=numero_simulacoes
    )

    vitorias_a = np.sum(
        simulacoes >= 0.50
    )

    probabilidade_a = (
        vitorias_a
        / numero_simulacoes
    )

    probabilidade_b = (
        1 - probabilidade_a
    )

    return (
        simulacoes,
        probabilidade_a,
        probabilidade_b
    )


# ============================================================
# MODELO PRINCIPAL
# ============================================================

def executar_modelo(
    df,
    df_2022,
    pesquisas_selecionadas=None,
    usar_ajuste=False,
    meia_vida=27
):

    data_final = pd.Timestamp(
        "2026-10-25"
    )

    # --------------------------------------------------------
    # CÓPIAS
    # --------------------------------------------------------

    df = df.copy()

    df_2022 = df_2022.copy()

    # --------------------------------------------------------
    # DATAS
    # --------------------------------------------------------

    df["data_fim"] = pd.to_datetime(
        df["data_fim"]
    )

    df_2022["data_fim"] = pd.to_datetime(
        df_2022["data_fim"]
    )

    # --------------------------------------------------------
    # FILTRO DAS PESQUISAS
    # --------------------------------------------------------

    if pesquisas_selecionadas:

        df = df[
            df["instituto"].isin(
                pesquisas_selecionadas
            )
        ].copy()

    if df.empty:

        raise ValueError(
            "Nenhuma pesquisa foi selecionada."
        )

    # --------------------------------------------------------
    # VIÉS HISTÓRICO
    # --------------------------------------------------------

    df_ajustado = calcular_vies(
        df,
        df_2022
    )

    # --------------------------------------------------------
    # JUNTA VIÉS + PESQUISAS
    # --------------------------------------------------------

    df_mesclado = df_ajustado.merge(
        df,
        on=[
            "instituto",
            "data_fim"
        ]
    )

    # --------------------------------------------------------
    # APLICA VIÉS
    # --------------------------------------------------------

    df_mesclado[
        "percentual_a_ajustado"
    ] = (
        df_mesclado["percentual_a"]
        - df_mesclado["vies_a"]
    )

    df_mesclado[
        "percentual_b_ajustado"
    ] = (
        df_mesclado["percentual_b"]
        - df_mesclado["vies_b"]
    )

    # --------------------------------------------------------
    # ESCOLHE PERCENTUAIS
    # --------------------------------------------------------

    if usar_ajuste:

        coluna_a = (
            "percentual_a_ajustado"
        )

        coluna_b = (
            "percentual_b_ajustado"
        )

    else:

        coluna_a = "percentual_a"

        coluna_b = "percentual_b"

    # --------------------------------------------------------
    # SÉRIE
    # --------------------------------------------------------

    serie = gerar_serie(
        df_mesclado,
        coluna_a,
        coluna_b
    )

    # --------------------------------------------------------
    # PROJEÇÃO
    # --------------------------------------------------------

    serie, projecao = gerar_projecao(
        serie,
        meia_vida,
        data_final
    )

    # --------------------------------------------------------
    # MONTE CARLO
    # --------------------------------------------------------

    (
        simulacoes,
        probabilidade_a,
        probabilidade_b
    ) = executar_monte_carlo(
        serie,
        projecao
    )

    # --------------------------------------------------------
    # RETORNO
    # --------------------------------------------------------

    return {

        "serie": serie,

        "projecao": projecao,

        "probabilidade_a":
            probabilidade_a,

        "probabilidade_b":
            probabilidade_b,

        "simulacoes":
            simulacoes,

        "pesquisas_consideradas":
            df_mesclado
    }