import pandas as pd


def resumo_financeiro(summary_fx):
    ind = summary_fx.groupby("Indicator")["value_usd"].sum()
    revenue = ind.get("Revenue", 0)
    budget = ind.get("Budget", 0)
    wages = ind.get("Wages Cost", 0)
    other = ind.get("Other Costs", 0)
    total_cost = wages + other
    profit = revenue - total_cost
    margin = (profit / revenue * 100) if revenue else 0
    attainment = (revenue / budget * 100) if budget else 0
    return {
        "revenue": revenue,
        "budget": budget,
        "wages": wages,
        "other": other,
        "total_cost": total_cost,
        "profit": profit,
        "margin": margin,
        "attainment": attainment,
        "budget_variance_pct": attainment - 100,
    }


def evolucao_mensal(summary_fx):
    df = (
        summary_fx[summary_fx["Indicator"].isin(["Revenue", "Wages Cost", "Other Costs"])]
        .groupby(["fx_year_month", "Indicator"])["value_usd"]
        .sum()
        .unstack(fill_value=0)
    )
    for c in ["Revenue", "Wages Cost", "Other Costs"]:
        if c not in df.columns:
            df[c] = 0
    df["Total Costs"] = df["Wages Cost"] + df["Other Costs"]
    df = df.loc["2024-01":"2025-12"] / 1_000_000
    out = df.reset_index()
    out["Month"] = out["fx_year_month"].astype(str)
    return out


def resumo_regiao(summary_fx):
    df = summary_fx.pivot_table(
        index="region", columns="Indicator", values="value_usd", aggfunc="sum", fill_value=0
    ).reset_index()
    for c in ["Revenue", "Budget", "Wages Cost", "Other Costs"]:
        if c not in df.columns:
            df[c] = 0
    df["Total Cost"] = df["Wages Cost"] + df["Other Costs"]
    df["Profit"] = df["Revenue"] - df["Total Cost"]
    df["Profit Margin"] = (
        df["Profit"] / df["Revenue"].where(df["Revenue"] != 0) * 100
    ).fillna(0)
    return df


def resumo_projeto(summary_fx):
    df = summary_fx[summary_fx["project"].notna()].pivot_table(
        index="project", columns="Indicator", values="value_usd", aggfunc="sum", fill_value=0
    ).reset_index()
    for c in ["Revenue", "Wages Cost", "Other Costs"]:
        if c not in df.columns:
            df[c] = 0
    df["Total Cost"] = df["Wages Cost"] + df["Other Costs"]
    df["Profit"] = df["Revenue"] - df["Total Cost"]
    df["Margin %"] = df["Profit"] / df["Revenue"].where(df["Revenue"] != 0) * 100
    df["Revenue_per_Cost"] = df["Revenue"] / df["Total Cost"].where(df["Total Cost"] != 0)
    return df


def resumo_business(summary_fx):
    df = summary_fx[summary_fx["business_unit"].notna()].pivot_table(
        index="business_unit", columns="Indicator", values="value_usd", aggfunc="sum", fill_value=0
    ).reset_index()
    for c in ["Revenue", "Wages Cost", "Other Costs"]:
        if c not in df.columns:
            df[c] = 0
    df["Total Cost"] = df["Wages Cost"] + df["Other Costs"]
    df["Profit"] = df["Revenue"] - df["Total Cost"]
    df["Margin"] = df["Profit"] / df["Revenue"].where(df["Revenue"] != 0) * 100
    return df


def analise_funcionarios(summary_fx, timecards, timecards_analysis):
    projetos_funcionario = (
        timecards[timecards["project"].notna()]
        .groupby("employee_id")["project"]
        .unique()
        .reset_index()
    )
    projetos_funcionario["project"] = projetos_funcionario["project"].apply(
        lambda x: ", ".join(sorted(set(x)))
    )

    custos = (
        summary_fx[
            (summary_fx["Indicator"] == "Wages Cost")
            & summary_fx["employee_id"].notna()
            & summary_fx["project"].notna()
        ]
        .groupby(["employee_id", "project"])["value_usd"]
        .sum()
        .reset_index(name="wages_cost")
    )

    horas = (
        timecards_analysis[timecards_analysis["project"].notna()]
        .groupby(["employee_id", "project"])["hours"]
        .sum()
        .reset_index(name="total_hours")
    )

    analise = custos.merge(horas, on=["employee_id", "project"], how="left")
    analise["cost_per_hour"] = analise["wages_cost"] / analise["total_hours"].where(analise["total_hours"] > 0)
    analise = analise.dropna(subset=["cost_per_hour"]).sort_values("cost_per_hour", ascending=False)

    projetos_mais_horas = (
        timecards_analysis[timecards_analysis["project"].notna()]
        .groupby("project")["hours"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(name="total_hours")
    )

    wages_mes = (
        summary_fx[(summary_fx["Indicator"] == "Wages Cost") & summary_fx["project"].notna()]
        .groupby(["project", "fx_year_month"])["value_usd"]
        .sum()
        .reset_index(name="wages_cost_usd")
    )
    horas_mes = (
        timecards_analysis[timecards_analysis["project"].notna()]
        .assign(fx_year_month=lambda x: x["date"].dt.to_period("M"))
        .groupby(["project", "fx_year_month"])["hours"]
        .sum()
        .reset_index(name="total_hours")
    )
    custo_hora_mes = wages_mes.merge(
        horas_mes, on=["project", "fx_year_month"], how="inner", validate="one_to_one"
    )
    custo_hora_mes["cost_per_hour_usd"] = (
        custo_hora_mes["wages_cost_usd"] / custo_hora_mes["total_hours"].where(custo_hora_mes["total_hours"] > 0)
    )
    custo_hora_mes = custo_hora_mes.dropna(subset=["cost_per_hour_usd"])
    custo_hora_mes["Month"] = custo_hora_mes["fx_year_month"].astype(str)

    return projetos_funcionario, analise, projetos_mais_horas, custo_hora_mes
