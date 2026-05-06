from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report


RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_synthetic_transactions(n_normal: int = 1500, n_anomalies: int = 45) -> pd.DataFrame:
    normal_data = pd.DataFrame({
        "transaction_id": [f"TXN_{i:05d}" for i in range(n_normal)],
        "customer_id": np.random.choice([f"CUST_{i:04d}" for i in range(250)], size=n_normal),
        "amount_eur": np.round(np.random.lognormal(mean=3.4, sigma=0.7, size=n_normal), 2),
        "transaction_hour": np.random.choice(
    	 range(24),
    	 size=n_normal,
    	 p=np.array([
	        0.01, 0.01, 0.005, 0.005, 0.005, 0.01,
	        0.03, 0.05, 0.06, 0.07, 0.07, 0.07,
	        0.08, 0.08, 0.08, 0.07, 0.07, 0.06,
	        0.06, 0.05, 0.04, 0.03, 0.02, 0.015
	 ]) / np.array([
	        0.01, 0.01, 0.005, 0.005, 0.005, 0.01,
	        0.03, 0.05, 0.06, 0.07, 0.07, 0.07,
	        0.08, 0.08, 0.08, 0.07, 0.07, 0.06,
	        0.06, 0.05, 0.04, 0.03, 0.02, 0.015
	    	]).sum()
	),
        "country": np.random.choice(
            ["DE", "FR", "NL", "AT", "IT", "ES"],
            size=n_normal,
            p=[0.82, 0.05, 0.04, 0.03, 0.03, 0.03]
        ),
        "merchant_category": np.random.choice(
            ["groceries", "restaurant", "transport", "online_retail", "utilities", "travel"],
            size=n_normal,
            p=[0.25, 0.20, 0.18, 0.17, 0.12, 0.08]
        ),
        "is_synthetic_anomaly": 0
    })

    anomaly_data = pd.DataFrame({
        "transaction_id": [f"TXN_ANOM_{i:05d}" for i in range(n_anomalies)],
        "customer_id": np.random.choice([f"CUST_{i:04d}" for i in range(250)], size=n_anomalies),
        "amount_eur": np.round(np.random.uniform(1200, 9000, size=n_anomalies), 2),
        "transaction_hour": np.random.choice([0, 1, 2, 3, 4, 23], size=n_anomalies),
        "country": np.random.choice(["US", "SG", "AE", "BR", "JP"], size=n_anomalies),
        "merchant_category": np.random.choice(
            ["luxury_goods", "cash_withdrawal", "unknown_merchant", "electronics"],
            size=n_anomalies
        ),
        "is_synthetic_anomaly": 1
    })

    transactions = pd.concat([normal_data, anomaly_data], ignore_index=True)
    transactions = transactions.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    return transactions


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["amount_log"] = np.log1p(df["amount_eur"])
    df["is_night_transaction"] = df["transaction_hour"].isin([0, 1, 2, 3, 4, 23]).astype(int)
    df["is_foreign_country"] = (df["country"] != "DE").astype(int)

    high_risk_categories = ["luxury_goods", "cash_withdrawal", "unknown_merchant", "electronics"]
    df["is_unusual_category"] = df["merchant_category"].isin(high_risk_categories).astype(int)

    return df


def train_anomaly_model(df: pd.DataFrame) -> pd.DataFrame:
    feature_columns = [
        "amount_log",
        "transaction_hour",
        "is_night_transaction",
        "is_foreign_country",
        "is_unusual_category",
    ]

    X = df[feature_columns]

    model = IsolationForest(
        n_estimators=200,
        contamination=0.03,
        random_state=RANDOM_SEED
    )

    model.fit(X)

    df = df.copy()
    df["model_prediction"] = model.predict(X)
    df["is_model_anomaly"] = (df["model_prediction"] == -1).astype(int)
    df["anomaly_score"] = -model.decision_function(X)

    return df


def explain_transaction(row: pd.Series, amount_threshold: float) -> str:
    reasons = []

    if row["amount_eur"] > amount_threshold:
        reasons.append("unusually high amount")

    if row["is_night_transaction"] == 1:
        reasons.append("transaction at uncommon hour")

    if row["is_foreign_country"] == 1:
        reasons.append("foreign country transaction")

    if row["is_unusual_category"] == 1:
        reasons.append("unusual merchant category")

    if not reasons:
        reasons.append("unusual combination of transaction features")

    return "; ".join(reasons)


def add_explanations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    amount_threshold = df["amount_eur"].quantile(0.97)

    df["explanation"] = df.apply(
        lambda row: explain_transaction(row, amount_threshold)
        if row["is_model_anomaly"] == 1
        else "",
        axis=1
    )

    return df


def create_plot(df: pd.DataFrame) -> None:
    """
    Creates visualizations for the anomaly detection results.
    """

    # Plot 1: Amount distribution with log scale
    plt.figure(figsize=(9, 5))

    normal_amounts = df.loc[df["is_model_anomaly"] == 0, "amount_eur"]
    anomaly_amounts = df.loc[df["is_model_anomaly"] == 1, "amount_eur"]

    plt.hist(normal_amounts, bins=40, alpha=0.7, label="Model: normal")
    plt.hist(anomaly_amounts, bins=40, alpha=0.7, label="Model: anomaly")

    plt.xscale("log")
    plt.title("Transaction Amount Distribution (Log Scale)")
    plt.xlabel("Transaction amount in EUR, log scale")
    plt.ylabel("Number of transactions")
    plt.legend()
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "anomaly_amount_distribution_log.png", dpi=150)
    plt.close()

    # Plot 2: Anomaly score vs amount
    plt.figure(figsize=(9, 5))

    normal = df[df["is_model_anomaly"] == 0]
    anomalies = df[df["is_model_anomaly"] == 1]

    plt.scatter(
        normal["amount_eur"],
        normal["anomaly_score"],
        alpha=0.5,
        label="Model: normal"
    )

    plt.scatter(
        anomalies["amount_eur"],
        anomalies["anomaly_score"],
        alpha=0.8,
        label="Model: anomaly"
    )

    plt.xscale("log")
    plt.title("Anomaly Score vs. Transaction Amount")
    plt.xlabel("Transaction amount in EUR, log scale")
    plt.ylabel("Anomaly score")
    plt.legend()
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "anomaly_score_vs_amount.png", dpi=150)
    plt.close()
    plt.figure(figsize=(9, 5))

    normal_amounts = df.loc[df["is_model_anomaly"] == 0, "amount_eur"]
    anomaly_amounts = df.loc[df["is_model_anomaly"] == 1, "amount_eur"]

    plt.hist(normal_amounts, bins=40, alpha=0.7, label="Model: normal")
    plt.hist(anomaly_amounts, bins=40, alpha=0.7, label="Model: anomaly")

    plt.title("Transaction Amount Distribution")
    plt.xlabel("Transaction amount in EUR")
    plt.ylabel("Number of transactions")
    plt.legend()
    plt.tight_layout()

    plt.savefig(OUTPUT_DIR / "anomaly_amount_distribution.png", dpi=150)
    plt.close()


def main() -> None:
    transactions = generate_synthetic_transactions()
    transactions = add_features(transactions)
    transactions = train_anomaly_model(transactions)
    transactions = add_explanations(transactions)

    transactions_sorted = transactions.sort_values("anomaly_score", ascending=False)

    transactions_sorted.to_csv(OUTPUT_DIR / "transactions_scored.csv", index=False)

    top_anomalies = transactions_sorted.loc[
        transactions_sorted["is_model_anomaly"] == 1,
        [
            "transaction_id",
            "customer_id",
            "amount_eur",
            "transaction_hour",
            "country",
            "merchant_category",
            "anomaly_score",
            "explanation",
            "is_synthetic_anomaly"
        ]
    ].head(25)

    top_anomalies.to_csv(OUTPUT_DIR / "top_anomalies.csv", index=False)

    create_plot(transactions)

    print("\nProject completed successfully.")
    print(f"Total transactions: {len(transactions)}")
    print(f"Model-flagged anomalies: {transactions['is_model_anomaly'].sum()}")

    print("\nTop 10 anomalies:")
    print(top_anomalies.head(10).to_string(index=False))

    print("\nSynthetic label evaluation:")
    print(classification_report(
        transactions["is_synthetic_anomaly"],
        transactions["is_model_anomaly"],
        target_names=["normal", "synthetic_anomaly"]
    ))

    print("\nFiles created:")
    print("- outputs/transactions_scored.csv")
    print("- outputs/top_anomalies.csv")
    print("- outputs/anomaly_amount_distribution.png")


if __name__ == "__main__":
    main()
