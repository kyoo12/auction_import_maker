# Auction Automator

A simple, lightweight Python tool designed to convert raw auction Excel dumps into a standard lot import template automatically.

Built by [Pixel 'n' Mesh](https://pixel-n-mesh.lovable.app).

## 🚀 Features

- **Animated GUI**: A fun chomping animation plays instead of a boring command line.
- **No Console Window**: Launches silently in the background on both Windows and Mac.
- **One-Time Install**: Automatically checks for and installs all dependencies on first run.
- **Dynamic File Detection**: Put any raw `.xlsx` file in the folder — the script finds and processes it automatically.
- **Pre-Configured**: `config.txt` is included in the package. Edit it before running to set your Seller Number, VAT, and Location.
- **Cross-Platform**: Includes launcher scripts for Windows (`run.bat`) and Mac (`run.command`).

## 📥 How to Use

1. **Download the Package**: Grab the latest `.zip` from the [Landing Page](https://kyoo12.github.io/auction_import_maker/).
2. **Extract**: Unzip the package into an empty folder.
3. **Configure** *(optional)*: Open `config.txt` in any text editor and set your `SELLER_NUM`, `LOCATION`, `VAT_PERCENTAGE`, and `TARGET_LANGUAGE`.
4. **Add Data**: Place exactly **one** raw auction excel dump (`.xlsx`) into the folder.
5. **Run**:
   - **Windows**: Double-click `run.bat`
   - **Mac**: Double-click `run.command` (right-click → "Open" on first use to bypass Gatekeeper)
6. **Get Results**: The animated GUI will appear, Tom will eat your files, and the formatted template `lot_import_[OriginalName].xlsx` will be generated!

## ⚙️ Configuration
Edit `config.txt` (included in the package) in any text editor to set your defaults:
- `SELLER_NUM` — your seller number
- `LOCATION` — location code
- `VAT_PERCENTAGE` — VAT rate (e.g. `20`)
- `TARGET_LANGUAGE` — language code (e.g. `en`, `nl`, `de`)

## 🛠️ Tech Stack
- Python 3.x
- Pandas / Numpy / Openpyxl
- Tkinter + Pillow (GUI & animation)
- HTML/CSS/JS (Landing Page)
