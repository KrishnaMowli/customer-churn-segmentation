# SQL query results

## Q1: Churn rate by contract type. Where is the problem concentrated?

| Contract       |   customers |   churned |   churn_rate_pct |
|:---------------|------------:|----------:|-----------------:|
| Month-to-month |        3875 |      1655 |             42.7 |
| One year       |        1473 |       166 |             11.3 |
| Two year       |        1695 |        48 |              2.8 |

## Q2: Retention by tenure bucket (replaces "cohort by signup month": the data has no signup date).

| tenure_bucket   |   customers |   churn_rate_pct |   retention_pct |
|:----------------|------------:|-----------------:|----------------:|
| 1) 0-6 mo       |        1481 |             52.9 |            47.1 |
| 2) 7-12 mo      |         705 |             35.9 |            64.1 |
| 3) 13-24 mo     |        1024 |             28.7 |            71.3 |
| 4) 25-48 mo     |        1594 |             20.4 |            79.6 |
| 5) 49+ mo       |        2239 |              9.5 |            90.5 |

## Q3: Average tenure and monthly charge by internet service, split by churn status.

| InternetService   | status   |   customers |   avg_tenure_mo |   avg_monthly_charge |
|:------------------|:---------|------------:|----------------:|---------------------:|
| DSL               | churned  |         459 |            14.1 |                49.08 |
| DSL               | retained |        1962 |            37.2 |                60.21 |
| Fiber optic       | churned  |        1297 |            20.2 |                88.13 |
| Fiber optic       | retained |        1799 |            42.1 |                93.93 |
| No                | churned  |         113 |             8.2 |                20.37 |
| No                | retained |        1413 |            32.3 |                21.14 |

## Q4: Monthly revenue already lost to churn, by contract, and its share of total monthly revenue.

| Contract       |   total_mrr |   lost_mrr |   lost_pct_of_contract_mrr |   share_of_all_lost_mrr_pct |
|:---------------|------------:|-----------:|---------------------------:|----------------------------:|
| Month-to-month |      257294 |     120847 |                       47   |                        86.9 |
| One year       |       95817 |      14118 |                       14.7 |                        10.1 |
| Two year       |      103006 |       4165 |                        4   |                         3   |

## Q5: Revenue at risk among CURRENT customers who match the high-risk profile found in Q1-Q3

|   active_high_risk_customers |   monthly_revenue_at_risk |   annualised_revenue_at_risk |
|-----------------------------:|--------------------------:|-----------------------------:|
|                          273 |                     22005 |                       264058 |

## Q6: Within each contract type, rank payment methods by churn rate (window function).

| Contract       | PaymentMethod             |   customers |   churn_rate_pct |   risk_rank |
|:---------------|:--------------------------|------------:|-----------------:|------------:|
| Month-to-month | Electronic check          |        1850 |             53.7 |           1 |
| Month-to-month | Bank transfer (automatic) |         589 |             34.1 |           2 |
| Month-to-month | Credit card (automatic)   |         543 |             32.8 |           3 |
| Month-to-month | Mailed check              |         893 |             31.6 |           4 |
| One year       | Electronic check          |         347 |             18.4 |           1 |
| One year       | Credit card (automatic)   |         398 |             10.3 |           2 |
| One year       | Bank transfer (automatic) |         391 |              9.7 |           3 |
| One year       | Mailed check              |         337 |              6.8 |           4 |
| Two year       | Electronic check          |         168 |              7.7 |           1 |
| Two year       | Bank transfer (automatic) |         564 |              3.4 |           2 |
| Two year       | Credit card (automatic)   |         581 |              2.2 |           3 |
| Two year       | Mailed check              |         382 |              0.8 |           4 |

## Q7: Churn by monthly-charge decile (NTILE) with cumulative share of all churners captured,

|   price_decile |   min_charge |   customers |   churners |   churn_rate_pct |   cum_churners_captured_pct |
|---------------:|-------------:|------------:|-----------:|-----------------:|----------------------------:|
|              1 |       102.6  |         705 |        174 |             24.7 |                         9.3 |
|              2 |        94.25 |         705 |        290 |             41.1 |                        24.8 |
|              3 |        85.5  |         705 |        240 |             34   |                        37.7 |
|              4 |        79.1  |         704 |        268 |             38.1 |                        52   |
|              5 |        70.35 |         704 |        266 |             37.8 |                        66.2 |
|              6 |        58.75 |         704 |        152 |             21.6 |                        74.4 |
|              7 |        45.85 |         704 |        174 |             24.7 |                        83.7 |
|              8 |        25.05 |         704 |        177 |             25.1 |                        93.2 |
|              9 |        20.05 |         704 |         67 |              9.5 |                        96.7 |
|             10 |        18.25 |         704 |         61 |              8.7 |                       100   |

## Q8: Number of protective add-ons (security, backup, protection, tech support) vs churn.

|   n_protective |   customers |   churn_rate_pct |
|---------------:|------------:|-----------------:|
|              0 |        1267 |             56.7 |
|              1 |        1467 |             38.9 |
|              2 |        1372 |             23.8 |
|              3 |         941 |             12.4 |
|              4 |         470 |              5.3 |
