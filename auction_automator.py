import os
import pandas as pd
import numpy as np

#pip install -r requirements.txt

# ==========================================
# 1. CONFIGURATION (Change these per auction!)
# ==========================================
SELLER_NUM = "159"          # Your specific seller number
LOCATION = "166"           # The location of the items
VAT_PERCENTAGE = 20        # The VAT percentage

# Language Options: 'en', 'de', 'fr', 'nl', 'it', 'es', 'sv'
TARGET_LANGUAGE = "en"         

# The file you got from the auction (Updated to match your screenshot)
FILE_NAME = 'Wollsdorf_Leder .xlsx'


# ==========================================
# 2. DO NOT TOUCH - THE AUTOMATION ENGINE
# ==========================================

# --- NEW: Tell Python to look in the script's current folder ---
script_dir = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(script_dir, FILE_NAME)

# Automatically generate the output file name in the same folder
base_name = os.path.splitext(FILE_NAME)[0].strip()
OUTPUT_FILE = os.path.join(script_dir, f'lot_import_{base_name}.xlsx')

print(f"Loading data from {SOURCE_FILE}...")

try:
    # Load the source data
    df_dump = pd.read_excel(SOURCE_FILE, sheet_name='Lots')
except FileNotFoundError:
    print(f"\nERROR: Could not find the file '{FILE_NAME}'.")
    print(f"I am looking for it right here: {SOURCE_FILE}")
    print("Make sure the Excel file is in that exact folder and the name matches perfectly!\n")
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