DROP TABLE IF EXISTS transactions_scored;

CREATE TABLE transactions_scored (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    amount_eur REAL NOT NULL,
    transaction_hour INTEGER NOT NULL,
    country TEXT NOT NULL,
    merchant_category TEXT NOT NULL,
    is_synthetic_anomaly INTEGER NOT NULL,
    amount_log REAL,
    is_night_transaction INTEGER NOT NULL,
    is_foreign_country INTEGER NOT NULL,
    is_unusual_category INTEGER NOT NULL,
    model_prediction INTEGER NOT NULL,
    is_model_anomaly INTEGER NOT NULL,
    anomaly_score REAL NOT NULL,
    explanation TEXT
);
