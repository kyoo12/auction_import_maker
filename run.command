#!/usr/bin/env bash
cd "$(dirname "$0")"

# Check and install dependencies (including tkinter for Mac)
if ! python3 -c "import pandas, numpy, openpyxl, PIL, tkinter" 2>/dev/null; then
    echo "Installing required packages..."
    pip3 install pandas numpy openpyxl Pillow
fi

# Launch the GUI app — terminal stays open until animation window closes
python3 auction_automator.py
