# modules/billings.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.auth import check_role_access
import os

BILLINGS_FILE = "billings.txt"


def load_billings_db():
    """Loads billings data from billings.txt if available."""
    if os.path.exists(BILLINGS_FILE):
        try:
            df = pd.read_csv(BILLINGS_FILE, sep="|")
            df = df.fillna("")
            for col, default_val in [
                ("Payment_ID", ""),
                ("Patient_UID", ""),
                ("Patient_Name", ""),
                ("Item_Type", ""),
                ("Item_ID", ""),
                ("Amount", "0.0"),
                ("Payment_Method", ""),
                ("Transaction_Ref", ""),
                ("Status", "Pending Verification"),
                ("Timestamp", "")
            ]:
                if col not in df.columns:
                    df[col] = default_val
                df[col] = df[col].astype(str).replace(["nan", "None", ""], default_val)
            return df
        except Exception:
            pass

    return pd.DataFrame(columns=[
        "Payment_ID", "Patient_UID", "Patient_Name", "Item_Type",
        "Item_ID", "Amount", "Payment_Method", "Transaction_Ref",
        "Status", "Timestamp"
    ])


def save_billings_db(df):
    """Saves billings data back to billings.txt."""
    try:
        df.to_csv(BILLINGS_FILE, sep="|", index=False)
    except Exception as e:
        st.error(f"Error saving billings data: {e}")


def render_patient_billing_tab(patient_uid, patient_full_name):
    """Renders the billing and payment submission tab for patients."""
    st.subheader("💳 Consultation & Procedure Billing")
    st.caption("Settle pending consultation fees or procedure charges securely online.")

    pay_df = load_billings_db()

    # Filter payments for current user
    if not pay_df.empty and patient_uid:
        my_payments = pay_df[pay_df["Patient_UID"] == patient_uid]
    elif not pay_df.empty:
        my_payments = pay_df[pay_df["Patient_Name"].str.lower() == patient_full_name.lower()]
    else:
        my_payments = pd.DataFrame(columns=pay_df.columns)

    st.markdown("### Make a New Payment")
    with st.form("patient_payment_form"):
        item_type = st.selectbox("Select Billing Category", ["Consultation Fee", "Procedure Charge"])
        reference_item_id = st.text_input("Reference ID (Appt ID or Procedure ID)",
                                          placeholder="e.g., APT-5001 or PROC-7001")
        amount = st.number_input("Amount Due ($ / INR)", min_value=10.0, value=150.0, step=10.0)

        payment_method = st.selectbox("Payment Gateway Method",
                                      ["Credit / Debit Card", "UPI / NetBanking", "Clinic Cash Counter Reference"])
        txn_ref = st.text_input("Transaction / UPI Reference Number", placeholder="e.g., TXN123456789 or UPI Ref ID")

        submit_pay = st.form_submit_button("Submit Payment for Verification", type="primary")

        if submit_pay:
            if not txn_ref.strip():
                st.error("Please provide a valid transaction reference or receipt number.")
            else:
                full_df = load_billings_db()
                new_pay_id = f"PAY-{1001 + len(full_df)}"
                new_payment_record = {
                    "Payment_ID": new_pay_id,
                    "Patient_UID": patient_uid if patient_uid else "PAT-SELF",
                    "Patient_Name": patient_full_name,
                    "Item_Type": item_type,
                    "Item_ID": reference_item_id.strip() if reference_item_id else "N/A",
                    "Amount": str(amount),
                    "Payment_Method": payment_method,
                    "Transaction_Ref": txn_ref.strip(),
                    "Status": "Pending Verification",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                updated_df = pd.concat([full_df, pd.DataFrame([new_payment_record])], ignore_index=True)
                save_billings_db(updated_df)

                st.success(
                    f"🎉 Payment submitted successfully! Reference ID: **{new_pay_id}**. Awaiting staff confirmation.")
                st.rerun()

    st.markdown("---")
    st.markdown("### Your Payment History & Verification Status")
    if my_payments.empty:
        st.info("No payment history recorded.")
    else:
        st.dataframe(
            my_payments[["Payment_ID", "Item_Type", "Item_ID", "Amount", "Payment_Method", "Status", "Timestamp"]],
            use_container_width=True)


def render_staff_billing_verification_module():
    """Renders the staff/admin billing verification dashboard."""
    st.subheader("💰 Patient Payment Confirmations & Verification Desk")
    st.caption("Review submitted online payments, transaction references, and confirm or reject charges.")

    # Enforce Admin / Staff Access
    if not check_role_access(["ADMIN", "STAFF", "DOCTOR"]):
        st.error("❌ Access Denied: Authorized clinical staff or administrators only.")
        return

    pay_df = load_billings_db()

    if pay_df.empty:
        st.info("No billing records found in the system.")
        return

    tab_pend, tab_all = st.tabs(["⏳ Pending Verification", "📋 Master Billings Registry"])

    with tab_pend:
        pending_payments = pay_df[pay_df["Status"] == "Pending Verification"]

        if pending_payments.empty:
            st.info("No pending payment verifications requiring staff attention.")
        else:
            for idx, row in pending_payments.iterrows():
                with st.expander(f"Payment ID: {row['Payment_ID']} — {row['Patient_Name']} (${row['Amount']})"):
                    st.write(f"**Patient UID**: `{row['Patient_UID']}`")
                    st.write(f"**Billing Category**: {row['Item_Type']} (Ref: `{row['Item_ID']}`)")
                    st.write(f"**Payment Method**: {row['Payment_Method']}")
                    st.write(f"**Transaction Ref / UPI ID**: `{row['Transaction_Ref']}`")
                    st.write(f"**Timestamp**: {row['Timestamp']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirm Payment", key=f"conf_pay_{row['Payment_ID']}"):
                            full_df = load_billings_db()
                            target_idx = full_df[full_df["Payment_ID"] == row["Payment_ID"]].index
                            if not target_idx.empty:
                                full_df.at[target_idx[0], "Status"] = "Confirmed & Paid"
                                save_billings_db(full_df)
                                st.success(f"Payment {row['Payment_ID']} successfully verified and confirmed!")
                                st.rerun()
                    with col2:
                        if st.button("❌ Reject / Flag", key=f"rej_pay_{row['Payment_ID']}"):
                            full_df = load_billings_db()
                            target_idx = full_df[full_df["Payment_ID"] == row["Payment_ID"]].index
                            if not target_idx.empty:
                                full_df.at[target_idx[0], "Status"] = "Rejected / Invalid"
                                save_billings_db(full_df)
                                st.warning(f"Payment {row['Payment_ID']} marked as rejected.")
                                st.rerun()

    with tab_all:
        st.markdown("### Complete Billings & Receipts Ledger")
        st.dataframe(pay_df, use_container_width=True)# modules/billings.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.auth import check_role_access
from modules.notifications import add_notification
import os

BILLINGS_FILE = "billings.txt"


def load_billings_db():
    """Loads billings data from billings.txt if available."""
    if os.path.exists(BILLINGS_FILE):
        try:
            df = pd.read_csv(BILLINGS_FILE, sep="|")
            df = df.fillna("")
            for col, default_val in [
                ("Payment_ID", ""),
                ("Patient_UID", ""),
                ("Patient_Name", ""),
                ("Item_Type", ""),
                ("Item_ID", ""),
                ("Amount", "0.0"),
                ("Payment_Method", ""),
                ("Transaction_Ref", ""),
                ("Status", "Pending Verification"),
                ("Timestamp", "")
            ]:
                if col not in df.columns:
                    df[col] = default_val
                df[col] = df[col].astype(str).replace(["nan", "None", ""], default_val)
            return df
        except Exception:
            pass

    return pd.DataFrame(columns=[
        "Payment_ID", "Patient_UID", "Patient_Name", "Item_Type",
        "Item_ID", "Amount", "Payment_Method", "Transaction_Ref",
        "Status", "Timestamp"
    ])


def save_billings_db(df):
    """Saves billings data back to billings.txt."""
    try:
        df.to_csv(BILLINGS_FILE, sep="|", index=False)
    except Exception as e:
        st.error(f"Error saving billings data: {e}")


def render_patient_billing_tab(patient_uid, patient_full_name):
    """Renders the billing and payment submission tab for patients."""
    st.subheader("💳 Consultation & Procedure Billing")
    st.caption("Settle pending consultation fees or procedure charges securely online.")

    pay_df = load_billings_db()

    # Filter payments for current user
    if not pay_df.empty and patient_uid:
        my_payments = pay_df[pay_df["Patient_UID"] == patient_uid]
    elif not pay_df.empty:
        my_payments = pay_df[pay_df["Patient_Name"].str.lower() == patient_full_name.lower()]
    else:
        my_payments = pd.DataFrame(columns=pay_df.columns)

    st.markdown("### Make a New Payment")
    with st.form("patient_payment_form"):
        item_type = st.selectbox("Select Billing Category", ["Consultation Fee", "Procedure Charge"])
        reference_item_id = st.text_input("Reference ID (Appt ID or Procedure ID)",
                                          placeholder="e.g., APT-5001 or PROC-7001")
        amount = st.number_input("Amount Due ($ / INR)", min_value=10.0, value=150.0, step=10.0)

        payment_method = st.selectbox("Payment Gateway Method",
                                      ["Credit / Debit Card", "UPI / NetBanking", "Clinic Cash Counter Reference"])
        txn_ref = st.text_input("Transaction / UPI Reference Number", placeholder="e.g., TXN123456789 or UPI Ref ID")

        submit_pay = st.form_submit_button("Submit Payment for Verification", type="primary")

        if submit_pay:
            if not txn_ref.strip():
                st.error("Please provide a valid transaction reference or receipt number.")
            else:
                full_df = load_billings_db()
                new_pay_id = f"PAY-{1001 + len(full_df)}"

                resolved_uid = patient_uid if patient_uid else "PAT-SELF"

                new_payment_record = {
                    "Payment_ID": new_pay_id,
                    "Patient_UID": resolved_uid,
                    "Patient_Name": patient_full_name,
                    "Item_Type": item_type,
                    "Item_ID": reference_item_id.strip() if reference_item_id else "N/A",
                    "Amount": str(amount),
                    "Payment_Method": payment_method,
                    "Transaction_Ref": txn_ref.strip(),
                    "Status": "Pending Verification",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                updated_df = pd.concat([full_df, pd.DataFrame([new_payment_record])], ignore_index=True)
                save_billings_db(updated_df)

                # Send notification to patient
                if resolved_uid != "PAT-SELF":
                    add_notification(resolved_uid, "Billing", f"Payment submission #{new_pay_id} for ₹{amount} received and is pending verification.")

                st.success(
                    f"🎉 Payment submitted successfully! Reference ID: **{new_pay_id}**. Awaiting staff confirmation.")
                st.rerun()

    st.markdown("---")
    st.markdown("### Your Payment History & Verification Status")
    if my_payments.empty:
        st.info("No payment history recorded.")
    else:
        st.dataframe(
            my_payments[["Payment_ID", "Item_Type", "Item_ID", "Amount", "Payment_Method", "Status", "Timestamp"]],
            use_container_width=True)


def render_staff_billing_verification_module():
    """Renders the staff/admin billing verification dashboard."""
    st.subheader("💰 Patient Payment Confirmations & Verification Desk")
    st.caption("Review submitted online payments, transaction references, and confirm or reject charges.")

    # Enforce Admin / Staff Access
    if not check_role_access(["ADMIN", "STAFF", "DOCTOR"]):
        st.error("❌ Access Denied: Authorized clinical staff or administrators only.")
        return

    pay_df = load_billings_db()

    if pay_df.empty:
        st.info("No billing records found in the system.")
        return

    tab_pend, tab_all = st.tabs(["⏳ Pending Verification", "📋 Master Billings Registry"])

    with tab_pend:
        pending_payments = pay_df[pay_df["Status"] == "Pending Verification"]

        if pending_payments.empty:
            st.info("No pending payment verifications requiring staff attention.")
        else:
            for idx, row in pending_payments.iterrows():
                with st.expander(f"Payment ID: {row['Payment_ID']} — {row['Patient_Name']} (${row['Amount']})"):
                    st.write(f"**Patient UID**: `{row['Patient_UID']}`")
                    st.write(f"**Billing Category**: {row['Item_Type']} (Ref: `{row['Item_ID']}`)")
                    st.write(f"**Payment Method**: {row['Payment_Method']}")
                    st.write(f"**Transaction Ref / UPI ID**: `{row['Transaction_Ref']}`")
                    st.write(f"**Timestamp**: {row['Timestamp']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirm Payment", key=f"conf_pay_{row['Payment_ID']}"):
                            full_df = load_billings_db()
                            target_idx = full_df[full_df["Payment_ID"] == row["Payment_ID"]].index
                            if not target_idx.empty:
                                full_df.at[target_idx[0], "Status"] = "Confirmed & Paid"
                                save_billings_db(full_df)

                                # Send notification to patient
                                p_uid = row['Patient_UID']
                                if p_uid and p_uid != "PAT-SELF":
                                    add_notification(p_uid, "Billing", f"Your payment #{row['Payment_ID']} for ${row['Amount']} has been confirmed and settled.")

                                st.success(f"Payment {row['Payment_ID']} successfully verified and confirmed!")
                                st.rerun()
                    with col2:
                        if st.button("❌ Reject / Flag", key=f"rej_pay_{row['Payment_ID']}"):
                            full_df = load_billings_db()
                            target_idx = full_df[full_df["Payment_ID"] == row["Payment_ID"]].index
                            if not target_idx.empty:
                                full_df.at[target_idx[0], "Status"] = "Rejected / Invalid"
                                save_billings_db(full_df)

                                # Send notification to patient
                                p_uid = row['Patient_UID']
                                if p_uid and p_uid != "PAT-SELF":
                                    add_notification(p_uid, "Billing", f"Your payment #{row['Payment_ID']} was marked as rejected/invalid. Please check transaction references.")

                                st.warning(f"Payment {row['Payment_ID']} marked as rejected.")
                                st.rerun()

    with tab_all:
        st.markdown("### Complete Billings & Receipts Ledger")
        st.dataframe(pay_df, use_container_width=True)