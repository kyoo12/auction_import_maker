#!/usr/bin/env bash
cd "$(dirname "$0")"

echo "Checking dependencies..."
if ! python3 -c "import pandas, numpy, openpyxl" &> /dev/null; then
    echo "Installing requirements..."
    pip3 install -r requirements.txt
else
    echo "Dependencies are already installed."
fi

echo
echo "Running Auction Automator..."
python3 auction_automator.py
echo
read -p "Press [Enter] to close..."
