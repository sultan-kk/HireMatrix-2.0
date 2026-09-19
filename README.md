# HireMatrix — AI-Assisted Resume Intelligence for HR Teams

A Final Year Project: upload CVs in **any common format** (PDF, DOCX, PNG,
JPG, JPEG), automatically extract structured candidate data (Name, Email,
Phone, Skills, Experience, Education), review and correct it, and export
verified records to a multi-sheet Excel workbook with a full audit trail.

This is a ground-up redesign — new UI, new extraction engine, new brand —
built to deploy cleanly on **Streamlit Community Cloud** straight from
GitHub.

## 1. What's new in this version

- **Multi-format uploads**: PDF, DOCX, PNG, JPG, JPEG — not just images.
- **Hybrid PDF extraction**: a PDF's real text layer is used directly
  when present (instant, 100% accurate — no OCR needed at all), and OCR
  only kicks in for pages that are actually scanned images with no
  selectable text. Each candidate's Review page tells you which path was
  used.
- **DOCX support**: read directly via `python-docx` — the most accurate
  path of all three formats, since there's no image/OCR step at all.
- **Fresh UI**: sidebar navigation (Dashboard / Upload & Extract /
  Review & Edit / Records) instead of one long scrolling page, a new
  indigo/coral visual identity, and a real HR dashboard with KPIs and a
  skills-frequency chart across everyone you've saved.
- **Duplicate detection**: before saving, HireMatrix checks the master
  workbook for a matching email or phone number and warns you if this
  candidate may already be on file.
- **Excluded/low-confidence text**: kept accurate (section-aware
  classification — see §6) but tucked into a collapsed, secondary panel
  per candidate rather than dominating the screen — delete anything
  that's genuinely noise, or move a wrongly-excluded line back into a
  field.
- **Records search**: filter saved candidates by name, email, or skill
  right from the Records page.
- **Streamlit Cloud ready**: `packages.txt` + `requirements.txt` are set
  up so Tesseract, Poppler, and the spaCy English model install
  automatically on deploy — no manual setup steps on the server.

## 2. Project Structure

```
hiremax/
├── app.py                  # Streamlit UI — sidebar nav, 4 pages
├── extraction_engine.py    # Multi-format extraction (image OCR / hybrid PDF / DOCX)
├── parser.py                # Section-aware classification + field extraction
├── excel_handler.py        # Multi-sheet Excel export, delete, duplicate check, formatting
├── theme.py                 # Indigo/coral design system (cards, KPIs, badges)
├── config.py                 # Branding, paths, keyword banks, i18n (EN/UR)
├── generate_icon.py          # Draws assets/icon.png + logo_banner.png (network-motif logo)
├── assets/
│   ├── icon.png / icon.ico     # App icon (already generated)
│   ├── logo_banner.png         # Header banner (already generated)
│   └── fonts/                   # Bundled OFL-licensed fonts used to draw the logo
├── packages.txt              # APT packages for Streamlit Cloud (tesseract, poppler, ...)
├── requirements.txt          # Python packages, incl. the spaCy model wheel
├── .streamlit/config.toml    # Theme colors + upload size limit
├── run_app.bat               # Local Windows launcher (venv-aware)
├── column_labels.json        # Auto-created once you rename columns in the UI
├── exports/                  # Candidates_Master.xlsx is created here
└── sample_data/              # put test CVs here
```

## 3. Deploying to Streamlit Community Cloud (what you asked about)

This is the part that actually makes Tesseract/Poppler work on the
server — **`packages.txt`** is the file Streamlit Cloud reads to install
system-level (apt) packages before your app starts:

```
tesseract-ocr
poppler-utils
libgl1
libglib2.0-0
```

You don't run this yourself — Streamlit Cloud runs `apt-get install` on
every line in this file automatically during deployment. Steps:

1. Push this whole folder to a GitHub repo (`packages.txt` and
   `requirements.txt` must sit at the repo root, next to `app.py`).
2. Go to share.streamlit.io, sign in, click **New app**, pick your
   repo/branch, and set the main file to `app.py`.
3. Deploy. Streamlit Cloud will:
   - read `packages.txt` → installs `tesseract-ocr` + `poppler-utils` (so
     OCR and PDF-page-rendering work out of the box, no path
     configuration needed — `config.py` only auto-probes a Windows path,
     and leaves `TESSERACT_CMD`/`POPPLER_PATH` as `None` on Linux, which
     is correct there since they're already on `PATH`).
   - read `requirements.txt` → installs everything including the spaCy
     model wheel directly (no separate download command needed, which is
     what fails silently on Cloud if you rely on
     `python -m spacy download`).
4. That's it — no server terminal access needed, no manual setup steps.

## 4. Running locally

### System dependencies (Tesseract + Poppler)

**Windows:**
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki (installer)
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases (zip)
- If either isn't on PATH, set `TESSERACT_CMD` / `POPPLER_PATH` as
  environment variables, or edit the paths directly in `config.py`.
  `config.py` already auto-detects the standard
  `C:\Program Files\Tesseract-OCR\tesseract.exe` install path.

**macOS:** `brew install tesseract poppler`

**Linux:** `sudo apt install tesseract-ocr poppler-utils`

### Python environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

The spaCy model installs automatically as part of this command (see the
wheel URL in `requirements.txt`) — no extra `spacy download` step, and no
risk of it landing in the wrong Python environment (a common issue if you
install packages from a separate admin/system terminal instead of your
activated venv).

### Run it

```bash
streamlit run app.py
```

or on Windows, just double-click `run_app.bat` (it activates `venv`
automatically if one exists next to it).

## 5. How the four pages work

- **Dashboard** — KPI tiles (Total Candidates, Processed This Session,
  Avg. Experience, Most Common Skill) and a bar chart of the top skills
  across every saved candidate. Empty and encouraging on first run, fills
  in as you save candidates.
- **Upload & Extract** — drop in any mix of PDF/DOCX/PNG/JPG/JPEG,
  click **Process Uploaded Files**, and each one gets a format badge
  (PDF / Word / Image) plus a status badge (Pending/Saved). Click
  **Review →** to jump straight to a candidate.
- **Review & Edit** — original document on the left (an image for
  photos/scanned PDFs, or the extracted text for DOCX/native-text PDFs
  where there's no "page picture" to show), editable fields on the
  right. A caption tells you whether this candidate's text came from a
  native text layer or from OCR. The **Excluded / Low-Confidence Text**
  panel is collapsed by default — open it to delete genuine noise or move
  a wrongly-excluded item back into a field. If the email/phone matches
  an existing saved candidate, you'll see a duplicate warning before
  saving.
- **Records** — search saved candidates, browse the audit log,
  download a freshly formatted copy of the master workbook, permanently
  delete a record, or rename any Excel column header.

## 6. How classification works (for your viva / report)

- Every extractor (OCR, native PDF, DOCX) produces the same shape: a list
  of lines with a confidence score. Native text (DOCX, PDF text layer)
  gets confidence=100 since it's exact, not a guess.
- **Section-zone tracking**: as the parser scans a resume top-to-bottom,
  it tracks which section it's currently in (Education / Skills /
  Hobbies / References / Personal Information / ...) by recognising
  header lines. This means a hobbies list like "Cricket" / "Chess" under
  a "Hobbies:" header is correctly excluded even though neither word
  contains "hobby" itself — the old naive per-line-keyword approach
  missed this.
- **Personal/demographic fields** (CNIC, date of birth, marital status,
  nationality, religion, father's name, ...) are their own category,
  separated from the core hire-relevant fields — this also supports
  fairer, more consistent initial screening.
- **Referee contact exclusion**: a referee's own email/phone sitting
  under a "References" section is excluded before field extraction runs,
  so it can never accidentally overwrite the actual candidate's contact
  info.
- **Symbol-aware noise filter**: technical punctuation common in skill
  lines (`C++`, `C#`, `ASP.NET`) is no longer mistaken for OCR garbage.
- **Precise "excluded" tracking**: extractors return the exact source
  line they used (by index, not fuzzy text matching), so a reformatted
  value (e.g. a phone number normalized by `phonenumbers`) never causes
  its source line to wrongly reappear as unclassified noise.
- **Worldwide phone detection** via Google's `phonenumbers` library,
  validated against real dialing-plan rules — not just "looks like a
  number."

## 7. Extending the project

- Add more skills/education keywords in `config.py`.
- Add more languages: add a new key to `config.TRANSLATIONS` and
  `config.LANGUAGES` in `config.py` — missing keys fall back to English
  automatically, so you can translate incrementally.
- Add authentication (`streamlit-authenticator`) for multi-user HR teams.
- Swap the regex/keyword skills extractor for a fine-tuned NER model for
  a stronger "AI" story in your report/demo.
