@echo off
echo Checking dependencies...
python -c "import pandas, numpy, openpyxl" 2>nul
if %errorlevel% neq 0 (
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    echo Dependencies are already installed.
)
echo.
echo Running Auction Automator...
python auction_automator.py
echo.
pause
