# Executive Summary: Customer Churn & Segmentation

**Data:** IBM Telco customer churn, 7,043 customers. **Period:** single snapshot.

## Problem
26.5% of customers have churned, which has already cost **$139K of monthly revenue (30.5% of the $456K base, about $1.7M a year)**. Retention budget is limited, so the question is *who* to target, *with what*, and *how sure are we*.

## Method (one line each)
- **SQL + EDA:** profiled the data in SQLite (8 stakeholder queries) and found the main risk patterns.
- **Segmentation:** K-Means (k=4) on scaled/encoded features; churn was *not* used to build clusters, yet the clusters separate it sharply.
- **Prediction:** logistic regression (class-weighted) vs random forest vs gradient boosting; held-out test set, threshold tuned on training data only.
- **Rigor:** bootstrap confidence intervals, hypothesis tests with effect sizes, Kaplan-Meier survival curves, Cox hazards model.

## Key findings
| Segment | Customers | Churn rate | Share of lost revenue |
|---|---|---|---|
| **At-risk fiber, month-to-month** | 1,957 (28%) | **56.6%** (95% CI 54.5-58.7) | **68%** |
| Mid-tier DSL, month-to-month | 1,507 (21%) | 27.6% | 14% |
| Loyal premium | 2,037 (29%) | 11.4% | 16% |
| Budget phone-only | 1,542 (22%) | 7.3% | 2% |

- **Contract and tenure dominate.** Month-to-month customers churn at 42.7% vs 2.8% on two-year plans; their median lifetime is **35 months**. 55% of all churners leave within their first 12 months.
- **The model ranks risk well.** Held-out ROC-AUC **0.839 (95% CI 0.815-0.860)**. Contacting the **top 20% by risk reaches 50% of churners (CI 45.7-54.0%) at 2.5x the lift of random targeting (CI 2.3-2.7)** and 56% of churned revenue.
- **Protective services go with lower churn.** Customers with online security or tech support have clearly lower hazard of churning (hazard ratios 0.53 and 0.66); electronic-check payers have a higher one (1.78 vs bank transfer).

## Recommendations
**1. At-risk fiber, month-to-month: offer a 12-month contract bundled with security/tech support.**
This segment holds **849 active customers paying $72K a month (about $870K a year)** and accounts for 68% of lost revenue. 43% of them have no protective add-on, and their churn is 64% in that group vs 49% for those with two or more. *Illustration:* preventing 10% of this segment's historical churn would be worth roughly **$114K a year** at today's prices. Use the model's top-risk list to choose who gets the offer.

**2. Electronic-check payers (63% of the at-risk segment): offer a small one-time credit to move to auto-pay.**
Within the at-risk segment, e-check payers churn at 62% vs 47% for everyone else. The effect persists after adjusting for other factors (hazard ratio 1.78 vs bank transfer), so it is not just a contract effect.

**3. Mid-tier DSL, month-to-month: trial a free protective add-on for 3 months instead of discounting price.**
In this segment churn is **43.6% with no add-ons vs 15.5% with two or more** (566 customers). An add-on trial is cheaper than a price cut and targets the behaviour most associated with staying. Pair it with early-tenure outreach for customers in months 1-6, when churn is 52.9%.

**Where not to spend:** *Loyal premium* (11% churn, long tenure) needs protection, not discounts, so use renewal outreach before contracts end. *Budget phone-only* (7% churn, about $21/month) needs no retention spend.

## How to validate before scaling
Run each offer as an **A/B test**: randomise within the top-risk list, hold out a control group, and compare 90-day churn. An offer is worth it when *(churn rate of targeted customers) x (share the offer actually saves) x (monthly revenue) x (expected months retained)* exceeds the offer's cost per customer.

## Caveats
- The data is a **snapshot**: relationships are associations, not proven causes. The lift numbers show how well *past* churners are ranked, not how many an offer would save.
- Contract type is measured at snapshot, so survival curves probably overstate its protective effect; the data has no signup dates or contract history.
- Segment boundaries between the two middle groups are soft (clustering silhouette about 0.23).
- Full detail, code and diagnostics: `notebooks/` (01-06), `sql/queries.sql`, `app/dashboard.py`.
