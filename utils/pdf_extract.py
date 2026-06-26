"""
PDF data extraction for BankShield's Dataset page.
Pulls tabular transaction data out of an uploaded PDF using pdfplumber,
stitches multi-page tables together, and returns a pandas DataFrame
in the same shape a CSV/Excel upload would produce.
"""
import io
import pandas as pd
import pdfplumber


def _clean_header(cells):
    return [str(c).strip() if c is not None else "" for c in cells]


def extract_tables_from_pdf(file_bytes: bytes) -> tuple[pd.DataFrame | None, dict]:
    """
    Extracts every table found across all pages of a PDF and stitches
    tables with matching headers into one DataFrame (handles statements
    where the table repeats per page with a header row each time).
    Returns (dataframe_or_None, info_dict).
    """
    info = {"pages": 0, "tables_found": 0, "rows_extracted": 0}
    tables_by_header = {}

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        info["pages"] = len(pdf.pages)
        for page in pdf.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                if not table or len(table) < 2:
                    continue
                header = tuple(_clean_header(table[0]))
                if not any(header):
                    continue
                rows = table[1:]
                tables_by_header.setdefault(header, []).extend(rows)
                info["tables_found"] += 1

    if not tables_by_header:
        return None, info

    # Use the header group with the most rows — the dominant transaction table.
    best_header = max(tables_by_header, key=lambda h: len(tables_by_header[h]))
    rows = tables_by_header[best_header]
    columns = [c if c else f"Column{i+1}" for i, c in enumerate(best_header)]

    df = pd.DataFrame(rows, columns=columns)
    df = df.dropna(how="all")
    df = df[~(df.apply(lambda r: list(r) == list(columns), axis=1))]  # drop repeated header rows
    info["rows_extracted"] = len(df)

    return df.reset_index(drop=True), info


COLUMN_ALIASES = {
    "customerid": "CustomerID", "customer id": "CustomerID", "custid": "CustomerID",
    "age": "Age",
    "gender": "Gender", "sex": "Gender",
    "occupation": "Occupation", "job": "Occupation",
    "income": "Income", "annualincome": "Income",
    "accountbalance": "AccountBalance", "balance": "AccountBalance",
    "transactionamount": "TransactionAmount", "amount": "TransactionAmount",
    "transactiontype": "TransactionType", "type": "TransactionType",
    "timestamp": "Timestamp", "date": "Timestamp", "transactiondate": "Timestamp",
    "location": "Location", "city": "Location",
    "creditscore": "CreditScore",
    "fraud": "Fraud", "isfraud": "Fraud", "fraudflag": "Fraud",
    "transactionid": "TransactionID", "txnid": "TransactionID",
    "deviceused": "DeviceUsed", "device": "DeviceUsed",
}


def auto_map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort rename of extracted PDF columns to BankShield's expected schema."""
    rename_map = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "").replace("_", "")
        if key in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[key]
    return df.rename(columns=rename_map)
