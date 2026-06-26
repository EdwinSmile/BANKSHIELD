import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))
from ui_helpers import inject_css, theme_picker

st.set_page_config(
    page_title="BankShield | Fraud Detection Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

home = st.Page("pages/0_Home.py", title="Home", default=True)
dataset = st.Page("pages/1_Dataset.py", title="Dataset")
preprocessing = st.Page("pages/2_Preprocessing.py", title="Preprocessing")
exploration = st.Page("pages/3_Exploration.py", title="Data Exploration")
fraud_detection = st.Page("pages/4_Fraud_Detection.py", title="Fraud Detection")
customer_risk = st.Page("pages/5_Customer_Risk.py", title="Customer Risk")
reports = st.Page("pages/6_Reports.py", title="Reports")

st.sidebar.title("BankShield")
st.sidebar.caption("Banking Fraud Detection & Customer Risk Dashboard")
st.sidebar.markdown("---")

pg = st.navigation(
    [home, dataset, preprocessing, exploration, fraud_detection, customer_risk, reports],
    position="sidebar"
)

st.sidebar.markdown("---")
theme_picker()

inject_css()
pg.run()
