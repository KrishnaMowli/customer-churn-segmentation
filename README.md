# Customer Segmentation & Churn Prediction

An end-to-end analytics project on the IBM Telco customer churn data (7,043 customers): SQL analysis, customer segmentation, a leakage-safe churn model, statistical uncertainty quantification, survival analysis, an interactive dashboard and an executive summary with segment-specific retention recommendations.

**Business question.** 26.5% of customers have churned, costing **$139K of monthly revenue (30.5% of the base, ~$1.7M a year)**. Who should a limited retention budget target, with what, and how sure are we?

## Headline results
- **Month-to-month contracts churn at 42.7%** vs 2.8% on two-year plans and account for **87% of lost revenue**. Median month-to-month customer lifetime is **35 months**.
- **K-Means found four segments** (churn was never used to build them). The *at-risk fiber, month-to-month* segment is 28% of customers but **68% of lost revenue**, churning at **56.6% (95% CI 54.5-58.7)**.
- **Held-out ROC-AUC 0.839 (95% CI 0.815-0.860).** Contacting the **top 20% by predicted risk reaches 50% of churners (CI 45.7-54.0%) at 2.5x lift over random targeting (CI 2.3-2.7)** and 56% of churned revenue.
- Contract, tenure and internet service drive predictions; logistic coefficients, permutation importance and a Cox survival model agree.

## Repository structure
```
data/        telco.csv (raw), telco_clean.csv, segments.csv, test_predictions.csv  (telco.db is rebuilt, git-ignored)
sql/         queries.sql                      8 stakeholder queries (joins, CTEs, RANK, NTILE, running SUM)
src/         clean.py build_db.py run_queries.py eda.py segment.py models.py stats_utils.py
notebooks/   01_cleaning  02_sql_layer  03_eda  04_segmentation  05_modeling  06_statistics
app/         dashboard.py                     Streamlit dashboard
reports/     executive_summary.md / .pdf, sql_results.md, figures/ (16 charts)
models/      logreg_churn.joblib, thresholds.json
run_all.sh   rebuilds everything from the raw CSV
```

## Reproduce
```bash
pip install -r requirements.txt
bash run_all.sh                    # cleaning -> SQLite -> notebooks 01-06 (a few minutes)
streamlit run app/dashboard.py     # interactive dashboard
```
All random seeds are fixed, so numbers reproduce exactly.

## What each notebook does
| Notebook | Contents | Main takeaway |
|---|---|---|
| 01 cleaning | Profile, fix `TotalCharges`, collapse redundant levels | 11 blank `TotalCharges` are brand-new customers (tenure 0), set to 0 rather than dropped or imputed |
| 02 SQL layer | 3 normalised tables, 8 queries | Retention by tenure bucket instead of signup month (no signup dates exist); electronic check ranks worst within every contract |
| 03 EDA | 6 labelled charts, informal segments | Median tenure 10 months for churners vs 38 for retained customers |
| 04 segmentation | Scale + one-hot + PCA, K-Means k=4, Ward check, profiles | Cluster profiles separate churn from 7% to 57% without seeing the label |
| 05 modeling | 3 models x 3 imbalance strategies, leakage check, lift, coefficients | All configs reach CV ROC-AUC 0.840-0.845, so the interpretable model wins and SMOTE never helps |
| 06 statistics | Bootstrap CIs, two-proportion tests, Kaplan-Meier, Cox | Effect sizes, not p-values, carry the message; found and fixed two modelling problems |

## Segments (notebook 04)
| Segment | % customers | Churn rate | % of lost monthly revenue |
|---|---|---|---|
| At-risk fiber, month-to-month | 27.8% | 56.6% | 68.1% |
| Mid-tier DSL, month-to-month | 21.4% | 27.6% | 14.0% |
| Loyal premium | 28.9% | 11.4% | 16.2% |
| Budget phone-only | 21.9% | 7.3% | 1.7% |

## Model performance (notebook 05, held-out test set of 1,409 customers)
| Metric | Logistic regression | Gradient boosting |
|---|---|---|
| ROC-AUC | 0.839 | 0.840 |
| PR-AUC | 0.628 | 0.659 |
| Recall / precision (threshold tuned on train out-of-fold predictions) | 74% / 52% | 74% / 54% |
| Accuracy (do-nothing baseline 73.5%, catches 0% of churners) | 75.2% | 76.3% |

A paired bootstrap shows no ROC-AUC difference between the models but a small PR-AUC edge for gradient boosting (+0.03, CI 0.007-0.054). Logistic regression is the primary model for interpretability.

## Dashboard and executive summary
- `app/dashboard.py` (Streamlit): KPI cards; churn by segment, contract, tenure and payment method with sidebar filters; revenue-at-risk table; a targeting simulator (choose the share of customers to contact and see churners reached, precision and churned revenue captured); driver and survival charts.
- `reports/executive_summary.md` / `.pdf`: findings and three segment-specific retention recommendations, each framed as an A/B test with a break-even rule.

## Design decisions worth knowing
- **Imbalance (2.8:1):** compared no handling, class weights and SMOTE inside the CV folds; SMOTE added nothing (and slightly hurt the random forest), so class weights are used. The threshold is tuned on training out-of-fold predictions, never on the test set.
- **Leakage:** all preprocessing, resampling and clustering sit inside sklearn pipelines fitted on training folds only. A fold-safe `SegmentFeature` transformer is included; segment labels turned out to add no predictive information beyond the raw features.
- **Collinearity:** `MonthlyCharges` is 99.9% explained by the service columns, so it was dropped from the Cox model, and the logistic streaming coefficients are flagged as unreliable.
- **Non-proportional hazards:** contract violates the Cox assumption, so the model is stratified on it.
- **Metrics:** accuracy is not used for model selection because a "nobody churns" model scores 73.5%.

## Limitations
- Single snapshot with no signup dates or contract history: no time-based validation, and contract type is treated as fixed, which probably overstates its protective effect in the survival curves.
- All findings are associations. Lift shows how well *past* churners are ranked, not how many an offer would save; that needs an A/B test.
- K-Means treats one-hot columns as numeric and silhouette is low (~0.23), so the boundary between the two middle segments is soft (K-Prototypes or Gower distance are alternatives).
- Several Cox covariates still fail the proportional-hazards test after stratification; their hazard ratios are time-averaged effects.
- Survival curve tails beyond ~65 months rest on very few customers.

## Tech stack
Python (pandas, NumPy, scikit-learn, imbalanced-learn, SciPy, statsmodels, lifelines), SQLite, matplotlib/seaborn, Streamlit/Altair, Jupyter.
