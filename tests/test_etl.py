"""Tests for the ETL / data-warehouse layer."""


def test_clean_data_removes_duplicates_and_fills_missing(etl_module, raw_df):
    clean, report = etl_module.clean_data(raw_df)
    assert report["duplicates_found"] >= 1
    assert clean.duplicated().sum() == 0
    assert clean.isna().sum().sum() == 0          # everything filled
    assert "Income" in report["missing_values_filled"]


def test_build_warehouse_and_roundtrip(etl_module, raw_df):
    summary = etl_module.build_warehouse(raw_df)
    assert summary["n_transactions"] > 0
    assert etl_module.warehouse_exists() is True

    fact = etl_module.get_fact_with_dims()
    for col in ["TransactionID", "CustomerID", "FraudFlag", "TransactionType",
                "Location", "Hour", "RiskLevel"]:
        assert col in fact.columns
    assert len(fact) == summary["n_transactions"]
    assert set(fact["FraudFlag"].unique()).issubset({0, 1})


def test_update_customer_risk_persists_and_busts_cache(etl_module, raw_df):
    etl_module.build_warehouse(raw_df)
    fact = etl_module.get_fact_with_dims()
    assert (fact["RiskLevel"] == "Unscored").all()

    a_customer = fact["CustomerID"].iloc[0]
    etl_module.update_customer_risk({a_customer: "High Risk"})

    fact2 = etl_module.get_fact_with_dims()          # must reflect the update, not a stale cache
    updated = fact2.loc[fact2["CustomerID"] == a_customer, "RiskLevel"]
    assert (updated == "High Risk").all()


def test_warehouse_exists_false_when_empty(etl_module):
    assert etl_module.warehouse_exists() is False
