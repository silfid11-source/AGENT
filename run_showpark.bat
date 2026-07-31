@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d C:\Users\silfi\Documents\Codex\2026-07-31\referenced-chatgpt-conversation-this-is-untrusted\AI

echo Starting ShowPark AI Studio...
echo Open http://localhost:8501 in your browser.
echo.

if exist ".venv\pyvenv.cfg" (
    findstr /C:"C:\Users\silfi\AI\.venv" ".venv\pyvenv.cfg" >nul
    if not errorlevel 1 (
        echo Removing old virtual environment...
        rmdir /s /q ".venv"
    )
    findstr /C:"C:\Users\silfi\Documents\Codex\AI\.venv" ".venv\pyvenv.cfg" >nul
    if not errorlevel 1 (
        echo Removing moved virtual environment...
        rmdir /s /q ".venv"
    )
    findstr /C:"C:\Users\silfi\Documents\Codex\2026-07-31\referenced-chatgpt-conversation-this-is-untrusted\AI\.venv" ".venv\pyvenv.cfg" >nul
    if errorlevel 1 (
        echo Removing mismatched virtual environment...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
        "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" -m venv .venv
    ) else (
        py -m venv .venv
    )
)

echo Checking packages...
".venv\Scripts\python.exe" -m pip install streamlit openai python-dotenv

echo Running app...
".venv\Scripts\python.exe" -m streamlit run app_v2.py --server.port 8501
