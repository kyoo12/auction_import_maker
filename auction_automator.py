import os
import glob
import threading
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ==========================================
# 1. DATA PROCESSING LOGIC
# ==========================================
def process_auction_data(script_dir):
    config_file = os.path.join(script_dir, 'config.txt')

    # Default Configuration
    config = {
        'SELLER_NUM': '159',
        'LOCATION': '166',
        'VAT_PERCENTAGE': '20',
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
    TARGET_LANGUAGE = config.get('TARGET_LANGUAGE', 'en')

    # Find all .xlsx files in the directory
    all_xlsx = glob.glob(os.path.join(script_dir, '*.xlsx'))

    # Filter out the template and already generated files
    valid_dumps = [
        f for f in all_xlsx 
        if not os.path.basename(f).startswith('lot_import_') 
        and 'template' not in os.path.basename(f).lower()
        and not os.path.basename(f).startswith('~$')
    ]

    if len(valid_dumps) == 0:
        raise ValueError(f"Could not find any raw auction excel dump.\nPlease place your Excel file in this folder: {script_dir}\nMake sure it is an .xlsx file and NOT named 'lot_import_...'")
    elif len(valid_dumps) > 1:
        files = "\n".join([f" - {os.path.basename(f)}" for f in valid_dumps])
        raise ValueError(f"Found multiple possible raw auction files:\n{files}\n\nPlease keep ONLY ONE raw auction file in the folder.")

    SOURCE_FILE = valid_dumps[0]
    FILE_NAME = os.path.basename(SOURCE_FILE)

    base_name = os.path.splitext(FILE_NAME)[0].strip()
    OUTPUT_FILE = os.path.join(script_dir, f'lot_import_{base_name}.xlsx')

    try:
        # Load the source data
        df_dump = pd.read_excel(SOURCE_FILE, sheet_name='Lots')
    except Exception as e:
        raise ValueError(f"ERROR reading the Excel file: {e}")

    df_target = pd.DataFrame()
    df_target[f'title_{TARGET_LANGUAGE}'] = df_dump['Title']
    df_target[f'description_{TARGET_LANGUAGE}'] = df_dump['Description']
    df_target['number'] = df_dump['Lotnumber']
    df_target['starting_bid'] = df_dump['StartingBid']
    df_target['estimated_price'] = df_dump['EstimatedPrice']
    df_target['reserve_bid'] = df_dump['ReserveBid']
    df_target['subcategory'] = df_dump['CategoryDomeId']
    df_target['brand'] = df_dump['Brand']
    df_target['attribute-type'] = df_dump['Type']
    df_target['attribute-year'] = df_dump['Year']
    df_target['attribute-serial_number'] = df_dump['SerialNumber']
    df_target['attribute-amount'] = df_dump['Amount']
    df_target['attribute-buy_amount'] = df_dump['BuyAmount']
    df_target['seller'] = SELLER_NUM
    df_target['location'] = LOCATION
    df_target['vat_percentage'] = VAT_PERCENTAGE
    df_target['video'] = "" 

    def convert_to_binary(val):
        if val == True or str(val).strip().lower() == 'true':
            return 1
        return ""

    if 'Allocation' in df_dump.columns:
        df_target['needs_manual_allocation'] = df_dump['Allocation'].apply(convert_to_binary)
    if 'Spotlight' in df_dump.columns:
        df_target['is_spotlight'] = df_dump['Spotlight'].apply(convert_to_binary)

    template_cols = [
        'title_en', 'title_de', 'title_fr', 'title_nl', 'title_it', 'title_es', 'title_sv', 
        'number', 'starting_bid', 'vat_percentage', 'description_en', 'description_de', 
        'description_fr', 'description_nl', 'description_it', 'description_es', 'description_sv', 
        'estimated_price', 'reserve_bid', 'subcategory', 'location', 'seller', 'brand', 
        'needs_manual_allocation', 'is_spotlight', 'video', 'attribute-type', 'attribute-year', 
        'attribute-serial_number', 'attribute-amount', 'attribute-buy_amount'
    ]

    df_target = df_target.reindex(columns=template_cols)
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
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        def load_img(filename):
            path = os.path.join(script_dir, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception:
                    pass
            return tk.PhotoImage(width=64, height=64)

        self.tom_img_open = load_img("tom_open.png")
        self.tom_img_closed = load_img("tom_closed.png")
        self.tom_img_relief = load_img("tom_relief.png")
        self.is_mouth_open = True
        self.frame_count = 0

        # File graphics
        self.file_color_dump = "#00BBA7"    # Teal for raw dump
        self.file_color_template = "#6B7280" # Gray for template
        
        self.tom_x = -50
        self.tom_y = 100
        
        # Draw track
        self.canvas.create_line(0, 132, 600, 132, fill="gray", width=2, dash=(4, 4))
        
        # Draw 2 raw files to be eaten (Template and Dump)
        self.file1_id = self.draw_file(250, 100, self.file_color_template)
        self.file2_id = self.draw_file(350, 100, self.file_color_dump)
        
        self.tom_id = self.canvas.create_image(self.tom_x, self.tom_y, image=self.tom_img_open)
        self.processed_file_id = None
        
        self.script_dir = script_dir
        self.processing_done = False
        self.output_file = None
        self.error_msg = None
        
        # Start animation
        self.after(40, self.animate)

    def draw_file(self, x, y, color):
        # Draw a little document icon
        poly = [x-15, y-20, x+10, y-20, x+15, y-15, x+15, y+20, x-15, y+20]
        return self.canvas.create_polygon(poly, fill=color, outline="#292524", width=2)
        
    def animate(self):
        # Move Tom right (4 pixels per 40ms = ~7.5 seconds to cross 750 pixels)
        self.tom_x += 4
        
        # Chomp animation (toggle every 8 frames)
        self.frame_count += 1
        if self.processing_done and not self.error_msg and self.tom_x > 450:
            self.canvas.itemconfig(self.tom_id, image=self.tom_img_relief)
        elif self.frame_count % 4 == 0:
            self.is_mouth_open = not self.is_mouth_open
            new_img = self.tom_img_open if self.is_mouth_open else self.tom_img_closed
            self.canvas.itemconfig(self.tom_id, image=new_img)
            
        self.canvas.coords(self.tom_id, self.tom_x, self.tom_y)
        
        # Eat file 1 (Template)
        if self.tom_x > 250 and self.file1_id:
            self.canvas.delete(self.file1_id)
            self.file1_id = None
            
        # Eat file 2 (Data Dump) and trigger processing
        if self.tom_x > 350 and self.file2_id:
            self.canvas.delete(self.file2_id)
            self.file2_id = None
            self.label.config(text="Processing...")
            
            # Run data processing in background so GUI stays smooth
            def run_processing():
                try:
                    self.output_file = process_auction_data(self.script_dir)
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
            
        if self.tom_x < 700:
            self.after(40, self.animate)
        else:
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