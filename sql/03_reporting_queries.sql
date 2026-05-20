-- SQL Reporting Queries for Banking Transaction Data
-- Database: SQLite
-- Table: transactions_scored

-- 1. Overall portfolio summary
SELECT
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT customer_id) AS unique_customers,
    ROUND(SUM(amount_eur), 2) AS total_volume_eur,
    ROUND(AVG(amount_eur), 2) AS average_amount_eur,
    ROUND(MAX(amount_eur), 2) AS max_amount_eur,
    SUM(is_model_anomaly) AS model_anomalies,
    ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
FROM transactions_scored;


-- 2. Transaction volume by country
SELECT
    country,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_eur), 2) AS total_volume_eur,
    ROUND(AVG(amount_eur), 2) AS average_amount_eur,
    SUM(is_model_anomaly) AS model_anomalies,
    ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
FROM transactions_scored
GROUP BY country
ORDER BY total_volume_eur DESC;


-- 3. Transaction volume by merchant category
SELECT
    merchant_category,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_eur), 2) AS total_volume_eur,
    ROUND(AVG(amount_eur), 2) AS average_amount_eur,
    SUM(is_model_anomaly) AS model_anomalies,
    ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
FROM transactions_scored
GROUP BY merchant_category
ORDER BY total_volume_eur DESC;


-- 4. Top 10 customers by transaction volume
SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_eur), 2) AS total_volume_eur,
    ROUND(AVG(amount_eur), 2) AS average_amount_eur,
    SUM(is_model_anomaly) AS model_anomalies
FROM transactions_scored
GROUP BY customer_id
ORDER BY total_volume_eur DESC
LIMIT 10;


-- 5. CTE: customer-level anomaly profile
WITH customer_profile AS (
    SELECT
        customer_id,
        COUNT(*) AS transaction_count,
        ROUND(SUM(amount_eur), 2) AS total_volume_eur,
        ROUND(AVG(amount_eur), 2) AS average_amount_eur,
        SUM(is_model_anomaly) AS model_anomalies,
        ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
    FROM transactions_scored
    GROUP BY customer_id
)
SELECT
    customer_id,
    transaction_count,
    total_volume_eur,
    average_amount_eur,
    model_anomalies,
    anomaly_rate_percent
FROM customer_profile
WHERE model_anomalies > 0
ORDER BY model_anomalies DESC, anomaly_rate_percent DESC, total_volume_eur DESC
LIMIT 20;


-- 6. CTE: high-value transactions compared to customer average
WITH customer_amount_stats AS (
    SELECT
        customer_id,
        AVG(amount_eur) AS customer_avg_amount,
        MAX(amount_eur) AS customer_max_amount
    FROM transactions_scored
    GROUP BY customer_id
)
SELECT
    t.transaction_id,
    t.customer_id,
    ROUND(t.amount_eur, 2) AS amount_eur,
    ROUND(s.customer_avg_amount, 2) AS customer_avg_amount,
    ROUND(t.amount_eur / s.customer_avg_amount, 2) AS amount_vs_customer_average,
    t.country,
    t.merchant_category,
    t.is_model_anomaly,
    ROUND(t.anomaly_score, 4) AS anomaly_score
FROM transactions_scored t
JOIN customer_amount_stats s
    ON t.customer_id = s.customer_id
WHERE t.amount_eur > 3 * s.customer_avg_amount
ORDER BY amount_vs_customer_average DESC
LIMIT 20;


-- 7. Night and foreign transaction profile
SELECT
    is_night_transaction,
    is_foreign_country,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_eur), 2) AS total_volume_eur,
    SUM(is_model_anomaly) AS model_anomalies,
    ROUND(100.0 * SUM(is_model_anomaly) / COUNT(*), 2) AS anomaly_rate_percent
FROM transactions_scored
GROUP BY
    is_night_transaction,
    is_foreign_country
ORDER BY anomaly_rate_percent DESC;


-- 8. Highest anomaly scores
SELECT
    transaction_id,
    customer_id,
    ROUND(amount_eur, 2) AS amount_eur,
    transaction_hour,
    country,
    merchant_category,
    is_model_anomaly,
    ROUND(anomaly_score, 4) AS anomaly_score,
    explanation
FROM transactions_scored
ORDER BY anomaly_score DESC
LIMIT 20;
