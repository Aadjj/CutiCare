# modules/patient_logs.py
import os
import pandas as pd
from datetime import datetime

PATIENT_LOGS_FILE = "patient_logs.txt"


def load_patient_logs():
    """Loads clinical consultation logs from patient_logs.txt, creating the file if it doesn't exist."""
    if os.path.exists(PATIENT_LOGS_FILE):
        try:
            df = pd.read_csv(PATIENT_LOGS_FILE, sep="|")
            df = df.fillna("")
            for col in ["Log_ID", "Patient_UID", "Doctor_Name", "Diagnosis", "Prescription", "Notes", "Timestamp"]:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass

    # Create empty DataFrame and file if it does not exist
    df = pd.DataFrame(columns=[
        "Log_ID", "Patient_UID", "Doctor_Name", "Diagnosis", "Prescription", "Notes", "Timestamp"
    ])
    try:
        df.to_csv(PATIENT_LOGS_FILE, sep="|", index=False)
    except Exception:
        pass
    return df


def save_patient_logs(df):
    """Saves the consultation logs back to patient_logs.txt."""
    try:
        df.to_csv(PATIENT_LOGS_FILE, sep="|", index=False)
    except Exception as e:
        print(f"Error saving patient logs: {e}")


def add_patient_log(patient_uid, doctor_name, diagnosis, prescription, notes):
    """Appends a new clinical consultation record for a specific patient."""
    df = load_patient_logs()
    log_id = f"LOG-{1001 + len(df)}"

    new_record = {
        "Log_ID": log_id,
        "Patient_UID": str(patient_uid).strip().upper(),
        "Doctor_Name": str(doctor_name),
        "Diagnosis": str(diagnosis),
        "Prescription": str(prescription),
        "Notes": str(notes),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    updated_df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    save_patient_logs(updated_df)
    return log_id