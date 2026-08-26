import streamlit as st
import plotly.express as px

from analytics import (
    resumo_financeiro,
    evolucao_mensal,
    resumo_regiao,
    resumo_projeto,
    resumo_business,
    analise_funcionarios,
)


def format_usd(v):
    return f"-${abs(v):,.0f}" if v < 0 else f"${v:,.0f}"


def format_millions(v):
    return f"-${abs(v)/1_000_000:.2f}M" if v < 0 else f"${v/1_000_000:.2f}M"


def mostrar_visao_geral(summary_fx):
    k = resumo_financeiro(summary_fx)
    evolucao = evolucao_mensal(summary_fx)

    st.subheader("Visão Geral")
    st.caption("Resumo financeiro dos principais indicadores da empresa em USD.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue Total", format_usd(k["revenue"]), format_millions(k["revenue"]))
    c2.metric("Budget Total", format_usd(k["budget"]), format_millions(k["budget"]))
    c3.metric("Wages Cost Total", format_usd(k["wages"]), format_millions(k["wages"]))
    c4.metric("Other Costs Total", format_usd(k["other"]), format_millions(k["other"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Profit Total", format_usd(k["profit"]), format_millions(k["profit"]))
    c6.metric("Profit Margin", f"{k['margin']:.2f}%")
    c7.metric("Total Cost", format_usd(k["total_cost"]), format_millions(k["total_cost"]))
    c8.metric("Budget Attainment", f"{k['attainment']:.2f}%", f"{k['budget_variance_pct']:+.2f}%")

    grafico, tabela = st.columns([3, 1], gap="medium")

    with grafico:
        st.markdown("### Evolução de Receitas e Custos ao Longo do Tempo")
        st.caption("Revenue vs Total Costs — USD Millions.")
        long = evolucao[["Month", "Revenue", "Total Costs"]].melt(
            id_vars="Month", value_vars=["Revenue", "Total Costs"],
            var_name="Financial Metric", value_name="USD Millions"
        )
        fig = px.line(long, x="Month", y="USD Millions", color="Financial Metric", markers=True)
        for trace in fig.data:
            trace.update(line=dict(width=3), marker=dict(size=7))
        meses = evolucao["Month"].tolist()
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=meses,
                         tickmode="array", tickvals=meses, ticktext=meses, tickangle=-45)
        maximo = long["USD Millions"].max()
        fig.update_yaxes(title="USD Millions", range=[1.0, maximo + 0.20], dtick=0.20,
                         ticksuffix="M", showgrid=True)
        fig.update_layout(height=430, hovermode="x unified",
                          legend=dict(orientation="h", y=1.02, x=0),
                          margin=dict(l=10, r=10, t=40, b=70))
        st.plotly_chart(fig, use_container_width=True)

    with tabela:
        st.markdown("### Monthly Financial Data")
        st.caption("USD Millions.")
        st.dataframe(
            evolucao[["Month", "Revenue", "Wages Cost", "Other Costs", "Total Costs"]],
            use_container_width=True, hide_index=True, height=430,
            column_config={
                "Revenue": st.column_config.NumberColumn("Revenue", format="$%.2fM"),
                "Wages Cost": st.column_config.NumberColumn("Wages", format="$%.2fM"),
                "Other Costs": st.column_config.NumberColumn("Other", format="$%.2fM"),
                "Total Costs": st.column_config.NumberColumn("Total", format="$%.2fM"),
            },
        )


def mostrar_regiao(summary_fx):
    reg = resumo_regiao(summary_fx)
    st.subheader("Análise por Região")
    st.caption("Principais indicadores financeiros e comparação entre regiões.")

    hp = reg.loc[reg["Profit"].idxmax()]
    lp = reg.loc[reg["Profit"].idxmin()]
    hm = reg.loc[reg["Profit Margin"].idxmax()]
    lm = reg.loc[reg["Profit Margin"].idxmin()]
    hc = reg.loc[reg["Total Cost"].idxmax()]
    lc = reg.loc[reg["Total Cost"].idxmin()]

    a, b, c = st.columns(3)
    a.metric("Highest Profit Region", hp["region"], format_millions(hp["Profit"]))
    b.metric("Lowest Profit Region", lp["region"], format_millions(lp["Profit"]))
    c.metric("Highest Margin Region", hm["region"], f"{hm['Profit Margin']:.2f}%")
    d, e, f = st.columns(3)
    d.metric("Lowest Margin Region", lm["region"], f"{lm['Profit Margin']:.2f}%")
    e.metric("Highest Cost Region", hc["region"], format_millions(hc["Total Cost"]))
    f.metric("Lowest Cost Region", lc["region"], format_millions(lc["Total Cost"]))

    metrics = reg[["region", "Budget", "Revenue", "Wages Cost", "Other Costs"]].copy()
    for col in ["Budget", "Revenue", "Wages Cost", "Other Costs"]:
        metrics[col] /= 1_000_000
    metrics["Total"] = metrics[["Budget", "Revenue", "Wages Cost", "Other Costs"]].sum(axis=1)
    metrics = metrics.sort_values("Total", ascending=False).drop(columns="Total")
    ordem = metrics["region"].tolist()
    long = metrics.melt(id_vars="region", var_name="Indicator", value_name="USD Millions")
    long["Label"] = long["USD Millions"].map(lambda x: f"{x:.1f}M")

    revenue = reg[["region", "Revenue"]].sort_values("Revenue", ascending=False).copy()
    revenue["Revenue"] /= 1_000_000

    left, right = st.columns([3, 1], gap="medium")
    with left:
        st.markdown("### Financial Metrics by Region")
        fig = px.bar(long, x="region", y="USD Millions", color="Indicator", barmode="group", text="Label",
                     category_orders={"region": ordem})
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(title="USD Millions", rangemode="tozero")
        fig.update_layout(height=400, legend=dict(orientation="h", y=1.02, x=0))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Revenue by Region")
        fig = px.bar(revenue, x="Revenue", y="region", orientation="h", text="Revenue")
        fig.update_traces(texttemplate="%{x:.1f}M", textposition="outside", cliponaxis=False)
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    profit = reg[["region", "Profit"]].sort_values("Profit", ascending=False).copy()
    profit["Profit Millions"] = profit["Profit"] / 1_000_000
    profit["Label"] = profit["Profit Millions"].map(lambda x: f"{x:.2f}M")

    margem = reg[["region", "Profit Margin"]].rename(columns={"Profit Margin": "Margin"})
    margem = margem.sort_values("Margin", ascending=False)
    margem["Label"] = margem["Margin"].map(lambda x: f"{x:.1f}%")
    cores = ["#16A34A" if x >= 0 else "#DC2626" for x in margem["Margin"]]

    left, right = st.columns([3, 1], gap="medium")
    with left:
        st.markdown("### Profit by Region")
        fig = px.bar(profit, x="region", y="Profit Millions", text="Label")
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.add_hline(y=0, line_width=1)
        fig.update_yaxes(title="USD Millions", ticksuffix="M")
        fig.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Margin by Region")
        fig = px.bar(margem, x="region", y="Margin", text="Label")
        fig.update_traces(marker_color=cores, textposition="outside", cliponaxis=False)
        fig.add_hline(y=0, line_width=1)
        fig.update_xaxes(tickangle=-45, tickfont=dict(size=9))
        fig.update_yaxes(title="Margin (%)", ticksuffix="%")
        fig.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def mostrar_pfb(summary_fx, timecards, timecards_analysis):
    st.subheader("PFB - Projetos, Funcionários e Business Units")
    st.caption("Análises financeiras e operacionais detalhadas.")

    # PROJETOS
    st.markdown("## Projetos")
    proj = resumo_projeto(summary_fx)
    validos = proj[proj["Revenue"].ne(0)].dropna(subset=["Margin %", "Revenue_per_Cost"]).copy()
    melhores = validos.nlargest(5, "Margin %").sort_values("Margin %", ascending=False)
    piores = validos.nsmallest(5, "Margin %").sort_values("Margin %", ascending=True)

    c1, c2 = st.columns(2, gap="medium")
    for container, df, titulo in [
        (c1, melhores, "5 Projects with Highest Margin"),
        (c2, piores, "5 Projects with Lowest Margin"),
    ]:
        with container:
            st.markdown(f"### {titulo}")
            temp = df.copy()
            temp["Label"] = temp["Margin %"].map(lambda x: f"{x:.1f}%")
            cores = ["#16A34A" if x >= 0 else "#DC2626" for x in temp["Margin %"]]
            fig = px.bar(temp, x="project", y="Margin %", text="Label")
            fig.update_traces(marker_color=cores, textposition="outside", cliponaxis=False)
            fig.add_hline(y=0, line_width=1)
            fig.update_xaxes(tickangle=-45)
            fig.update_yaxes(title="Margin (%)", ticksuffix="%")
            fig.update_layout(height=430, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Project Return Analysis")
    retorno = validos.sort_values("Revenue_per_Cost", ascending=True).copy()
    tabela = retorno[["project", "Revenue", "Total Cost", "Profit", "Revenue_per_Cost", "Margin %"]].copy()
    tabela[["Revenue", "Total Cost", "Profit"]] /= 1_000_000
    graf = retorno[["project", "Revenue_per_Cost"]].copy()
    graf["Label"] = graf["Revenue_per_Cost"].map(lambda x: f"${x:.2f}")
    cores = ["#DC2626" if x < 1 else "#16A34A" for x in graf["Revenue_per_Cost"]]

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown("#### Project Return Data")
        st.dataframe(tabela, use_container_width=True, hide_index=True, height=430,
                     column_config={
                         "Revenue": st.column_config.NumberColumn("Revenue", format="$%.2fM"),
                         "Total Cost": st.column_config.NumberColumn("Total Costs", format="$%.2fM"),
                         "Profit": st.column_config.NumberColumn("Profit", format="$%.2fM"),
                         "Revenue_per_Cost": st.column_config.NumberColumn("Return", format="$%.2f"),
                         "Margin %": st.column_config.NumberColumn("Margin", format="%.1f%%"),
                     })
    with right:
        st.markdown("#### Return by Project")
        fig = px.bar(graf, x="Revenue_per_Cost", y="project", orientation="h", text="Label")
        fig.update_traces(marker_color=cores, textposition="outside", cliponaxis=False)
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_xaxes(title="Revenue per US$ 1 Cost", tickprefix="$", tickformat=".2f")
        fig.add_vline(x=1, line_width=2, line_dash="dash", annotation_text="$1.00")
        fig.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # FUNCIONÁRIOS
    st.divider()
    st.markdown("## Funcionários")
    projetos_funcionario, analise, projetos_horas, custo_hora_mes = analise_funcionarios(
        summary_fx, timecards, timecards_analysis
    )
    st.markdown("### Employee Projects")
    st.dataframe(projetos_funcionario.head(10), use_container_width=True, hide_index=True,
                 column_config={"employee_id": "Employee", "project": "Projects"})

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown("### Highest Employee Cost per Hour")
        st.dataframe(analise.head(10), use_container_width=True, hide_index=True, height=430,
                     column_config={
                         "wages_cost": st.column_config.NumberColumn("Wages Cost", format="$%.2f"),
                         "total_hours": st.column_config.NumberColumn("Hours", format="%.1f"),
                         "cost_per_hour": st.column_config.NumberColumn("Cost / Hour", format="$%.2f"),
                     })
    with right:
        st.markdown("### Projects with Most Worked Hours")
        temp = projetos_horas.copy()
        temp["Label"] = temp["total_hours"].map(lambda x: f"{x:,.0f}h")
        fig = px.bar(temp, x="total_hours", y="project", orientation="h", text="Label")
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_xaxes(title="Total Hours")
        fig.update_layout(height=430, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Project Cost per Hour by Month")
    st.dataframe(custo_hora_mes[["project", "Month", "wages_cost_usd", "total_hours", "cost_per_hour_usd"]],
                 use_container_width=True, hide_index=True, height=400,
                 column_config={
                     "wages_cost_usd": st.column_config.NumberColumn("Wages Cost", format="$%.2f"),
                     "total_hours": st.column_config.NumberColumn("Hours", format="%.1f"),
                     "cost_per_hour_usd": st.column_config.NumberColumn("Cost / Hour", format="$%.2f"),
                 })

    # BUSINESS UNIT
    st.divider()
    st.markdown("## Business Unit")
    business = resumo_business(summary_fx).sort_values("Profit", ascending=False).copy()
    business["Profit Millions"] = business["Profit"] / 1_000_000
    business["Label"] = business["Profit Millions"].map(
        lambda x: f"${x:.2f}M" if x >= 0 else f"-${abs(x):.2f}M"
    )
    cores = ["#16A34A" if x >= 0 else "#DC2626" for x in business["Profit Millions"]]
    st.markdown("### Profit by Business Unit")
    fig = px.bar(business, x="business_unit", y="Profit Millions", text="Label")
    fig.update_traces(marker_color=cores, textposition="outside", cliponaxis=False)
    fig.add_hline(y=0, line_width=2)
    fig.update_xaxes(title="Business Unit", tickangle=-35)
    fig.update_yaxes(title="Profit - USD Millions", ticksuffix="M")
    fig.update_layout(height=450, showlegend=False, margin=dict(l=10, r=10, t=20, b=80))
    st.plotly_chart(fig, use_container_width=True)
