# %%
import pandas as pd
from conexao_banco import conectar_banco

conexao = conectar_banco()

cursor = conexao.cursor()
print("conectado")
df = pd.read_csv(
    "../data/pesquisa_2022_segundo_turno_lula_bolsonaro.csv"
)

for index, row in df.iterrows():

    nome_instituto = row["Instituto de Pesquisa"]
    tamanho_amostra = row["Tamanho da Amostra"]
    percentual_candidato_a = row["Bolsonaro PL"]
    percentual_candidato_b = row["Lula PT"]
    data_inicio = row["Data_Inicio"]
    data_fim = row["Data_Fim"]

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
            1,
            2,
            1,
            tamanho_amostra,
            percentual_candidato_a,
            percentual_candidato_b,
            data_inicio,
            data_fim,
            instituto_id,
            None
        )
    )

conexao.commit()

cursor.close()
conexao.close()
print("conexao encerrada")


# %%
