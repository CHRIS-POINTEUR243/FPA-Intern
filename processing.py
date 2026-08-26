import pandas as pd


def limpar_summary(summary):
    summary = summary.copy()
    summary["date"] = pd.to_datetime(summary["date"], errors="coerce")
    summary["Indicator_value"] = pd.to_numeric(
        summary["Indicator_value"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )
    summary["currency"] = summary["currency"].str.strip().str.upper()
    summary["project"] = (
        summary["project"].str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    )
    summary["fx_year_month"] = summary["date"].dt.to_period("M")
    return summary


def limpar_fx(fx):
    fx = fx.copy()
    fx.columns = fx.iloc[0]
    fx = fx.iloc[1:].reset_index(drop=True)

    fx_long = fx.melt(
        id_vars="from_currency",
        var_name="fx_year_month",
        value_name="exchange_rate",
    )
    fx_long = fx_long.rename(columns={"from_currency": "currency"})
    fx_long["currency"] = fx_long["currency"].str.strip().str.upper()
    fx_long["fx_year_month"] = pd.PeriodIndex(fx_long["fx_year_month"], freq="M")
    fx_long["exchange_rate"] = pd.to_numeric(fx_long["exchange_rate"], errors="coerce")
    fx_long["rate_was_missing"] = fx_long["exchange_rate"].isna()
    fx_long = fx_long.sort_values(["currency", "fx_year_month"])
    fx_long["exchange_rate"] = (
        fx_long.groupby("currency")["exchange_rate"]
        .transform(lambda x: x.interpolate(limit_area="inside"))
    )
    return fx_long


def criar_summary_fx(summary, fx_long):
    summary_fx = summary.merge(
        fx_long[["currency", "fx_year_month", "exchange_rate", "rate_was_missing"]],
        on=["currency", "fx_year_month"],
        how="left",
        validate="many_to_one",
    )
    summary_fx["value_usd"] = summary_fx["Indicator_value"] * summary_fx["exchange_rate"]
    return summary_fx


def limpar_timecards(timecards):
    timecards = timecards.copy()
    timecards["date"] = pd.to_datetime(timecards["date"], errors="coerce")
    timecards["employee_id"] = timecards["employee_id"].str.strip()
    timecards["project"] = (
        timecards["project"].str.strip().str.replace(r"\s+", " ", regex=True).str.title()
    )
    for coluna in ["Grade", "contract_type", "hour_type"]:
        timecards[coluna] = timecards[coluna].str.strip()
    timecards = timecards.drop_duplicates().reset_index(drop=True)
    timecards["hours_negative_flag"] = timecards["hours"] < 0
    timecards["project_missing_flag"] = timecards["project"].isna()
    return timecards


def preparar_dados(summary, fx, timecards):
    summary = limpar_summary(summary)
    fx_long = limpar_fx(fx)
    summary_fx = criar_summary_fx(summary, fx_long)
    timecards = limpar_timecards(timecards)
    timecards_analysis = timecards[timecards["hours"] > 0].copy()
    return summary_fx, timecards, timecards_analysis


# =========================================================
# UPLOAD / AUTOMAÇÃO
# =========================================================

COLUNAS_ESPERADAS = {
    "summary": {
        "market", "business_unit", "country", "region", "employee_id",
        "date", "Indicator", "Indicator_value", "currency", "project"
    },
    "timecards": {
        "employee_id", "Grade", "contract_type", "date",
        "project", "hour_type", "hours"
    },
}


def carregar_arquivo_externo(arquivo):
    """Lê CSV, XLSX ou XLS recebido pelo Streamlit."""
    nome = getattr(arquivo, "name", "").lower()
    if nome.endswith(".csv"):
        return pd.read_csv(arquivo, low_memory=False)
    if nome.endswith((".xlsx", ".xls")):
        return pd.read_excel(arquivo)
    raise ValueError("Formato não suportado. Envie CSV, XLSX ou XLS.")


def validar_arquivo_externo(df, tipo_base):
    """Valida a estrutura mínima antes de gravar no banco."""
    tipo_base = str(tipo_base).strip().lower()
    if df is None or df.empty:
        return False, "O arquivo está vazio."

    if tipo_base in COLUNAS_ESPERADAS:
        atuais = {str(c).strip() for c in df.columns}
        faltantes = COLUNAS_ESPERADAS[tipo_base] - atuais
        if faltantes:
            return False, "Colunas obrigatórias ausentes: " + ", ".join(sorted(faltantes))
        return True, "Estrutura validada com sucesso."

    if tipo_base == "fx":
        colunas = [str(c).strip() for c in df.columns]
        if "from_currency" in colunas:
            return True, "Estrutura FX validada com sucesso."

        primeira_linha = [str(v).strip() for v in df.iloc[0].tolist()]
        if "from_currency" in primeira_linha:
            return True, "Estrutura FX validada com sucesso."

        return False, "Não foi possível localizar 'from_currency' no arquivo FX."

    return False, "Tipo de base inválido."
