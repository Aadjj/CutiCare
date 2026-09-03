# modules/notifications.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

NOTIFICATIONS_FILE = "notifications.txt"


def load_notifications_db():
    """Loads notifications from notifications.txt if available."""
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            df = pd.read_csv(NOTIFICATIONS_FILE, sep="|")
            df = df.fillna("")
            for col, default_val in [
                ("Notification_ID", ""),
                ("Recipient_UID", ""),
                ("Category", ""),
                ("Message", ""),
                ("Read_Status", "Unread"),
                ("Timestamp", "")
            ]:
                if col not in df.columns:
                    df[col] = default_val
                df[col] = df[col].astype(str).replace(["nan", "None", ""], default_val)
            return df
        except Exception:
            pass

    return pd.DataFrame(columns=[
        "Notification_ID", "Recipient_UID", "Category",
        "Message", "Read_Status", "Timestamp"
    ])


def save_notifications_db(df):
    """Saves notifications DataFrame back to notifications.txt."""
    try:
        df.to_csv(NOTIFICATIONS_FILE, sep="|", index=False)
    except Exception as e:
        st.error(f"Error saving notifications: {e}")


def add_notification(recipient_uid, category, message):
    """Utility function to add a notification for a specific patient/user UID or role."""
    df = load_notifications_db()
    notif_id = f"NOTIF-{1001 + len(df)}"
    new_record = {
        "Notification_ID": notif_id,
        "Recipient_UID": str(recipient_uid),
        "Category": category,
        "Message": message,
        "Read_Status": "Unread",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    updated_df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    save_notifications_db(updated_df)


def check_background_alerts():
    """Automated background checks for low inventory stock and pending lab tests."""
    # 1. Low stock daily reminder for Pharmacy
    if "pharmacy_inventory" in st.session_state and not st.session_state.pharmacy_inventory.empty:
        inv_df = st.session_state.pharmacy_inventory
        for _, item in inv_df.iterrows():
            try:
                stock = int(item.get("Stock_Quantity", 15))
                item_name = item.get("Item_Name", "Item")
                if stock <= 10:
                    low_stock_msg = f"Low Stock Alert: '{item_name}' has only {stock} units remaining. Please restock."
                    existing_notifs = load_notifications_db()
                    if existing_notifs.empty or not ((existing_notifs["Recipient_UID"].str.upper() == "PHARMACY") & (
                            existing_notifs["Message"] == low_stock_msg) & (existing_notifs[
                                                                                "Read_Status"].str.upper() == "UNREAD")).any():
                        add_notification("PHARMACY", "Low Stock", low_stock_msg)
            except Exception:
                continue

    # 2. Lab reminders for Lab desk specifically
    if "lab_reports_db" in st.session_state and not st.session_state.lab_reports_db.empty:
        labs_df = st.session_state.lab_reports_db
        pending_labs = labs_df[labs_df["Status"].astype(str).str.lower().isin(["pending", "assigned by doctor"])]

        today_date = date.today()
        for _, lab in pending_labs.iterrows():
            timestamp_str = str(lab.get("Timestamp", ""))
            try:
                lab_date = datetime.strptime(timestamp_str.split(" ")[0], "%Y-%m-%d").date()
                if (today_date - lab_date).days >= 3:
                    reminder_msg = f"Reminder: Lab test '{lab.get('Test_Name')}' for {lab.get('Patient_Name')} is pending after 3 days."
                    existing_notifs = load_notifications_db()
                    if existing_notifs.empty or not ((existing_notifs["Recipient_UID"].str.upper() == "LAB") & (
                            existing_notifs["Message"] == reminder_msg) & (existing_notifs[
                                                                               "Read_Status"].str.upper() == "UNREAD")).any():
                        add_notification("LAB", "Lab Reminder", reminder_msg)
            except Exception:
                continue


def get_unread_notification_count():
    """Returns the count of unread notifications for the active user/role with strict isolation."""
    if not st.session_state.get("authenticated", False):
        return 0

    current_role = str(st.session_state.get("current_role", "PATIENT")).strip().upper()
    current_uid = str(st.session_state.get("current_uid", "")).strip().upper()

    df = load_notifications_db()
    if df.empty:
        return 0

    df["Recipient_UID"] = df["Recipient_UID"].astype(str).str.strip().str.upper()
    df["Read_Status"] = df["Read_Status"].astype(str).str.strip().str.upper()
    df["Category"] = df["Category"].astype(str).str.strip().str.upper()

    # ADMIN sees all unread notifications across the entire system
    if current_role == "ADMIN":
        unread_df = df[df["Read_Status"] == "UNREAD"]
        return len(unread_df)

    # STRICT ROLE-BASED ISOLATION FILTERING
    if current_role == "PATIENT":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL")
        ]
    elif current_role == "STAFF":
        # Staff should NOT see Pharmacy or Lab specific alerts
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "STAFF")
        ]
        role_filtered = role_filtered[
            ~(role_filtered["Recipient_UID"] == "PHARMACY") &
            ~(role_filtered["Recipient_UID"] == "LAB") &
            ~(role_filtered["Category"].isin(["PRESCRIPTION", "LOW STOCK", "LAB REMINDER"]))
        ]
    elif current_role == "DOCTOR":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "DOCTOR")
        ]
    elif current_role == "PHARMACY":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "PHARMACY") |
            (df["Category"] == "PRESCRIPTION")
        ]
    elif current_role == "LAB":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "LAB") |
            (df["Category"] == "LAB REMINDER")
        ]
    else:
        role_filtered = df[df["Recipient_UID"] == current_uid]

    unread_df = role_filtered[role_filtered["Read_Status"] == "UNREAD"]
    return len(unread_df)


def render_notifications_page():
    """Renders the dedicated Notifications page with strict role isolation (Admin sees all)."""
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to view notifications.")
        return

    check_background_alerts()

    st.markdown("## 🔔 System Notifications")
    st.write("View all your recent active alerts and system reminders below.")

    current_role = str(st.session_state.get("current_role", "PATIENT")).strip().upper()
    current_uid = str(st.session_state.get("current_uid", "")).strip().upper()

    df = load_notifications_db()

    # Debug utility expander to verify raw rows and active session identifiers
    with st.expander("🛠️ Debug: View Raw Database Rows"):
        st.write("Current Role in Session:", current_role)
        st.write("Current UID in Session:", current_uid)
        st.dataframe(df)

    if df.empty:
        st.info("notifications.txt is completely empty.")
        return

    df["Recipient_UID"] = df["Recipient_UID"].astype(str).str.strip().str.upper()
    df["Read_Status"] = df["Read_Status"].astype(str).str.strip().str.upper()
    df["Category"] = df["Category"].astype(str).str.strip().str.upper()

    # STRICT ROLE-BASED ISOLATION LOGIC
    if current_role == "ADMIN":
        # Admin gets absolute visibility over all notifications in the system
        role_filtered = df
    elif current_role == "STAFF":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "STAFF")
        ]
        # Exclude pharmacy and lab items from staff view completely
        role_filtered = role_filtered[
            ~(role_filtered["Recipient_UID"] == "PHARMACY") &
            ~(role_filtered["Recipient_UID"] == "LAB") &
            ~(role_filtered["Category"].isin(["PRESCRIPTION", "LOW STOCK", "LAB REMINDER"]))
        ]
    elif current_role == "DOCTOR":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "DOCTOR")
        ]
    elif current_role == "PHARMACY":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "PHARMACY") |
            (df["Category"] == "PRESCRIPTION")
        ]
    elif current_role == "LAB":
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL") |
            (df["Recipient_UID"] == "LAB") |
            (df["Category"] == "LAB REMINDER")
        ]
    else:
        role_filtered = df[
            (df["Recipient_UID"] == current_uid) |
            (df["Recipient_UID"] == "ALL")
        ]

    # Filter down strictly to unread items
    my_notifs = role_filtered[role_filtered["Read_Status"] == "UNREAD"]

    if my_notifs.empty:
        st.info(f"No new unread notifications found for role: {current_role}")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Unread Alerts for `{current_role}`:** {len(my_notifs)}")
    with col2:
        if st.button("Mark All as Read", use_container_width=True):
            full_df = load_notifications_db()
            full_df.loc[full_df["Notification_ID"].isin(my_notifs["Notification_ID"]), "Read_Status"] = "Read"
            save_notifications_db(full_df)
            st.success("All notifications marked as read!")
            st.rerun()

    st.markdown("---")

    # Display unread notifications list (newest first)
    for idx, row in my_notifs.tail(20).iloc[::-1].iterrows():
        notif_id = row["Notification_ID"]
        category = row["Category"]
        message = row["Message"]
        timestamp = row["Timestamp"]
        recipient = row["Recipient_UID"]

        if current_role == "ADMIN":
            st.markdown(f"🔴 **[{category}]** (Target: `{recipient}`) {message}")
        else:
            st.markdown(f"🔴 **[{category}]** {message}")

        st.caption(f"Time: {timestamp}")

        if st.button("Mark as Read", key=f"tab_read_btn_{notif_id}"):
            full_df = load_notifications_db()
            full_df.loc[full_df["Notification_ID"] == notif_id, "Read_Status"] = "Read"
            save_notifications_db(full_df)
            st.rerun()

        st.markdown("---")