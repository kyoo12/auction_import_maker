import os
import glob
import threading
import time
import re
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

NUMERIC_COLS = {
    'starting_bid', 'estimated_price', 'reserve_bid',
    'vat_percentage', 'fee_vat_percentage',
    'attribute-amount', 'attribute-buy_amount'
}

BINARY_COLS = {
    'needs_manual_allocation', 'is_spotlight'
}

def sanitize_multi_line(val):
    if pd.isna(val) or val is None or val == "":
        return ""
    if isinstance(val, (int, float, np.number)):
        if np.isnan(val):
            return ""
        val = str(val)
    s = str(val)

    # 1. Decode OpenXML hex entities (handling double-escaped _x005F_ first)
    while re.search(r'_x005[fF]_x([0-9a-fA-F]{4})_', s):
        s = re.sub(r'_x005[fF]_x([0-9a-fA-F]{4})_', r'_x\1_', s)
    s = re.sub(r'_x005[fF]_', '_', s, flags=re.IGNORECASE)
    def _decode_hex(m):
        try:
            return chr(int(m.group(1), 16))
        except Exception:
            return m.group(0)
    s = re.sub(r'_x([0-9a-fA-F]{4})_', _decode_hex, s, flags=re.IGNORECASE)
    s = re.sub(r'_x000[dD]_?', '\r', s, flags=re.IGNORECASE)

    # 2. Eliminate \r, \r\n, \u2028, \u2029 -> normalize to clean \n
    s = s.replace('\r\n', '\n')
    s = re.sub(r'[\r\u2028\u2029]', '\n', s)

    # 3. Clean non-breaking and Unicode spaces
    s = re.sub(r'[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]', ' ', s)

    # 4. Strip zero-width and invisible control characters (preserve \n)
    s = re.sub(r'[\u200B-\u200D\uFEFF\u2060\u180E]', '', s)
    s = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', s)

    # 5. Trim
    s = s.strip()

    # 6. Cap at Excel's 32,767 limit
    return s[:32767]

def sanitize_single_line(val):
    if pd.isna(val) or val is None or val == "":
        return ""
    # Preserve numeric types directly
    if isinstance(val, (int, float, np.number)):
        if np.isnan(val):
            return ""
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return val
    s = str(val)

    # 1. Decode OpenXML hex entities
    while re.search(r'_x005[fF]_x([0-9a-fA-F]{4})_', s):
        s = re.sub(r'_x005[fF]_x([0-9a-fA-F]{4})_', r'_x\1_', s)
    s = re.sub(r'_x005[fF]_', '_', s, flags=re.IGNORECASE)
    def _decode_hex(m):
        try:
            return chr(int(m.group(1), 16))
        except Exception:
            return m.group(0)
    s = re.sub(r'_x([0-9a-fA-F]{4})_', _decode_hex, s, flags=re.IGNORECASE)
    s = re.sub(r'_x000[dD]_?', ' ', s, flags=re.IGNORECASE)

    # 2. Collapse internal newlines and line breaks to spaces
    s = re.sub(r'[\r\n\u2028\u2029\t]+', ' ', s)

    # 3. Clean non-breaking and Unicode spaces
    s = re.sub(r'[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]', ' ', s)

    # 4. Strip zero-width and invisible control characters
    s = re.sub(r'[\u200B-\u200D\uFEFF\u2060\u180E]', '', s)
    s = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', s)

    # 5. Collapse multiple spaces and trim
    s = re.sub(r' +', ' ', s).strip()

    # 6. Cap at Excel's 32,767 limit
    return s[:32767]

def sanitize_numeric(val):
    if pd.isna(val) or val is None or val == "":
        return ""
    if isinstance(val, (int, float, np.number)):
        if np.isnan(val):
            return ""
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return val
    clean = sanitize_single_line(val)
    if clean == "":
        return ""
    try:
        if '.' in str(clean):
            f = float(clean)
            return int(f) if f.is_integer() else f
        return int(clean)
    except ValueError:
        return clean

def convert_to_binary(val):
    if pd.isna(val) or val is None or val == "":
        return ""
    if val is True or val == 1:
        return 1
    val_str = str(val).strip().lower()
    if val_str in ('true', '1', '1.0', 'yes', 'y'):
        return 1
    return ""

def sanitize_column_value(col_name, val):
    if col_name in BINARY_COLS:
        return convert_to_binary(val)
    if col_name.startswith('description'):
        return sanitize_multi_line(val)
    if col_name in NUMERIC_COLS:
        return sanitize_numeric(val)
    return sanitize_single_line(val)

# ==========================================
# 1. DATA PROCESSING LOGIC
# ==========================================
def process_auction_data(app_dir, asset_dir):
    config_file = os.path.join(app_dir, 'config.txt')

    # Default Configuration
    config = {
        'SELLER_NUM': '159',
        'LOCATION': '166',
        'VAT_PERCENTAGE': '20',
        'FEE_VAT_PERCENTAGE': '2',
        'TARGET_LANGUAGE': 'en'
    }

    # Create config.txt if it doesn't exist
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            f.write("# Auction Automator Configuration\n")
            f.write("# You can change these values. Do not add spaces around the equals sign.\n")
            for key, value in config.items():
                f.write(f"{key}={value}\n")
    else:
        # Read existing config
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    SELLER_NUM = config.get('SELLER_NUM', '159')
    LOCATION = config.get('LOCATION', '166')
    VAT_PERCENTAGE = config.get('VAT_PERCENTAGE', '20')
    FEE_VAT_PERCENTAGE = config.get('FEE_VAT_PERCENTAGE', '2')
    TARGET_LANGUAGE = config.get('TARGET_LANGUAGE', 'en')

    # Find all .xlsx files in the directory
    all_xlsx = glob.glob(os.path.join(app_dir, '*.xlsx'))

    # Filter out the template and already generated files
    valid_dumps = [
        f for f in all_xlsx 
        if not os.path.basename(f).startswith('lot_import_') 
        and 'template' not in os.path.basename(f).lower()
        and not os.path.basename(f).startswith('~$')
    ]

    if len(valid_dumps) == 0:
        raise ValueError(f"Could not find any raw auction excel dump.\nPlease place your Excel file in this folder: {app_dir}\nMake sure it is an .xlsx file and NOT named 'lot_import_...'")
    elif len(valid_dumps) > 1:
        files = "\n".join([f" - {os.path.basename(f)}" for f in valid_dumps])
        raise ValueError(f"Found multiple possible raw auction files:\n{files}\n\nPlease keep ONLY ONE raw auction file in the folder.")

    SOURCE_FILE = valid_dumps[0]
    FILE_NAME = os.path.basename(SOURCE_FILE)

    base_name = os.path.splitext(FILE_NAME)[0].strip()
    OUTPUT_FILE = os.path.join(app_dir, f'lot_import_{base_name}.xlsx')

    try:
        # Load the source data
        df_dump = pd.read_excel(SOURCE_FILE, sheet_name='Lots')
    except Exception as e:
        raise ValueError(f"ERROR reading the Excel file: {e}")

    if df_dump.empty:
        raise ValueError("No data found in 'Lots' sheet.")

    # Clean column headers: strip whitespace and UTF-8 BOM
    df_dump.columns = [str(col).strip().lstrip('\ufeff') for col in df_dump.columns]

    template_cols = [
        'title_en', 'title_de', 'title_fr', 'title_nl', 'title_it', 'title_es', 'title_sv', 'title_pl', 
        'number', 'starting_bid', 'vat_percentage', 'fee_vat_percentage', 'description_en', 'description_de', 
        'description_fr', 'description_nl', 'description_it', 'description_es', 'description_sv', 'description_pl', 
        'estimated_price', 'reserve_bid', 'subcategory', 'location', 'seller', 'brand', 
        'needs_manual_allocation', 'is_spotlight', 'video', 'attribute-type', 'attribute-year', 
        'attribute-serial_number', 'attribute-amount', 'attribute-buy_amount'
    ]
    
    mapping = {
        "title": "Title",
        "description": "Description",
        "number": "Lotnumber",
        "starting_bid": "StartingBid",
        "estimated_price": "EstimatedPrice",
        "reserve_bid": "ReserveBid",
        "subcategory": "CategoryDomeId",
        "brand": "Brand",
        "attribute-type": "Type",
        "attribute-year": "Year",
        "attribute-serial_number": "SerialNumber",
        "attribute-amount": "Amount",
        "attribute-buy_amount": "BuyAmount",
        "needs_manual_allocation": "Allocation",
        "is_spotlight": "Spotlight"
    }
    
    langs = ['en', 'de', 'fr', 'nl', 'it', 'es', 'sv', 'pl']

    # Prefer schema.json next to the executable, fallback to bundled one
    schema_path = os.path.join(app_dir, 'schema.json')
    if not os.path.exists(schema_path):
        schema_path = os.path.join(asset_dir, 'schema.json')
        
    if os.path.exists(schema_path):
        try:
            import json
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                if 'template_cols' in schema:
                    template_cols = schema['template_cols']
                if 'mapping' in schema:
                    mapping = schema['mapping']
                if 'languages' in schema:
                    langs = schema['languages']
        except Exception:
            pass

    df_target = pd.DataFrame(index=df_dump.index)

    # Preset language titles/desc to blanks
    for l in langs:
        df_target[f'title_{l}'] = ""
        df_target[f'description_{l}'] = ""

    # Populate selected language columns
    title_src = mapping.get('title', 'Title')
    if title_src in df_dump.columns:
        df_target[f'title_{TARGET_LANGUAGE}'] = df_dump[title_src].apply(lambda v: sanitize_column_value(f'title_{TARGET_LANGUAGE}', v))
    else:
        df_target[f'title_{TARGET_LANGUAGE}'] = ""

    desc_src = mapping.get('description', 'Description')
    if desc_src in df_dump.columns:
        df_target[f'description_{TARGET_LANGUAGE}'] = df_dump[desc_src].apply(lambda v: sanitize_column_value(f'description_{TARGET_LANGUAGE}', v))
    else:
        df_target[f'description_{TARGET_LANGUAGE}'] = ""

    # Populate standard fields with universal sanitization and preserved types
    standard_fields = [
        'number', 'starting_bid', 'estimated_price', 'reserve_bid', 'subcategory', 'brand',
        'attribute-type', 'attribute-year', 'attribute-serial_number', 'attribute-amount', 'attribute-buy_amount'
    ]
    for field in standard_fields:
        src_col = mapping.get(field)
        if src_col and src_col in df_dump.columns:
            df_target[field] = df_dump[src_col].apply(lambda v, f=field: sanitize_column_value(f, v))
        else:
            df_target[field] = ""

    alloc_col = mapping.get('needs_manual_allocation', 'Allocation')
    if alloc_col in df_dump.columns:
        df_target['needs_manual_allocation'] = df_dump[alloc_col].apply(convert_to_binary)
    else:
        df_target['needs_manual_allocation'] = ""

    spot_col = mapping.get('is_spotlight', 'Spotlight')
    if spot_col in df_dump.columns:
        df_target['is_spotlight'] = df_dump[spot_col].apply(convert_to_binary)
    else:
        df_target['is_spotlight'] = ""

    # Config columns
    df_target['seller'] = sanitize_column_value('seller', SELLER_NUM)
    df_target['location'] = sanitize_column_value('location', LOCATION)
    df_target['vat_percentage'] = sanitize_column_value('vat_percentage', VAT_PERCENTAGE)
    df_target['fee_vat_percentage'] = sanitize_column_value('fee_vat_percentage', FEE_VAT_PERCENTAGE)
    df_target['video'] = ""

    # Map any additional keys from mapping not yet in df_target
    for out_key, src_key in mapping.items():
        if out_key in ('title', 'description'):
            continue
        if out_key not in df_target.columns:
            if src_key in df_dump.columns:
                df_target[out_key] = df_dump[src_key].apply(lambda v, k=out_key: sanitize_column_value(k, v))
            else:
                df_target[out_key] = ""

    # Reindex columns to match template, filling any inactive language or missing cols with empty strings
    df_target = df_target.reindex(columns=template_cols).fillna('')
    df_target.to_excel(OUTPUT_FILE, index=False)
    return OUTPUT_FILE

# ==========================================
# 2. GUI & ANIMATION LOGIC
# ==========================================
class AutomatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auction Automator")
        self.configure(bg="#FFF7ED") # Match website bg color
        
        # Make the window borderless
        self.overrideredirect(True)
        
        # Manually center the window on screen
        w, h = 600, 300
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.canvas = tk.Canvas(self, width=600, height=200, bg="#FFF7ED", highlightthickness=0)
        self.canvas.pack(pady=20)
        
        self.label = tk.Label(self, text="Eating files...", font=("Courier", 14, "bold"), bg="#FFF7ED", fg="#292524")
        self.label.pack()

        # Load Tom's head images (open and closed mouth)
        import sys
        if getattr(sys, 'frozen', False):
            # Running as bundled executable
            app_dir = os.path.dirname(sys.executable)
            asset_dir = sys._MEIPASS
        else:
            # Running as standard script
            app_dir = os.path.dirname(os.path.abspath(__file__))
            asset_dir = app_dir
            
        self.app_dir = app_dir
        self.asset_dir = asset_dir
        
        def load_img(filename):
            path = os.path.join(asset_dir, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img = img.resize((128, 128), Image.Resampling.LANCZOS)
                    
                    # Create a solid warm cream background matching "#FFF7ED" exactly (R=255, G=247, B=237)
                    bg = Image.new("RGBA", img.size, (255, 247, 237, 255))
                    # Composite transparent portrait over the solid background to bypass any Tkinter transparency bugs
                    img = Image.alpha_composite(bg, img.convert("RGBA"))
                    
                    return ImageTk.PhotoImage(img)
                except Exception:
                    pass
            return tk.PhotoImage(width=128, height=128)

        self.tom_img_open = load_img("tom_open.png")
        self.tom_img_closed = load_img("tom_closed.png")
        self.tom_img_relief = load_img("tom_relief.png")
        self.is_mouth_open = True
        self.frame_count = 0

        # File graphics
        self.file_color_dump = "#00BBA7"    # Teal for raw dump
        self.file_color_template = "#6B7280" # Gray for template
        
        # Easing and timing configuration matching website perfectly
        self.start_time = time.time()
        self.duration = 9.0 # Exactly 9 seconds
        self.start_x = -100
        self.final_x = 700
        self.tom_x = self.start_x
        self.tom_y = 100
        
        # Draw track
        self.canvas.create_line(0, 132, 600, 132, fill="gray", width=2, dash=(4, 4))
        
        # Draw 2 raw files to be eaten (Template and Dump)
        self.file1_id = self.draw_file(250, 100, self.file_color_template)
        self.file2_id = self.draw_file(350, 100, self.file_color_dump)
        
        self.tom_id = self.canvas.create_image(self.tom_x, self.tom_y, image=self.tom_img_open)
        self.processed_file_id = None
        
        # Speech bubble vector items (hidden initially)
        self.bubble_pointer = self.canvas.create_polygon([0,0, 0,0, 0,0], fill="#FEF08A", outline="#1C1917", width=2, state=tk.HIDDEN)
        self.bubble_rect = self.canvas.create_polygon([0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0], fill="#FEF08A", outline="#1C1917", width=2, state=tk.HIDDEN)
        self.bubble_text = self.canvas.create_text(0, 0, text="NUM NUM!", font=("Arial", 11, "bold"), fill="#1C1917", state=tk.HIDDEN)
        
        self.script_dir = app_dir
        self.processing_done = False
        self.output_file = None
        self.error_msg = None
        
        # Start animation
        self.after(40, self.animate)

    def draw_file(self, x, y, color):
        # Draw a little document icon
        poly = [x-15, y-20, x+10, y-20, x+15, y-15, x+15, y+20, x-15, y+20]
        return self.canvas.create_polygon(poly, fill=color, outline="#292524", width=2)

    def update_speech_bubble(self, show=True, text="NUM NUM!", bg="#FEF08A", fg="#1C1917", border="#1C1917"):
        if not show:
            self.canvas.itemconfig(self.bubble_rect, state=tk.HIDDEN)
            self.canvas.itemconfig(self.bubble_pointer, state=tk.HIDDEN)
            self.canvas.itemconfig(self.bubble_text, state=tk.HIDDEN)
            return
        
        x, y = self.tom_x, self.tom_y
        
        # Update text
        self.canvas.itemconfig(self.bubble_text, text=text, fill=fg, state=tk.NORMAL)
        
        # Get half width based on text length
        half_w = max(40, len(text) * 4.5 + 10)
        
        # Bubble box coordinates adjusted perfectly for larger 128px Tom
        box_pts = [
            x - half_w, y - 104,
            x + half_w, y - 104,
            x + half_w, y - 74,
            x - half_w, y - 74
        ]
        
        # Pointer coordinates pointing down to Tom's head top at y-64
        pointer_pts = [
            x - 12, y - 74,
            x - 2, y - 74,
            x - 7, y - 64
        ]
        
        self.canvas.coords(self.bubble_rect, *box_pts)
        self.canvas.coords(self.bubble_pointer, *pointer_pts)
        self.canvas.coords(self.bubble_text, x, y - 89)
        
        self.canvas.itemconfig(self.bubble_rect, fill=bg, outline=border, state=tk.NORMAL)
        self.canvas.itemconfig(self.bubble_pointer, fill=bg, outline=border, state=tk.NORMAL)
        
        # Lift speech bubble above files & mascot
        self.canvas.tag_raise(self.bubble_rect)
        self.canvas.tag_raise(self.bubble_pointer)
        self.canvas.tag_raise(self.bubble_text)

    def animate(self):
        # Calculate time-based cubic ease-in-out progress matching the web landing page perfectly
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Cubic ease-in-out formula
        if progress < 0.5:
            eased = 4 * progress * progress * progress
        else:
            eased = 1 - (-2 * progress + 2)**3 / 2
            
        self.tom_x = self.start_x + (self.final_x - self.start_x) * eased
        
        # Chomp animation and speech bubble logic
        self.frame_count += 1
        if self.processing_done and not self.error_msg and self.tom_x > 450:
            self.canvas.itemconfig(self.tom_id, image=self.tom_img_relief)
            self.update_speech_bubble(True, "YAM!", "#10B981", "#FFFFFF", "#064E3B")
        elif self.tom_x > 120 and self.tom_x <= 450:
            if self.frame_count % 4 == 0:
                self.is_mouth_open = not self.is_mouth_open
            new_img = self.tom_img_open if self.is_mouth_open else self.tom_img_closed
            self.canvas.itemconfig(self.tom_id, image=new_img)
            self.update_speech_bubble(True, "NUM NUM!", "#FEF08A", "#1C1917", "#1C1917")
        else:
            if self.frame_count % 4 == 0:
                self.is_mouth_open = not self.is_mouth_open
            new_img = self.tom_img_open if self.is_mouth_open else self.tom_img_closed
            self.canvas.itemconfig(self.tom_id, image=new_img)
            self.update_speech_bubble(False)
            
        self.canvas.coords(self.tom_id, self.tom_x, self.tom_y)
        
        # Eat file 1 (Template) when Tom's front-edge reaches X=250
        if self.tom_x > 186 and self.file1_id:
            self.canvas.delete(self.file1_id)
            self.file1_id = None
            
        # Eat file 2 (Data Dump) when Tom's front-edge reaches X=350 and trigger processing
        if self.tom_x > 286 and self.file2_id:
            self.canvas.delete(self.file2_id)
            self.file2_id = None
            self.label.config(text="Processing...")
            
            # Run data processing in background so GUI stays smooth
            def run_processing():
                try:
                    self.output_file = process_auction_data(self.app_dir, self.asset_dir)
                except Exception as e:
                    self.error_msg = str(e)
                finally:
                    self.processing_done = True
                    
            thread = threading.Thread(target=run_processing, daemon=True)
            thread.start()
                
        # Poop output file
        if self.processing_done and not self.error_msg and self.tom_x > 450 and not self.processed_file_id:
            # Drop file behind him
            self.processed_file_id = self.draw_file(400, 100, "#F59E0B") # Gold color for output
            self.label.config(text="Success! File formatted.")
            
        if elapsed < self.duration:
            self.after(40, self.animate)
        else:
            # Ensure Tom finishes off-screen
            self.tom_x = self.final_x
            self.canvas.coords(self.tom_id, self.tom_x, self.tom_y)
            
            # Tom has walked off screen — now handle result
            if self.error_msg:
                messagebox.showerror("Error", self.error_msg)
                self.destroy()
            elif self.processing_done:
                self.label.config(text="Done! You can close this window.")
                btn = tk.Button(self, text="Close", command=self.destroy, font=("Courier", 12), bg=self.file_color_dump, fg="white", relief=tk.FLAT, padx=20, pady=5)
                btn.pack(pady=10)
            else:
                # Processing still running, wait a little longer
                self.after(100, self.finish_check)

    def finish_check(self):
        """Wait for background processing to complete after animation ends."""
        if self.processing_done:
            if self.error_msg:
                messagebox.showerror("Error", self.error_msg)
                self.destroy()
            else:
                self.label.config(text="Done! You can close this window.")
                btn = tk.Button(self, text="Close", command=self.destroy, font=("Courier", 12), bg=self.file_color_dump, fg="white", relief=tk.FLAT, padx=20, pady=5)
                btn.pack(pady=10)
        else:
            self.after(100, self.finish_check)

if __name__ == "__main__":
    app = AutomatorApp()
    app.mainloop()