@echo off
REM Launches HireMatrix from wherever this .bat file lives.
cd /d "%~dp0"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python -m streamlit run app.py
pause
