"""
parser.py
---------
Turns OCR line output (list of {"text", "confidence", "bbox"}) into:

    relevant   -> dict with keys: name, email, phone, skills,
                  experience_years, education
    irrelevant -> list of dicts: {"text", "confidence", "reason"}

Accuracy notes for this version (vs. the first release):
  1. SECTION-ZONE AWARENESS. Classification no longer looks at each line
     in isolation. It tracks which resume section it's currently inside
     (Hobbies / References / Personal Information / Education / ...) as
     it scans top to bottom, using config.SECTION_HEADERS. This fixes a
     real gap: a hobbies list like "- Cricket\n- Chess" under a "Hobbies:"
     header has NO hobby keyword on those lines themselves, so the old
     per-line-only keyword check let them slip into "relevant". Now every
     line inside a recognised noise section is classified by that
     section, not just lines that happen to repeat the section's keyword.
  2. PERSONAL/DEMOGRAPHIC FIELDS. CNIC, date of birth, marital status,
     nationality, religion, father's name, etc. are now their own
     "personal_info" category — routed to irrelevant instead of being
     left as unmapped noise. This also supports fairer/blinder initial
     screening, since these fields don't bear on qualification.
  3. SYMBOL-AWARE GARBAGE CHECK. The old alpha-ratio garbage filter
     mis-flagged legitimate skill lines like "C++, C#, ASP.NET" (lots of
     punctuation) as noise. Technical symbols common in skills (+ # . /
     &) are no longer counted against a line, and any line containing a
     known skill keyword is never flagged as garbage.
  4. PRECISE "CONSUMED LINE" TRACKING. Previously, "unmapped" leftover
     lines were computed with fuzzy substring matching against the
     extracted field VALUES — which broke silently whenever a value was
     reformatted (e.g. a phone number reformatted by `phonenumbers` no
     longer matches the raw OCR text), causing the source line to
     wrongly reappear as "unmapped". Extractors now return the exact
     source line INDEX they used, so consumption is tracked by identity,
     not string matching.

Design note for the FYP report: extraction is regex/keyword-driven by
default (fast, deterministic, easy to defend in a viva). If spaCy and
its English model are installed, name detection is upgraded to use
NER (PERSON entities) for better accuracy — but the app degrades
gracefully without it.
"""

import re
import logging

import config

logger = logging.getLogger(__name__)

# Try to load spaCy once, at import time. If unavailable, fall back silently.
_NLP = None
try:
    import spacy
    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning(
            "spaCy is installed but 'en_core_web_sm' model is missing. "
            "Run: python -m spacy download en_core_web_sm  -- falling back to regex."
        )
except ImportError:
    logger.info("spaCy not installed — using regex-only heuristics for name extraction.")

# Try to load the `phonenumbers` library (Google's libphonenumber port) for
# accurate, WORLDWIDE phone number detection + validation. Falls back to a
# conservative regex heuristic if it isn't installed.
try:
    import phonenumbers
    _PHONENUMBERS_AVAILABLE = True
except ImportError:
    _PHONENUMBERS_AVAILABLE = False
    logger.info("`phonenumbers` not installed — using regex-only phone detection "
                "(run: pip install phonenumbers for accurate global detection).")


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Fallback-only regex (used when `phonenumbers` isn't installed).
PHONE_FALLBACK_RE = re.compile(
    r"(?<!\d)(\+?\d{1,3}[\s\-.]?)?(\(?\d{2,4}\)?[\s\-.]?){2,4}\d{2,4}(?!\d)"
)

_NON_PHONE_CONTEXT_RE = re.compile(
    r"(years?|yrs?|salary|rs\.?|pkr|usd|\$|cgpa|gpa|percent|%|/\d{2,4})",
    re.IGNORECASE,
)

EXPERIENCE_RE = re.compile(
    r"(\d{1,2})\+?\s*(?:years|yrs|year)\s*(?:of)?\s*(?:experience)?",
    re.IGNORECASE,
)

# Technical symbols that show up legitimately in skill lines ("C++", "C#",
# "ASP.NET", "R&D") — not counted as "garbage" when judging line quality.
_TECH_SYMBOLS = set("+#./&-")


def _is_probably_phone(candidate: str, context_line: str = "") -> bool:
    """Guards against regex matching things like page numbers, years, or GPAs."""
    digits = re.sub(r"\D", "", candidate)
    if not (7 <= len(digits) <= 15):
        return False
    if _NON_PHONE_CONTEXT_RE.search(context_line):
        return False
    if len(digits) == 4 and 1950 <= int(digits) <= 2035:
        return False
    return True


def _line_looks_like_phone(line: str) -> bool:
    """Used by extract_name() to skip a line that's actually a phone number."""
    if _PHONENUMBERS_AVAILABLE:
        for _ in phonenumbers.PhoneNumberMatcher(line, None):
            return True
        for region in config.PHONE_FALLBACK_REGIONS:
            for _ in phonenumbers.PhoneNumberMatcher(line, region):
                return True
        return False
    return bool(PHONE_FALLBACK_RE.search(line))


# ---------------------------------------------------------------------------
# Field extractors — each takes the (already-filtered) RELEVANT lines list
# and returns (value, source_line_index) so the caller can mark exactly
# which line was consumed — no fuzzy string matching required.
# ---------------------------------------------------------------------------
def extract_email(lines: list):
    for idx, l in enumerate(lines):
        match = EMAIL_RE.search(l["text"])
        if match:
            return match.group(0), idx
    return None, None


def extract_phone(lines: list):
    """
    Detects a phone number ANYWHERE in the world while filtering out other
    numbers (years, GPAs, salaries, ID numbers). Checked per-line (not on
    one giant joined blob) so the source line is known precisely and a
    number can't accidentally be assembled across unrelated lines.

    Primary path: Google's `phonenumbers` library — validates against real
    international dialing-plan rules, so it recognises "+92 300 1234567",
    "+1 (415) 555-2671", "+44 20 7946 0958", etc. worldwide.
      - Pass 1: numbers with an explicit country code (any country).
      - Pass 2 (only if nothing found): retry each region in
        config.PHONE_FALLBACK_REGIONS, for local-format numbers with no
        country code (e.g. "0300-1234567").
    Fallback: conservative regex + context checks if the library isn't installed.
    """
    if _PHONENUMBERS_AVAILABLE:
        for idx, l in enumerate(lines):
            for match in phonenumbers.PhoneNumberMatcher(l["text"], None):
                return phonenumbers.format_number(
                    match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                ), idx
        for region in config.PHONE_FALLBACK_REGIONS:
            for idx, l in enumerate(lines):
                for match in phonenumbers.PhoneNumberMatcher(l["text"], region):
                    return phonenumbers.format_number(
                        match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    ), idx
        return None, None

    for idx, l in enumerate(lines):
        for match in PHONE_FALLBACK_RE.finditer(l["text"]):
            candidate = match.group(0).strip()
            if _is_probably_phone(candidate, context_line=l["text"]):
                return candidate, idx
    return None, None


def extract_experience_years(lines: list):
    """Takes the LARGEST 'N years' mention across all lines (usually the total)."""
    best_value, best_idx = None, None
    for idx, l in enumerate(lines):
        for m in EXPERIENCE_RE.findall(l["text"]):
            val = int(m)
            if best_value is None or val > best_value:
                best_value, best_idx = val, idx
    return best_value, best_idx


def extract_education(lines: list):
    """Returns the highest-ranked education keyword found, in order of seniority."""
    ranked = ["phd", "ph.d", "doctorate", "mphil", "m.phil", "master of", "masters",
              "m.sc", "msc", "mba", "ms ", "bachelor of", "bachelors", "b.sc", "bsc",
              "bs ", "bba", "be ", "b.e", "associate degree", "diploma",
              "intermediate", "fsc", "matriculation", "high school"]
    for keyword in ranked:
        for idx, l in enumerate(lines):
            if keyword in l["text"].lower():
                return l["text"].strip(), idx
    return None, None


def extract_skills(lines: list):
    """
    Returns (skills_string, consumed_indices) — every line containing at
    least one recognised skill keyword is consumed (kept out of "unmapped"),
    even though several lines can each contribute different skills.
    """
    found = set()
    consumed = set()
    for idx, l in enumerate(lines):
        low = l["text"].lower()
        hit = False
        for kw in config.SKILL_KEYWORDS:
            if kw in low:
                found.add(kw)
                hit = True
        if hit:
            consumed.add(idx)
    skills_str = ", ".join(s.title() if len(s) > 3 else s.upper() for s in sorted(found))
    return skills_str, consumed


def extract_name(lines: list):
    """
    Name heuristic:
    1. If spaCy is available, run NER on the first ~6 lines and take the
       first PERSON entity.
    2. Fallback: the first non-empty line that (a) isn't an email/phone
       line and (b) is short (<=4 words) and mostly alphabetic — resumes
       almost always put the candidate's name as the very first line.
    """
    top = lines[:6]

    if _NLP is not None:
        snippet = "\n".join(l["text"].strip() for l in top if l["text"].strip())
        doc = _NLP(snippet)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name_text = ent.text.strip()
                for idx, l in enumerate(top):
                    if name_text and name_text in l["text"]:
                        return name_text, idx
                return name_text, None

    for idx, l in enumerate(top):
        line = l["text"].strip()
        if not line:
            continue
        if "@" in line or _line_looks_like_phone(line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4 and sum(c.isalpha() or c.isspace() for c in line) / max(len(line), 1) > 0.8:
            return line.title(), idx
    return None, None


def reformat_as_phone_if_possible(text: str) -> str:
    """
    Used when an HR reviewer manually moves an irrelevant item into the
    Phone field ("mark as relevant"): tries to validate/reformat it as a
    real phone number so the master sheet stays consistent; if it isn't a
    valid number, the raw text is returned unchanged (still editable by hand).
    """
    if not _PHONENUMBERS_AVAILABLE:
        return text
    try:
        for region in [None] + config.PHONE_FALLBACK_REGIONS:
            try:
                parsed = phonenumbers.parse(text, region)
            except phonenumbers.NumberParseException:
                continue
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except Exception:
        pass
    return text


# ---------------------------------------------------------------------------
# Section-zone detection — recognises a line as a section HEADER (e.g.
# "Hobbies:", "References", "Personal Information") so everything AFTER it,
# until the next recognised header, can be classified by that section
# rather than needing its own keyword match.
# ---------------------------------------------------------------------------
NOISE_ZONES = {"hobbies": "hobby", "references": "reference", "personal_info": "personal_info"}


def _detect_section(text_lower: str):
    """Returns a section key (from config.SECTION_HEADERS) if this line IS a
    header line, else None. Headers are short — this guards against a long
    sentence that merely happens to contain a header word."""
    cleaned = text_lower.strip(" :-–—\t")
    if not cleaned or len(cleaned) > 40:
        return None
    for section, headers in config.SECTION_HEADERS.items():
        for h in headers:
            if cleaned == h or cleaned.startswith(h + " ") or cleaned.startswith(h + ":"):
                return section
    return None


# ---------------------------------------------------------------------------
# Line-level classification: relevant vs irrelevant
# ---------------------------------------------------------------------------
def _classify_line_reason(line: dict, zone: str = None) -> str:
    """
    Returns a short reason string if a line should be treated as
    irrelevant/noise, or None if it should be considered for relevant
    field extraction. `zone` is the current section (if any) as tracked
    by classify_lines() — e.g. lines under a "Hobbies:" header are zoned
    "hobbies" even if the line itself doesn't repeat the word "hobby".
    """
    text_lower = line["text"].lower().strip()

    if not text_lower or len(text_lower) < 2:
        return "empty_or_too_short"

    if line["confidence"] < config.OCR_CONFIDENCE_THRESHOLD:
        return "low_ocr_confidence"

    if zone in NOISE_ZONES:
        return NOISE_ZONES[zone]

    if any(kw in text_lower for kw in config.HOBBY_KEYWORDS):
        return "hobby"

    if any(kw in text_lower for kw in config.REFERENCE_KEYWORDS):
        return "reference"

    if any(kw in text_lower for kw in config.PERSONAL_INFO_KEYWORDS):
        return "personal_info"

    # Mostly symbols/garbage (common OCR artefact on borders, logos, etc.)
    # — but never flag a line that contains a recognised skill keyword
    # (e.g. "C++, C#, ASP.NET" has a low raw alpha ratio but is real data).
    if not any(kw in text_lower for kw in config.SKILL_KEYWORDS):
        meaningful = sum(1 for c in text_lower if c.isalnum() or c in _TECH_SYMBOLS or c.isspace())
        if meaningful / len(text_lower) < 0.4:
            return "garbage_symbols"

    return None  # considered potentially relevant


def classify_lines(lines: list):
    """
    Splits OCR lines into:
        relevant_lines   -> used for field extraction
        irrelevant_items -> [{"text", "confidence", "reason"}]

    Tracks the current resume SECTION as it scans top to bottom (see
    _detect_section), so a whole block of hobbies/references/personal-info
    lines is classified correctly even when only the header line itself
    contains the section's keyword.
    """
    relevant_lines = []
    irrelevant_items = []
    current_zone = None

    for line in lines:
        text_lower = line["text"].lower().strip()
        section = _detect_section(text_lower)
        if section:
            current_zone = section

        reason = _classify_line_reason(line, zone=current_zone)
        if reason:
            irrelevant_items.append({
                "text": line["text"],
                "confidence": line["confidence"],
                "reason": reason,
            })
        else:
            relevant_lines.append(line)

    return relevant_lines, irrelevant_items


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------
def parse_resume(lines: list) -> dict:
    """
    Main entry point used by app.py.

    Input:  list of OCR line dicts (from ocr_engine.ocr_image_to_lines)
    Output: {
        "relevant": {name, email, phone, skills, experience_years, education},
        "irrelevant": [ {text, confidence, reason}, ... ],
        "unmapped_relevant_lines": [line dicts kept but not mapped to a field]
    }
    """
    relevant_lines, irrelevant_items = classify_lines(lines)

    name, name_idx = extract_name(relevant_lines)
    email, email_idx = extract_email(relevant_lines)
    phone, phone_idx = extract_phone(relevant_lines)
    skills, skills_idx_set = extract_skills(relevant_lines)
    experience_years, exp_idx = extract_experience_years(relevant_lines)
    education, edu_idx = extract_education(relevant_lines)

    # Precise consumption tracking by line INDEX (not fuzzy string
    # matching) — a reformatted phone number, for example, no longer
    # causes its source line to wrongly reappear as "unmapped".
    consumed = set(skills_idx_set)
    for idx in (name_idx, email_idx, phone_idx, exp_idx, edu_idx):
        if idx is not None:
            consumed.add(idx)

    unmapped = [l for i, l in enumerate(relevant_lines) if i not in consumed]

    return {
        "relevant": {
            "name": name or "",
            "email": email or "",
            "phone": phone or "",
            "skills": skills or "",
            "experience_years": experience_years if experience_years is not None else "",
            "education": education or "",
        },
        "irrelevant": irrelevant_items,
        "unmapped_relevant_lines": unmapped,
    }
