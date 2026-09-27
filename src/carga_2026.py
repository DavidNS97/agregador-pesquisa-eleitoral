# %%

import pandas as pd
from conexao_banco import conectar_banco

conexao = conectar_banco()

cursor = conexao.cursor()
print("conectado")
df = pd.read_csv(
    "data/pesquisa_2026_segundo_turno_lula_flavio.csv"
)

def normalizar_instituto(nome):

    nome = nome.upper().strip()

    if "DATAFOLHA" in nome:
        return "DATAFOLHA"

    if "QUAEST" in nome:
        return "QUAEST"

    if "NEXUS" in nome:
        return "NEXUS"

    if "IPESPE" in nome:
        return "IPESPE"

    if "ATLASINSTEL" in nome or "ATLASINTEL" in nome:
        return "ATLASINTEL"

    if "VERITÁ" in nome or "VERITA" in nome:
        return "VERITÁ"

    if "IPEC" in nome:
        return "IPEC"

    if "PARANÁ PESQUISAS" in nome:
        return "PARANÁ PESQUISAS"

    if "FSB" in nome:
        return "FSB"

    if "IDEIA" in nome:
        return "IDEIA"

    if "FUTURA" in nome:
        return "FUTURA"

    if "SENSUS" in nome:
        return "SENSUS"

    if "PODERDATA" in nome:
        return "PODERDATA"

    if "VOX POPULI" in nome:
        return "VOX POPULI"

    if "REAL TIME BIG DATA" in nome or "REAL TIME" in nome:
        return "REAL TIME BIG DATA"

    if "IPSOS" in nome:
        return "IPSOS"

    if "GERP" in nome:
        return "GERP"

    if "CNT/MDA" in nome or ("CNT" in nome and "MDA" in nome):
        return "CNT/MDA"

    if "BRASMARKET" in nome:
        return "BRASMARKET"

    if "MODALMAIS/FUTURA" in nome:
        return "FUTURA"

    if "PROGRESSISTAS/PARANÁ" in nome:
        return "PARANÁ PESQUISAS"

    if "EQUILÍBRIO BRASIL" in nome:
        return "EQUILÍBRIO BRASIL"

    if "GRUPO 6SIGMA" in nome:
        return "GRUPO 6SIGMA"

    if "BGC LIQUIDEZ/PARANÁ" in nome:
        return "PARANÁ PESQUISAS"

    if "RANKING BRASIL" in nome:
        return "RANKING BRASIL"

    if "PONTEIO POLÍTICA" in nome:
        return "PONTEIO POLÍTICA"

    if "DATATEMPO" in nome:
        return "DATATEMPO"

    if "DEM/IPSOS" in nome:
        return "IPSOS"

    if "REVISTA FÓRUM/OFFERWISE" in nome:
        return "OFFERWISE"

    if "PALVER" in nome:
        return "PALVER"

    if "PODERDATA/AYA" in nome:
        return "PODERDATA"

    if "DATATRENDS" in nome:
        return "DATATRENDS"

    if "INDEXA/BROADCAST" in nome or "INDEXA" in nome:
        return "INDEXA"

    if "MEIO/IDEIA" in nome:
        return "IDEIA"

    if "VOX BRASIL" in nome:
        return "VOX BRASIL"

    if "ALFA/TMC" in nome:
        return "ALFA/TMC"

    if "ALFA INTELIGÊNCIA" in nome:
        return "ALFA INTELIGÊNCIA"

    if "VETOR/ARROW" in nome:
        return "VETOR/ARROW"

    if "AMERICAN ANALYTICS" in nome:
        return "AMERICAN ANALYTICS"

    if nome == "VOX":
        return "VOX"

    if nome == "ATLAS":
        return "ATLAS"

    if nome == "ATLAS POLÍTICO":
        return "ATLAS POLÍTICO"

    return nome

for index, row in df.iterrows():

    nome_instituto = normalizar_instituto(row["Instituto de Pesquisa"])
    tamanho_amostra = row["Tamanho da Amostra"]
    margem_erro = row["Margem de erro (pontos percentuais)"]
    percentual_candidato_a = row["Flávio PL"]
    percentual_candidato_b = row["Lula PT"]
    data_inicio = row["data_inicio_pesquisa"]
    data_fim = row["data_fim_pesquisa"]

    cursor.execute(
        "SELECT id FROM institutos WHERE nome = %s",
        (nome_instituto,)
    )

    resultado = cursor.fetchone()

    if resultado is not None:
        instituto_id = resultado[0]

    else:
        cursor.execute(
            "INSERT INTO institutos (nome) VALUES(%s) RETURNING id",
            (nome_instituto,)
        )

        resultado = cursor.fetchone()
        instituto_id = resultado[0]

    cursor.execute(
        """
        INSERT INTO pesquisas (
            eleicao_id,
            candidato_a_id,
            candidato_b_id,
            amostra,
            percentual_a,
            percentual_b,
            data_inicio,
            data_fim,
            instituto_id,
            margem_erro
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (eleicao_id, instituto_id, data_inicio, data_fim)
        DO NOTHING
        """,
        (
            2,
            3,
            1,
            tamanho_amostra,
            percentual_candidato_a,
            percentual_candidato_b,
            data_inicio,
            data_fim,
            instituto_id,
            margem_erro
        )
    )

conexao.commit()

cursor.close()
conexao.close()
print("conexao encerrada")


# %%
