from __future__ import annotations

import html
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_store import get_all_records, get_counts, init_db, search_records
from src.data_store import SOURCE_URL
from src.data_store import save_openfda_records
from src.reference_sync import fetch_openfda_records
from src.verification import record_matches_name, select_official_matches

ROOT = Path(__file__).resolve().parent
LOGO_PATH = ROOT / "assets" / "logo.png"
LOGO_SVG_PATH = ROOT / "assets" / "logo.svg"

st.set_page_config(
    page_title="Counterfeit Medicine System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Palette and styling are original, inspired by modern healthcare dashboard layouts.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root {
      --ink: #10233f;
      --muted: #667992;
      --blue: #2563eb;
      --blue-dark: #1646ae;
      --cyan: #47c5e9;
      --pale: #f3f7ff;
      --line: #e3ebf6;
      --green: #087f68;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: linear-gradient(130deg, #f5f8ff 0%, #eff6ff 46%, #f9fbff 100%); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(245, 248, 255, .75); }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e6edf7; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #61738c; }
    [data-testid="stSidebar"] .stRadio > label { display: none; }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: .36rem; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
      background: transparent; border: 1px solid transparent; padding: .72rem .8rem;
      border-radius: 12px; transition: all .18s ease; color: #50627a;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #f1f6ff; border-color: #e1ebff; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #eaf2ff; border-color: #d6e5ff; color: #1e55bf; font-weight: 700; }
    [data-testid="stSidebar"] [role="radiogroup"] label p { font-weight: 600; font-size: .94rem; }
    .brand-wrap { display:flex; align-items:center; gap: 11px; padding: 0 .25rem 1.1rem; }
    .brand-name { color:#10233f; font-family:'Manrope',sans-serif; font-size:1.03rem; font-weight:800; line-height:1.18; }
    .brand-sub { color:#8a9bb1; font-size:.7rem; letter-spacing:.13em; text-transform:uppercase; margin-top:4px; }
    .sidebar-note { border:1px solid #e3ebf6; background:#f8fbff; padding:12px 13px; border-radius:14px; color:#6a7b91; font-size:.78rem; line-height:1.55; }
    h1, h2, h3, h4 { font-family: 'Manrope', sans-serif !important; color: var(--ink); letter-spacing: -.025em; }
    h1 { font-weight: 800 !important; }
    .eyebrow { color:#2563eb; font-size:.75rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:9px; }
    .hero {
      position:relative; overflow:hidden; padding: 34px 36px 31px; border-radius:28px;
      background: radial-gradient(circle at 87% 10%, rgba(90,199,255,.35), transparent 25%),
                  radial-gradient(circle at 72% 100%, rgba(73,124,255,.3), transparent 34%),
                  linear-gradient(118deg, #102b63 0%, #1746a7 54%, #2376d9 100%);
      color:#fff; box-shadow:0 22px 55px rgba(31,76,154,.17); margin-bottom:1.15rem;
      border:1px solid rgba(255,255,255,.16);
    }
    .hero:after { content:''; position:absolute; width:210px; height:210px; right:-40px; top:-64px; border:1px solid rgba(255,255,255,.16); border-radius:50%; box-shadow:0 0 0 26px rgba(255,255,255,.035), 0 0 0 54px rgba(255,255,255,.025); }
    .hero h1 { font-family:'Manrope',sans-serif; color:white !important; font-size:clamp(2rem, 3.4vw, 3.05rem); line-height:1.08; margin:4px 0 13px; max-width:740px; }
    .hero p { color:rgba(255,255,255,.78); font-size:1rem; line-height:1.65; max-width:680px; margin:0; }
    .hero-kicker { display:inline-flex; align-items:center; gap:7px; border:1px solid rgba(255,255,255,.25); background:rgba(255,255,255,.10); padding:7px 11px; border-radius:99px; font-size:.73rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#eaf4ff; }
    .hero-pill { position:absolute; right:7%; bottom:21%; width:94px; height:36px; border-radius:30px; border:2px solid rgba(255,255,255,.68); transform:rotate(-32deg); opacity:.8; }
    .hero-pill:before { content:''; position:absolute; left:45px; top:0; height:100%; border-left:2px solid rgba(255,255,255,.62); }
    .surface { background:rgba(255,255,255,.92); border:1px solid #e5edf8; border-radius:20px; padding:21px 22px; box-shadow:0 7px 24px rgba(31,65,116,.045); }
    .surface h3 { margin:0 0 9px; font-size:1.08rem; }
    .muted { color:#6b7e97; font-size:.91rem; line-height:1.6; }
    .mini-label { color:#8192a9; text-transform:uppercase; letter-spacing:.1em; font-size:.69rem; font-weight:800; }
    .step-num { height:34px; width:34px; display:inline-flex; align-items:center; justify-content:center; border-radius:11px; background:#e8f1ff; color:#2057c1; font-weight:800; margin-bottom:11px; }
    .status-chip { display:inline-block; border:1px solid #cbdcf7; color:#1c55bd; background:#f0f6ff; padding:5px 9px; border-radius:99px; font-size:.73rem; font-weight:800; letter-spacing:.04em; }
    .notice { padding:14px 16px; border:1px solid #d8e6fb; background:#f5f9ff; border-radius:14px; color:#536b89; font-size:.87rem; line-height:1.6; }
    .warn-notice { padding:14px 16px; border:1px solid #f6ddb0; background:#fff9ed; border-radius:14px; color:#805a14; font-size:.87rem; line-height:1.6; }
    .result-panel { border:1px solid #d8e6fb; border-radius:20px; background:white; padding:22px; box-shadow:0 10px 32px rgba(30,70,140,.06); }
    .result-title { font-family:'Manrope',sans-serif; font-weight:800; font-size:1.35rem; margin:0 0 7px; color:#17305b; }
    .result-label { color:#6b7e97; font-size:.75rem; text-transform:uppercase; font-weight:800; letter-spacing:.1em; }
    .result-value { color:#142947; font-weight:700; margin:3px 0 10px; overflow-wrap:anywhere; }
    .section-head { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:18px 0 12px; }
    .section-head h2 { font-size:1.35rem; margin:0; }
    .small-caps { color:#8092a9; font-size:.7rem; letter-spacing:.11em; font-weight:800; text-transform:uppercase; }
    div[data-testid="stMetric"] { background:white; border:1px solid #e5edf8; border-radius:17px; padding:16px 18px; box-shadow:0 6px 20px rgba(31,65,116,.035); }
    div[data-testid="stMetricLabel"] p { color:#71839b; font-weight:600; font-size:.83rem; }
    div[data-testid="stMetricValue"] { color:#183764; font-family:'Manrope',sans-serif; font-weight:800; }
    div.stButton > button, div.stDownloadButton > button { border-radius:12px; border:1px solid #d8e4f6; padding:.58rem 1rem; font-weight:700; transition:all .2s ease; }
    div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] { background:linear-gradient(110deg,#2563eb,#337ce9); color:white; border:0; box-shadow:0 7px 17px rgba(37,99,235,.18); }
    div.stButton > button:hover, div.stDownloadButton > button:hover { transform:translateY(-1px); border-color:#a9c7f8; }
    div[data-baseweb="input"] input, div[data-baseweb="select"] > div, div[data-baseweb="textarea"] textarea { border-radius:11px !important; }
    div[data-testid="stForm"] { border:1px solid #e2eaf5; border-radius:20px; background:rgba(255,255,255,.9); padding:20px 22px 15px; }
    .footer { color:#94a2b5; font-size:.76rem; padding:18px 0 6px; border-top:1px solid #e5edf8; margin-top:30px; }
    a { color:#2363d1 !important; }
    @media(max-width: 750px) { .hero { padding:26px 22px; border-radius:22px; } .hero-pill { opacity:.25; right:5%; bottom:8%; } .surface { padding:17px; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def set_page(page: str) -> None:
    st.session_state["nav"] = page


def header(title: str, subtitle: str, eyebrow: str = "COUNTERFEIT MEDICINE SYSTEM") -> None:
    st.markdown(
        f"<div class='eyebrow'>{eyebrow}</div><h1 style='font-size:2.0rem;margin:0 0 7px'>{title}</h1>"
        f"<p style='color:#6b7e97;margin:0 0 24px;line-height:1.65'>{subtitle}</p>",
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        "<div class='footer'>Student project prototype · Reference lookup only · Never use this page as the sole basis for taking or rejecting medicine.</div>",
        unsafe_allow_html=True,
    )


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def load_presentation_case() -> None:
    """Fill the form with clearly fictional sample details for a live demo."""
    st.session_state["medicine_name_input"] = "DEMO Paracetamol 500"
    st.session_state["manufacturer_input"] = "Demo Therapeutics Ltd."
    st.session_state["batch_number_input"] = "DEMO-BATCH-001"
    st.session_state["product_code_input"] = "DEMO-001"
    st.session_state["manufacture_date_input"] = date.today() - timedelta(days=30)
    st.session_state["expiry_date_input"] = date.today() + timedelta(days=365)
    st.session_state["country_input"] = "Fictional demo location"


def result_panel(title: str, message: str, status: str, details: list[tuple[str, str]] | None = None, tone: str = "blue") -> None:
    title, message, status = html.escape(str(title)), html.escape(str(message)), html.escape(str(status))
    border = "#f4d8a8" if tone == "amber" else ("#f2c8c8" if tone == "red" else "#d8e6fb")
    bg = "#fffaf0" if tone == "amber" else ("#fff6f6" if tone == "red" else "#f7faff")
    status_color = "#8a5d0c" if tone == "amber" else ("#a12626" if tone == "red" else "#1c55bd")
    parts = [f"<div class='result-panel' style='border-color:{border};background:{bg}'>",
            f"<div style='display:inline-block;padding:5px 10px;border-radius:99px;background:white;border:1px solid {border};color:{status_color};font-size:.72rem;font-weight:800;letter-spacing:.07em'>{status}</div>",
            f"<div class='result-title' style='margin-top:13px'>{title}</div>",
            f"<div style='color:#5e728d;line-height:1.65;margin-bottom:12px'>{message}</div>"]
    if details:
        parts.append("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px 18px;margin-top:15px'>")
        for key, value in details:
            parts.append(f"<div><div class='result-label'>{html.escape(str(key))}</div><div class='result-value'>{html.escape(str(value or 'Not listed'))}</div></div>")
        parts.append("</div>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# Initial database setup. The included local data is fictional UI/demo data only.
init_db()
counts = get_counts()

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=54)
    st.markdown(
        "<div class='brand-wrap' style='padding-top:2px'><div><div class='brand-name'>Counterfeit Medicine<br>System</div><div class='brand-sub'>Verify with care</div></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:1px;background:#e7edf6;margin:7px 0 18px'></div>", unsafe_allow_html=True)
    page_options = ["Overview", "Verify medicine", "Medicine database", "How it works"]
    page_icons = {"Overview": "⌂  Overview", "Verify medicine": "⌕  Verify medicine", "Medicine database": "▦  Medicine database", "How it works": "ⓘ  How it works"}
    page = st.radio("Navigation", page_options, format_func=lambda p: page_icons[p], key="nav", label_visibility="collapsed")
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sidebar-note'><span style='font-weight:800;color:#1c55bd'>Safety note</span><br>Matching a medicine name does not authenticate its batch. Check through the manufacturer or a licensed pharmacist.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='small-caps'>Database status</div><div style='margin-top:5px;color:#203b61;font-weight:800'>{counts['official']:,} official listing records</div><div style='font-size:.75rem;color:#8192a9'>{counts['demo']} demo records · locally stored</div>", unsafe_allow_html=True)

if page == "Overview":
    st.markdown(
        """
        <div class="hero" style="padding:28px 30px 26px">
          <div class="hero-kicker">Medicine label checker</div>
          <h1>Check a medicine label.</h1>
          <p>Enter the details from the pack. Get a simple score, see what looks wrong, and review matching reference products.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    a, b = st.columns([1, 1], gap="medium")
    with a:
        st.markdown("<div class='surface'><h3>How it works</h3><div class='muted'>1. Enter label details.<br>2. Compare with saved product listings.<br>3. Review the score and warnings.</div></div>", unsafe_allow_html=True)
        st.button("Check a medicine →", type="primary", use_container_width=True, on_click=set_page, args=("Verify medicine",))
    with b:
        st.markdown(f"<div class='surface'><h3>Reference database</h3><div style='font-size:2rem;font-weight:800;color:#1d4ed8'>{counts['official']:,}</div><div class='muted'>Product listings loaded</div><div class='muted' style='margin-top:8px'>Listings help compare labels. They do not prove a batch is genuine.</div></div>", unsafe_allow_html=True)
        st.button("Open database →", use_container_width=True, on_click=set_page, args=("Medicine database",))
    st.caption("Student project. For real concerns, contact the manufacturer or a licensed pharmacist.")
    render_footer()

elif page == "Verify medicine":
    header("Check a medicine", "Enter the details from the pack and review the result.", "MEDICINE CHECK")
    st.markdown("<div class='notice' style='margin-bottom:17px'>Your batch number is checked locally. A product listing alone cannot prove a batch is genuine.</div>", unsafe_allow_html=True)
    st.markdown("<div class='surface' style='margin-bottom:12px'><div class='muted'>Need a quick demo? Load fictional sample details.</div></div>", unsafe_allow_html=True)
    st.button("Load sample presentation case", on_click=load_presentation_case, use_container_width=True)

    form_defaults = {
        "medicine_name_input": "",
        "manufacturer_input": "",
        "batch_number_input": "",
        "product_code_input": "",
        "manufacture_date_input": date.today() - timedelta(days=30),
        "expiry_date_input": date.today() + timedelta(days=365),
        "country_input": "",
    }
    for state_key, default_value in form_defaults.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = default_value

    with st.form("medicine_check_form", clear_on_submit=False):
        st.markdown("<div class='mini-label' style='margin-bottom:8px'>Medicine details</div>", unsafe_allow_html=True)
        left, right = st.columns(2, gap="large")
        with left:
            medicine_name = st.text_input("Medicine name on label *", placeholder="Example: brand name or generic name", help="Use the name as printed on the pack.", key="medicine_name_input")
            manufacturer = st.text_input("Manufacturer / marketer", placeholder="Company name as printed on the label", key="manufacturer_input")
            batch_number = st.text_input("Batch / lot number *", placeholder="Enter the batch number from the pack", key="batch_number_input")
            product_code = st.text_input("Product code / NDC (optional)", placeholder="Enter an NDC product or package code", help="The current reference source compares NDC product/package codes. Retail barcode lookup is not connected.", key="product_code_input")
        with right:
            manufacture_date = st.date_input("Manufacturing date", min_value=date(1950, 1, 1), max_value=date.today() + timedelta(days=365), key="manufacture_date_input")
            expiry_date = st.date_input("Expiry date", min_value=date(1950, 1, 1), max_value=date.today() + timedelta(days=3650), key="expiry_date_input")
            country = st.text_input("Manufacturing country / location", placeholder="As printed on the label", key="country_input")
            st.markdown("<div style='font-size:.76rem;color:#8192a9;line-height:1.5;padding-top:5px'>Dates are checked for consistency only. This source does not confirm printed dates or manufacturing country/site.</div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Check medicine", type="primary", use_container_width=True)

    if submitted:
        if not clean_text(medicine_name) or not clean_text(batch_number):
            st.error("Enter both the medicine name and the batch / lot number.")
        else:
            official_records = get_all_records(source_type="official_openfda")
            official_matches, match_case = select_official_matches(official_records, medicine_name, product_code)
            official_matches = official_matches[:5]
            demo_matches = [r for r in search_records(medicine_name, limit=30, include_demo=True) if r.get("source_type") == "demo" and record_matches_name(r, medicine_name)]

            date_issues: list[str] = []
            if manufacture_date > date.today():
                date_issues.append("The manufacturing date is in the future.")
            if expiry_date <= manufacture_date:
                date_issues.append("The expiry date is not later than the manufacturing date.")
            if expiry_date < date.today():
                date_issues.append("The expiry date entered is in the past.")

            # This is a transparent screening score, not a probability that a medicine is genuine.
            issues: list[str] = []
            if date_issues:
                issues.extend(date_issues)
            if match_case == "code_mismatch":
                issues.append("Product code did not match the product listing.")
            elif match_case == "code_name_mismatch":
                issues.append("Product code matched a listing with a different medicine name.")
            entered_manufacturer = clean_text(manufacturer).casefold()
            manufacturer_match = (not entered_manufacturer or any(
                clean_text(rec.get("labeler_name")) and
                (entered_manufacturer in clean_text(rec.get("labeler_name")).casefold()
                 or clean_text(rec.get("labeler_name")).casefold() in entered_manufacturer)
                for rec in official_matches
            )) if official_matches else False
            if official_matches and manufacturer and not manufacturer_match:
                issues.append("Manufacturer name differs from the reference listing.")
            if not official_matches and not demo_matches:
                issues.append("No matching product listing was found in the loaded database.")
            if demo_matches and not official_matches:
                issues.append("Only a fictional demo record matched.")

            score = 100
            if date_issues:
                score -= 45
            if match_case in {"code_mismatch", "code_name_mismatch"}:
                score -= 30
            if official_matches and manufacturer and not manufacturer_match:
                score -= 20
            if not official_matches:
                score -= 35
            if demo_matches and not official_matches:
                score -= 15
            score = max(0, min(100, score))

            if date_issues or match_case in {"code_mismatch", "code_name_mismatch"} or (official_matches and manufacturer and not manufacturer_match):
                verdict, tone = "SUSPICIOUS", "red"
                summary = "Some details do not match or need checking. Do not rely on this score alone."
            elif official_matches and not issues:
                verdict, tone = "NO OBVIOUS ISSUE FOUND", "blue"
                summary = "The entered details match a product listing. The batch itself is still unverified."
            else:
                verdict, tone = "NEEDS CHECKING", "amber"
                summary = "The database did not confirm enough details. A missing match does not prove a medicine is fake."

            st.markdown("<div class='section-head'><h2>Result</h2></div>", unsafe_allow_html=True)
            border = "#f2c8c8" if tone == "red" else ("#f4ddb0" if tone == "amber" else "#d8e6fb")
            bg = "#fff6f6" if tone == "red" else ("#fffaf0" if tone == "amber" else "#f7faff")
            st.markdown(
                f"<div class='result-panel' style='border-color:{border};background:{bg}'>"
                f"<div class='result-label'>Screening result</div>"
                f"<div class='result-title' style='font-size:1.55rem;margin-top:7px'>{html.escape(verdict)}</div>"
                f"<div style='font-size:2.5rem;font-weight:800;color:#173b75;margin:8px 0'> {score}<span style='font-size:1rem;color:#6b7e97'> / 100</span></div>"
                f"<div style='color:#5e728d;line-height:1.6'>{html.escape(summary)}</div></div>",
                unsafe_allow_html=True,
            )
            st.caption("Score = simple rule-based screening score, not a medical or regulatory authenticity probability.")

            st.markdown("### What needs attention")
            if issues:
                for issue in issues:
                    st.write(f"• {issue}")
            else:
                st.write("• No obvious mismatch was found in the fields checked.")
            st.markdown("### Details checked")
            d1, d2, d3 = st.columns(3)
            d1.metric("Name match", "Yes" if official_matches else "Not confirmed")
            d2.metric("Code check", "Matched" if match_case == "name_and_code" else ("Not entered" if not product_code else "Needs review"))
            d3.metric("Expiry", "Expired" if expiry_date < date.today() else "Date entered")

            # Show reference alternatives only when the supplied name/code has a mismatch.
            if official_matches and (match_case in {"code_mismatch", "code_name_mismatch"} or (manufacturer and not manufacturer_match)):
                st.markdown("### Similar product listings to review")
                st.caption("These are reference matches, not a recommendation to replace or take a medicine. Confirm with a pharmacist or prescriber.")
                for rec in official_matches[:3]:
                    product_name = clean_text(rec.get("brand_name")) or clean_text(rec.get("generic_name")) or "Unnamed product"
                    st.write(f"• **{product_name}** | {clean_text(rec.get('labeler_name')) or 'Company not listed'} | Code: {clean_text(rec.get('product_ndc')) or 'Not listed'}")
            elif not official_matches:
                st.info("No verified alternative is available from the current reference results. Try the generic ingredient name, or ask a licensed pharmacist to identify an appropriate equivalent.")
            st.markdown("""<div class='warn-notice' style='margin-top:15px'><b>Important:</b> Never take, discard or return medicine based only on this prototype. For a suspicious pack in India, check the official <a href="https://cdscoonline.gov.in/CDSCO/viewPublicNSQDrug" target="_blank" rel="noopener noreferrer">CDSCO NSQ and spurious-drug alerts</a>, then contact the manufacturer using details from its official website or ask a licensed pharmacist.</div>""", unsafe_allow_html=True)
    render_footer()

elif page == "Medicine database":
    header("Medicine database", "Search saved products or load 500 reference listings.", "DATABASE")
    counts = get_counts()
    m1, m2, m3 = st.columns(3)
    m1.metric("Official listing records", f"{counts['official']:,}")
    m2.metric("Demo-only records", f"{counts['demo']:,}")
    m3.metric("Total local records", f"{counts['total']:,}")

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown("<div class='surface'><h3>Sync official product listings</h3><div class='muted'>Fetch 500 unique finished-product records from openFDA. An internet connection is required. This imports product names, labelers, ingredients, dosage form and product identifiers when available.</div><div style='margin-top:12px' class='notice'>The NDC Directory is a US product-listing reference. FDA states that inclusion does not mean the FDA independently verified the submitted details or that the product is FDA-approved.</div></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='surface'><h3>Fields not covered</h3><div class='muted'>Public product listings do not validate your pack's batch number, manufacturing date, expiry date, seal, hologram, contents or manufacturing location. Those require a manufacturer or regulator source.</div></div>", unsafe_allow_html=True)

    sync_col, info_col = st.columns([1, 2])
    with sync_col:
        do_sync = st.button("Sync 500 records  ↻", type="primary", use_container_width=True)
    with info_col:
        st.caption("Typical first sync: five API requests. Your downloaded reference records are stored locally in SQLite.")
    if do_sync:
        with st.spinner("Contacting openFDA and importing reference records..."):
            try:
                records = fetch_openfda_records(target=500)
                saved = save_openfda_records(records)
                st.success(f"Imported {saved:,} unique product reference records. The existing demo records are retained and remain clearly labelled.")
                st.rerun()
            except Exception as exc:
                st.error(f"Sync did not complete: {exc}")
                st.caption("No partial update was saved. Check your internet connection and try again.")

    st.markdown("<div class='section-head'><h2>Browse saved records</h2><span class='small-caps'>Search and export</span></div>", unsafe_allow_html=True)
    query = st.text_input("Search product, ingredient, labeler or product code", placeholder="Type a name, company or identifier…")
    source_filter = st.selectbox("Show records from", ["All records", "Official openFDA listings", "Demo-only records"])
    all_rows = get_all_records()
    if source_filter == "Official openFDA listings":
        all_rows = [r for r in all_rows if r.get("source_type") == "official_openfda"]
    elif source_filter == "Demo-only records":
        all_rows = [r for r in all_rows if r.get("source_type") == "demo"]
    if query:
        q = query.casefold()
        all_rows = [r for r in all_rows if any(q in clean_text(r.get(field)).casefold() for field in ["brand_name", "generic_name", "active_ingredients", "labeler_name", "product_ndc", "package_ndc"])]
    display_rows = [{
        "Brand / product": r.get("brand_name") or r.get("generic_name") or "Not listed",
        "Generic name": r.get("generic_name") or "Not listed",
        "Active ingredients": r.get("active_ingredients") or "Not listed",
        "Labeler / company": r.get("labeler_name") or "Not listed",
        "Product code": r.get("product_ndc") or "Not listed",
        "Dosage form": r.get("dosage_form") or "Not listed",
        "Source status": "Official listing, labeler-submitted" if r.get("source_type") == "official_openfda" else "DEMO ONLY, fictional",
    } for r in all_rows]
    st.caption(f"Showing {len(display_rows):,} records after filters.")
    if display_rows:
        df = pd.DataFrame(display_rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=420)
        st.download_button("Download filtered records as CSV", data=df.to_csv(index=False).encode("utf-8-sig"), file_name="medicine_reference_export.csv", mime="text/csv")
    else:
        st.info("No records match this filter. Sync official product listings or try a different search term.")

    st.markdown("<div class='section-head'><h2>Data source and limitations</h2></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='surface'>
          <h3>openFDA Drug NDC Directory</h3>
          <div class='muted'>Reference provider: <a href="{SOURCE_URL}" target="_blank" rel="noopener noreferrer">openFDA NDC API documentation</a>. The entries are labeler-submitted listings. The application preserves this source label so users do not confuse a product listing with a genuine batch certificate.</div>
          <div style='height:10px'></div>
          <h3>Indian medicine approvals</h3>
          <div class='muted'>For an India-specific approval lookup, consult the <a href="https://www.cdscoonline.gov.in/CDSCO/cdscoDrugs/" target="_blank" rel="noopener noreferrer">CDSCO approved drugs portal</a>. For published quality-defect and spurious-drug reports, consult <a href="https://cdscoonline.gov.in/CDSCO/viewPublicNSQDrug" target="_blank" rel="noopener noreferrer">CDSCO NSQ and spurious-drug alerts</a>. These are separate resources. This prototype does not automatically import either CDSCO dataset and does not certify approval in India.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()

else:
    header("How it works", "Three steps to review a medicine label.", "HELP")
    sections = [
        ("01", "Label input", "The user enters the medicine name, batch or lot number, manufacturing date, expiry date, manufacturer and optional product code."),
        ("02", "Reference lookup", "The app searches its local SQLite database for product-name, ingredient, labeler and product-code matches. Official openFDA listings and fictional demo rows remain separated."),
        ("03", "Date consistency", "The app checks whether the expiry date is in the past, whether manufacturing appears in the future, and whether expiry is later than manufacturing."),
        ("04", "Screening result", "The output reports a reference match, missing match, demo-only match or date warning. It never declares a pack genuine based only on a catalogue match."),
    ]
    for i in range(0, len(sections), 2):
        cols = st.columns(2, gap="medium")
        for col, item in zip(cols, sections[i:i+2]):
            with col:
                st.markdown(f"<div class='surface' style='margin-bottom:15px'><div class='step-num'>{item[0]}</div><h3>{item[1]}</h3><div class='muted'>{item[2]}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-head'><h2>Current limitations</h2></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="warn-notice">
          <b>This is an educational prototype.</b><br>
          • It does not connect to a pharmaceutical manufacturer's batch-verification system.<br>
          • The openFDA NDC Directory contains US product listing data and is not an Indian approvals database.<br>
          • The directory does not prove that details submitted by a labeler are independently verified by FDA.<br>
          • A fake pack might copy the exact name, code and manufacturer of a real medicine.<br>
          • For real batch authentication, integrate a manufacturer-authorised serialisation API or an approved regulator workflow.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='section-head'><h2>Official resources</h2></div>", unsafe_allow_html=True)
    st.markdown(f"- [openFDA NDC Directory API]({SOURCE_URL})\n- [FDA National Drug Code Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory)\n- [CDSCO approved drugs portal](https://www.cdscoonline.gov.in/CDSCO/cdscoDrugs/)")
    st.button("Go to verification form  →", type="primary", on_click=set_page, args=("Verify medicine",))
    render_footer()
