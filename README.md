# Auction Automator

A simple, lightweight Python tool designed to convert raw auction Excel dumps into a standard lot import template automatically.

Built by [Pixel 'n' Mesh](https://pixel-n-mesh.lovable.app).

## 🚀 Features

- **Drag-and-Drop Simple**: No command-line experience required.
- **One-Time Install**: Automatically checks for and installs dependencies (`pandas`, `numpy`, `openpyxl`) only when needed.
- **Dynamic File Detection**: Put any raw `.xlsx` file in the folder and the script will automatically detect and process it.
- **Accessible Configuration**: Hardcoded variables are stored in an auto-generated `config.txt` file that anyone can edit in Notepad.
- **Cross-Platform**: Includes launcher scripts for both Windows (`run.bat`) and Mac (`run.command`).

## 📥 How to Use

1. **Download the Package**: Grab the latest `.zip` package from the [Landing Page](https://kyoo12.github.io/auction_import_maker/).
2. **Extract**: Unzip the package into an empty folder.
3. **Add Data**: Place exactly **one** raw auction excel dump (`.xlsx`) into the folder. The file name doesn't matter.
4. **Run**:
   - **Windows**: Double-click `run.bat`
   - **Mac**: Double-click `run.command` (right-click and select "Open" on first use)
5. **Get Results**: The script will instantly generate your formatted template as `lot_import_[OriginalName].xlsx`!

## ⚙️ Configuration
The first time you run the script, it will create a `config.txt` file. You can open this file in any text editor to modify the default values:
- `SELLER_NUM`
- `LOCATION`
- `VAT_PERCENTAGE`
- `TARGET_LANGUAGE`

## 🛠️ Tech Stack
- Python 3.x
- Pandas
- Numpy
- Openpyxl
- HTML/CSS/JS (Landing Page)
