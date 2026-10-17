#!/usr/bin/env bash
# Rebuild everything from the raw CSV: cleaning -> SQLite -> notebooks 01-06.
# Usage: bash run_all.sh   (from the repo root)
set -euo pipefail
python src/clean.py
python src/build_db.py
python src/run_queries.py > /dev/null
for nb in 01_cleaning 02_sql_layer 03_eda 04_segmentation 05_modeling 06_statistics; do
  echo ">> executing notebooks/$nb.ipynb"
  jupyter nbconvert --to notebook --execute --inplace "notebooks/$nb.ipynb" 2> /dev/null
done
echo "done. Launch the dashboard with: streamlit run app/dashboard.py"
