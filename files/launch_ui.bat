@echo off
echo RAG System with Gradio UI Launcher
echo =====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script from the rag-system directory
    pause
    exit /b 1
)

REM Install requirements if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Launch the system
echo Launching RAG System...
echo.
echo The system will open in your default web browser
echo Gradio UI: http://localhost:7860
echo API Server: http://localhost:8000
echo.
echo Press Ctrl+C to stop the system
echo.

python launch_ui.py

echo.
echo RAG System stopped
pause 