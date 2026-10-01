import os
import shutil
import tempfile
import pandas as pd
import numpy as np
import openpyxl

from auction_automator import (
    sanitize_multi_line,
    sanitize_single_line,
    sanitize_numeric,
    convert_to_binary,
    sanitize_column_value,
    process_auction_data
)

def test_multi_line_sanitization():
    print("Testing multi-line sanitization...")
    # Clean \n preserved
    assert sanitize_multi_line("Line 1\nLine 2") == "Line 1\nLine 2"
    # CRLF -> \n
    assert sanitize_multi_line("Line 1\r\nLine 2") == "Line 1\nLine 2"
    # Isolated \r -> \n
    assert sanitize_multi_line("Line 1\rLine 2") == "Line 1\nLine 2"
    # OpenXML hex entity _x000D_
    assert sanitize_multi_line("Line 1_x000D_\nLine 2") == "Line 1\nLine 2"
    assert sanitize_multi_line("Line 1_x000d_Line 2") == "Line 1\nLine 2"
    assert sanitize_multi_line("Line 1_x000d_\r\nLine 2") == "Line 1\nLine 2"
    # Double-escaped OpenXML hex entity _x005F_x000D_
    assert sanitize_multi_line("Line 1_x005F_x000D_\nLine 2") == "Line 1\nLine 2"
    assert sanitize_multi_line("Line 1_x005F_x000D_Line 2") == "Line 1\nLine 2"
    # Part numbers and text with _xXXXX_ must NEVER be corrupted
    assert sanitize_multi_line("BATTERY_x2000_MAX") == "BATTERY_x2000_MAX"
    assert sanitize_multi_line("MODEL_x1234_ABC") == "MODEL_x1234_ABC"
    # Unicode line separators \u2028, \u2029 -> \n
    assert sanitize_multi_line("Line 1\u2028Line 2\u2029Line 3") == "Line 1\nLine 2\nLine 3"
    # Unicode spaces -> ' '
    assert sanitize_multi_line("Word 1\u00A0Word 2\u2003Word 3") == "Word 1 Word 2 Word 3"
    # Zero-width chars stripped
    assert sanitize_multi_line("Zero\u200BWidth\uFEFFBOM\u200DJoiner") == "ZeroWidthBOMJoiner"
    # Invisible control chars stripped (preserve \n)
    assert sanitize_multi_line("Clean\x00Text\x07With\x1FLines\nLine 2") == "CleanTextWithLines\nLine 2"
    # Cap at 32,767
    long_str = "a" * 40000
    res = sanitize_multi_line(long_str)
    assert len(res) == 32767
    print("[OK] Multi-line sanitization passed!")

def test_single_line_sanitization():
    print("Testing single-line sanitization...")
    # Internal newlines collapsed to spaces
    assert sanitize_single_line("Title Line 1\r\nTitle Line 2") == "Title Line 1 Title Line 2"
    assert sanitize_single_line("Title Line 1\nTitle Line 2") == "Title Line 1 Title Line 2"
    assert sanitize_single_line("Title Line 1\rTitle Line 2") == "Title Line 1 Title Line 2"
    assert sanitize_single_line("Title\u2028Line 2\u2029Line 3") == "Title Line 2 Line 3"
    # OpenXML hex entities
    assert sanitize_single_line("Brand_x000D_\nName") == "Brand Name"
    assert sanitize_single_line("Brand_x005F_x000D_Name") == "Brand Name"
    assert sanitize_single_line("Brand_x005F_REV1") == "Brand_REV1"
    # Part numbers, model codes, serial numbers with _xXXXX_ must NEVER be corrupted
    assert sanitize_single_line("BATTERY_x2000_MAX") == "BATTERY_x2000_MAX"
    assert sanitize_single_line("MODEL_x1234_ABC") == "MODEL_x1234_ABC"
    assert sanitize_single_line("SN_x0041_123") == "SN_x0041_123"
    # Multiple spaces collapsed & trimmed
    assert sanitize_single_line("   Brand   with    spaces   ") == "Brand with spaces"
    # Numbers preserved
    assert sanitize_single_line(0) == 0
    assert sanitize_single_line(42) == 42
    assert sanitize_single_line(150.5) == 150.5
    # Strings with leading zeros preserved
    assert sanitize_single_line("007") == "007"
    # Cap at 32,767
    long_str = "b" * 40000
    res = sanitize_single_line(long_str)
    assert len(res) == 32767
    print("[OK] Single-line sanitization passed!")

def test_numeric_sanitization():
    print("Testing numeric sanitization...")
    # Numeric 0 preserved
    assert sanitize_numeric(0) == 0
    assert type(sanitize_numeric(0)) is int
    # Float preserved
    assert sanitize_numeric(150.5) == 150.5
    assert type(sanitize_numeric(150.5)) is float
    # Float integer converted to int
    assert sanitize_numeric(150.0) == 150
    assert type(sanitize_numeric(150.0)) is int
    # Numeric strings converted to numbers
    assert sanitize_numeric("0") == 0
    assert type(sanitize_numeric("0")) is int
    assert sanitize_numeric(" 150.5 ") == 150.5
    assert type(sanitize_numeric(" 150.5 ")) is float
    # Booleans are not numeric bids/prices
    assert sanitize_numeric(True) == ""
    assert sanitize_numeric(False) == ""
    # Empty / None / NaN
    assert sanitize_numeric("") == ""
    assert sanitize_numeric(None) == ""
    assert sanitize_numeric(np.nan) == ""
    # Non-numeric string returned as string
    assert sanitize_numeric("N/A") == "N/A"
    print("[OK] Numeric sanitization passed!")

def test_binary_conversion():
    print("Testing binary conversion...")
    assert convert_to_binary(1) == 1
    assert convert_to_binary('1') == 1
    assert convert_to_binary('1.0') == 1
    assert convert_to_binary(1.0) == 1
    assert convert_to_binary(True) == 1
    assert convert_to_binary('true') == 1
    assert convert_to_binary('True') == 1
    assert convert_to_binary('yes') == 1
    assert convert_to_binary('y') == 1

    assert convert_to_binary(0) == ""
    assert convert_to_binary('0') == ""
    assert convert_to_binary(False) == ""
    assert convert_to_binary('false') == ""
    assert convert_to_binary('no') == ""
    assert convert_to_binary(None) == ""
    assert convert_to_binary(np.nan) == ""
    assert convert_to_binary("") == ""
    print("[OK] Binary conversion passed!")

def test_end_to_end_auction_data():
    print("Testing End-to-End Excel generation with messy data...")
    temp_dir = tempfile.mkdtemp()
    try:
        # Create a raw Excel file with lots of edge cases:
        # 1. BOM in header: '\ufeffTitle'
        # 2. Whitespace in header: ' StartingBid '
        # 3. Row 1: starting_bid = 0 (numeric 0 must be preserved!), reserve_bid = 0
        # 4. Row 2: starting_bid = 150.5, reserve_bid = 300
        # 5. Row 3: starting_bid as string ' 250.75 ', Allocation as string '1', Spotlight as True
        # 6. Description with _x005F_x000D_, CRLF, \u2028, non-breaking spaces
        # 7. Title with newlines
        # 8. SerialNumber with leading zeroes '00042'
        
        raw_data = {
            ' \ufeff Title ': [
                'Item 1 with\r\nNewline in Title',
                'Item 2_x000D_\nWith CR',
                'Item 3\u2028With LineSep',
                None
            ],
            'Description': [
                'Line 1_x005F_x000D_\nLine 2\r\nLine 3\u00A0nonbreak',
                'Desc with clean \n newline\r\nand CRLF',
                'Desc 3\u200Bwith zero width',
                None
            ],
            'Lotnumber': [1, 2, '3A', None],
            ' StartingBid ': [0, 150.5, ' 250.75 ', None],
            'EstimatedPrice': [100, 200, 300, None],
            'ReserveBid': [0, 120.0, 250, None],
            'CategoryDomeId': [10, 20, 30, None],
            'Brand': ['Cat\r\nEquipment', 'BATTERY_x2000_MAX', 'Scania\u00A0Co', None],
            'Type': ['Excavator\nType', 'Truck', 'Loader', None],
            'Year': [2020, 2021, 2022, None],
            'SerialNumber': ['SN-0001', 'SN-0002', 'SN-0003', None],
            'Amount': [1, 2, 3, None],
            'BuyAmount': [1, 2, 3, None],
            'Allocation': ['1', '0', True, None],
            'Spotlight': [True, 'true', '1', None]
        }
        raw_df = pd.DataFrame(raw_data)
        input_file = os.path.join(temp_dir, 'raw_dump.xlsx')
        with pd.ExcelWriter(input_file, engine='openpyxl') as writer:
            raw_df.to_excel(writer, sheet_name='Lots', index=False)
            
        # Also copy schema.json into temp_dir
        repo_dir = os.path.abspath(os.path.dirname(__file__))
        shutil.copy(os.path.join(repo_dir, 'schema.json'), os.path.join(temp_dir, 'schema.json'))
        
        output_file = process_auction_data(temp_dir, temp_dir)
        assert os.path.exists(output_file), "Output file was not created!"
        
        # Read with openpyxl to verify exact data types and cell values
        wb = openpyxl.load_workbook(output_file)
        ws = wb.active
        
        # Verify only 3 data rows created (trailing empty row dropped!)
        data_rows = list(ws.iter_rows(min_row=2, values_only=True))
        assert len(data_rows) == 3, f"Expected 3 rows, got {len(data_rows)}"

        headers = [cell.value for cell in ws[1]]
        # Verify template column order
        import json
        with open(os.path.join(repo_dir, 'schema.json'), 'r') as f:
            expected_cols = json.load(f)['template_cols']
        assert headers == expected_cols, f"Headers mismatch: {headers} vs {expected_cols}"
        
        col_idx = {h: i for i, h in enumerate(headers)}
        
        # Row 1 (ws row 2):
        row1_vals = [cell.value for cell in ws[2]]
        
        # Title must have newlines collapsed to spaces
        assert row1_vals[col_idx['title_en']] == 'Item 1 with Newline in Title', f"Title got: {row1_vals[col_idx['title_en']]}"
        # Inactive languages must be empty string
        assert row1_vals[col_idx['title_de']] == '' or row1_vals[col_idx['title_de']] is None
        assert row1_vals[col_idx['description_fr']] == '' or row1_vals[col_idx['description_fr']] is None
        
        # Description must preserve clean \n and eliminate _x005F_x000D_ and normalize spaces
        desc1 = row1_vals[col_idx['description_en']]
        assert '_x005F_' not in desc1 and '_x000D_' not in desc1 and '\r' not in desc1
        assert desc1 == 'Line 1\nLine 2\nLine 3 nonbreak', f"Desc got: {repr(desc1)}"
        
        # StartingBid 0 MUST BE PRESERVED AS NUMERIC 0
        sb1 = row1_vals[col_idx['starting_bid']]
        assert sb1 == 0 and type(sb1) is int, f"starting_bid 0 got: {sb1} ({type(sb1)})"
        
        # ReserveBid 0 MUST BE PRESERVED AS NUMERIC 0
        rb1 = row1_vals[col_idx['reserve_bid']]
        assert rb1 == 0 and type(rb1) is int, f"reserve_bid 0 got: {rb1} ({type(rb1)})"
        
        # Allocation '1' MUST BE NUMERIC 1
        alloc1 = row1_vals[col_idx['needs_manual_allocation']]
        assert alloc1 == 1, f"Allocation '1' got: {alloc1} ({type(alloc1)})"
        
        # SerialNumber 'SN-0001' MUST PRESERVE STRING
        sn1 = str(row1_vals[col_idx['attribute-serial_number']])
        assert sn1 == 'SN-0001', f"SerialNumber got: {sn1}"
        
        # Brand must have newlines collapsed
        b1 = row1_vals[col_idx['brand']]
        assert b1 == 'Cat Equipment', f"Brand got: {b1}"
        
        # Row 2 (ws row 3):
        row2_vals = [cell.value for cell in ws[3]]
        sb2 = row2_vals[col_idx['starting_bid']]
        assert sb2 == 150.5 and type(sb2) is float, f"starting_bid 150.5 got: {sb2} ({type(sb2)})"
        b2 = row2_vals[col_idx['brand']]
        assert b2 == 'BATTERY_x2000_MAX', f"Brand BATTERY got corrupted: {b2}"
        
        # Row 3 (ws row 4): string ' 250.75 ' converted to numeric 250.75
        row3_vals = [cell.value for cell in ws[4]]
        sb3 = row3_vals[col_idx['starting_bid']]
        assert sb3 == 250.75 and type(sb3) is float, f"starting_bid string got: {sb3} ({type(sb3)})"
        
        print("[OK] End-to-End Excel generation passed perfectly!")
    finally:
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    test_multi_line_sanitization()
    test_single_line_sanitization()
    test_numeric_sanitization()
    test_binary_conversion()
    test_end_to_end_auction_data()
    print("\nALL PYTHON TESTS PASSED SUCCESSFULLY!")
