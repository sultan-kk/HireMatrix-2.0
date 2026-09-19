"""
theme.py  (Style C — indigo/coral "command center")
------------------------------------------------------
Design system for the fresh HireMatrix redesign. Pairs with
generate_icon.py's network-motif logo. Introduces a few new pieces on
top of the earlier theme.py's API (inject_css, render_banner,
metric_card, section_header): kpi_card (a bolder metric tile for the
Dashboard page) and a nav-radio style so the sidebar page switcher
reads as an app navigation menu, not a generic Streamlit radio button.
"""

import base64
import os

import streamlit as st

import config

INDIGO_DARK = "#1E1B4B"
INDIGO = "#312E81"
INDIGO_SOFT = "#4338CA"
CORAL = "#FB7185"
CORAL_DARK = "#E11D48"
BG = "#F8FAFC"
CARD_BG = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#1E1B4B"
MUTED = "#6B7280"
INK_ON_DARK = "#E2E8F0"



def _b64_image(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def inject_css():
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
        }}
        .stApp {{ background: {BG}; }}

        /* ---- Header banner ---- */
        .hm-banner-wrap {{
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 1.4rem;
            box-shadow: 0 4px 14px rgba(30, 27, 75, 0.18);
        }}
        .hm-banner-wrap img {{ width: 100%; display: block; }}

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {{
            background: {INDIGO_DARK};
        }}
        section[data-testid="stSidebar"] * {{ color: {INK_ON_DARK} !important; }}

        /* Sidebar nav radio styled as a vertical menu list */
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 0.55rem 0.8rem;
            margin-bottom: 0.4rem;
            width: 100%;
            transition: background 0.15s ease;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(251, 113, 133, 0.15);
            border-color: {CORAL};
        }}
        section[data-testid="stSidebar"] .stButton>button {{
            background: transparent;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 6px;
            color: #fff !important;
        }}
        section[data-testid="stSidebar"] .stButton>button:hover {{
            background: {CORAL};
            border-color: {CORAL};
        }}
        section[data-testid="stSidebar"] input, 
        section[data-testid="stSidebar"] textarea, 
        section[data-testid="stSidebar"] [data-baseweb="select"] 
        section[data-testid="stSidebar"] [data-baseweb="select"] span, 
        section[data-testid="stSidebar"] [data-baseweb="select"] div {{
            color: {TEXT} !important;
            
        }}

        /* ---- Cards ---- */
        .hm-card {{
            background: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 1px 3px rgba(30, 27, 75, 0.05);
        }}
        .hm-section-title {{
            font-weight: 700;
            font-size: 1.05rem;
            color: {INDIGO_DARK};
            margin-bottom: 0.15rem;
        }}
        .hm-section-caption {{
            color: {MUTED};
            font-size: 0.88rem;
            margin-bottom: 0.9rem;
        }}

        /* ---- Metric / KPI tiles ---- */
        .hm-metric, .hm-kpi {{
            background: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            text-align: left;
        }}
        .hm-metric {{ border-left: 4px solid {CORAL}; }}
        .hm-kpi {{
            background: linear-gradient(135deg, {INDIGO} 0%, {INDIGO_DARK} 100%);
            border: none;
        }}
        .hm-metric .value, .hm-kpi .value {{
            font-size: 1.7rem;
            font-weight: 800;
            line-height: 1.1;
        }}
        .hm-metric .value {{ color: {INDIGO_DARK}; }}
        .hm-kpi .value {{ color: #fff; }}
        .hm-metric .label {{ color: {MUTED}; font-size: 0.82rem; }}
        .hm-kpi .label {{ color: {INK_ON_DARK}; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}

        /* ---- Buttons ---- */
        .stButton>button[kind="primary"] {{
            background: {CORAL};
            border: 1px solid {CORAL_DARK};
            color: #fff;
            font-weight: 600;
            border-radius: 8px;
        }}
        .stButton>button[kind="primary"]:hover {{
            background: {CORAL_DARK};
            border-color: {CORAL_DARK};
        }}
        .stButton>button {{ border-radius: 8px; }}
        .stDownloadButton>button {{
            border-radius: 8px;
            border: 1px solid {INDIGO};
            color: {INDIGO_DARK};
            font-weight: 600;
        }}
        .stDownloadButton>button:hover {{ background: {INDIGO}; color: #fff; }}

        /* ---- Badges ---- */
        .hm-badge {{
            display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
            font-size: 0.76rem; font-weight: 600;
        }}
        .hm-badge-saved {{ background: #ECFDF5; color: #059669; }}
        .hm-badge-pending {{ background: #FFF1F2; color: {CORAL_DARK}; }}
        .hm-badge-native {{ background: #EEF2FF; color: {INDIGO}; }}
        .hm-badge-ocr {{ background: #FFF7ED; color: #C2410C; }}

        .block-container {{ padding-top: 1.6rem; }}
        [theme]

        base="light"
        primaryColor="#0c83c1"
        secondaryBackgroundColor="#f1c997"
        textColor="#0a0a0a"
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_banner():
    b64 = _b64_image(config.BANNER_PATH)
    if not b64:
        st.title(config.APP_NAME)
        st.caption(config.APP_TAGLINE)
        return
    st.markdown(
        f'<div class="hm-banner-wrap"><img src="data:image/png;base64,{b64}"/></div>',
        unsafe_allow_html=True,
    )


def metric_card(value, label):
    st.markdown(
        f'<div class="hm-metric"><div class="value">{value}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def kpi_card(value, label):
    """Bolder, dark-gradient tile — used on the Dashboard page."""
    st.markdown(
        f'<div class="hm-kpi"><div class="value">{value}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, caption: str = ""):
    st.markdown(f'<div class="hm-section-title">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="hm-section-caption">{caption}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "pending"):
    """kind: 'saved' | 'pending' | 'native' | 'ocr'"""
    return f'<span class="hm-badge hm-badge-{kind}">{text}</span>'
