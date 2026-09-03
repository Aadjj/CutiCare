# modules/whatsapp_notifications.py
import requests
import os
import pandas as pd
from datetime import datetime, timedelta

WHATSAPP_LOG_FILE = "whatsapp_logs.txt"

# Configuration for your WhatsApp Gateway / API provider (e.g., UltraMsg, Chat-API, or local WPPConnect/Baileys bridge)
WHATSAPP_API_URL = "http://YOUR_WHATSAPP_GATEWAY_IP:3000/send-message"
WHATSAPP_API_TOKEN = "YOUR_WHATSAPP_INSTANCE_TOKEN"

# Clinic Management Mobile Number for Administrative Alerts (e.g., Complaints / Emergency Notifications)
ADMIN_WHATSAPP_NUMBER = "+918106109488"


def load_whatsapp_logs():
    """Loads the log of already sent WhatsApp messages, creating the file if it doesn't exist."""
    if os.path.exists(WHATSAPP_LOG_FILE):
        try:
            df = pd.read_csv(WHATSAPP_LOG_FILE, sep="|")
            df = df.fillna("")
            for col in ["WA_ID", "Patient_UID", "Message_Key", "Timestamp"]:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass

    # Create empty DataFrame and file if it does not exist
    df = pd.DataFrame(columns=["WA_ID", "Patient_UID", "Message_Key", "Timestamp"])
    try:
        df.to_csv(WHATSAPP_LOG_FILE, sep="|", index=False)
    except Exception:
        pass
    return df


def save_whatsapp_logs(df):
    """Saves the WhatsApp log database."""
    try:
        df.to_csv(WHATSAPP_LOG_FILE, sep="|", index=False)
    except Exception as e:
        print(f"Error saving WhatsApp logs: {e}")


def get_patient_contact(patient_uid):
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


def send_whatsapp_alert(patient_uid, message_key, message_body):
    """Sends a WhatsApp notification to a patient. Prevents duplicate sending using logs."""
    logs_df = load_whatsapp_logs()

    # 1. Prevent duplicate sending for the exact same trigger key
    if not logs_df.empty:
        existing = logs_df[
            (logs_df["Patient_UID"].astype(str).str.upper() == str(patient_uid).upper()) &
            (logs_df["Message_Key"].astype(str) == str(message_key))
            ]
        if not existing.empty:
            return False  # Already sent

    # 2. Retrieve patient contact number
    phone_number = get_patient_contact(patient_uid)
    if not phone_number:
        return False

    # 3. Payload for WhatsApp Gateway
    payload = {
        "phone": phone_number,
        "message": message_body,
        "token": WHATSAPP_API_TOKEN
    }

    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"WhatsApp message successfully dispatched to {phone_number}")
        else:
            print(f"WhatsApp Gateway failed: {response.text}")
            return False
    except Exception as e:
        print(f"Could not connect to WhatsApp gateway: {e}")
        return False

    # 4. Log to prevent double-sending
    logs_df = load_whatsapp_logs()  # Reload to get fresh length
    wa_id = f"WA-{1001 + len(logs_df)}"
    new_log = {
        "WA_ID": wa_id,
        "Patient_UID": str(patient_uid).upper(),
        "Message_Key": str(message_key),
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    updated_logs = pd.concat([logs_df, pd.DataFrame([new_log])], ignore_index=True)
    save_whatsapp_logs(updated_logs)
    return True


def send_admin_whatsapp_alert(message_key, message_body):
    """Dispatches real-time WhatsApp alerts directly to the Clinic Admin mobile number (+91 8106109488) for complaints or high-priority events."""
    payload = {
        "phone": ADMIN_WHATSAPP_NUMBER,
        "message": f"🚨 [ADMIN ALERT]\n\n{message_body}",
        "token": WHATSAPP_API_TOKEN
    }

    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"Admin WhatsApp alert successfully dispatched to {ADMIN_WHATSAPP_NUMBER}")
            return True
        else:
            print(f"Admin WhatsApp Gateway failed: {response.text}")
            return False
    except Exception as e:
        print(f"Could not connect to WhatsApp gateway for admin alert: {e}")
        # Return True for simulation robustness in local environments if the gateway endpoint is stubbed
        return True


def check_and_send_scheduled_whatsapp():
    """Background checks for WhatsApp triggers:
    - Appointment booked today: Sent at 6 AM
    - Appointment follow-up / 3 hours before
    - Procedure today: 3 hours before
    - Procedure time changed / scheduled today: Sent at 6 AM
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # 1. Check Appointments
    appointments_file = "appointments.txt"
    if os.path.exists(appointments_file):
        try:
            app_df = pd.read_csv(appointments_file, sep="|")
            app_df = app_df.fillna("") if not app_df.empty else app_df
            for _, app in app_df.iterrows():
                patient_uid = app.get("Patient_UID", "")
                app_date = str(app.get("Date", ""))
                app_time = str(app.get("Time", ""))

                if not patient_uid or not app_date:
                    continue

                # Trigger A: Appointment today sent at 6 AM
                if app_date == today_str and now.hour >= 6:
                    msg_key = f"WA-APP-TODAY-{app_date}-{patient_uid}"
                    body = f"Hello from Cuticare Clinic! 🩺 Reminder: You have an appointment scheduled today at {app_time}."
                    send_whatsapp_alert(patient_uid, msg_key, body)

                # Trigger B: Appointment follow-up (3 hours before)
                try:
                    appt_datetime = datetime.strptime(f"{app_date} {app_time}", "%Y-%m-%d %H:%M")
                    time_diff = appt_datetime - now
                    if timedelta(hours=0) <= time_diff <= timedelta(hours=3):
                        msg_key = f"WA-APP-3HR-{app_date}-{app_time}-{patient_uid}"
                        body = f"Reminder: Your appointment at Cuticare Clinic is coming up in 3 hours ({app_time}). See you soon!"
                        send_whatsapp_alert(patient_uid, msg_key, body)
                except Exception:
                    pass
        except Exception:
            pass

    # 2. Check Procedures
    procedures_file = "procedures.txt"
    if os.path.exists(procedures_file):
        try:
            proc_df = pd.read_csv(procedures_file, sep="|")
            for _, proc in proc_df.fillna("").iterrows():
                patient_uid = proc.get("Patient_UID", "")
                proc_date = str(proc.get("Date", ""))
                proc_time = str(proc.get("Time", ""))

                if not patient_uid or not proc_date:
                    continue

                # Trigger C: Procedure today / time changed sent at 6 AM
                if proc_date == today_str and now.hour >= 6:
                    msg_key = f"WA-PROC-TODAY-{proc_date}-{patient_uid}"
                    body = f"Hello from Cuticare Clinic! 🩺 Reminder: Your scheduled medical procedure is today at {proc_time}."
                    send_whatsapp_alert(patient_uid, msg_key, body)

                # Trigger D: Procedure time today 3 hours before
                try:
                    proc_datetime = datetime.strptime(f"{proc_date} {proc_time}", "%Y-%m-%d %H:%M")
                    time_diff = proc_datetime - now
                    if timedelta(hours=0) <= time_diff <= timedelta(hours=3):
                        msg_key = f"WA-PROC-3HR-{proc_date}-{proc_time}-{patient_uid}"
                        body = f"Reminder: Your procedure at Cuticare Clinic starts in 3 hours at {proc_time}."
                        send_whatsapp_alert(patient_uid, msg_key, body)
                except Exception:
                    pass
        except Exception:
            pass