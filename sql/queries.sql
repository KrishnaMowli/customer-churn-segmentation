-- Telco churn: stakeholder queries (SQLite). Tables: customers, services, billing.
-- Each query starts with "-- Q<n>:" so run_queries.py can split the file.

-- Q1: Churn rate by contract type. Where is the problem concentrated?
SELECT b.Contract,
       COUNT(*)                                   AS customers,
       SUM(c.Churn)                               AS churned,
       ROUND(100.0 * AVG(c.Churn), 1)             AS churn_rate_pct
FROM customers c
JOIN billing b USING (customerID)
GROUP BY b.Contract
ORDER BY churn_rate_pct DESC;

-- Q2: Retention by tenure bucket (replaces "cohort by signup month": the data has no signup date).
WITH bucketed AS (
    SELECT customerID, Churn,
           CASE WHEN tenure <= 6  THEN '1) 0-6 mo'
                WHEN tenure <= 12 THEN '2) 7-12 mo'
                WHEN tenure <= 24 THEN '3) 13-24 mo'
                WHEN tenure <= 48 THEN '4) 25-48 mo'
                ELSE                   '5) 49+ mo' END AS tenure_bucket
    FROM customers
)
SELECT tenure_bucket,
       COUNT(*)                                    AS customers,
       ROUND(100.0 * AVG(Churn), 1)                AS churn_rate_pct,
       ROUND(100.0 * (1 - AVG(Churn)), 1)          AS retention_pct
FROM bucketed
GROUP BY tenure_bucket
ORDER BY tenure_bucket;

-- Q3: Average tenure and monthly charge by internet service, split by churn status.
SELECT s.InternetService,
       CASE c.Churn WHEN 1 THEN 'churned' ELSE 'retained' END AS status,
       COUNT(*)                         AS customers,
       ROUND(AVG(c.tenure), 1)          AS avg_tenure_mo,
       ROUND(AVG(b.MonthlyCharges), 2)  AS avg_monthly_charge
FROM customers c
JOIN services s USING (customerID)
JOIN billing  b USING (customerID)
GROUP BY s.InternetService, c.Churn
ORDER BY s.InternetService, c.Churn DESC;

-- Q4: Monthly revenue already lost to churn, by contract, and its share of total monthly revenue.
WITH rev AS (
    SELECT b.Contract,
           SUM(b.MonthlyCharges)                                   AS total_mrr,
           SUM(CASE WHEN c.Churn = 1 THEN b.MonthlyCharges END)    AS lost_mrr
    FROM customers c JOIN billing b USING (customerID)
    GROUP BY b.Contract
)
SELECT Contract,
       ROUND(total_mrr, 0)                                          AS total_mrr,
       ROUND(lost_mrr, 0)                                           AS lost_mrr,
       ROUND(100.0 * lost_mrr / total_mrr, 1)                       AS lost_pct_of_contract_mrr,
       ROUND(100.0 * lost_mrr / SUM(lost_mrr) OVER (), 1)           AS share_of_all_lost_mrr_pct
FROM rev
ORDER BY lost_mrr DESC;

-- Q5: Revenue at risk among CURRENT customers who match the high-risk profile found in Q1-Q3
-- (month-to-month, tenure <= 12, fiber optic). Phase 5 replaces this rule with model scores.
SELECT COUNT(*)                           AS active_high_risk_customers,
       ROUND(SUM(b.MonthlyCharges), 0)    AS monthly_revenue_at_risk,
       ROUND(SUM(b.MonthlyCharges) * 12, 0) AS annualised_revenue_at_risk
FROM customers c
JOIN billing  b USING (customerID)
JOIN services s USING (customerID)
WHERE c.Churn = 0
  AND b.Contract = 'Month-to-month'
  AND c.tenure <= 12
  AND s.InternetService = 'Fiber optic';

-- Q6: Within each contract type, rank payment methods by churn rate (window function).
WITH pm AS (
    SELECT b.Contract, b.PaymentMethod,
           COUNT(*)                        AS customers,
           ROUND(100.0 * AVG(c.Churn), 1)  AS churn_rate_pct
    FROM customers c JOIN billing b USING (customerID)
    GROUP BY b.Contract, b.PaymentMethod
)
SELECT Contract, PaymentMethod, customers, churn_rate_pct,
       RANK() OVER (PARTITION BY Contract ORDER BY churn_rate_pct DESC) AS risk_rank
FROM pm
ORDER BY Contract, risk_rank;

-- Q7: Churn by monthly-charge decile (NTILE) with cumulative share of all churners captured,
-- i.e. a lift-table: if we target the top N deciles by price, how many churners do we reach?
WITH deciles AS (
    SELECT c.Churn,
           b.MonthlyCharges,
           NTILE(10) OVER (ORDER BY b.MonthlyCharges DESC) AS price_decile  -- 1 = most expensive
    FROM customers c JOIN billing b USING (customerID)
),
agg AS (
    SELECT price_decile,
           COUNT(*)                         AS customers,
           SUM(Churn)                       AS churners,
           ROUND(MIN(MonthlyCharges), 2)    AS min_charge
    FROM deciles GROUP BY price_decile
)
SELECT price_decile, min_charge, customers, churners,
       ROUND(100.0 * churners / customers, 1)                                         AS churn_rate_pct,
       ROUND(100.0 * SUM(churners) OVER (ORDER BY price_decile) / SUM(churners) OVER (), 1) AS cum_churners_captured_pct
FROM agg
ORDER BY price_decile;

-- Q8: Number of protective add-ons (security, backup, protection, tech support) vs churn.
WITH addon AS (
    SELECT customerID,
           (s.OnlineSecurity = 'Yes') + (s.OnlineBackup = 'Yes')
         + (s.DeviceProtection = 'Yes') + (s.TechSupport = 'Yes') AS n_protective
    FROM services s
    WHERE s.InternetService <> 'No'
)
SELECT a.n_protective,
       COUNT(*)                         AS customers,
       ROUND(100.0 * AVG(c.Churn), 1)   AS churn_rate_pct
FROM addon a JOIN customers c USING (customerID)
GROUP BY a.n_protective
ORDER BY a.n_protective;
