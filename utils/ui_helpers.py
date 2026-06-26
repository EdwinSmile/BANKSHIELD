"""
Shared UI helpers to keep the dashboard friendly for non-technical users:
plain-language KPI cards, explainer boxes, consistent styling, and a
user-selectable visual theme.

Visual system: report-canvas look — flat, square-cornered cards, hairline
borders, dense layout — available in several selectable color themes.
"""
import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------
# THEMES
# Each theme defines the full set of colors the rest of the app reads.
# Adding a new theme = adding one entry here; nothing else has to change.
# ---------------------------------------------------------------------
THEMES = {
    "Power BI Blue": {
        "palette": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7",
                    "#744EC2", "#D9B300", "#D64550"],
        "accent": "#118DFF",
        "ink": "#252423",
        "subtext": "#605E5C",
        "border": "#E1E1E1",
        "canvas": "#F3F2F1",
        "card_bg": "#FFFFFF",
        "sidebar_bg": "#FFFFFF",
        "red": "#D64550",
        "amber": "#D9B300",
        "green": "#107C41",
        "heat_low": "#FFFFFF",
        "heat_high": "#118DFF",
    },
    "Dark Mode": {
        "palette": ["#3DA1FF", "#7B83EB", "#FF8C5A", "#C77DFF", "#FF7AC6",
                    "#9D8DF1", "#F2C94C", "#FF6B6B"],
        "accent": "#3DA1FF",
        "ink": "#F3F2F1",
        "subtext": "#B3B0AD",
        "border": "#3A3A3A",
        "canvas": "#1E1E1E",
        "card_bg": "#262626",
        "sidebar_bg": "#181818",
        "red": "#FF6B6B",
        "amber": "#F2C94C",
        "green": "#3DDC97",
        "heat_low": "#262626",
        "heat_high": "#3DA1FF",
    },
    "Colorblind Safe": {
        # Okabe-Ito palette — distinguishable for the most common forms of CVD.
        "palette": ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9",
                    "#D55E00", "#F0E442", "#000000"],
        "accent": "#0072B2",
        "ink": "#202020",
        "subtext": "#5A5A5A",
        "border": "#D8D8D8",
        "canvas": "#F4F4F4",
        "card_bg": "#FFFFFF",
        "sidebar_bg": "#FFFFFF",
        "red": "#D55E00",
        "amber": "#E69F00",
        "green": "#009E73",
        "heat_low": "#FFFFFF",
        "heat_high": "#0072B2",
    },
    "Monochrome Slate": {
        "palette": ["#334155", "#64748B", "#94A3B8", "#1E293B", "#475569",
                    "#0F172A", "#CBD5E1", "#7C8896"],
        "accent": "#334155",
        "ink": "#1E1E1E",
        "subtext": "#6B7280",
        "border": "#DADDE1",
        "canvas": "#F5F6F7",
        "card_bg": "#FFFFFF",
        "sidebar_bg": "#FFFFFF",
        "red": "#7A2E2E",
        "amber": "#8A6D1A",
        "green": "#2F4F3E",
        "heat_low": "#FFFFFF",
        "heat_high": "#334155",
    },
}

DEFAULT_THEME = "Power BI Blue"


def get_theme() -> dict:
    """Returns the currently active theme dict, defaulting if none selected yet."""
    name = st.session_state.get("active_theme", DEFAULT_THEME)
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def theme_picker():
    """Sidebar control letting the user pick the dashboard's color theme via buttons."""
    if "active_theme" not in st.session_state:
        st.session_state["active_theme"] = DEFAULT_THEME

    st.sidebar.caption("Theme")
    choice = st.sidebar.segmented_control(
        "Theme", options=list(THEMES.keys()),
        default=st.session_state["active_theme"],
        label_visibility="collapsed",
        key="theme_picker_widget"
    )
    if choice:
        st.session_state["active_theme"] = choice


def chart_type_toggle(label: str, options: list, key: str, default: str | None = None):
    """
    Renders a small button-style toggle for choosing how a single chart is
    visualized (e.g. Bar vs Pie). Returns the selected option. Persists the
    user's choice in session_state across reruns/pages.
    """
    state_key = f"chart_choice_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default or options[0]

    choice = st.segmented_control(
        label, options=options,
        default=st.session_state[state_key],
        key=f"widget_{state_key}"
    )
    if choice:
        st.session_state[state_key] = choice
    return st.session_state[state_key]


def inject_css():
    t = get_theme()
    st.markdown(f"""
    <style>
    html, body, [class*="css"] {{
        font-family: "Segoe UI", "Segoe UI Web", -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    }}

    .stApp {{
        background-color: {t['canvas']};
    }}

    [data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']};
        border-right: 1px solid {t['border']};
    }}

    [data-testid="stHeader"] {{
        background-color: {t['canvas']};
    }}

    h1, h2, h3, h4 {{
        color: {t['ink']};
        font-weight: 600;
        letter-spacing: 0;
    }}

    h1 {{ font-size: 22px; border-bottom: 1px solid {t['border']}; padding-bottom: 10px; }}
    h3 {{ font-size: 15px; text-transform: uppercase; letter-spacing: 0.03em; color: {t['subtext']}; }}

    p, span, div, label {{ color: {t['ink']}; }}

    /* Flat, square-cornered "visual" cards, report-canvas style */
    .kpi-card {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-top: 3px solid {t['accent']};
        border-radius: 0;
        padding: 14px 16px;
        text-align: left;
        box-shadow: none;
    }}
    .kpi-value {{
        font-size: 26px;
        font-weight: 600;
        color: {t['ink']};
        margin: 2px 0 0 0;
        line-height: 1.15;
    }}
    .kpi-label {{
        font-size: 11px;
        color: {t['subtext']};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin: 0;
        font-weight: 600;
    }}
    .kpi-sub {{
        font-size: 11.5px;
        color: {t['subtext']};
        margin-top: 4px;
    }}

    .explain-box {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-left: 3px solid {t['accent']};
        border-radius: 0;
        padding: 10px 14px;
        margin: 8px 0 16px 0;
        font-size: 13.5px;
        color: {t['ink']};
    }}

    .risk-high {{ color: {t['red']}; font-weight: 600; }}
    .risk-medium {{ color: {t['amber']}; font-weight: 600; }}
    .risk-low {{ color: {t['green']}; font-weight: 600; }}
    .risk-dot {{
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 0;
        margin-right: 6px;
        vertical-align: middle;
    }}
    .risk-dot-high {{ background: {t['red']}; }}
    .risk-dot-medium {{ background: {t['amber']}; }}
    .risk-dot-low {{ background: {t['green']}; }}

    .step-badge {{
        display: inline-block;
        background: {t['accent']};
        color: white;
        border-radius: 0;
        width: 22px; height: 22px;
        text-align: center;
        line-height: 22px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }}

    /* Flatten Streamlit's native rounded elements to match the report-canvas look */
    div[data-testid="stMetric"] {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-top: 3px solid {t['accent']};
        padding: 10px 14px;
        border-radius: 0;
    }}
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] div {{
        color: {t['ink']} !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        border-radius: 0;
        border: 1px solid {t['border']};
        font-weight: 600;
        font-size: 13px;
        background-color: {t['card_bg']};
        color: {t['ink']};
    }}
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
        background-color: {t['accent']};
        border-color: {t['accent']};
        color: #FFFFFF;
    }}
    div[data-testid="stExpander"] {{
        border-radius: 0;
        border: 1px solid {t['border']};
        background-color: {t['card_bg']};
    }}
    div[data-testid="stFileUploader"] section {{
        border-radius: 0;
        border: 1px dashed {t['border']};
        background-color: {t['card_bg']};
    }}
    div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
        border-radius: 0 !important;
        background-color: {t['card_bg']} !important;
        color: {t['ink']} !important;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {t['border']};
    }}
    .stAlert {{
        border-radius: 0;
    }}
    div[data-testid="stTabs"] button {{
        border-radius: 0;
    }}

    /* Segmented control / button-group toggles (theme picker, chart-type toggles) */
    div[data-testid="stSegmentedControl"] label {{
        border-radius: 0 !important;
        border: 1px solid {t['border']} !important;
    }}
    div[data-testid="stSegmentedControl"] label[data-checked="true"] {{
        background-color: {t['accent']} !important;
        border-color: {t['accent']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def pbi_layout(fig, height=380):
    """Apply the active theme's report-canvas styling to a Plotly figure."""
    t = get_theme()
    fig.update_layout(
        height=height,
        font=dict(family="Segoe UI, Arial, sans-serif", size=12, color=t['ink']),
        plot_bgcolor=t['card_bg'],
        paper_bgcolor=t['card_bg'],
        margin=dict(l=40, r=20, t=30, b=40),
        colorway=t['palette'],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=11, color=t['ink'])),
    )
    fig.update_xaxes(showgrid=False, linecolor=t['border'], ticks="outside", tickcolor=t['border'],
                      color=t['ink'])
    fig.update_yaxes(showgrid=True, gridcolor=t['canvas'], zeroline=False, color=t['ink'])
    return fig


def get_color_maps():
    """Returns (risk_color_map, fraud_color_map) built from the active theme."""
    t = get_theme()
    risk_map = {"Low Risk": t['green'], "Medium Risk": t['amber'], "High Risk": t['red']}
    fraud_map = {"Fraudulent": t['red'], "Legitimate": t['accent']}
    return risk_map, fraud_map


def get_heatmap_scale():
    t = get_theme()
    return [[0, t['red']], [0.5, t['heat_low']], [1, t['heat_high']]]


def explain(text: str):
    st.markdown(f'<div class="explain-box">{text}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = ""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">{label}</p>
        <p class="kpi-value">{value}</p>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def risk_badge(level: str) -> str:
    level_lower = str(level).lower()
    if "high" in level_lower:
        return f'<span class="risk-high"><span class="risk-dot risk-dot-high"></span>{level}</span>'
    elif "medium" in level_lower:
        return f'<span class="risk-medium"><span class="risk-dot risk-dot-medium"></span>{level}</span>'
    elif "low" in level_lower:
        return f'<span class="risk-low"><span class="risk-dot risk-dot-low"></span>{level}</span>'
    return level


def step_header(num: int, title: str):
    st.markdown(f'<h3><span class="step-badge">{num}</span>{title}</h3>', unsafe_allow_html=True)


REQUIRED_COLUMNS = [
    "CustomerID", "Age", "Gender", "Occupation", "Income", "AccountBalance",
    "TransactionAmount", "TransactionType", "Timestamp", "Location", "CreditScore", "Fraud"
]

OPTIONAL_COLUMNS = ["TransactionID", "DeviceUsed", "PreviousFraudHistory", "DailyTransactionCount"]


def validate_columns(df: pd.DataFrame) -> tuple[bool, list]:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return len(missing) == 0, missing


def ensure_optional_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "TransactionID" not in df.columns:
        df["TransactionID"] = [f"TXN{i+1:06d}" for i in range(len(df))]
    if "DeviceUsed" not in df.columns:
        df["DeviceUsed"] = "Unknown Device"
    if "PreviousFraudHistory" not in df.columns:
        df["PreviousFraudHistory"] = 0
    if "DailyTransactionCount" not in df.columns:
        df["DailyTransactionCount"] = 1
    return df
