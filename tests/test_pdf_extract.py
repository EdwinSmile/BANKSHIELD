"""Tests for PDF column auto-mapping. Skipped if pdfplumber isn't installed."""
import pytest

pytest.importorskip("pdfplumber")

import pandas as pd  # noqa: E402
import pdf_extract     # noqa: E402


def test_auto_map_columns_renames_known_aliases():
    df = pd.DataFrame(columns=["Cust ID", "Sex", "Amount", "Txn ID", "City"])
    out = pdf_extract.auto_map_columns(df)
    assert "CustomerID" in out.columns
    assert "Gender" in out.columns
    assert "TransactionAmount" in out.columns
    assert "TransactionID" in out.columns
    assert "Location" in out.columns


def test_auto_map_columns_leaves_unknown_columns_untouched():
    df = pd.DataFrame(columns=["Mystery", "Age"])
    out = pdf_extract.auto_map_columns(df)
    assert "Mystery" in out.columns
    assert "Age" in out.columns
