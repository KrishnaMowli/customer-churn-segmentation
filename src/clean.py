"""Phase 1: load and clean the IBM Telco churn data."""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "telco.csv"
CLEAN = ROOT / "data" / "telco_clean.csv"

ADDONS = ["OnlineSecurity", "OnlineBackup", "DeviceProtection",
          "TechSupport", "StreamingTV", "StreamingMovies"]


def load_raw() -> pd.DataFrame:
    return pd.read_csv(RAW)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # TotalCharges is a string because 11 rows are blank. All 11 have tenure == 0:
    # brand-new customers who have not been billed yet, so the true value is 0.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    blank = df["TotalCharges"].isna()
    assert (df.loc[blank, "tenure"] == 0).all(), "blank TotalCharges outside tenure==0"
    df.loc[blank, "TotalCharges"] = 0.0

    # "No internet service" / "No phone service" are redundant with InternetService /
    # PhoneService. Collapse to "No" so each add-on is a clean binary feature.
    for c in ADDONS + ["MultipleLines"]:
        df[c] = df[c].replace({"No internet service": "No", "No phone service": "No"})

    df["Churn"] = (df["Churn"] == "Yes").astype(int)
    assert df["customerID"].is_unique
    return df


if __name__ == "__main__":
    out = clean(load_raw())
    out.to_csv(CLEAN, index=False)
    print(f"saved {CLEAN.name}: {out.shape}, churn rate {out.Churn.mean():.3%}")
