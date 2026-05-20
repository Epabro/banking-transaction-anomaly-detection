-- SQL Data Quality Checks for Banking Transaction Data
-- Database: SQLite
-- Table: transactions_scored

-- 1. Overview: number of rows and customers
SELECT
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM transactions_scored;


-- 2. Missing required values
SELECT
    SUM(CASE WHEN transaction_id IS NULL OR transaction_id = '' THEN 1 ELSE 0 END) AS missing_transaction_id,
    SUM(CASE WHEN customer_id IS NULL OR customer_id = '' THEN 1 ELSE 0 END) AS missing_customer_id,
    SUM(CASE WHEN amount_eur IS NULL THEN 1 ELSE 0 END) AS missing_amount_eur,
    SUM(CASE WHEN transaction_hour IS NULL THEN 1 ELSE 0 END) AS missing_transaction_hour,
    SUM(CASE WHEN country IS NULL OR country = '' THEN 1 ELSE 0 END) AS missing_country,
    SUM(CASE WHEN merchant_category IS NULL OR merchant_category = '' THEN 1 ELSE 0 END) AS missing_merchant_category
FROM transactions_scored;


-- 3. Duplicate transaction IDs
SELECT
    transaction_id,
    COUNT(*) AS duplicate_count
FROM transactions_scored
GROUP BY transaction_id
HAVING COUNT(*) > 1;


-- 4. Plausibility check: invalid amounts
SELECT
    transaction_id,
    customer_id,
    amount_eur,
    country,
    merchant_category
FROM transactions_scored
WHERE amount_eur <= 0
   OR amount_eur > 100000
ORDER BY amount_eur DESC;


-- 5. Plausibility check: invalid transaction hours
SELECT
    transaction_id,
    customer_id,
    transaction_hour
FROM transactions_scored
WHERE transaction_hour < 0
   OR transaction_hour > 23;


-- 6. Category-level anomaly rate
SELECT
    merchant_category,
    COUNT(*) AS transaction_count,
    SUM(is_model_anomaly) AS model_anomalies,
    ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
FROM transactions_scored
GROUP BY merchant_category
ORDER BY anomaly_rate_percent DESC;


-- 7. Country-level anomaly rate
SELECT
    country,
    COUNT(*) AS transaction_count,
    SUM(is_model_anomaly) AS model_anomalies,
    ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
FROM transactions_scored
GROUP BY country
ORDER BY anomaly_rate_percent DESC;


-- 8. Model anomalies without explanation
SELECT
    transaction_id,
    customer_id,
    amount_eur,
    country,
    merchant_category,
    anomaly_score,
    explanation
FROM transactions_scored
WHERE is_model_anomaly = 1
  AND (explanation IS NULL OR explanation = '');


-- 9. Consistency check: model anomaly flags vs. explanation text
SELECT
    transaction_id,
    is_night_transaction,
    is_foreign_country,
    is_unusual_category,
    explanation
FROM transactions_scored
WHERE is_model_anomaly = 1
  AND explanation IS NOT NULL
  AND explanation != ''
  AND (
       (is_night_transaction = 1 AND explanation NOT LIKE '%uncommon hour%')
    OR (is_foreign_country = 1 AND explanation NOT LIKE '%foreign country%')
    OR (is_unusual_category = 1 AND explanation NOT LIKE '%unusual merchant category%')
  );
