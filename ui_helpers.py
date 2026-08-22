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
    "BankShield Dark": {
        # Rounded, dark fintech look — inspired by the BankShield product concept:
        # deep navy canvas, soft-glow emerald accent, pill buttons, ring/dial gauges.
        "palette": ["#22C55E", "#38BDF8", "#F59E0B", "#A78BFA", "#F472B6",
                    "#2DD4BF", "#FACC15", "#FB7185"],
        "accent": "#22C55E",
        "accent_soft": "rgba(34, 197, 94, 0.14)",
        "ink": "#F3F6FA",
        "subtext": "#8A98AE",
        "border": "#22304A",
        "canvas": "#0A1220",
        "card_bg": "#101B30",
        "sidebar_bg": "#0A1220",
        "red": "#F87171",
        "amber": "#FBBF24",
        "green": "#22C55E",
        "heat_low": "#101B30",
        "heat_high": "#22C55E",
        "radius": "16px",
        "radius_sm": "10px",
        "shadow": "0 10px 30px rgba(0, 0, 0, 0.35)",
        "font": '"Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, Arial, sans-serif',
    },
    "Power BI Blue": {
        "palette": ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#E044A7",
                    "#744EC2", "#D9B300", "#D64550"],
        "accent": "#118DFF",
        "accent_soft": "rgba(17, 141, 255, 0.10)",
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
        "radius": "0",
        "radius_sm": "0",
        "shadow": "none",
        "font": '"Segoe UI", "Segoe UI Web", -apple-system, BlinkMacSystemFont, Arial, sans-serif',
    },
    "Dark Mode": {
        "palette": ["#3DA1FF", "#7B83EB", "#FF8C5A", "#C77DFF", "#FF7AC6",
                    "#9D8DF1", "#F2C94C", "#FF6B6B"],
        "accent": "#3DA1FF",
        "accent_soft": "rgba(61, 161, 255, 0.12)",
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
        "radius": "0",
        "radius_sm": "0",
        "shadow": "none",
        "font": '"Segoe UI", "Segoe UI Web", -apple-system, BlinkMacSystemFont, Arial, sans-serif',
    },
    "Colorblind Safe": {
        # Okabe-Ito palette — distinguishable for the most common forms of CVD.
        "palette": ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9",
                    "#D55E00", "#F0E442", "#000000"],
        "accent": "#0072B2",
        "accent_soft": "rgba(0, 114, 178, 0.10)",
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
        "radius": "0",
        "radius_sm": "0",
        "shadow": "none",
        "font": '"Segoe UI", "Segoe UI Web", -apple-system, BlinkMacSystemFont, Arial, sans-serif',
    },
    "Monochrome Slate": {
        "palette": ["#334155", "#64748B", "#94A3B8", "#1E293B", "#475569",
                    "#0F172A", "#CBD5E1", "#7C8896"],
        "accent": "#334155",
        "accent_soft": "rgba(51, 65, 85, 0.10)",
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
        "radius": "0",
        "radius_sm": "0",
        "shadow": "none",
        "font": '"Segoe UI", "Segoe UI Web", -apple-system, BlinkMacSystemFont, Arial, sans-serif',
    },
}

DEFAULT_THEME = "BankShield Dark"


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
    r = t.get("radius", "0")
    r_sm = t.get("radius_sm", "0")
    shadow = t.get("shadow", "none")
    font = t.get("font", '"Segoe UI", -apple-system, BlinkMacSystemFont, Arial, sans-serif')
    accent_soft = t.get("accent_soft", "rgba(0,0,0,0.05)")
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: {font};
    }}

    .stApp {{
        background-color: {t['canvas']};
    }}

    [data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']};
        border-right: 1px solid {t['border']};
    }}
    [data-testid="stSidebar"] * {{ color: {t['ink']}; }}

    [data-testid="stHeader"] {{
        background-color: {t['canvas']};
    }}

    h1, h2, h3, h4 {{
        color: {t['ink']};
        font-weight: 700;
        letter-spacing: 0;
    }}

    h1 {{ font-size: 24px; border-bottom: 1px solid {t['border']}; padding-bottom: 12px; }}
    h3 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: {t['subtext']}; font-weight: 700; }}

    p, span, div, label {{ color: {t['ink']}; }}

    /* KPI / stat cards */
    .kpi-card {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-top: 3px solid {t['accent']};
        border-radius: {r};
        padding: 16px 18px;
        text-align: left;
        box-shadow: {shadow};
        transition: transform 120ms ease, border-color 120ms ease;
    }}
    .kpi-card:hover {{ transform: translateY(-2px); border-color: {t['accent']}; }}
    .kpi-icon {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px; height: 34px;
        border-radius: {r_sm};
        background: {accent_soft};
        color: {t['accent']};
        font-size: 16px;
        margin-bottom: 10px;
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 800;
        color: {t['ink']};
        margin: 2px 0 0 0;
        line-height: 1.15;
    }}
    .kpi-label {{
        font-size: 11px;
        color: {t['subtext']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0;
        font-weight: 700;
    }}
    .kpi-sub {{
        font-size: 11.5px;
        color: {t['subtext']};
        margin-top: 4px;
    }}

    .explain-box {{
        background: {accent_soft};
        border: 1px solid {t['border']};
        border-left: 3px solid {t['accent']};
        border-radius: {r_sm};
        padding: 12px 16px;
        margin: 8px 0 16px 0;
        font-size: 13.5px;
        color: {t['ink']};
    }}

    /* Hero / landing banner */
    .hero-card {{
        background: linear-gradient(135deg, {t['card_bg']} 0%, {t['canvas']} 100%);
        border: 1px solid {t['border']};
        border-radius: {r};
        padding: 36px 40px;
        margin-bottom: 22px;
        box-shadow: {shadow};
    }}
    .hero-eyebrow {{
        display: inline-block;
        background: {accent_soft};
        color: {t['accent']};
        border-radius: 999px;
        padding: 4px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 14px;
    }}
    .hero-title {{
        font-size: 34px;
        font-weight: 800;
        color: {t['ink']};
        margin: 0 0 10px 0;
        line-height: 1.15;
    }}
    .hero-subtitle {{
        font-size: 15px;
        color: {t['subtext']};
        max-width: 640px;
        line-height: 1.55;
        margin: 0;
    }}

    /* Pill-style nav / next-step cards */
    .next-card {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-radius: {r};
        padding: 18px 20px;
        height: 100%;
        box-shadow: {shadow};
    }}
    .next-card-title {{ font-weight: 700; color: {t['ink']}; font-size: 14.5px; margin-bottom: 4px; }}
    .next-card-caption {{ color: {t['subtext']}; font-size: 12.5px; }}

    .risk-high {{ color: {t['red']}; font-weight: 700; }}
    .risk-medium {{ color: {t['amber']}; font-weight: 700; }}
    .risk-low {{ color: {t['green']}; font-weight: 700; }}
    .risk-dot {{
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
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
        border-radius: 50%;
        width: 22px; height: 22px;
        text-align: center;
        line-height: 22px;
        font-size: 12px;
        font-weight: 700;
        margin-right: 8px;
    }}

    /* Streamlit native elements, restyled to match the rounded card look */
    div[data-testid="stMetric"] {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-top: 3px solid {t['accent']};
        padding: 12px 16px;
        border-radius: {r};
        box-shadow: {shadow};
    }}
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] div {{
        color: {t['ink']} !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        border-radius: 999px;
        border: 1px solid {t['border']};
        font-weight: 700;
        font-size: 13px;
        background-color: {t['card_bg']};
        color: {t['ink']};
        padding: 8px 18px;
    }}
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
        background-color: {t['accent']};
        border-color: {t['accent']};
        color: #06170F;
        box-shadow: 0 6px 18px {accent_soft};
    }}
    div[data-testid="stExpander"] {{
        border-radius: {r_sm};
        border: 1px solid {t['border']};
        background-color: {t['card_bg']};
        overflow: hidden;
    }}
    div[data-testid="stFileUploader"] section {{
        border-radius: {r_sm};
        border: 1px dashed {t['border']};
        background-color: {t['card_bg']};
    }}
    div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
        border-radius: {r_sm} !important;
        background-color: {t['card_bg']} !important;
        color: {t['ink']} !important;
        border-color: {t['border']} !important;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid {t['border']};
        border-radius: {r_sm};
        overflow: hidden;
    }}
    .stAlert {{
        border-radius: {r_sm};
    }}
    div[data-testid="stTabs"] button {{
        border-radius: {r_sm} {r_sm} 0 0;
    }}

    /* Segmented control / button-group toggles (theme picker, chart-type toggles) */
    div[data-testid="stSegmentedControl"] label {{
        border-radius: 999px !important;
        border: 1px solid {t['border']} !important;
    }}
    div[data-testid="stSegmentedControl"] label[data-checked="true"] {{
        background-color: {t['accent']} !important;
        border-color: {t['accent']} !important;
    }}

    /* Gauge card wrapper (used with ring_gauge / half_gauge) */
    .gauge-card {{
        background: {t['card_bg']};
        border: 1px solid {t['border']};
        border-radius: {r};
        padding: 14px 10px 4px 10px;
        box-shadow: {shadow};
        text-align: center;
    }}
    .gauge-card-title {{
        font-size: 12px;
        font-weight: 700;
        color: {t['subtext']};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
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


def kpi_card(label: str, value: str, sub: str = "", icon: str = ""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""
    st.markdown(f"""
    <div class="kpi-card">
        {icon_html}
        <p class="kpi-label">{label}</p>
        <p class="kpi-value">{value}</p>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def hero_banner(eyebrow: str, title: str, subtitle: str):
    """Landing-page style hero card: small eyebrow pill, big title, muted subtitle."""
    st.markdown(f"""
    <div class="hero-card">
        <span class="hero-eyebrow">{eyebrow}</span>
        <p class="hero-title">{title}</p>
        <p class="hero-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def next_step_card(title: str, caption: str):
    st.markdown(f"""
    <div class="next-card">
        <div class="next-card-title">{title}</div>
        <div class="next-card-caption">{caption}</div>
    </div>
    """, unsafe_allow_html=True)


def ring_gauge(value: float, title: str = "", subtitle: str = "", color: str = None, height: int = 220):
    """
    Full circular ring gauge with the percentage centered inside — the
    'Safe 97%' style dial. `value` is 0-100.
    """
    import plotly.graph_objects as go
    t = get_theme()
    color = color or t["accent"]
    value = max(0, min(100, value))
    fig = go.Figure(data=[go.Pie(
        values=[value, 100 - value],
        hole=0.78,
        marker=dict(colors=[color, t["border"]], line=dict(width=0)),
        textinfo="none",
        sort=False,
        direction="clockwise",
        rotation=0,
    )])
    fig.update_traces(hoverinfo="skip")
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(text=f"<b>{value:.0f}%</b>", x=0.5, y=0.56, font=dict(size=26, color=t["ink"]), showarrow=False),
            dict(text=subtitle or title, x=0.5, y=0.38, font=dict(size=12, color=t["subtext"]), showarrow=False),
        ],
    )
    return fig


def half_gauge(value: float, title: str = "", vmin: float = 0, vmax: float = 100, height: int = 230):
    """
    Semi-circle dial with green/amber/red risk zones — the 'speedometer'
    style gauge used for overall risk scores.
    """
    import plotly.graph_objects as go
    t = get_theme()
    value = max(vmin, min(vmax, value))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"size": 30, "color": t["ink"]}},
        gauge={
            "axis": {"range": [vmin, vmax], "tickcolor": t["subtext"],
                     "tickfont": {"color": t["subtext"], "size": 10}},
            "bar": {"color": t["ink"], "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [vmin, vmin + (vmax - vmin) * 0.33], "color": t["green"]},
                {"range": [vmin + (vmax - vmin) * 0.33, vmin + (vmax - vmin) * 0.66], "color": t["amber"]},
                {"range": [vmin + (vmax - vmin) * 0.66, vmax], "color": t["red"]},
            ],
        },
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=25, r=25, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["ink"]),
    )
    return fig


def gauge_card(fig, title: str):
    """Wraps a gauge figure (ring_gauge / half_gauge) in a themed card with a title."""
    st.markdown(f'<div class="gauge-card"><div class="gauge-card-title">{title}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


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
