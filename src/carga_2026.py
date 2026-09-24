# %%

import pandas as pd
from conexao_banco import conectar_banco

conexao = conectar_banco()

cursor = conexao.cursor()
print("conectado")
df = pd.read_csv(
    "data/pesquisa_2026_segundo_turno_lula_flavio.csv"
)

for index, row in df.iterrows():

    nome_instituto = row["Instituto de Pesquisa"]
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
