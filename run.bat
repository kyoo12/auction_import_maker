@echo off
python -c "import pandas, numpy, openpyxl, PIL" 2>nul
if %errorlevel% neq 0 (
    pip install -r requirements.txt >nul 2>&1
)
wscript run.vbs
