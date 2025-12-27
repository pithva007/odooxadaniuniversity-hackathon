import pandas as pd

FILE_PATH = "Stock2.xlsx"  # Your file

try:
    # 1. Load the Excel File
    xls = pd.ExcelFile(FILE_PATH)
    
    print(f"📄 This Excel file has {len(xls.sheet_names)} sheet(s):")
    print(f"   👉 {xls.sheet_names}\n")

    # 2. Loop through every sheet to see what's inside
    for sheet in xls.sheet_names:
        print(f"--- 🔎 INSPECTING SHEET: '{sheet}' ---")
        df = pd.read_excel(FILE_PATH, sheet_name=sheet)
        
        # Print the first 5 rows so we can see the headers
        print(df.head(10)) 
        print("\n" + "="*50 + "\n")

except Exception as e:
    print(f"❌ Error: {e}")