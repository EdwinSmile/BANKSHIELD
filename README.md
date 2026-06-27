# BankShield — Banking Fraud Detection & Customer Risk Dashboard

A point-and-click dashboard for spotting fraudulent transactions and risky customers —
built so that **no coding knowledge is required to use it**. (You do need to install
it once using the steps below — that part involves a few command-line steps.)

---

## What this does

1. **Upload** a banking transactions file (or use the built-in sample data)
2. **Automatically cleans** the data (missing values, duplicates)
3. **Trains an AI model** to flag fraudulent transactions
4. **Groups customers** into Low / Medium / High risk
5. **Shows charts and a downloadable report**

Everything runs on your own computer — your data never leaves your machine.

---

## How to install and run it (one-time setup)

You'll need **Python 3.10 or newer** installed. If you don't have Python, download it
from [python.org](https://www.python.org/downloads/) first (check "Add Python to PATH"
during installation on Windows).

### Step 1 — Open a terminal in this folder
- **Windows:** open the `bankshield` folder, type `cmd` in the address bar, press Enter
- **Mac:** right-click the `bankshield` folder → "New Terminal at Folder" (or open
  Terminal and type `cd ` then drag the folder in)

### Step 2 — Install the required packages
Copy and paste this command, then press Enter:
```
pip install -r requirements.txt
```
(This downloads the tools the dashboard needs. It only needs to be done once.)

### Step 3 — Start the dashboard
```
streamlit run app.py
```
A browser tab will open automatically at `http://localhost:8501` with the dashboard.

### Step 4 — Stop the dashboard
Go back to the terminal window and press `Ctrl + C`. Closing the browser tab alone
does not stop it.

---

## Customizing how it looks

In the sidebar, under **Theme**, click any of the four buttons to change the whole
dashboard's color scheme instantly — no need to reload anything:

- **Power BI Blue** — the default, modeled on Microsoft Power BI's report style
- **Dark Mode** — dark background, easier on the eyes in low light
- **Colorblind Safe** — a palette designed to stay distinguishable for the most
  common forms of color vision deficiency
- **Monochrome Slate** — a quiet grayscale-leaning look for printing or screenshots

On top of most charts you'll also see small **"View as"** buttons — these let you
switch that individual chart between formats (e.g. Bar vs Pie, Line vs Area vs Bar,
Scatter vs Density) to see the same data however makes the most sense to you.

---

## Using the dashboard

Just follow the sidebar in order:

| Page | What to do |
|---|---|
| **Dataset** | Click "Use Sample Dataset" to try it instantly, or upload your own CSV, Excel, or PDF file |
| **Preprocessing** | Click the clean-up button — this fixes messy data automatically |
| **Data Exploration** | Browse charts — no action needed, just explore |
| **Fraud Detection** | Click "Train Fraud Detection Model" to flag suspicious transactions |
| **Customer Risk** | Click "Run Customer Risk Clustering" to group customers by risk |
| **Reports** | Download CSV reports to share with your team |

---

## Using your own data

If you upload your own file, it should have one row per transaction with these columns:

```
CustomerID, Age, Gender, Occupation, Income, AccountBalance, TransactionAmount,
TransactionType, Timestamp, Location, CreditScore, Fraud
```

`Fraud` should contain `Yes` or `No`. If a few optional columns (TransactionID,
DeviceUsed, PreviousFraudHistory, DailyTransactionCount) are missing, the dashboard
fills in reasonable defaults automatically.

**PDF statements:** if you upload a PDF, the dashboard looks for a transaction table
on each page, stitches multi-page tables together, and tries to automatically match
column headers (e.g. "Cust ID" → CustomerID, "Sex" → Gender) to the schema above.
This works best for statements with a clear table layout — not scanned images of text.

---

## About the sample dataset

The included `data/sample_banking_transactions.csv` is a **synthetic** dataset
(30,000 transactions, 2,000 customers, ~2.5% fraud rate) generated to mirror the
structure and patterns of well-known public banking-fraud datasets. It's meant for
demonstration — swap in your real data any time via the Dataset page.

---

## Technical details (for IT / data teams)

- **Frontend:** Streamlit, styled to match the Power BI report-canvas look (flat
  square-cornered cards, Segoe UI, Power BI's standard data-color palette)
- **Backend:** Python (pandas, scikit-learn, plotly, pdfplumber for PDF table extraction)
- **Database:** SQLite, star-schema data warehouse (`db/bankshield.db`, rebuilt each
  time preprocessing is run)
- **ML models:** Decision Tree / Random Forest (fraud classification), K-Means
  (customer risk clustering)
- All processing is local — nothing is sent to an external server

---

## Development

Run the test suite:
```
pip install -r requirements-dev.txt
pytest
```

The tests cover the ETL/warehouse roundtrip, the fraud and clustering models, and
the input-validation helpers. The PDF-extraction test is skipped automatically if
`pdfplumber` isn't installed.

## License

Released under the [MIT License](LICENSE).
