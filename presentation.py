import pandas as pd
import streamlit as st

from analytics import (
    resumo_financeiro,
    resumo_regiao,
    resumo_projeto,
    resumo_business,
)


def fm(v):
    return f"-${abs(v)/1_000_000:.2f}M" if v < 0 else f"${v/1_000_000:.2f}M"


def fp(v):
    return f"{v:.1f}%"


def mostrar_apresentacao(summary_fx, timecards, timecards_analysis):
    st.subheader("Apresentação do Case")


    geral = resumo_financeiro(summary_fx)
    regiao = resumo_regiao(summary_fx)
    projeto = resumo_projeto(summary_fx).dropna(subset=["Margin %", "Revenue_per_Cost"])
    business = resumo_business(summary_fx).dropna(subset=["Margin"])

    st.markdown("## Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", fm(geral["revenue"]))
    c2.metric("Total Cost", fm(geral["total_cost"]))
    c3.metric("Profit", fm(geral["profit"]))
    c4.metric("Profit Margin", fp(geral["margin"]))

    st.divider()

    st.markdown("## 1. Ferramentas escolhidas e por quê")
    st.markdown(
        """
- **Python + Pandas:** limpeza, transformação, integração e cálculos financeiros.
- **SQLite:** armazenamento local simples e reproduzível para o volume do case.
- **Streamlit:** aplicação interativa para análise e apresentação.
- **Plotly:** visualizações interativas e comparações financeiras.
- **Jupyter:** exploração inicial e validação dos cálculos.
        """
    )

    st.markdown("## 2. Como usei IA (LLMs) e como validei")
    st.markdown(
        """
A IA foi usada como apoio para estruturar hipóteses, acelerar trechos de código,
revisar abordagens de tratamento e melhorar a comunicação dos resultados.

Os resultados foram validados com operações reproduzíveis em Pandas totais antes/depois das transformações,
verificação da conversão de FX e comparação dos cálculos de Revenue,
Costs, Profit, Margin e horas trabalhadas.
        """
    )

    st.markdown("## 3. Principais desafios e como foram resolvidos")
    st.markdown(
        """
- **Moedas diferentes:** normalização para USD por moeda e mês.
- **Formato da base FX:** transformação para formato longo antes do merge.
- **Valores ausentes:** identificação e tratamento controlado.
- **Integração financeira + operacional:** conexão entre Summary e Timecards por projeto, funcionário e período.
- **Atualização recorrente:** separação entre banco, processamento, dashboard e apresentação.
        """
    )

    st.markdown("## 4. Principais insights financeiros")

    if not regiao.empty:
        best_reg = regiao.loc[regiao["Profit"].idxmax()]
        worst_reg = regiao.loc[regiao["Profit"].idxmin()]
        st.markdown(f"- **Região com maior lucro:** {best_reg['region']} ({fm(best_reg['Profit'])}).")
        st.markdown(f"- **Região com menor lucro:** {worst_reg['region']} ({fm(worst_reg['Profit'])}).")

    if not projeto.empty:
        best_proj = projeto.loc[projeto["Margin %"].idxmax()]
        worst_proj = projeto.loc[projeto["Margin %"].idxmin()]
        low_return = projeto[projeto["Revenue_per_Cost"] < 1]
        st.markdown(f"- **Projeto com maior margem:** {best_proj['project']} ({fp(best_proj['Margin %'])}).")
        st.markdown(f"- **Projeto com menor margem:** {worst_proj['project']} ({fp(worst_proj['Margin %'])}).")
        st.markdown(f"- **Projetos com retorno abaixo de US$ 1 por US$ 1 de custo:** {len(low_return)}.")
    else:
        low_return = pd.DataFrame()
        worst_proj = None

    if not business.empty:
        best_bu = business.loc[business["Profit"].idxmax()]
        worst_bu = business.loc[business["Profit"].idxmin()]
        st.markdown(f"- **Business Unit com maior lucro:** {best_bu['business_unit']} ({fm(best_bu['Profit'])}).")
        st.markdown(f"- **Business Unit com menor lucro:** {worst_bu['business_unit']} ({fm(worst_bu['Profit'])}).")
    else:
        worst_bu = None

    if timecards_analysis is not None and not timecards_analysis.empty:
        horas = (
            timecards_analysis[timecards_analysis["project"].notna()]
            .groupby("project")["hours"].sum().sort_values(ascending=False)
        )
        if not horas.empty:
            st.markdown(f"- **Projeto com maior concentração de horas:** {horas.index[0]} ({horas.iloc[0]:,.0f} horas).")

    st.markdown("## 5. Recomendação para a liderança")
    recomendacoes = []
    if worst_proj is not None:
        recomendacoes.append(f"revisar o projeto **{worst_proj['project']}**, que apresenta a menor margem")
    if worst_bu is not None:
        recomendacoes.append(f"investigar a Business Unit **{worst_bu['business_unit']}**, que apresenta o menor lucro")
    if not low_return.empty:
        recomendacoes.append("priorizar os projetos com retorno abaixo de **US$ 1,00** de receita por US$ 1,00 de custo")

    if recomendacoes:
        st.markdown(
            "Minha recomendação é **" + "; ".join(recomendacoes) + "**. "
            "A liderança deve avaliar preço, escopo, estrutura de equipe, horas alocadas e custos não salariais antes de decidir entre corrigir, renegociar, redimensionar ou descontinuar atividades de baixo retorno."
        )

    st.markdown("## 6. Atualização mensal e adaptação a novos pedidos")
    st.markdown(
        """
O fluxo mensal foi desenhado para reduzir trabalho manual:

**CSV/Excel → validação automática → SQLite → processamento → dashboard → apresentação**

As regras de tratamento ficam em `processing.py`, o banco em `database.py`,
a tela de atualização em `data_upload.py`, as análises visuais em `dashboard.py`
e esta apresentação em `presentation.py`.

Assim, uma nova base pode ser incorporada sem reconstruir a análise,
e novos pedidos da liderança podem ser atendidos adicionando novos cálculos
ou visualizações sobre a mesma camada de dados tratada.
        """
    )
