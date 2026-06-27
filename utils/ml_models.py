"""
Data Mining module for BankShield:
  1. Fraud Classification (Decision Tree / Random Forest)
  2. Customer Risk Clustering (K-Means)
Designed to be called from Streamlit; returns plain dicts/dataframes
so the UI layer never has to touch sklearn objects directly except
for the trained model object itself (kept in session_state).
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc
)

FRAUD_FEATURES = [
    "Age", "AccountBalance", "TransactionAmount", "CreditScore",
    "PreviousFraudHistory", "DailyTransactionCount",
    "Gender", "TransactionType", "DeviceUsed", "Hour"
]

CLUSTER_FEATURES_MAP = {
    "Transaction Frequency": "DailyTransactionCount",
    "Average Transaction Amount": "TransactionAmount",
    "Account Balance": "AccountBalance",
    "Credit Score": "CreditScore",
    "Monthly Spending": "TransactionAmount",
    "Previous Fraud Count": "PreviousFraudHistory",
}


# ---------------------------------------------------------------------
# FRAUD CLASSIFICATION
# ---------------------------------------------------------------------
def train_fraud_model(df: pd.DataFrame, algorithm: str = "Random Forest", test_size: float = 0.25):
    data = df.copy()
    data = data.dropna(subset=["FraudFlag"])

    available_features = [f for f in FRAUD_FEATURES if f in data.columns]
    X = data[available_features].copy()
    y = data["FraudFlag"].astype(int)

    # Encode categoricals. LabelEncoder is target-independent (it only maps
    # categories to integers), so fitting it on the full column does not leak the
    # label into the model.
    encoders = {}
    for col in X.select_dtypes(include=["object"]).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le

    # Only stratify when every class has at least 2 samples; otherwise
    # train_test_split raises on tiny or extremely imbalanced uploads.
    class_counts = y.value_counts()
    stratify = y if (y.nunique() > 1 and class_counts.min() >= 2) else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )

    # Impute missing numbers using TRAIN medians only, then apply the same fill to
    # the test set and the full scoring set. Computing the median over all rows
    # (as before) leaks test-set information into training.
    fill_values = X_train.median(numeric_only=True)
    X_train = X_train.fillna(fill_values)
    X_test = X_test.fillna(fill_values)

    if algorithm == "Decision Tree":
        model = DecisionTreeClassifier(max_depth=6, random_state=42, class_weight="balanced")
    else:
        model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight="balanced")

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    if y_proba is not None and y_test.nunique() > 1:
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        metrics["roc_fpr"] = fpr.tolist()
        metrics["roc_tpr"] = tpr.tolist()
        metrics["auc"] = auc(fpr, tpr)

    feature_importance = None
    if hasattr(model, "feature_importances_"):
        feature_importance = pd.DataFrame({
            "Feature": available_features,
            "Importance": model.feature_importances_
        }).sort_values("Importance", ascending=False)

    full_X = X.fillna(fill_values)
    full_pred = model.predict(full_X)
    full_proba = model.predict_proba(full_X)[:, 1] if hasattr(model, "predict_proba") else full_pred

    predictions_df = data[["TransactionID", "CustomerID"]].copy() if "TransactionID" in data.columns else pd.DataFrame()
    predictions_df["ActualFraud"] = y.values
    predictions_df["PredictedFraud"] = full_pred
    predictions_df["FraudProbability"] = full_proba
    # Flag which rows were held out of training. Predictions on training rows are
    # optimistic (the model has seen them), so the UI can be honest about it.
    predictions_df["InTestSet"] = predictions_df.index.isin(X_test.index)

    return {
        "model": model,
        "encoders": encoders,
        "features_used": available_features,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "predictions": predictions_df,
        "algorithm": algorithm,
    }


# ---------------------------------------------------------------------
# CUSTOMER RISK CLUSTERING
# ---------------------------------------------------------------------
def run_customer_clustering(df: pd.DataFrame, n_clusters: int = 3):
    customer_agg = df.groupby("CustomerID").agg(
        DailyTransactionCount=("DailyTransactionCount", "mean"),
        TransactionAmount=("TransactionAmount", "mean"),
        AccountBalance=("AccountBalance", "mean"),
        CreditScore=("CreditScore", "mean"),
        PreviousFraudHistory=("PreviousFraudHistory", "max"),
        FraudFlag=("FraudFlag", "sum"),
    ).reset_index()

    feature_cols = ["DailyTransactionCount", "TransactionAmount", "AccountBalance",
                     "CreditScore", "PreviousFraudHistory"]
    X = customer_agg[feature_cols].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    customer_agg["Cluster"] = kmeans.fit_predict(X_scaled)

    # Rank clusters by a composite risk score so labels are meaningful
    cluster_profile = customer_agg.groupby("Cluster").agg(
        AvgAmount=("TransactionAmount", "mean"),
        AvgFraudCount=("FraudFlag", "mean"),
        AvgPrevFraud=("PreviousFraudHistory", "mean"),
        AvgCreditScore=("CreditScore", "mean"),
        Count=("CustomerID", "count"),
    ).reset_index()

    cluster_profile["risk_score"] = (
        cluster_profile["AvgAmount"].rank(pct=True) * 0.35
        + cluster_profile["AvgFraudCount"].rank(pct=True) * 0.35
        + cluster_profile["AvgPrevFraud"].rank(pct=True) * 0.2
        + (1 - cluster_profile["AvgCreditScore"].rank(pct=True)) * 0.1
    )
    cluster_profile = cluster_profile.sort_values("risk_score").reset_index(drop=True)

    if n_clusters == 3:
        labels = ["Low Risk", "Medium Risk", "High Risk"]
    else:
        labels = [f"Risk Tier {i+1}" for i in range(n_clusters)]

    cluster_to_label = {row["Cluster"]: labels[i] for i, row in cluster_profile.iterrows()}
    customer_agg["RiskLevel"] = customer_agg["Cluster"].map(cluster_to_label)

    cluster_profile["RiskLevel"] = cluster_profile["Cluster"].map(cluster_to_label)

    return {
        "customer_clusters": customer_agg,
        "cluster_profile": cluster_profile,
        "label_map": cluster_to_label,
        "feature_cols": feature_cols,
    }
