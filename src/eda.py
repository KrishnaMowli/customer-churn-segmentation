"""Phase 3: EDA plotting helpers (each returns the figure's underlying numbers)."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
PAL = {0: "#4C78A8", 1: "#E4572E"}
sns.set_theme(style="whitegrid", context="notebook")

BUCKETS = [-1, 6, 12, 24, 48, 100]
LABELS = ["0-6", "7-12", "13-24", "25-48", "49+"]
PROTECT = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"]


def load() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "telco_clean.csv")
    df["tenure_bucket"] = pd.cut(df.tenure, BUCKETS, labels=LABELS)
    df["n_protective"] = sum((df[c] == "Yes").astype(int) for c in PROTECT)
    return df


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)


def fig_tenure(df):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, lab in [(0, "Retained"), (1, "Churned")]:
        ax.hist(df.loc[df.Churn == k, "tenure"], bins=36, alpha=.65, color=PAL[k], label=lab, density=True)
    ax.set(xlabel="Tenure (months)", ylabel="Density", title="Churners are concentrated in the first year")
    ax.legend()
    _save(fig, "01_tenure_by_churn.png")
    return df.groupby("Churn").tenure.median()


def fig_monthly(df):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, lab in [(0, "Retained"), (1, "Churned")]:
        sns.kdeplot(df.loc[df.Churn == k, "MonthlyCharges"], ax=ax, color=PAL[k], fill=True, alpha=.4, label=lab)
    ax.set(xlabel="Monthly charge ($)", title="Churners skew to higher bills (median $80 vs $64)")
    ax.legend()
    _save(fig, "02_monthly_charges_by_churn.png")
    return df.groupby("Churn").MonthlyCharges.median()


def _bar(df, col, name, title, order=None):
    g = df.groupby(col, observed=True).Churn.agg(["mean", "size"]).mul([100, 1])
    if order: g = g.loc[order]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(g.index.astype(str), g["mean"], color="#E4572E")
    ax.axhline(df.Churn.mean() * 100, ls="--", c="grey", lw=1)
    ax.text(len(g) - .5, df.Churn.mean() * 100 + 1, "overall 26.5%", ha="right", color="grey", fontsize=9)
    for i, (m, n) in enumerate(zip(g["mean"], g["size"])):
        ax.text(i, m + 1, f"{m:.1f}%\n(n={int(n):,})", ha="center", fontsize=9)
    ax.set(ylabel="Churn rate (%)", title=title, ylim=(0, g["mean"].max() * 1.3))
    plt.setp(ax.get_xticklabels(), rotation=10 if len(g) > 3 else 0)
    _save(fig, name)
    return g["mean"].round(1)


def fig_contract(df):
    return _bar(df, "Contract", "03_churn_by_contract.png",
                "Month-to-month customers churn at ~15x the two-year rate",
                ["Month-to-month", "One year", "Two year"])


def fig_payment(df):
    return _bar(df, "PaymentMethod", "04_churn_by_payment.png",
                "Electronic-check payers churn at ~2.5x the rate of other methods")


def fig_heatmap(df):
    p = df.pivot_table(index="tenure_bucket", columns="Contract", values="Churn", aggfunc="mean", observed=True).mul(100)
    p = p[["Month-to-month", "One year", "Two year"]]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    sns.heatmap(p, annot=True, fmt=".0f", cmap="Reds", cbar_kws={"label": "Churn rate (%)"}, ax=ax)
    ax.set(xlabel="", ylabel="Tenure (months)", title="Risk is highest where short tenure meets no commitment")
    _save(fig, "05_churn_heatmap_tenure_contract.png")
    return p.round(1)


def fig_addons(df):
    d = df[df.InternetService != "No"]
    p = d.pivot_table(index="n_protective", columns="InternetService", values="Churn", aggfunc="mean").mul(100)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    p.plot(marker="o", ax=ax, color=["#4C78A8", "#E4572E"])
    ax.set(xlabel="Number of protective add-ons (0-4)", ylabel="Churn rate (%)",
           title="Each protective add-on cuts churn, for both DSL and fiber", xticks=range(5))
    _save(fig, "06_churn_by_addons.png")
    return p.round(1)


def segments(df):
    """Informal candidate segments from the EDA (formal clustering comes in Phase 4)."""
    rules = {
        "A: new, month-to-month, fiber": (df.Contract == "Month-to-month") & (df.tenure <= 12) & (df.InternetService == "Fiber optic"),
        "B: month-to-month, e-check, any tenure": (df.Contract == "Month-to-month") & (df.PaymentMethod == "Electronic check"),
        "C: committed, long-tenure (1-2yr, 25+ mo)": (df.Contract != "Month-to-month") & (df.tenure > 24),
        "D: no internet service": df.InternetService == "No",
    }
    rows = []
    for k, m in rules.items():
        s = df[m]
        rows.append({"segment": k, "customers": len(s), "pct_of_base": round(100 * len(s) / len(df), 1),
                     "churn_rate_pct": round(100 * s.Churn.mean(), 1),
                     "avg_monthly_charge": round(s.MonthlyCharges.mean(), 2),
                     "share_of_all_churners_pct": round(100 * s.Churn.sum() / df.Churn.sum(), 1)})
    return pd.DataFrame(rows)
