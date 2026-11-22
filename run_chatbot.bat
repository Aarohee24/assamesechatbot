@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python 3.10 or newer is required. Install Python and enable the PATH option.
        pause
        exit /b 1
    )
    echo Creating the project virtual environment...
    python -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo Could not create the virtual environment.
        pause
        exit /b 1
    )
)

"%PYTHON%" -c "import requests,streamlit,fasttext,huggingface_hub,numpy" >nul 2>nul
if errorlevel 1 (
    echo Installing missing project dependencies without upgrading installed packages...
    "%PYTHON%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo Dependency installation failed. Check the network and requirements.txt.
        pause
        exit /b 1
    )
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_chatbot.ps1"
if errorlevel 1 (
    echo Chatbot did not start. Review the error above and logs folder.
    pause
    exit /b 1
)
endlocal
