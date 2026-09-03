# modules/medicine_inventory.py
import os
import pandas as pd
from datetime import datetime, date

MEDICINE_FILE = "medicine.txt"


def load_medicine_inventory():
    """Loads the medicine inventory from medicine.txt, creating the file with default columns if it doesn't exist."""
    if os.path.exists(MEDICINE_FILE):
        try:
            df = pd.read_csv(MEDICINE_FILE, sep="|")
            df = df.fillna("")
            expected_cols = ["Med_ID", "Medication_Name", "Category", "Stock_Quantity", "Unit_Price", "Expiry_Date",
                             "Last_Updated", "Batch_Number"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass

    # Default initial inventory dataset for Cuticare Clinic with Batch Numbers
    default_data = [
        {
            "Med_ID": "MED-1001",
            "Medication_Name": "Clobetasol Propionate 0.05% Ointment",
            "Category": "Topical Corticosteroid",
            "Stock_Quantity": 150,
            "Unit_Price": "₹250",
            "Expiry_Date": "2027-12-31",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-CLO-01"
        },
        {
            "Med_ID": "MED-1002",
            "Medication_Name": "Tacrolimus 0.1% Topical Cream",
            "Category": "Immunomodulator",
            "Stock_Quantity": 80,
            "Unit_Price": "₹450",
            "Expiry_Date": "2027-06-30",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-TAC-02"
        },
        {
            "Med_ID": "MED-1003",
            "Medication_Name": "Cetirizine 10mg Tablets",
            "Category": "Antihistamine",
            "Stock_Quantity": 500,
            "Unit_Price": "₹40",
            "Expiry_Date": "2028-03-15",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-CET-03"
        },
        {
            "Med_ID": "MED-1004",
            "Medication_Name": "Ketoconazole 2% Antifungal Shampoo",
            "Category": "Antifungal",
            "Stock_Quantity": 120,
            "Unit_Price": "₹320",
            "Expiry_Date": "2027-09-10",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-KET-04"
        },
        {
            "Med_ID": "MED-1005",
            "Medication_Name": "Isotretinoin 20mg Capsules",
            "Category": "Retinoid",
            "Stock_Quantity": 200,
            "Unit_Price": "₹650",
            "Expiry_Date": "2028-01-20",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-ISO-05"
        },
        {
            "Med_ID": "MED-1006",
            "Medication_Name": "Clindamycin 1% Topical Gel",
            "Category": "Antibiotic",
            "Stock_Quantity": 95,
            "Unit_Price": "₹180",
            "Expiry_Date": "2027-11-05",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-CLI-06"
        },
        {
            "Med_ID": "MED-1007",
            "Medication_Name": "Mupirocin 2% Ointment",
            "Category": "Antibiotic",
            "Stock_Quantity": 110,
            "Unit_Price": "₹150",
            "Expiry_Date": "2027-08-14",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-MUP-07"
        },
        {
            "Med_ID": "MED-1008",
            "Medication_Name": "Hydrocortisone 1% Cream",
            "Category": "Mild Corticosteroid",
            "Stock_Quantity": 300,
            "Unit_Price": "₹120",
            "Expiry_Date": "2028-05-30",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Batch_Number": "BATCH-HYD-08"
        }
    ]

    df = pd.DataFrame(default_data)
    try:
        df.to_csv(MEDICINE_FILE, sep="|", index=False)
    except Exception as e:
        print(f"Error creating medicine inventory file: {e}")
    return df


def save_medicine_inventory(df):
    """Saves the updated inventory immediately to medicine.txt."""
    try:
        df.to_csv(MEDICINE_FILE, sep="|", index=False)
        return True
    except Exception as e:
        print(f"Error saving medicine inventory: {e}")
        return False


def check_expiring_stock(days_threshold=60):
    """Checks for stock expiring within the specified threshold in days."""
    df = load_medicine_inventory()
    if df.empty:
        return pd.DataFrame()

    today = date.today()

    # Ensure Expiry_Date is parsed correctly
    df['Expiry_Date_Parsed'] = pd.to_datetime(df['Expiry_Date'], errors='coerce').dt.date

    # Filter for items expiring within threshold
    expiring_df = df[
        (df['Expiry_Date_Parsed'] - today).dt.days <= days_threshold
        ].sort_values(by='Expiry_Date_Parsed')

    # Drop temporary parsing column before returning
    if 'Expiry_Date_Parsed' in expiring_df.columns:
        expiring_df = expiring_df.drop(columns=['Expiry_Date_Parsed'])

    return expiring_df


def update_medicine_stock(med_id_or_name, quantity_change, is_addition=False):
    """Updates stock quantity for a specific medicine immediately."""
    df = load_medicine_inventory()
    if df.empty:
        return False

    # Match by Med_ID or Medication_Name (case-insensitive)
    match_mask = (
            (df["Med_ID"].astype(str).str.strip().str.upper() == str(med_id_or_name).strip().upper()) |
            (df["Medication_Name"].astype(str).str.strip().str.lower() == str(med_id_or_name).strip().lower())
    )

    if not df[match_mask].empty:
        idx = df[match_mask].index[0]
        current_stock = int(pd.to_numeric(df.loc[idx, "Stock_Quantity"], errors="coerce") or 0)

        if is_addition:
            new_stock = current_stock + int(quantity_change)
        else:
            new_stock = max(0, current_stock - int(quantity_change))

        df.loc[idx, "Stock_Quantity"] = new_stock
        df.loc[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_medicine_inventory(df)
        return True
    return False


def add_or_update_medicine(med_name, category, stock_qty, unit_price, expiry_date, batch_number=""):
    """Adds a new medicine or updates an existing one immediately in medicine.txt."""
    df = load_medicine_inventory()

    match_mask = df["Medication_Name"].astype(str).str.strip().str.lower() == str(med_name).strip().lower()

    if not df[match_mask].empty:
        idx = df[match_mask].index[0]
        df.loc[idx, "Category"] = str(category)
        df.loc[idx, "Stock_Quantity"] = int(stock_qty)
        df.loc[idx, "Unit_Price"] = str(unit_price)
        df.loc[idx, "Expiry_Date"] = str(expiry_date)
        if batch_number:
            df.loc[idx, "Batch_Number"] = str(batch_number)
        df.loc[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        next_id = f"MED-{1001 + len(df)}"
        new_row = {
            "Med_ID": next_id,
            "Medication_Name": str(med_name),
            "Category": str(category),
            "Stock_Quantity": int(stock_qty),
            "Unit_Price": str(unit_price),
            "Expiry_Date": str(expiry_date),
            "Batch_Number": str(batch_number) if batch_number else f"BATCH-{next_id}",
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    save_medicine_inventory(df)
    return True