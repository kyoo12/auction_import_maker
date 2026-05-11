#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! python3 -c "import pandas, numpy, openpyxl, PIL" &> /dev/null; then
    pip3 install -r requirements.txt > /dev/null 2>&1
fi

python3 auction_automator.py &
exit
