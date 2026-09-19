"""
config.py
---------
Central constants for HireMatrix: branding, paths, platform-aware OCR
tool detection (works both on local Windows/Mac/Linux AND on Streamlit
Community Cloud), keyword banks, column-label customization, and
English/Urdu UI translations.
"""

import json
import os
import platform

# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
APP_NAME = "HireMatrix"
APP_TAGLINE = "AI-Assisted Resume Intelligence for HR Teams"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.png")
BANNER_PATH = os.path.join(BASE_DIR, "assets", "logo_banner.png")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
LOG_DIR = os.path.join(BASE_DIR, "logs")
MASTER_EXCEL_PATH = os.path.join(EXPORT_DIR, "Candidates_Master.xlsx")
COLUMN_LABELS_PATH = os.path.join(BASE_DIR, "column_labels.json")

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# OCR / document tool detection
# ---------------------------------------------------------------------------
# On Streamlit Community Cloud (Linux) and on macOS/Linux after
# brew/apt install, tesseract & poppler are already on PATH — nothing to
# configure. Only Windows commonly needs an explicit path, so we only
# auto-probe the standard Windows install location there. You can always
# override with the TESSERACT_CMD / POPPLER_PATH environment variables.
OCR_CONFIDENCE_THRESHOLD = 45  # 0-100 scale, as returned by pytesseract

TESSERACT_CMD = os.environ.get("TESSERACT_CMD")
if not TESSERACT_CMD and platform.system() == "Windows":
    _default_win_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_default_win_tesseract):
        TESSERACT_CMD = _default_win_tesseract

POPPLER_PATH = os.environ.get("POPPLER_PATH")  # only needed on Windows; leave None elsewhere

# Accepted upload types — shown in the uploader and used to route each
# file to the right extractor in extraction_engine.py.
ACCEPTED_EXTENSIONS = ["png", "jpg", "jpeg", "pdf", "docx"]

FORMAT_BADGES = {
    "png": "🖼️ Image (OCR)",
    "jpg": "🖼️ Image (OCR)",
    "jpeg": "🖼️ Image (OCR)",
    "pdf": "📄 PDF",
    "docx": "📝 Word Document (direct text)",
}

# ---------------------------------------------------------------------------
# Phone number detection fallback regions (used by parser.py via the
# `phonenumbers` library) for numbers written WITHOUT a country code.
# ---------------------------------------------------------------------------
PHONE_FALLBACK_REGIONS = ["PK", "US", "GB", "IN", "AE", "SA", "CA", "AU"]

# ---------------------------------------------------------------------------
# Classification keyword banks
# ---------------------------------------------------------------------------
SKILL_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "html",
    "css", "react", "angular", "vue", "node.js", "django", "flask", "streamlit",
    "pandas", "numpy", "tensorflow", "pytorch", "machine learning", "deep learning",
    "nlp", "opencv", "power bi", "excel", "tableau", "aws", "azure", "docker",
    "kubernetes", "git", "github", "linux", "php", "laravel", "wordpress",
    "figma", "photoshop", "illustrator", "canva", "seo", "digital marketing",
    "salesforce", "sap", "erp", "crm",
    "communication", "leadership", "teamwork", "problem solving", "project management",
    "time management", "negotiation", "customer service", "data analysis",
    "microsoft office", "ms office",
]

EDUCATION_KEYWORDS = [
    "phd", "ph.d", "doctorate", "mphil", "m.phil",
    "master of", "masters", "m.sc", "msc", "mba", "ms ",
    "bachelor of", "bachelors", "b.sc", "bsc", "bs ", "bba", "be ", "b.e",
    "associate degree", "diploma", "intermediate", "fsc", "matriculation",
    "high school",
]

HOBBY_KEYWORDS = [
    "hobbies", "interests", "hobby", "reading books", "playing cricket",
    "playing football", "traveling", "travelling", "photography", "gaming",
    "cooking", "swimming", "music", "painting", "chess", "watching movies",
    "cycling", "hiking", "sketching", "blogging", "video games", "sports",
    "listening to music", "socializing", "gardening", "calligraphy",
]

REFERENCE_KEYWORDS = [
    "references", "reference available", "reference:", "referee",
    "available upon request",
]

PERSONAL_INFO_KEYWORDS = [
    "date of birth", "d.o.b", "dob:", "marital status", "nationality",
    "religion", "father's name", "father name", "husband name", "cnic",
    "gender:", "domicile", "place of birth", "blood group", "nic no",
    "n.i.c", "passport no",
]

SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "education": ["education", "academic background", "qualification", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "key skills"],
    "hobbies": ["hobbies", "interests", "hobbies & interests", "hobbies and interests"],
    "references": ["references", "reference"],
    "personal_info": ["personal information", "personal details", "personal profile",
                       "bio data", "biodata", "cnic", "personal data"],
    "summary": ["summary", "objective", "profile", "about me", "career objective"],
}

# ---------------------------------------------------------------------------
# Candidate Excel columns — internal keys (never change; used as dict keys
# throughout the code) + DEFAULT display labels. Labels CAN be customized
# at runtime via the UI, persisted to column_labels.json.
# ---------------------------------------------------------------------------
CANDIDATE_FIELD_KEYS = [
    "candidate_id", "name", "email", "phone", "skills",
    "experience_years", "education", "source_file", "saved_at", "saved_by",
]

DEFAULT_COLUMN_LABELS = {
    "candidate_id": "Candidate ID",
    "name": "Full Name",
    "email": "Email",
    "phone": "Phone",
    "skills": "Skills",
    "experience_years": "Experience (Years)",
    "education": "Highest Education",
    "source_file": "Source File",
    "saved_at": "Saved At",
    "saved_by": "Saved By",
}

AUDIT_FIELD_KEYS = [
    "candidate_id", "candidate_name", "text", "reason",
    "confidence", "status", "logged_at",
]

DEFAULT_AUDIT_LABELS = {
    "candidate_id": "Candidate ID",
    "candidate_name": "Related Candidate Name",
    "text": "Item Text",
    "reason": "Reason",
    "confidence": "OCR Confidence",
    "status": "Status",
    "logged_at": "Logged At",
}


def load_column_labels() -> dict:
    labels = {"candidate": dict(DEFAULT_COLUMN_LABELS), "audit": dict(DEFAULT_AUDIT_LABELS)}
    if os.path.exists(COLUMN_LABELS_PATH):
        try:
            with open(COLUMN_LABELS_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            labels["candidate"].update(saved.get("candidate", {}))
            labels["audit"].update(saved.get("audit", {}))
        except Exception:
            pass
    return labels


def save_column_labels(candidate_labels: dict, audit_labels: dict):
    with open(COLUMN_LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump({"candidate": candidate_labels, "audit": audit_labels}, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Internationalization (English / Urdu). Missing keys fall back to English
# automatically (see t()), so new features can ship with English-only
# strings without breaking the Urdu mode.
# ---------------------------------------------------------------------------
LANGUAGES = {"English": "en", "اردو (Urdu)": "ur"}

TRANSLATIONS = {
    "en": {
        "app_title": "HireMatrix",
        "app_tagline": "AI-Assisted Resume Intelligence for HR Teams",
        "nav_dashboard": "📊 Dashboard",
        "nav_upload": "📥 Upload & Extract",
        "nav_review": "🧾 Review & Edit",
        "nav_records": "🗂️ Records",
        "language_label": "Language",
        "reviewer_name": "Reviewer name (for audit log)",
        "upload_label": "Upload CVs — PDF, DOCX, PNG, JPG, JPEG",
        "upload_help": "Mix and match formats — scanned images and photos are read with OCR, "
                        "PDFs use their built-in text when possible (faster, more accurate) and "
                        "fall back to OCR for scanned pages, Word documents are read directly.",
        "process_btn": "⚙️ Process Uploaded Files",
        "kpi_total": "Total Candidates",
        "kpi_session": "Processed This Session",
        "kpi_avg_exp": "Avg. Experience (yrs)",
        "kpi_top_skill": "Most Common Skill",
        "dashboard_empty": "No candidates saved yet. Head to **Upload & Extract** to process your first CV.",
        "skill_chart_title": "Top Skills Across Saved Candidates",
        "select_candidate": "Select a candidate to review",
        "original_doc": "Original Document",
        "docx_native_notice": "📝 Extracted directly from the Word document — no OCR needed, so this text is 100% accurate to the source file.",
        "pdf_native_notice": "📄 Text layer found in this PDF — extracted directly (no OCR), for maximum accuracy.",
        "pdf_ocr_notice": "📄 No selectable text layer found — this page was processed with OCR.",
        "extracted_data": "Extracted Data",
        "full_name": "Full Name",
        "phone": "Phone Number",
        "experience": "Total Years of Experience",
        "email": "Email",
        "education": "Highest Education Degree",
        "skills": "Key Skills (comma-separated)",
        "excluded_header": "Excluded / Low-Confidence Text",
        "excluded_caption": "Text the parser set aside as noise (hobbies, references, personal details, "
                             "low-confidence OCR). Nothing is discarded — review it here and move anything "
                             "back into a field if it was excluded by mistake.",
        "col_text": "Text", "col_reason": "Reason", "col_confidence": "Confidence",
        "no_excluded": "Nothing was excluded for this candidate — all detected text mapped to a field.",
        "delete": "Delete", "move_to_field": "Move to", "apply": "Apply",
        "select_field_placeholder": "— choose —",
        "duplicate_warning": "⚠️ A candidate with this email or phone is already saved (Candidate ID #{id}). Saving again will create a duplicate record.",
        "save_candidate": "💾 Save Candidate to Excel",
        "already_saved": "✅ Already Saved",
        "saved_success": "Saved as Candidate ID #{id}.",
        "records_search": "🔍 Search saved candidates (name, email, or skill)",
        "records_intro": "Browse, search, export, and manage everything saved in your master workbook.",
        "saved_candidates": "Saved Candidates",
        "audit_logs": "Excluded-Data Audit Log",
        "download_master": "⬇️ Download Formatted Master Excel",
        "delete_record_header": "Delete a Saved Record",
        "delete_record_caption": "Permanently removes the candidate row and its related audit rows. This cannot be undone.",
        "select_candidate_to_delete": "Candidate ID to delete",
        "delete_record_btn": "🗑️ Delete Permanently",
        "record_deleted": "Candidate record #{id} deleted.",
        "no_saved_records": "No saved candidate records yet.",
        "confirm_delete": "I understand this cannot be undone",
        "customize_columns": "🏷️ Customize Excel Column Names",
        "save_column_settings": "Save Column Settings",
        "column_settings_saved": "Column names updated.",
        "clear_cv_data": "Clear this candidate's fields",
        "remove_cv": "Remove from list",
        "no_files_processed": "No files processed yet in this session.",
    },
    "ur": {
        "app_title": "HireMatrix",
        "app_tagline": "ایچ آر ٹیموں کے لیے ذہین ریزیومے تجزیہ",
        "nav_dashboard": "📊 ڈیش بورڈ",
        "nav_upload": "📥 اپلوڈ اور نکالنا",
        "nav_review": "🧾 جائزہ اور ترمیم",
        "nav_records": "🗂️ ریکارڈز",
        "language_label": "زبان",
        "reviewer_name": "جائزہ لینے والے کا نام",
        "upload_label": "سی ویز اپلوڈ کریں — PDF, DOCX, PNG, JPG, JPEG",
        "upload_help": "کوئی بھی فارمیٹ ملا کر اپلوڈ کریں — تصاویر OCR سے پڑھی جاتی ہیں، PDF کا موجود متن براہ راست "
                        "استعمال ہوتا ہے (زیادہ درست)، اور Word دستاویزات براہ راست پڑھی جاتی ہیں۔",
        "process_btn": "⚙️ اپلوڈ شدہ فائلیں پراسیس کریں",
        "kpi_total": "کل امیدوار",
        "kpi_session": "اس سیشن میں پراسیس شدہ",
        "kpi_avg_exp": "اوسط تجربہ (سال)",
        "kpi_top_skill": "سب سے عام مہارت",
        "dashboard_empty": "ابھی تک کوئی امیدوار محفوظ نہیں۔ **اپلوڈ اور نکالنا** سے شروع کریں۔",
        "skill_chart_title": "محفوظ شدہ امیدواروں میں سرِفہرست مہارتیں",
        "select_candidate": "جائزے کے لیے امیدوار منتخب کریں",
        "original_doc": "اصل دستاویز",
        "extracted_data": "نکالا گیا ڈیٹا",
        "full_name": "پورا نام",
        "phone": "فون نمبر",
        "experience": "تجربے کے کل سال",
        "email": "ای میل",
        "education": "اعلیٰ ترین تعلیمی ڈگری",
        "skills": "اہم مہارتیں",
        "excluded_header": "خارج شدہ / کم اعتماد متن",
        "col_text": "متن", "col_reason": "وجہ", "col_confidence": "اعتماد",
        "delete": "حذف کریں", "move_to_field": "منتقل کریں", "apply": "لاگو کریں",
        "save_candidate": "💾 ایکسل میں محفوظ کریں",
        "already_saved": "✅ پہلے سے محفوظ",
        "records_intro": "اپنی ماسٹر ورک بک میں محفوظ ہر چیز دیکھیں اور اس کا انتظام کریں۔",
        "saved_candidates": "محفوظ شدہ امیدوار",
        "download_master": "⬇️ ماسٹر ایکسل ڈاؤن لوڈ کریں",
        "no_saved_records": "ابھی تک کوئی محفوظ شدہ ریکارڈ نہیں۔",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translation helper. Falls back to English, then to the raw key."""
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text
