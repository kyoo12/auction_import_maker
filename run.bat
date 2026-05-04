@echo off
echo Installing requirements...
pip install -r requirements.txt
echo.
echo Running Auction Automator...
python auction_automator.py
echo.
pause
