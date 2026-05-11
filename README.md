# Auction Automator

A highly secure, zero-friction client-side web converter (and optional offline Python script) designed to convert raw auction Excel dumps into standard lot import templates automatically.

Built by [Pixel 'n' Mesh](https://pixel-n-mesh.lovable.app).

---

## 🌐 Web-Based Converter (Recommended)

No installation, no Python, no security warnings, and 100% private. 

👉 **Run it now**: [https://kyoo12.github.io/auction_import_maker/](https://kyoo12.github.io/auction_import_maker/)

### Why the Web Converter is Best:
* 🔒 **100% Private**: All processing runs locally inside your browser memory using WebAssembly/JavaScript. Your auction spreadsheets are **never uploaded** to any server.
* ⚡ **Instant**: Tom plays a smooth 60fps chomping animation in the browser and downloads your processed file immediately.
* 🖥️ **Full Config UI**: Easily set your Seller ID, Location, VAT %, and Target Language using clean sliders/inputs directly on the page before converting.
* 📱 **Cross-Platform**: Works perfectly on Windows, macOS, Linux, Chromebooks, and even iPads or tablets.

---

## 🖥️ Desktop / Offline Mode (Python Script)

If you need to process files offline or want to run the code locally as a python script, the desktop bundle is still fully supported.

### How to Use Offline:
1. **Download the Package**: Grab `auction_automator_package.zip` from this repository.
2. **Extract**: Unzip the package into an empty folder.
3. **Configure**: Open `config.txt` in any text editor to set your default `SELLER_NUM`, `LOCATION`, `VAT_PERCENTAGE`, and `TARGET_LANGUAGE`.
4. **Add Data**: Place exactly **one** raw auction excel dump (`.xlsx`) into the folder.
5. **Run**:
   * **Windows**: Double-click `run.bat` (creates a clean local `.venv` automatically).
   * **Mac**: Double-click `run.command` (right-click → "Open" on first use).
6. **Chomp**: Tom's head will chomp across the screen and save `lot_import_[OriginalName].xlsx` inside the folder.

---

## 🛠️ Tech Stack
* **Web Converter**: HTML5 / CSS3 / Vanilla JS + [SheetJS](https://sheetjs.com/) (Local Excel Parsing)
* **Desktop App**: Python 3.x + Pandas / Openpyxl + Tkinter & Pillow (GUI)
