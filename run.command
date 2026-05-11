#!/usr/bin/env bash
cd "$(dirname "$0")"

# --- Check Python 3 is installed ---
if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python 3 Not Found" message "Please install Python 3 from https://python.org and try again." as critical buttons {"OK"} default button "OK"'
    exit 1
fi

# --- Check tkinter is available ---
if ! python3 -c "import tkinter" 2>/dev/null; then
    osascript -e 'display alert "Missing Component: tkinter" message "Your Python installation is missing tkinter (required for the animation window).\n\nPlease download and install Python from:\nhttps://python.org/downloads\n\n(Do not use the Homebrew version)" as critical buttons {"OK"} default button "OK"'
    exit 1
fi

# --- Create local virtual environment if it doesn't exist ---
if [ ! -d ".venv" ]; then
    osascript -e 'display notification "Setting up local environment for the first time. This may take a moment." with title "Auction Automator"'
    python3 -m venv .venv
fi

# --- Install dependencies into local venv ---
.venv/bin/pip install -q -r requirements.txt

# --- Launch the app ---
.venv/bin/python auction_automator.py
