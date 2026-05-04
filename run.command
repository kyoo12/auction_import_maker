#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Installing requirements..."
pip3 install -r requirements.txt
echo
echo "Running Auction Automator..."
python3 auction_automator.py
echo
read -p "Press [Enter] to close..."
