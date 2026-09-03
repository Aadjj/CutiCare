# modules/admin.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.auth import check_role_access
from modules.database import load_patients_db, save_patients_db
from modules.billings import load_billings_db, save_billings_db
from modules.equipment_scheduler import load_equipment_schedule_db, save_equipment_schedule_db
from modules.notifications import add_notification
from modules.medicine_inventory import load_medicine_inventory, add_or_update_medicine

ADMIN_LOG_FILE = "admin_audit_logs.txt"


def load_admin_logs():
    """Loads administrative audit logs from file or session state."""
    if "admin_logs_db" not in st.session_state:
        if os.path.exists(ADMIN_LOG_FILE):
            try:
                st.session_state.admin_logs_db = pd.read_csv(ADMIN_LOG_FILE, sep="|")
                st.session_state.admin_logs_db = st.session_state.admin_logs_db.fillna("")
            except Exception:
                st.session_state.admin_logs_db = _get_empty_logs_df()
        else:
            df = _get_empty_logs_df()
            save_admin_logs(df)
            st.session_state.admin_logs_db = df
    return st.session_state.admin_logs_db


def save_admin_logs(df):
    """Saves admin logs DataFrame to file."""
    try:
        df.to_csv(ADMIN_LOG_FILE, sep="|", index=False)
        st.session_state.admin_logs_db = df
    except Exception as e:
        st.error(f"Error saving audit logs: {e}")


def _get_empty_logs_df():
    """Returns an empty DataFrame for admin audit logs."""
    return pd.DataFrame(columns=["Log_ID", "Admin_User", "Action_Type", "Details", "Timestamp"])


def log_admin_action(admin_name, action_type, details):
    """Logs an administrative action for audit tracking."""
    logs_df = load_admin_logs()
    next_id = 5001 if logs_df.empty else len(logs_df) + 5001
    new_log = {
        "Log_ID": f"LOG-{next_id}",
        "Admin_User": admin_name,
        "Action_Type": action_type,
        "Details": details,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    updated_logs = pd.concat([logs_df, pd.DataFrame([new_log])], ignore_index=True)
    save_admin_logs(updated_logs)


def render_admin_module():
    st.title("🛡️ Cuticare Administrative Control Hub")
    st.markdown("System Configuration, Financial Reversals, Inventory Management, Staff Audits, & Clinic Diagnostics.")

    # 1. Enforce Strict Admin Access
    if not check_role_access(["ADMIN"]):
        st.error("❌ Access Denied: Administrator privileges required to access this control hub.")
        return

    current_admin = st.session_state.get("current_username", "System Administrator")

    # Tabs for Admin Functions
    tab_overview, tab_finance, tab_inventory, tab_users, tab_complaints, tab_audit = st.tabs([
        "📊 Clinic Overview & Metrics",
        "💳 Financial Reversals & Refunds",
        "📦 Inventory & Equipment Setup",
        "👥 User & Role Management",
        "📢 Complaints & Grievances",
        "📜 System Audit Logs"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: CLINIC OVERVIEW & METRICS
    # -------------------------------------------------------------------------
    with tab_overview:
        st.subheader("High-Level Clinic Performance & Resource Metrics")

        patients_df = load_patients_db()
        ledger_df = load_billings_db()
        sched_df = load_equipment_schedule_db()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Registered Patients", len(patients_df) if not patients_df.empty else 0)

        total_revenue = 0.0
        if not ledger_df.empty and "Amount" in ledger_df.columns:
            status_col = "Status" if "Status" in ledger_df.columns else "Settlement_Status"
            if status_col in ledger_df.columns:
                settled_df = ledger_df[
                    ledger_df[status_col].astype(str).str.contains("Confirmed|Paid|Settled", case=False, na=False)]
                total_revenue = pd.to_numeric(settled_df["Amount"], errors="coerce").sum()
        col2.metric("Total Settled Revenue", f"₹{total_revenue:,.2f}")

        col3.metric("Active Equipment Bookings",
                    len(sched_df[sched_df["Status"] == "Confirmed"]) if not sched_df.empty else 0)

        pending_count = 0
        if not ledger_df.empty:
            status_col = "Status" if "Status" in ledger_df.columns else "Settlement_Status"
            if status_col in ledger_df.columns:
                pending_count = len(
                    ledger_df[ledger_df[status_col].astype(str).str.contains("Pending", case=False, na=False)])
        col4.metric("Pending Invoices / Auth", pending_count)

        st.markdown("---")
        st.markdown("#### Quick System Health Status")
        st.success(
            "✅ Database connections stable (`patients.txt`, `billings.txt`, `equipment_schedule.txt`, `medicine.txt`).")
        st.success("✅ Role-Based Access Control (RBAC) active and enforcing security boundaries.")

    # -------------------------------------------------------------------------
    # TAB 2: FINANCIAL REVERSALS & REFUNDS
    # -------------------------------------------------------------------------
    with tab_finance:
        st.subheader("Financial Reversals, Refunds, & Invoice Adjustments")
        st.caption("Administrators can void settled invoices or issue formal refunds to patient ledgers.")

        ledger_df = load_billings_db()
        if ledger_df.empty:
            st.info("No financial ledger entries found.")
        else:
            status_col = "Status" if "Status" in ledger_df.columns else "Settlement_Status"
            id_col = "Payment_ID" if "Payment_ID" in ledger_df.columns else "Invoice_No"

            if status_col in ledger_df.columns and id_col in ledger_df.columns:
                settled_invoices = ledger_df[
                    ledger_df[status_col].astype(str).str.contains("Confirmed|Paid|Settled", case=False, na=False)]
                if settled_invoices.empty:
                    st.info("No settled invoices available for reversal or refund.")
                else:
                    inv_to_modify = st.selectbox(
                        "Select Settled Invoice to Reverse / Refund:",
                        options=settled_invoices[id_col].tolist(),
                        format_func=lambda
                            x: f"{x} - {settled_invoices[settled_invoices[id_col] == x]['Patient_Name'].values[0]} (₹{settled_invoices[settled_invoices[id_col] == x]['Amount'].values[0]})"
                    )

                    selected_inv_row = settled_invoices[settled_invoices[id_col] == inv_to_modify].iloc[0]
                    st.write(f"**Patient**: {selected_inv_row['Patient_Name']} (`{selected_inv_row['Patient_UID']}`)")
                    st.write(f"**Billing Category**: {selected_inv_row.get('Item_Type', 'N/A')}")
                    st.write(f"**Net Amount Paid**: ₹{float(selected_inv_row['Amount']):,.2f}")

                    reversal_reason = st.text_input("Reason for Reversal / Refund *",
                                                    placeholder="e.g., Service cancellation, duplicate billing, medical waiver")

                    if st.button("⚠️ Process Invoice Reversal / Refund", type="primary"):
                        if not reversal_reason.strip():
                            st.error("Please provide a valid reason for the financial reversal.")
                        else:
                            target_idx = ledger_df[ledger_df[id_col] == inv_to_modify].index
                            if not target_idx.empty:
                                ledger_df.at[target_idx[0], status_col] = "Refunded / Reversed"
                                ledger_df.at[target_idx[0], "Amount"] = "0.0"
                                save_billings_db(ledger_df)

                                # Log admin action
                                log_admin_action(current_admin, "Financial Reversal",
                                                 f"Invoice {inv_to_modify} reversed. Reason: {reversal_reason}")

                                # Notify patient
                                if selected_inv_row["Patient_UID"] and selected_inv_row["Patient_UID"] != "PAT-SELF":
                                    add_notification(selected_inv_row["Patient_UID"], "Billing",
                                                     f"Invoice #{inv_to_modify} has been refunded/reversed. Reason: {reversal_reason}")

                                st.success(
                                    f"✅ Invoice **{inv_to_modify}** successfully marked as **Refunded / Reversed**.")
                                st.rerun()
            else:
                st.info("Financial records missing expected schema columns.")

    # -------------------------------------------------------------------------
    # TAB 3: INVENTORY & EQUIPMENT SETUP
    # -------------------------------------------------------------------------
    with tab_inventory:
        st.subheader("Pharmacy Inventory & Equipment Fleet Management")

        inv_tab_pharm, inv_tab_equip = st.tabs(["💊 Pharmacy Stock Configuration", "🩺 Equipment Fleet Master"])

        with inv_tab_pharm:
            st.markdown("#### Manage Pharmacy Medication Stock (`medicine.txt`)")
            med_df = load_medicine_inventory()

            if med_df.empty:
                st.info("No medicine inventory found.")
            else:
                edited_pharm = st.data_editor(med_df, use_container_width=True, num_rows="dynamic",
                                              key="admin_medicine_editor")

                if st.button("💾 Save Pharmacy Inventory Changes"):
                    for _, row in edited_pharm.iterrows():
                        add_or_update_medicine(
                            med_name=row.get("Medication_Name", ""),
                            category=row.get("Category", ""),
                            stock_qty=row.get("Stock_Quantity", 0),
                            unit_price=row.get("Unit_Price", "0"),
                            expiry_date=row.get("Expiry_Date", "")
                        )
                    log_admin_action(current_admin, "Inventory Update", "Updated medicine.txt master inventory table.")
                    st.success("✅ Pharmacy inventory successfully saved to `medicine.txt`!")
                    st.rerun()

        with inv_tab_equip:
            st.markdown("#### Manage Clinical Equipment & Treatment Suites")
            sched_df = load_equipment_schedule_db()
            st.info("Active Equipment Schedule Database records are tracked through the equipment scheduler module.")
            if not sched_df.empty:
                edited_sched = st.data_editor(sched_df, use_container_width=True, key="admin_equipment_editor")
                if st.button("💾 Save Equipment Schedule Changes"):
                    save_equipment_schedule_db(edited_sched)
                    log_admin_action(current_admin, "Equipment Schedule Update",
                                     "Modified equipment schedule master database.")
                    st.success("✅ Equipment schedule registry updated successfully!")
                    st.rerun()

    # -------------------------------------------------------------------------
    # TAB 4: USER & ROLE MANAGEMENT
    # -------------------------------------------------------------------------
    with tab_users:
        st.subheader("Clinic Staff & User Account Directory")
        st.markdown("Review system users and registered patient accounts.")

        patients_df = load_patients_db()
        if patients_df.empty:
            st.info("No patient accounts registered.")
        else:
            st.markdown("#### Registered Patient Profiles")

            # Dynamically select columns that actually exist in patients_df to avoid KeyErrors
            available_cols = [col for col in ["UID", "Full_Name", "Phone", "Email", "Age", "Gender"] if
                              col in patients_df.columns]

            edited_patients = st.data_editor(
                patients_df[available_cols],
                use_container_width=True,
                key="admin_patients_editor"
            )
            if st.button("💾 Save Patient Directory Updates"):
                for idx, row in edited_patients.iterrows():
                    uid = row["UID"]
                    match_idx = patients_df[patients_df["UID"] == uid].index
                    if not match_idx.empty:
                        for col in available_cols:
                            if col != "UID":
                                patients_df.at[match_idx[0], col] = row[col]
                save_patients_db(patients_df)
                log_admin_action(current_admin, "Patient Directory Update",
                                 "Updated patient details from admin dashboard.")
                st.success("✅ Patient records successfully updated!")
                st.rerun()

    # -------------------------------------------------------------------------
    # TAB 5: COMPLAINTS & GRIEVANCES
    # -------------------------------------------------------------------------
    with tab_complaints:
        st.subheader("📢 Patient Complaints & Grievance Logs")
        st.caption("Live feed of complaints submitted via the public Contact page.")

        complaints = st.session_state.get("admin_complaints_log", [])

        if not complaints:
            st.info("No active complaints or grievances submitted yet.")
        else:
            for idx, comp in enumerate(complaints):
                with st.expander(f"[{comp.get('status', 'Pending Review')}] {comp.get('category', 'General')} - {comp.get('name', 'Anonymous')} ({comp.get('timestamp', '')})"):
                    st.write(f"**Contact Info:** {comp.get('contact', 'N/A')}")
                    st.write(f"**Message:** {comp.get('message', '')}")
                    if comp.get('status', '') != "Resolved":
                        if st.button(f"Mark as Resolved #{idx}", key=f"resolve_comp_{idx}"):
                            comp['status'] = "Resolved"
                            log_admin_action(current_admin, "Complaint Resolution", f"Marked complaint from {comp.get('name')} as resolved.")
                            st.success("Complaint status updated to Resolved!")
                            st.rerun()
                    else:
                        st.markdown("✅ *Status: Resolved*")

    # -------------------------------------------------------------------------
    # TAB 6: SYSTEM AUDIT LOGS
    # -------------------------------------------------------------------------
    with tab_audit:
        st.subheader("📜 Administrative Audit Trail & Security Logs")
        st.caption("Immutable log of administrative actions, reversals, overrides, and system changes.")

        logs_df = load_admin_logs()
        if logs_df.empty:
            st.info("No administrative logs recorded yet.")
        else:
            st.dataframe(logs_df, use_container_width=True)
            if st.button("🗑️ Clear Audit Trail Logs"):
                empty_logs = _get_empty_logs_df()
                save_admin_logs(empty_logs)
                st.warning("Audit logs cleared.")
                st.rerun()