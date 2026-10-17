"""Churn & segmentation dashboard.  Run from the repo root:  streamlit run app/dashboard.py"""
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import eda  # noqa: E402

st.set_page_config(page_title="Customer Churn & Segmentation", layout="wide")
SEG_ORDER = ["At-risk fiber, month-to-month", "Mid-tier DSL, month-to-month", "Loyal premium", "Budget phone-only"]
RED, BLUE = "#E4572E", "#4C78A8"


@st.cache_data
def load():
    df = eda.load()
    seg = pd.read_csv(ROOT / "data" / "segments.csv")[["customerID", "segment"]]
    df = df.merge(seg, on="customerID")
    df["lost_mrr"] = df.MonthlyCharges * df.Churn
    df["active_mrr"] = df.MonthlyCharges * (1 - df.Churn)
    pred = pd.read_csv(ROOT / "data" / "test_predictions.csv")
    return df, pred


df, pred = load()

# ---------------------------------------------------------------- sidebar filters
st.sidebar.header("Filters")
contracts = st.sidebar.multiselect("Contract", sorted(df.Contract.unique()), default=sorted(df.Contract.unique()))
internet = st.sidebar.multiselect("Internet service", sorted(df.InternetService.unique()), default=sorted(df.InternetService.unique()))
segs = st.sidebar.multiselect("Segment", SEG_ORDER, default=SEG_ORDER)
tmin, tmax = st.sidebar.slider("Tenure (months)", 0, int(df.tenure.max()), (0, int(df.tenure.max())))
f = df[df.Contract.isin(contracts) & df.InternetService.isin(internet) & df.segment.isin(segs) & df.tenure.between(tmin, tmax)]

st.title("Customer Churn & Segmentation")
st.caption("IBM Telco customer churn data (7,043 customers). Filters on the left apply to the Overview and Revenue tabs.")

if f.empty:
    st.warning("No customers match the current filters.")
    st.stop()

# ---------------------------------------------------------------- KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Customers", f"{len(f):,}")
k2.metric("Churn rate", f"{100 * f.Churn.mean():.1f}%", delta=f"{100 * (f.Churn.mean() - df.Churn.mean()):+.1f} pp vs all", delta_color="inverse")
k3.metric("Monthly revenue", f"${f.MonthlyCharges.sum():,.0f}")
k4.metric("Monthly revenue lost to churn", f"${f.lost_mrr.sum():,.0f}", delta=f"{100 * f.lost_mrr.sum() / f.MonthlyCharges.sum():.1f}% of segment revenue", delta_color="off")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Revenue at risk", "Targeting (model)", "Drivers & survival"])


def bar(data, x, y, title, fmt=".1f", color=RED, sort=None, horizontal=False):
    base = alt.Chart(data, title=title)
    if horizontal:
        c = base.mark_bar(color=color).encode(y=alt.Y(f"{x}:N", sort=sort, title=None), x=alt.X(f"{y}:Q", title=None))
        t = base.mark_text(align="left", dx=3).encode(y=alt.Y(f"{x}:N", sort=sort), x=f"{y}:Q", text=alt.Text(f"{y}:Q", format=fmt))
    else:
        c = base.mark_bar(color=color).encode(x=alt.X(f"{x}:N", sort=sort, title=None), y=alt.Y(f"{y}:Q", title=None))
        t = base.mark_text(dy=-6).encode(x=alt.X(f"{x}:N", sort=sort), y=f"{y}:Q", text=alt.Text(f"{y}:Q", format=fmt))
    return (c + t).properties(height=260)


with tab1:
    c1, c2 = st.columns(2)
    seg = f.groupby("segment").agg(churn=("Churn", "mean"), n=("Churn", "size")).reset_index()
    seg["churn"] *= 100
    c1.altair_chart(bar(seg, "segment", "churn", "Churn rate (%) by segment", sort=SEG_ORDER, horizontal=True), width="stretch")
    con = f.groupby("Contract").Churn.mean().mul(100).reset_index()
    c2.altair_chart(bar(con, "Contract", "Churn", "Churn rate (%) by contract", sort=["Month-to-month", "One year", "Two year"]), width="stretch")
    c3, c4 = st.columns(2)
    tb = f.groupby("tenure_bucket", observed=True).Churn.mean().mul(100).reset_index()
    tb["tenure_bucket"] = tb.tenure_bucket.astype(str)
    c3.altair_chart(bar(tb, "tenure_bucket", "Churn", "Churn rate (%) by tenure (months)", sort=eda.LABELS), width="stretch")
    pm = f.groupby("PaymentMethod").Churn.mean().mul(100).reset_index()
    c4.altair_chart(bar(pm, "PaymentMethod", "Churn", "Churn rate (%) by payment method", horizontal=True), width="stretch")
    st.info("Month-to-month contracts, the first year of tenure and electronic-check payment are the clearest churn hot-spots in the data.")

with tab2:
    g = f.groupby("segment").agg(customers=("Churn", "size"), churn_rate=("Churn", "mean"), monthly_revenue=("MonthlyCharges", "sum"),
                                 lost_mrr=("lost_mrr", "sum"), active_customers=("Churn", lambda s: int((s == 0).sum())),
                                 active_mrr=("active_mrr", "sum")).reindex([s for s in SEG_ORDER if s in f.segment.unique()])
    g["share_of_lost_mrr_%"] = 100 * g.lost_mrr / g.lost_mrr.sum() if g.lost_mrr.sum() else 0
    g["annualised_lost_revenue"] = g.lost_mrr * 12
    g["churn_rate"] = (100 * g.churn_rate).round(1)
    show = g.round(0).astype({"customers": int, "active_customers": int})
    show["churn_rate"] = g.churn_rate
    show["share_of_lost_mrr_%"] = g["share_of_lost_mrr_%"].round(1)
    st.dataframe(show.rename(columns={"churn_rate": "churn_rate_%"}), width="stretch")
    lm = g.reset_index()[["segment", "lost_mrr"]]
    st.altair_chart(bar(lm, "segment", "lost_mrr", "Monthly revenue lost to churn ($) by segment", fmt=",.0f", sort=SEG_ORDER, horizontal=True), width="stretch")
    st.caption("'Lost' revenue is the monthly charge of customers who have already churned in this snapshot. 'Active' columns are customers still on the books.")

with tab3:
    st.subheader("If we contact only the highest-risk customers")
    st.caption(f"Uses the logistic-regression risk scores on the held-out test set ({len(pred):,} customers, never seen during training). This tab ignores the sidebar filters.")
    pct = st.slider("Share of customers contacted (highest predicted risk first)", 5, 50, 20, step=5)
    d = pred.sort_values("p_logreg", ascending=False).reset_index(drop=True)
    d["lost_mrr"] = d.MonthlyCharges * d.churn
    k = int(len(d) * pct / 100)
    top = d.head(k)
    reached, precision = top.churn.sum() / d.churn.sum(), top.churn.mean()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Customers contacted", f"{k:,}")
    m2.metric("Churners reached", f"{100 * reached:.0f}%", delta=f"vs {pct}% at random", delta_color="off")
    m3.metric("Precision", f"{100 * precision:.0f}%", delta=f"vs {100 * d.churn.mean():.0f}% at random", delta_color="off")
    m4.metric("Churned revenue reached", f"{100 * top.lost_mrr.sum() / d.lost_mrr.sum():.0f}%")
    x = np.arange(0, len(d) + 1)
    gains = pd.DataFrame({"pct_contacted": 100 * x / len(d), "model": np.r_[0, d.churn.cumsum().values] / d.churn.sum() * 100, "random": 100 * x / len(d)})
    gl = gains.melt("pct_contacted", var_name="targeting", value_name="pct_churners_reached")
    line = alt.Chart(gl, title="Cumulative gains: churners reached vs customers contacted").mark_line().encode(
        x=alt.X("pct_contacted:Q", title="% of customers contacted"), y=alt.Y("pct_churners_reached:Q", title="% of churners reached"),
        color=alt.Color("targeting:N", scale=alt.Scale(domain=["model", "random"], range=[RED, "#999"])))
    pt = alt.Chart(pd.DataFrame({"x": [pct], "y": [100 * reached]})).mark_point(size=120, filled=True, color="black").encode(x="x:Q", y="y:Q")
    st.altair_chart((line + pt).properties(height=320), width="stretch")
    st.caption("These are associations from a historical snapshot: the chart shows how well the model ranks customers who already churned, not how many an offer would save. Measuring that needs an A/B test.")

with tab4:
    st.subheader("What drives churn?")
    st.caption("Static results from notebooks 05 and 06.")
    d1, d2 = st.columns(2)
    d1.image(str(ROOT / "reports" / "figures" / "16_cox_hazard_ratios.png"), caption="Cox model (stratified by contract): hazard ratios with 95% CI")
    d2.image(str(ROOT / "reports" / "figures" / "12_permutation_importance.png"), caption="Gradient boosting: permutation importance on the test set")
    st.image(str(ROOT / "reports" / "figures" / "15_kaplan_meier.png"), caption="Kaplan-Meier retention curves by contract and by segment")
