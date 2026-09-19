"""
app.py
------
HireMatrix — fresh redesign.

Structure (sidebar navigation instead of tabs — reads like a real app
console rather than a single long form):
    📊 Dashboard        — KPIs + a skills-frequency chart across saved candidates
    📥 Upload & Extract — multi-format upload (PDF/DOCX/PNG/JPG/JPEG), auto-routed
                           to the right extractor, with a format badge per file
    🧾 Review & Edit    — original document + editable fields for one candidate,
                           with excluded/low-confidence text tucked into a
                           collapsed, accurate (but secondary) panel
    🗂️ Records          — search, browse, export, delete, rename columns

Run with:  streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st

import config
import extraction_engine
import parser
import excel_handler
import theme
from config import t

st.set_page_config(
    page_title=config.APP_NAME,
    layout="wide",
    page_icon=config.ICON_PATH if os.path.exists(config.ICON_PATH) else "🧩",
)
theme.inject_css()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "candidates" not in st.session_state:
    st.session_state.candidates = {}
if "active_file" not in st.session_state:
    st.session_state.active_file = None
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "nav" not in st.session_state:
    st.session_state.nav = "dashboard"

L = st.session_state.lang

if L == "ur":
    st.markdown(
        "<style>.block-container, .stMarkdown, .stTextInput, .stTextArea "
        "{direction: rtl; text-align: right;}</style>",
        unsafe_allow_html=True,
    )


def process_uploaded_file(uploaded_file):
    with st.spinner(f"{uploaded_file.name} ..."):
        lines, preview, notice = extraction_engine.extract_lines_from_file(uploaded_file)
        result = parser.parse_resume(lines)

    ext = uploaded_file.name.lower().rsplit(".", 1)[-1]
    st.session_state.candidates[uploaded_file.name] = {
        "ext": ext,
        "preview": preview,
        "notice": notice,
        "relevant": result["relevant"],
        "irrelevant": [dict(item, status="flagged") for item in result["irrelevant"]],
        "unmapped": result["unmapped_relevant_lines"],
        "saved": False,
    }


# ---------------------------------------------------------------------------
# Sidebar — branding, language, navigation, reviewer name
# ---------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists(config.ICON_PATH):
        st.image(config.ICON_PATH, width=56)
    st.markdown(f"### {t('app_title', L)}")
    st.caption(t("app_tagline", L))

    lang_choice = st.selectbox(
        t("language_label", L), options=list(config.LANGUAGES.keys()),
        index=list(config.LANGUAGES.values()).index(L), label_visibility="collapsed",
    )
    new_lang = config.LANGUAGES[lang_choice]
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown("---")
    nav_options = ["dashboard", "upload", "review", "records"]
    nav_labels = {
        "dashboard": t("nav_dashboard", L), "upload": t("nav_upload", L),
        "review": t("nav_review", L), "records": t("nav_records", L),
    }
    nav_choice = st.radio(
        "nav", options=nav_options, format_func=lambda k: nav_labels[k],
        index=nav_options.index(st.session_state.nav), label_visibility="collapsed",
    )
    st.session_state.nav = nav_choice

    st.markdown("---")
    reviewer_name = st.text_input(t("reviewer_name", L), value="HR Reviewer")

# ---------------------------------------------------------------------------
# Header (every page)
# ---------------------------------------------------------------------------
theme.render_banner()

# =============================================================================
# PAGE: Dashboard
# =============================================================================
if st.session_state.nav == "dashboard":
    df_candidates = excel_handler.load_all_candidates()
    labels = config.load_column_labels()["candidate"]

    total = len(df_candidates)
    session_count = len(st.session_state.candidates)

    avg_exp = "—"
    if not df_candidates.empty and labels["experience_years"] in df_candidates.columns:
        numeric_exp = pd.to_numeric(df_candidates[labels["experience_years"]], errors="coerce").dropna()
        if len(numeric_exp):
            avg_exp = round(numeric_exp.mean(), 1)

    top_skill = "—"
    skill_counts = pd.Series(dtype=int)
    if not df_candidates.empty and labels["skills"] in df_candidates.columns:
        all_skills = (
            df_candidates[labels["skills"]].dropna().astype(str)
            .str.split(",").explode().str.strip()
        )
        all_skills = all_skills[all_skills != ""]
        if len(all_skills):
            skill_counts = all_skills.value_counts().head(10)
            top_skill = skill_counts.index[0]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        theme.kpi_card(total, t("kpi_total", L))
    with k2:
        theme.kpi_card(session_count, t("kpi_session", L))
    with k3:
        theme.kpi_card(avg_exp, t("kpi_avg_exp", L))
    with k4:
        theme.kpi_card(top_skill, t("kpi_top_skill", L))

    st.write("")

    if df_candidates.empty:
        st.info(t("dashboard_empty", L))
    else:
        st.markdown('<div class="hm-card">', unsafe_allow_html=True)
        theme.section_header(t("skill_chart_title", L))
        if len(skill_counts):
            st.bar_chart(skill_counts)
        else:
            st.caption("No skill data extracted yet.")
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# PAGE: Upload & Extract
# =============================================================================
elif st.session_state.nav == "upload":
    st.markdown('<div class="hm-card">', unsafe_allow_html=True)
    theme.section_header(t("nav_upload", L), t("upload_help", L))
    uploaded_files = st.file_uploader(
        t("upload_label", L), type=config.ACCEPTED_EXTENSIONS,
        accept_multiple_files=True, label_visibility="collapsed",
    )

    if uploaded_files:
        new_files = [f for f in uploaded_files if f.name not in st.session_state.candidates]
        if new_files:
            st.caption(f"{len(new_files)} new file(s) ready — click below to extract.")
            if st.button(t("process_btn", L), type="primary"):
                for f in new_files:
                    process_uploaded_file(f)
                if st.session_state.active_file is None:
                    st.session_state.active_file = new_files[0].name
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.candidates:
        st.markdown('<div class="hm-card">', unsafe_allow_html=True)
        theme.section_header("Processed Files")
        for fname, data in st.session_state.candidates.items():
            c1, c2, c3, c4 = st.columns([3, 2, 1.3, 1.2])
            c1.write(f"**{fname}**")
            c2.markdown(config.FORMAT_BADGES.get(data["ext"], data["ext"]), unsafe_allow_html=False)
            badge_kind = "saved" if data["saved"] else "pending"
            badge_text = t("already_saved", L) if data["saved"] else "Pending"
            c3.markdown(theme.badge(badge_text, badge_kind), unsafe_allow_html=True)
            if c4.button("Review →", key=f"gorev_{fname}"):
                st.session_state.active_file = fname
                st.session_state.nav = "review"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption(t("no_files_processed", L))

# =============================================================================
# PAGE: Review & Edit
# =============================================================================
elif st.session_state.nav == "review":
    if not st.session_state.candidates:
        st.info(t("no_files_processed", L))
    else:
        file_names = list(st.session_state.candidates.keys())
        if st.session_state.active_file not in file_names:
            st.session_state.active_file = file_names[0]

        selected = st.selectbox(
            t("select_candidate", L), options=file_names,
            index=file_names.index(st.session_state.active_file),
        )
        st.session_state.active_file = selected
        data = st.session_state.candidates[selected]

        top_l, top_r = st.columns([4, 1])
        with top_l:
            st.markdown(f"#### {selected}  {config.FORMAT_BADGES.get(data['ext'], '')}")
        with top_r:
            cbtn1, cbtn2 = st.columns(2)
            if cbtn1.button("🧹", help=t("clear_cv_data", L), use_container_width=True):
                data["relevant"] = {k: "" for k in data["relevant"]}
                data["irrelevant"], data["unmapped"], data["saved"] = [], [], False
                st.rerun()
            if cbtn2.button("🗑️", help=t("remove_cv", L), use_container_width=True):
                del st.session_state.candidates[selected]
                st.session_state.active_file = next(iter(st.session_state.candidates), None)
                st.rerun()

        notice_map = {
            "native": t("pdf_native_notice", L) if data["ext"] == "pdf" else t("docx_native_notice", L),
            "ocr": t("pdf_ocr_notice", L),
            "mixed": t("pdf_ocr_notice", L) + " " + t("pdf_native_notice", L),
        }
        if data.get("notice") in notice_map:
            st.caption(notice_map[data["notice"]])

        left_col, right_col = st.columns([1, 1.3], gap="large")

        with left_col:
            st.markdown('<div class="hm-card">', unsafe_allow_html=True)
            theme.section_header(t("original_doc", L))
            if data["preview"] is not None:
                st.image(data["preview"], use_container_width=True)
            else:
                all_text = "\n".join(
                    l["text"] for l in (data["unmapped"] or [])
                ) or "(Text extracted — see fields on the right.)"
                st.text_area(" ", value=all_text, height=380, disabled=True, label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="hm-card">', unsafe_allow_html=True)
            theme.section_header(t("extracted_data", L))
            rel = data["relevant"]
            c1, c2 = st.columns(2)
            with c1:
                rel["name"] = st.text_input(t("full_name", L), value=rel.get("name", ""))
                rel["phone"] = st.text_input(t("phone", L), value=str(rel.get("phone", "")))
                rel["experience_years"] = st.text_input(t("experience", L), value=str(rel.get("experience_years", "")))
            with c2:
                rel["email"] = st.text_input(t("email", L), value=rel.get("email", ""))
                rel["education"] = st.text_input(t("education", L), value=rel.get("education", ""))
            rel["skills"] = st.text_area(t("skills", L), value=rel.get("skills", ""), height=80)
            st.markdown("</div>", unsafe_allow_html=True)

            # --- Excluded / low-confidence text: accurate, but secondary & collapsed ---
            active_irrelevant = [i for i in data["irrelevant"] if i["status"] not in ("deleted", "restored")]
            with st.expander(f"{t('excluded_header', L)} ({len(active_irrelevant)})"):
                st.caption(t("excluded_caption", L))
                FIELD_OPTIONS = {
                    t("select_field_placeholder", L): None,
                    t("full_name", L): "name", t("email", L): "email", t("phone", L): "phone",
                    t("skills", L): "skills", t("experience", L): "experience_years",
                    t("education", L): "education",
                }
                if not active_irrelevant:
                    st.success(t("no_excluded", L))
                else:
                    for idx, item in enumerate(data["irrelevant"]):
                        if item["status"] in ("deleted", "restored"):
                            continue
                        row = st.columns([4, 2, 1.3, 2, 1, 1])
                        row[0].write(item["text"])
                        row[1].write(item["reason"].replace("_", " "))
                        row[2].write(f"{item['confidence']}%")
                        target_label = row[3].selectbox(
                            " ", options=list(FIELD_OPTIONS.keys()),
                            key=f"mv_{selected}_{idx}", label_visibility="collapsed",
                        )
                        if row[4].button(t("apply", L), key=f"ap_{selected}_{idx}"):
                            target_field = FIELD_OPTIONS[target_label]
                            if target_field:
                                value = item["text"]
                                if target_field == "phone":
                                    value = parser.reformat_as_phone_if_possible(value)
                                if target_field == "skills":
                                    rel["skills"] = f"{rel.get('skills', '')}, {value}".strip(", ")
                                else:
                                    rel[target_field] = value
                                item["status"] = "restored"
                                st.rerun()
                        if row[5].button(t("delete", L), key=f"del_{selected}_{idx}"):
                            item["status"] = "deleted"
                            st.rerun()

            # --- Duplicate check + Save ---
            dup_id = excel_handler.find_duplicate(rel.get("email", ""), rel.get("phone", ""))
            if dup_id is not None and not data["saved"]:
                st.warning(t("duplicate_warning", L, id=dup_id))

            save_disabled = data["saved"]
            if st.button(
                t("save_candidate", L) if not save_disabled else t("already_saved", L),
                disabled=save_disabled, type="primary", use_container_width=True,
            ):
                candidate_id = excel_handler.save_candidate(
                    candidate_data=rel,
                    irrelevant_items=[i for i in data["irrelevant"] if i["status"] == "deleted"],
                    source_file_name=selected,
                    saved_by=reviewer_name or "HR Reviewer",
                )
                data["saved"] = True
                st.success(t("saved_success", L, id=candidate_id))
                st.rerun()

# =============================================================================
# PAGE: Records
# =============================================================================
elif st.session_state.nav == "records":
    st.caption(t("records_intro", L))

    df_candidates = excel_handler.load_all_candidates()
    search_term = st.text_input(t("records_search", L), value="")
    if search_term and not df_candidates.empty:
        mask = df_candidates.astype(str).apply(
            lambda col: col.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        df_candidates = df_candidates[mask]

    st.markdown('<div class="hm-card">', unsafe_allow_html=True)
    theme.section_header(t("saved_candidates", L))
    st.dataframe(df_candidates, use_container_width=True)
    theme.section_header(t("audit_logs", L))
    st.dataframe(excel_handler.load_audit_log(), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.markdown('<div class="hm-card">', unsafe_allow_html=True)
        theme.section_header(t("delete_record_header", L), t("delete_record_caption", L))
        all_candidates = excel_handler.load_all_candidates()
        id_col = config.load_column_labels()["candidate"]["candidate_id"]
        if all_candidates.empty:
            st.caption(t("no_saved_records", L))
        else:
            options = all_candidates[id_col].tolist()
            selected_id = st.selectbox(t("select_candidate_to_delete", L), options=options)
            confirm = st.checkbox(t("confirm_delete", L), key="confirm_delete_chk")
            if st.button(t("delete_record_btn", L), disabled=not confirm, use_container_width=True):
                excel_handler.delete_candidate(selected_id)
                st.success(t("record_deleted", L, id=selected_id))
                st.rerun()

        st.markdown("---")
        try:
            excel_bytes = excel_handler.build_formatted_download()
            st.download_button(
                t("download_master", L), data=excel_bytes, file_name="Candidates_Master.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as exc:
            st.caption(f"⚠️ {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="hm-card">', unsafe_allow_html=True)
        theme.section_header(t("customize_columns", L))
        labels = config.load_column_labels()
        new_candidate_labels = {}
        for key in config.CANDIDATE_FIELD_KEYS:
            new_candidate_labels[key] = st.text_input(f"`{key}`", value=labels["candidate"][key], key=f"collabel_{key}")
        if st.button(t("save_column_settings", L), use_container_width=True):
            config.save_column_labels(new_candidate_labels, labels["audit"])
            excel_handler.rewrite_column_headers()
            st.success(t("column_settings_saved", L))
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
