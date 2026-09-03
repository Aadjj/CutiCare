# modules/post_care_notifications.py
import os
import pandas as pd
from datetime import datetime, timedelta

POST_CARE_LOG_FILE = "post_care_logs.txt"


def load_post_care_logs():
    """Loads the log of already sent post-care messages, creating the file if it doesn't exist."""
    if os.path.exists(POST_CARE_LOG_FILE):
        try:
            df = pd.read_csv(POST_CARE_LOG_FILE, sep="|")
            df = df.fillna("")
            for col in ["Log_ID", "Patient_UID", "Message_Key", "Timestamp"]:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass

    # Create empty DataFrame and file if it does not exist
    df = pd.DataFrame(columns=["Log_ID", "Patient_UID", "Message_Key", "Timestamp"])
    try:
        df.to_csv(POST_CARE_LOG_FILE, sep="|", index=False)
    except Exception:
        pass
    return df


def save_post_care_logs(df):
    """Saves the post-care notification log."""
    try:
        df.to_csv(POST_CARE_LOG_FILE, sep="|", index=False)
    except Exception as e:
        print(f"Error saving post-care logs: {e}")


def get_patient_contact(patient_uid):
    """Retrieves the contact number for a specific patient from patients.txt."""
    patients_file = "patients.txt"
    if os.path.exists(patients_file):
        try:
            df = pd.read_csv(patients_file, sep="|")
            df = df.fillna("")
            if "Patient_UID" in df.columns:
                match = df[df["Patient_UID"].astype(str).str.strip().str.upper() == str(patient_uid).strip().upper()]
                if not match.empty and "Contact_Number" in match.columns:
                    return str(match.iloc[0]["Contact_Number"]).strip()
        except Exception:
            pass
    return None


def send_post_care_alert(patient_uid, message_key, message_body):
    """Sends post-care instructions and logs them to prevent duplicate sending."""
    logs_df = load_post_care_logs()

    # Prevent duplicate triggers
    if not logs_df.empty:
        existing = logs_df[
            (logs_df["Patient_UID"].astype(str).str.upper() == str(patient_uid).upper()) &
            (logs_df["Message_Key"].astype(str) == str(message_key))
            ]
        if not existing.empty:
            return False

    phone_number = get_patient_contact(patient_uid)
    if not phone_number:
        return False

    # Integration hook with WhatsApp module
    try:
        from modules.whatsapp_notifications import send_whatsapp_alert
        send_whatsapp_alert(patient_uid, message_key, message_body)
    except Exception:
        print(f"\n[POST-CARE ALERT DISPATCHED TO {phone_number}]: {message_body}\n")

    # Log dispatch
    logs_df = load_post_care_logs()
    log_id = f"PC-{1001 + len(logs_df)}"
    new_log = {
        "Log_ID": log_id,
        "Patient_UID": str(patient_uid).upper(),
        "Message_Key": str(message_key),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    updated_logs = pd.concat([logs_df, pd.DataFrame([new_log])], ignore_index=True)
    save_post_care_logs(updated_logs)
    return True


def check_and_send_post_care_reminders():
    """Scans completed procedures and sends timed post-care instructions:
    - 2 hours post-procedure (Immediate care)
    - 24 hours post-procedure (Sun protection & recovery checks)
    """
    procedures_file = "procedures.txt"
    if not os.path.exists(procedures_file):
        return

    try:
        proc_df = pd.read_csv(procedures_file, sep="|")
        if proc_df.empty:
            return

        now = datetime.now()
        for _, proc in proc_df.fillna("").iterrows():
            patient_uid = proc.get("Patient_UID", "")
            proc_date = str(proc.get("Date", ""))
            proc_time = str(proc.get("Time", ""))
            test_name = str(proc.get("Test_Name", proc.get("Procedure_Name", "Skin Treatment"))).lower()

            if not patient_uid or not proc_date or not proc_time:
                continue

            try:
                proc_datetime = datetime.strptime(f"{proc_date} {proc_time}", "%Y-%m-%d %H:%M")
                time_elapsed = now - proc_datetime

                # Trigger 1: 2 Hours Post-Procedure (Immediate Care)
                if timedelta(hours=2) <= time_elapsed <= timedelta(hours=4) and proc_datetime.date() == now.date():
                    msg_key = f"PC-2HR-{proc_date}-{patient_uid}"
                    body = f"Hello from Cuticare Clinic! Hope your {test_name} went well. Remember to keep the treated area clean, avoid touching it unnecessarily, and stay hydrated."
                    send_post_care_alert(patient_uid, msg_key, body)

                # Trigger 2: 24 Hours Post-Procedure (Sun Protection / Laser Care Reminder)
                if timedelta(hours=24) <= time_elapsed <= timedelta(hours=28):
                    msg_key = f"PC-24HR-{proc_date}-{patient_uid}"
                    body = f"Cuticare Post-Care Reminder: It's been 24 hours since your {test_name}. Please ensure strict sun protection (apply SPF 30+ sunscreen and avoid direct sunlight) for optimal healing."
                    send_post_care_alert(patient_uid, msg_key, body)

            except Exception:
                continue
    except Exception:
        pass