import requests
import os
import pandas as pd
from datetime import datetime, timedelta

SMS_LOG_FILE = "sms_logs.txt"

# Configuration for your Android Gateway App
ANDROID_GATEWAY_URL = "http://YOUR_ANDROID_PHONE_LOCAL_IP:8080/send-sms"
GATEWAY_API_KEY = "YOUR_APP_SECRET_TOKEN"


def load_sms_logs():
    """Loads the log of already sent SMS messages, creating the file if it doesn't exist."""
    if os.path.exists(SMS_LOG_FILE):
        try:
            df = pd.read_csv(SMS_LOG_FILE, sep="|")
            df = df.fillna("")
            for col in ["SMS_ID", "Patient_UID", "Message_Key", "Timestamp"]:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass

    # Create empty DataFrame and file if it does not exist
    df = pd.DataFrame(columns=["SMS_ID", "Patient_UID", "Message_Key", "Timestamp"])
    try:
        df.to_csv(SMS_LOG_FILE, sep="|", index=False)
    except Exception:
        pass
    return df


def save_sms_logs(df):
    """Saves the SMS log database."""
    try:
        df.to_csv(SMS_LOG_FILE, sep="|", index=False)
    except Exception as e:
        print(f"Error saving SMS logs: {e}")


def get_patient_phone(patient_uid):
    """Retrieves the contact number for a specific patient from patients.txt."""
    patients_file = "patients.txt"
    if os.path.exists(patients_file):
        try:
            df = pd.read_csv(patients_file, sep="|")
            df = df.fillna("")
            if "Patient_UID" in df.columns:
                match = df[df["Patient_UID"].astype(str).str.strip().str.upper() == str(patient_uid).strip().upper()]
                if not match.empty:
                    if "Contact_Number" in match.columns:
                        return str(match.iloc[0]["Contact_Number"]).strip()
        except Exception:
            pass
    return None


def send_sms_alert(patient_uid, message_key, message_body):
    """Sends SMS via your local Android Gateway app using your phone plan."""
    logs_df = load_sms_logs()

    # 1. Prevent duplicate sending
    if not logs_df.empty:
        existing = logs_df[
            (logs_df["Patient_UID"].astype(str).str.upper() == str(patient_uid).upper()) &
            (logs_df["Message_Key"].astype(str) == str(message_key))
        ]
        if not existing.empty:
            return False  # Already sent

    # 2. Retrieve patient phone number from database using Contact_Number
    phone_number = get_patient_phone(patient_uid)
    if not phone_number:
        return False

    # 3. Fire HTTP request to your Android Gateway phone
    payload = {
        "phone": phone_number,
        "message": message_body,
        "token": GATEWAY_API_KEY
    }

    try:
        response = requests.post(ANDROID_GATEWAY_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"SMS successfully dispatched via Android Gateway to {phone_number}")
        else:
            print(f"Gateway failed: {response.text}")
            return False
    except Exception as e:
        print(f"Could not connect to Android gateway: {e}")
        return False

    # 4. Log to prevent double-sending
    logs_df = load_sms_logs()  # Reload to get fresh length
    sms_id = f"SMS-{1001 + len(logs_df)}"
    new_log = {
        "SMS_ID": sms_id,
        "Patient_UID": str(patient_uid).upper(),
        "Message_Key": str(message_key),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    updated_logs = pd.concat([logs_df, pd.DataFrame([new_log])], ignore_index=True)
    save_sms_logs(updated_logs)
    return True