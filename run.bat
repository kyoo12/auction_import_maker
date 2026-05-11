@echo off
cd /d "%~dp0"

:: Create local virtual environment if it doesn't exist
if not exist ".venv" (
    echo Setting up local environment for the first time...
    python -m venv .venv
    if %errorlevel% neq 0 (
        powershell -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python 3 was not found. Please install it from https://python.org and try again.', 'Python Not Found', 'OK', 'Error')"
        exit /b 1
    )
)

:: Install / update dependencies into the local venv (silently)
echo Checking dependencies...
.venv\Scripts\pip install -q -r requirements.txt

:: Launch the GUI without a console window using the local Python
wscript run.vbs
