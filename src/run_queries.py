"""Run every query in sql/queries.sql and write readable results to reports/sql_results.md."""
import re, sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run() -> str:
    text = (ROOT / "sql" / "queries.sql").read_text()
    blocks = re.split(r"(?m)^-- (Q\d+): ", text)[1:]
    out = ["# SQL query results\n"]
    with sqlite3.connect(ROOT / "data" / "telco.db") as con:
        for tag, body in zip(blocks[::2], blocks[1::2]):
            title, _, sql = body.partition("\n")
            df = pd.read_sql_query(sql, con)
            out.append(f"## {tag}: {title}\n\n{df.to_markdown(index=False)}\n")
    return "\n".join(out)

if __name__ == "__main__":
    md = run()
    (ROOT / "reports" / "sql_results.md").write_text(md)
    print(md)
