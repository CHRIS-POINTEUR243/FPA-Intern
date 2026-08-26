import pandas as pd
import streamlit as st

from database import carregar_banco
from processing import preparar_dados
from dashboard import mostrar_visao_geral, mostrar_regiao, mostrar_pfb
from data_upload import mostrar_upload_dados
from presentation import mostrar_apresentacao


st.set_page_config(
    page_title="FP&A - Análise de Empresa Multinacional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data
def carregar_dados():
    summary, fx, timecards = carregar_banco()
    return preparar_dados(summary, fx, timecards)


summary_fx, timecards, timecards_analysis = carregar_dados()

DATA_INICIAL = pd.Timestamp("2024-01-01")
DATA_FINAL = pd.Timestamp("2025-12-31")
summary_fx = summary_fx[
    (summary_fx["date"] >= DATA_INICIAL)
    & (summary_fx["date"] <= DATA_FINAL)
].copy()


st.title("FP&A - Análise de Empresa Multinacional")
st.write(
    "Análise financeira e operacional integrada de uma empresa multinacional, "
    "com foco em receita, custos, regiões, projetos, funcionários, "
    "Business Units e alocação de horas."
)


with st.expander("Dados Financeiros da Empresa", expanded=False):
    st.subheader("Lançamentos Financeiros")
    st.dataframe(summary_fx.head(10), use_container_width=True, hide_index=True)
    st.caption(f"Total de registros financeiros: {len(summary_fx):,}")

    if not summary_fx.empty:
        st.caption(
            "Período financeiro: "
            f"{summary_fx['date'].min().strftime('%d/%m/%Y')} até "
            f"{summary_fx['date'].max().strftime('%d/%m/%Y')}"
        )

    st.divider()
    st.subheader("Horas Apontadas por Funcionário")
    st.dataframe(timecards.head(10), use_container_width=True, hide_index=True)
    st.caption(f"Total de registros de Timecards: {len(timecards):,}")


tabs = st.tabs([
    "Visão Geral",
    "Região",
    "PFB",
    "Carregar Dados",
    "Apresentação",
])

with tabs[0]:
    mostrar_visao_geral(summary_fx)

with tabs[1]:
    mostrar_regiao(summary_fx)

with tabs[2]:
    mostrar_pfb(summary_fx, timecards, timecards_analysis)

with tabs[3]:
    mostrar_upload_dados()

with tabs[4]:
    mostrar_apresentacao(summary_fx, timecards, timecards_analysis)


st.divider()
st.caption("FP&A - Análise de Empresa Multinacional")
