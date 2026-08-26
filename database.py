import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DATABASE_DIR, "fpa.db")

ARQUIVOS_PADRAO = {
    "summary": "base_dados_ficticia_Summary.csv",
    "fx": "base_dados_ficticia_FX_.csv",
    "timecards": "base_dados_ficticia_Timecards.csv",
}


def conectar_banco():
    os.makedirs(DATABASE_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def criar_banco():
    """Cria/recria o SQLite usando os CSVs originais da pasta data."""
    os.makedirs(DATABASE_DIR, exist_ok=True)

    bases = {}
    for tabela, arquivo in ARQUIVOS_PADRAO.items():
        caminho = os.path.join(DATA_DIR, arquivo)
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        bases[tabela] = pd.read_csv(caminho, low_memory=False)

    with conectar_banco() as conn:
        for tabela, df in bases.items():
            df.to_sql(tabela, conn, if_exists="replace", index=False)


def carregar_banco():
    """Carrega as três bases brutas do SQLite."""
    if not os.path.exists(DB_PATH):
        criar_banco()

    with conectar_banco() as conn:
        summary = pd.read_sql_query("SELECT * FROM summary", conn)
        fx = pd.read_sql_query("SELECT * FROM fx", conn)
        timecards = pd.read_sql_query("SELECT * FROM timecards", conn)

    return summary, fx, timecards


def atualizar_tabela_banco(tipo_base, novos_dados, modo="append"):
    """Atualiza summary, timecards ou fx e retorna um resumo da operação."""
    tabela = str(tipo_base).strip().lower()
    if tabela not in {"summary", "fx", "timecards"}:
        raise ValueError("tipo_base deve ser summary, fx ou timecards.")
    if modo not in {"append", "replace"}:
        raise ValueError("modo deve ser append ou replace.")

    novos_dados = novos_dados.copy()

    with conectar_banco() as conn:
        try:
            atual = pd.read_sql_query(f'SELECT * FROM "{tabela}"', conn)
        except Exception:
            atual = pd.DataFrame()

        linhas_antes = len(atual)
        linhas_recebidas = len(novos_dados)

        if modo == "replace":
            final = novos_dados.copy()
        else:
            final = pd.concat([atual, novos_dados], ignore_index=True, sort=False)
            final = final.drop_duplicates().reset_index(drop=True)

        linhas_final = len(final)
        duplicados_evitados = max(
            0,
            linhas_antes + linhas_recebidas - linhas_final,
        )

        final.to_sql(tabela, conn, if_exists="replace", index=False)

    return {
        "tabela": tabela,
        "modo": modo,
        "linhas_antes": linhas_antes,
        "linhas_recebidas": linhas_recebidas,
        "linhas_final": linhas_final,
        "duplicados_evitados": duplicados_evitados,
    }


if __name__ == "__main__":
    criar_banco()
    print("Banco criado/atualizado com sucesso.")
