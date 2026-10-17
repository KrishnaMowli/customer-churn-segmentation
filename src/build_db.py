"""Phase 2: load the cleaned data into SQLite as three normalised tables."""
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "telco.db"

TABLES = {
    "customers": ["customerID", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "Churn"],
    "services": ["customerID", "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
                 "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"],
    "billing": ["customerID", "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges"],
}

def build() -> None:
    df = pd.read_csv(ROOT / "data" / "telco_clean.csv")
    DB.unlink(missing_ok=True)
    with sqlite3.connect(DB) as con:
        for name, cols in TABLES.items():
            df[cols].to_sql(name, con, index=False)
            con.execute(f"CREATE UNIQUE INDEX idx_{name}_id ON {name}(customerID)")
        for name in TABLES:
            n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            print(f"{name}: {n} rows")

if __name__ == "__main__":
    build()
