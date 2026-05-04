import os
import glob
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURATION LOADING
# ==========================================

script_dir = os.path.dirname(os.path.abspath(__file__))
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
    print("Creating default config.txt...")
    with open(config_file, 'w') as f:
        f.write("# Auction Automator Configuration\n")
        f.write("# You can change these values. Do not add spaces around the equals sign.\n")
        for key, value in config.items():
            f.write(f"{key}={value}\n")
else:
    # Read existing config
    print("Loading settings from config.txt...")
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


# ==========================================
# 2. DYNAMIC FILE DETECTION
# ==========================================

# Find all .xlsx files in the directory
all_xlsx = glob.glob(os.path.join(script_dir, '*.xlsx'))

# Filter out the template and already generated files
valid_dumps = [
    f for f in all_xlsx 
    if not os.path.basename(f).startswith('lot_import_') 
    and 'template' not in os.path.basename(f).lower()
    and not os.path.basename(f).startswith('~$') # Ignore open Excel temp files
]

if len(valid_dumps) == 0:
    print("\nERROR: Could not find any raw auction excel dump.")
    print(f"Please place your Excel file in this folder: {script_dir}")
    print("Make sure it is an .xlsx file and NOT named 'lot_import_...'")
    input("\nPress Enter to exit...")
    exit()
elif len(valid_dumps) > 1:
    print("\nERROR: Found multiple possible raw auction files:")
    for f in valid_dumps:
        print(f" - {os.path.basename(f)}")
    print("\nPlease keep ONLY ONE raw auction file in the folder so I know which one to process.")
    input("\nPress Enter to exit...")
    exit()

SOURCE_FILE = valid_dumps[0]
FILE_NAME = os.path.basename(SOURCE_FILE)

# Automatically generate the output file name in the same folder
base_name = os.path.splitext(FILE_NAME)[0].strip()
OUTPUT_FILE = os.path.join(script_dir, f'lot_import_{base_name}.xlsx')


# ==========================================
# 3. THE AUTOMATION ENGINE
# ==========================================

print(f"Processing data from: {FILE_NAME}...")

try:
    # Load the source data
    df_dump = pd.read_excel(SOURCE_FILE, sheet_name='Lots')
except Exception as e:
    print(f"\nERROR reading the Excel file: {e}")
    input("\nPress Enter to exit...")
    exit()

# Create a fresh, empty dataframe for our target data
df_target = pd.DataFrame()

# --- Dynamic Language Mapping ---
df_target[f'title_{TARGET_LANGUAGE}'] = df_dump['Title']
df_target[f'description_{TARGET_LANGUAGE}'] = df_dump['Description']

# --- Direct Mappings ---
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

# --- Custom Insertions ---
df_target['seller'] = SELLER_NUM
df_target['location'] = LOCATION
df_target['vat_percentage'] = VAT_PERCENTAGE
df_target['video'] = "" # Always left empty

# --- Boolean Handling (True = 1, False/Empty = Blank) ---
def convert_to_binary(val):
    if val == True or str(val).strip().lower() == 'true':
        return 1
    return ""

if 'Allocation' in df_dump.columns:
    df_target['needs_manual_allocation'] = df_dump['Allocation'].apply(convert_to_binary)
if 'Spotlight' in df_dump.columns:
    df_target['is_spotlight'] = df_dump['Spotlight'].apply(convert_to_binary)

# --- Final Template Formatting ---
template_cols = [
    'title_en', 'title_de', 'title_fr', 'title_nl', 'title_it', 'title_es', 'title_sv', 
    'number', 'starting_bid', 'vat_percentage', 'description_en', 'description_de', 
    'description_fr', 'description_nl', 'description_it', 'description_es', 'description_sv', 
    'estimated_price', 'reserve_bid', 'subcategory', 'location', 'seller', 'brand', 
    'needs_manual_allocation', 'is_spotlight', 'video', 'attribute-type', 'attribute-year', 
    'attribute-serial_number', 'attribute-amount', 'attribute-buy_amount'
]

# Force the dataframe into the exact template structure
df_target = df_target.reindex(columns=template_cols)

# Save the final file
df_target.to_excel(OUTPUT_FILE, index=False)
print(f"Success! Your file has been generated and saved to: {OUTPUT_FILE}")