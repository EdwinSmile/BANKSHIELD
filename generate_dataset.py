"""
Generates a realistic synthetic banking transactions dataset matching the
structure of well-known Kaggle banking/credit-card fraud datasets.
Columns: CustomerID, Age, Gender, Occupation, Income, AccountBalance,
TransactionAmount, TransactionType, Timestamp, Location, CreditScore, Fraud
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

N_CUSTOMERS = 2000
N_TRANSACTIONS = 30000
FRAUD_RATE = 0.025  # ~2.5%, realistic for these datasets

genders = ["Male", "Female"]
occupations = ["Salaried", "Self-Employed", "Business Owner", "Student", "Retired", "Unemployed"]
txn_types = ["Deposit", "Withdrawal", "Transfer", "Payment"]
locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
             "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
             "Miami", "Seattle", "Denver", "Boston", "Atlanta"]
high_risk_locations = ["Unknown", "Offshore-X", "Foreign-Unverified"]

# ---- Build customer profiles ----
customers = []
for cid in range(1, N_CUSTOMERS + 1):
    age = int(np.clip(np.random.normal(40, 14), 18, 85))
    gender = np.random.choice(genders)
    occupation = np.random.choice(occupations, p=[0.45, 0.15, 0.10, 0.10, 0.15, 0.05])
    base_income = {
        "Salaried": 55000, "Self-Employed": 60000, "Business Owner": 90000,
        "Student": 8000, "Retired": 30000, "Unemployed": 5000
    }[occupation]
    income = max(0, np.random.normal(base_income, base_income * 0.3))
    credit_score = int(np.clip(np.random.normal(680, 80), 300, 850))
    balance = max(0, np.random.normal(income * 0.4, income * 0.25))
    prev_fraud = np.random.choice([0, 1], p=[0.95, 0.05])
    home_location = np.random.choice(locations)
    customers.append({
        "CustomerID": f"CUST{cid:05d}", "Age": age, "Gender": gender,
        "Occupation": occupation, "Income": round(income, 2),
        "CreditScore": credit_score, "BaseBalance": round(balance, 2),
        "PrevFraudHistory": prev_fraud, "HomeLocation": home_location
    })
cust_df = pd.DataFrame(customers)

# ---- Generate transactions ----
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31)
date_range_seconds = int((end_date - start_date).total_seconds())

rows = []
n_fraud_target = int(N_TRANSACTIONS * FRAUD_RATE)
fraud_indices = set(np.random.choice(N_TRANSACTIONS, n_fraud_target, replace=False))

for i in range(N_TRANSACTIONS):
    cust = cust_df.iloc[np.random.randint(0, N_CUSTOMERS)]
    is_fraud = i in fraud_indices

    txn_type = np.random.choice(txn_types, p=[0.25, 0.30, 0.25, 0.20])

    rand_seconds = np.random.randint(0, date_range_seconds)
    timestamp = start_date + timedelta(seconds=rand_seconds)

    if is_fraud:
        # Fraud patterns: odd hours, larger amounts, unusual/foreign locations
        hour = np.random.choice([0, 1, 2, 3, 4, 23], p=[0.2, 0.2, 0.2, 0.15, 0.15, 0.1])
        timestamp = timestamp.replace(hour=int(hour), minute=np.random.randint(0, 60))
        amount = max(10, np.random.normal(cust["BaseBalance"] * 0.6 + 800, 600))
        location = np.random.choice(high_risk_locations + [cust["HomeLocation"]], p=[0.3, 0.3, 0.2, 0.2])
        device = np.random.choice(["New Device", "Unknown Device"], p=[0.5, 0.5])
        daily_count = np.random.randint(4, 12)
        balance_at_txn = max(0, cust["BaseBalance"] - amount * np.random.uniform(0.5, 1.0))
    else:
        hour = int(np.clip(np.random.normal(14, 4), 6, 22))
        timestamp = timestamp.replace(hour=hour, minute=np.random.randint(0, 60))
        amount = max(5, np.random.exponential(150))
        location = cust["HomeLocation"] if np.random.rand() > 0.05 else np.random.choice(locations)
        device = np.random.choice(["Known Device", "Mobile App", "Web Browser"], p=[0.6, 0.25, 0.15])
        daily_count = np.random.randint(1, 4)
        balance_at_txn = max(0, cust["BaseBalance"] + np.random.normal(0, 200))

    rows.append({
        "TransactionID": f"TXN{i+1:06d}",
        "CustomerID": cust["CustomerID"],
        "Age": cust["Age"],
        "Gender": cust["Gender"],
        "Occupation": cust["Occupation"],
        "Income": cust["Income"],
        "AccountBalance": round(balance_at_txn, 2),
        "TransactionAmount": round(amount, 2),
        "TransactionType": txn_type,
        "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Location": location,
        "DeviceUsed": device,
        "CreditScore": cust["CreditScore"],
        "PreviousFraudHistory": cust["PrevFraudHistory"],
        "DailyTransactionCount": daily_count,
        "Fraud": "Yes" if is_fraud else "No"
    })

df = pd.DataFrame(rows)

# Inject a small amount of realistic messiness: missing values + duplicates
missing_idx = np.random.choice(df.index, size=int(len(df) * 0.01), replace=False)
df.loc[missing_idx, "Income"] = np.nan
missing_idx2 = np.random.choice(df.index, size=int(len(df) * 0.005), replace=False)
df.loc[missing_idx2, "CreditScore"] = np.nan

dup_rows = df.sample(n=50, random_state=1)
df = pd.concat([df, dup_rows], ignore_index=True)
df = df.sample(frac=1, random_state=7).reset_index(drop=True)

df.to_csv("/home/claude/bankshield/data/sample_banking_transactions.csv", index=False)
print(df.shape)
print(df["Fraud"].value_counts())
print(df.head(3).to_string())
