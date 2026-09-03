# modules/procedures.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
from modules.auth import check_role_access
from modules.database import load_patients_db
from modules.billings import render_staff_billing_verification_module
from modules.equipment_scheduler import (
    load_equipment_schedule_db,
    save_equipment_schedule_db,
    get_suggested_equipment,
    PROCEDURE_EQUIPMENT_MAP
)
from modules.notifications import add_notification

PROCEDURES_FILE = "procedures.txt"


def load_procedures_db():
    """Loads procedures from procedures.txt into session state with required schema columns."""
    if "procedures_db" not in st.session_state:
        if os.path.exists(PROCEDURES_FILE):
            try:
                st.session_state.procedures_db = pd.read_csv(PROCEDURES_FILE, sep="|")
                # Fill NaN/missing values across dataframe with empty strings first
                st.session_state.procedures_db = st.session_state.procedures_db.fillna("")

                # Ensure request tracking columns exist for migration/legacy files and are strings
                for col, default_val in [
                    ("Request_Status", "None"),
                    ("Requested_New_Date", ""),
                    ("Requested_New_Time", "")
                ]:
                    if col not in st.session_state.procedures_db.columns:
                        st.session_state.procedures_db[col] = default_val
                    st.session_state.procedures_db[col] = st.session_state.procedures_db[col].astype(str).replace(
                        ["nan", "None", ""], default_val)
            except Exception as e:
                st.error(f"Error loading {PROCEDURES_FILE}: {e}")
                st.session_state.procedures_db = _get_empty_procedures_df()
        else:
            df = _get_empty_procedures_df()
            save_procedures_db(df)
            st.session_state.procedures_db = df
    return st.session_state.procedures_db


def save_procedures_db(df):
    """Saves the current pandas DataFrame back to procedures.txt using pipe separation."""
    try:
        df.to_csv(PROCEDURES_FILE, sep="|", index=False)
        st.session_state.procedures_db = df
    except Exception as e:
        st.error(f"Error saving to {PROCEDURES_FILE}: {e}")


def _get_empty_procedures_df():
    """Returns an empty DataFrame with the required procedure schema headers."""
    headers = [
        "Procedure_ID", "Patient_UID", "Patient_Name", "Procedure_Name",
        "Performing_Doctor", "Date", "Time_Slot", "Status", "Clinical_Notes",
        "Request_Status", "Requested_New_Date", "Requested_New_Time"
    ]
    return pd.DataFrame(columns=headers)


def render_procedure_management_module():
    st.title("🩺 Clinical Procedure Management Desk")
    st.markdown(
        "Schedule, manage, and verify patient rescheduling or cancellation requests with automated suite locking.")

    # 1. Enforce Role Access: Only DOCTOR, STAFF, or ADMIN can manage/book procedures
    is_authorized_staff = check_role_access(["DOCTOR", "STAFF", "ADMIN"])
    is_patient = check_role_access(["PATIENT"])

    load_procedures_db()
    patients_df = load_patients_db()

    if is_authorized_staff:
        # ----------------------------------------------------
        # STAFF / DOCTOR VIEW: BOOK, VERIFY, & MANAGE PROCEDURES
        # ----------------------------------------------------
        tab_book, tab_requests, tab_manage, tab_billing = st.tabs([
            "➕ Schedule New Procedure",
            "🔔 Patient Requests (Verification)",
            "📋 Master Procedures Registry",
            "💳 Billing & Payments"
        ])

        with tab_book:
            st.subheader("Book a Clinical Procedure (Auto-Locks Required Suite)")

            if patients_df.empty:
                st.warning("⚠️ No patient records found. Please register patients before booking procedures.")
                return

            with st.form("procedure_booking_form"):
                patient_options = [f"{row['Full_Name']} ({row['UID']})" for _, row in patients_df.iterrows()]
                selected_patient_str = st.selectbox("Select Patient *", patient_options)

                procedure_name = st.selectbox(
                    "Procedure Type *",
                    list(PROCEDURE_EQUIPMENT_MAP.keys()) + [
                        "Minor Biopsy & Excision",
                        "Wound Suturing & Dressing",
                        "General Diagnostic Screening"
                    ]
                )

                doctor_choice = st.selectbox(
                    "Assigned Specialist / Doctor *",
                    [
                        "Dr. Sarah Jenkins (General Medicine)",
                        "Dr. Rajesh Rao (Dermatology)",
                        "Dr. Anita Sharma (Cardiology)",
                        "Nurse Priya (Senior Aesthetician)",
                        "Tech. Rahul (Laser Specialist)"
                    ]
                )

                col1, col2 = st.columns(2)
                with col1:
                    proc_date = st.date_input("Procedure Date *", min_value=date.today())
                with col2:
                    proc_time = st.selectbox("Time Slot *",
                                             ["09:30 AM - 10:30 AM", "10:30 AM - 11:30 AM", "11:30 AM - 12:30 PM",
                                              "02:00 PM - 03:00 PM", "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM"])

                clinical_notes = st.text_area("Clinical Notes / Pre-procedure Instructions",
                                              placeholder="Enter notes or special instructions for the procedure")

                submit_proc = st.form_submit_button("Confirm & Schedule Procedure", type="primary")

                if submit_proc:
                    patient_uid = selected_patient_str.split("(")[-1].strip(")")
                    patient_name = selected_patient_str.split("(")[0].strip()
                    date_str = proc_date.strftime("%Y-%m-%d")

                    # 1. Check Equipment/Suite Availability via Auto-Mapping
                    assigned_suite = get_suggested_equipment(procedure_name)
                    sched_df = load_equipment_schedule_db()

                    conflict_check = sched_df[
                        (sched_df["Resource_Name"] == assigned_suite) &
                        (sched_df["Date"] == date_str) &
                        (sched_df["Time_Slot"] == proc_time) &
                        (sched_df["Status"] == "Confirmed")
                        ]

                    if not conflict_check.empty:
                        st.error(
                            f"❌ **Suite Booking Conflict!** Required suite **'{assigned_suite}'** is already locked for **{date_str}** during **{proc_time}**.")
                    else:
                        # 2. Save Procedure Record
                        procs_df = st.session_state.procedures_db
                        next_id = 7001 if procs_df.empty else len(procs_df) + 7001
                        proc_id = f"PROC-{next_id}"

                        new_proc = {
                            "Procedure_ID": proc_id,
                            "Patient_UID": patient_uid,
                            "Patient_Name": patient_name,
                            "Procedure_Name": procedure_name,
                            "Performing_Doctor": doctor_choice,
                            "Date": date_str,
                            "Time_Slot": proc_time,
                            "Status": "Scheduled",
                            "Clinical_Notes": clinical_notes.strip() if clinical_notes else "None",
                            "Request_Status": "None",
                            "Requested_New_Date": "",
                            "Requested_New_Time": ""
                        }

                        new_row_df = pd.DataFrame([new_proc])
                        st.session_state.procedures_db = pd.concat([st.session_state.procedures_db, new_row_df],
                                                                   ignore_index=True)
                        save_procedures_db(st.session_state.procedures_db)

                        # 3. Automatically Lock Suite in Equipment Schedule
                        next_res_id = 9001 if sched_df.empty else len(sched_df) + 9001
                        auto_res_id = f"RES-{next_res_id}"

                        auto_resource_record = {
                            "Booking_ID": auto_res_id,
                            "Resource_Name": assigned_suite,
                            "Resource_Type": "Auto-Linked Suite",
                            "Patient_UID": patient_uid,
                            "Patient_Name": patient_name,
                            "Assigned_Staff": doctor_choice,
                            "Date": date_str,
                            "Time_Slot": proc_time,
                            "Status": "Confirmed"
                        }

                        updated_sched_df = pd.concat([sched_df, pd.DataFrame([auto_resource_record])],
                                                     ignore_index=True)
                        save_equipment_schedule_db(updated_sched_df)

                        st.success(
                            f"🎉 Procedure successfully scheduled (ID: **{proc_id}**) and suite **{assigned_suite}** automatically locked!")
                        st.balloons()

        with tab_requests:
            st.subheader("Pending Patient Modification / Cancellation Requests")
            df_procs = st.session_state.procedures_db

            if df_procs.empty or "Request_Status" not in df_procs.columns:
                pending_reqs = pd.DataFrame()
            else:
                pending_reqs = df_procs[
                    df_procs["Request_Status"].astype(str).isin(["Pending Reschedule", "Pending Cancellation"])]

            if pending_reqs.empty:
                st.info("No pending requests requiring staff verification at this time.")
            else:
                for idx, row in pending_reqs.iterrows():
                    with st.expander(
                            f"{row['Procedure_ID']} | {row['Patient_Name']} — Request: {row['Request_Status']}"):
                        st.write(f"**Procedure**: {row['Procedure_Name']}")
                        st.write(f"**Current Schedule**: {row['Date']} at {row['Time_Slot']}")

                        if row["Request_Status"] == "Pending Reschedule":
                            st.warning(
                                f"Requested New Date/Time: **{row['Requested_New_Date']}** at **{row['Requested_New_Time']}**")
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button("Approve Reschedule", key=f"app_res_{row['Procedure_ID']}"):
                                    df_procs.at[idx, "Date"] = row["Requested_New_Date"]
                                    df_procs.at[idx, "Time_Slot"] = row["Requested_New_Time"]
                                    df_procs.at[idx, "Status"] = "Rescheduled"
                                    df_procs.at[idx, "Request_Status"] = "Approved"
                                    df_procs.at[idx, "Requested_New_Date"] = ""
                                    df_procs.at[idx, "Requested_New_Time"] = ""
                                    save_procedures_db(df_procs)

                                    # Notify patient regarding approval
                                    add_notification(row["Patient_UID"], "Procedure",
                                                     f"Your reschedule request for procedure {row['Procedure_ID']} has been approved.")

                                    st.success("Rescheduling approved successfully!")
                                    st.rerun()
                            with col_b:
                                if st.button("Reject Request", key=f"rej_res_{row['Procedure_ID']}"):
                                    df_procs.at[idx, "Request_Status"] = "Rejected"
                                    df_procs.at[idx, "Requested_New_Date"] = ""
                                    df_procs.at[idx, "Requested_New_Time"] = ""
                                    save_procedures_db(df_procs)

                                    # Notify patient regarding rejection
                                    add_notification(row["Patient_UID"], "Procedure",
                                                     f"Your reschedule request for procedure {row['Procedure_ID']} was rejected by clinic staff.")

                                    st.info("Rescheduling request rejected.")
                                    st.rerun()

                        elif row["Request_Status"] == "Pending Cancellation":
                            st.error("Patient requested cancellation of this procedure.")
                            col_c, col_d = st.columns(2)
                            with col_c:
                                if st.button("Approve Cancellation", key=f"app_can_{row['Procedure_ID']}"):
                                    df_procs.at[idx, "Status"] = "Cancelled"
                                    df_procs.at[idx, "Request_Status"] = "Approved Cancellation"
                                    save_procedures_db(df_procs)

                                    # Notify patient regarding cancellation approval
                                    add_notification(row["Patient_UID"], "Procedure",
                                                     f"Your cancellation request for procedure {row['Procedure_ID']} has been approved.")

                                    st.success("Cancellation approved.")
                                    st.rerun()
                            with col_d:
                                if st.button("Reject Cancellation", key=f"rej_can_{row['Procedure_ID']}"):
                                    df_procs.at[idx, "Request_Status"] = "Rejected Cancellation"
                                    save_procedures_db(df_procs)

                                    # Notify patient regarding cancellation rejection
                                    add_notification(row["Patient_UID"], "Procedure",
                                                     f"Your cancellation request for procedure {row['Procedure_ID']} was rejected by clinic staff.")

                                    st.info("Cancellation request rejected.")
                                    st.rerun()

        with tab_manage:
            st.subheader("All Scheduled Clinic Procedures")
            df_procs = st.session_state.procedures_db

            if df_procs.empty:
                st.info("No procedures currently recorded in the system.")
            else:
                edited_procs = st.data_editor(
                    df_procs,
                    use_container_width=True,
                    num_rows="dynamic",
                    key="procedures_master_editor"
                )
                if st.button("💾 Save Changes to Registry", type="secondary"):
                    save_procedures_db(edited_procs)
                    st.success("✅ Procedure registry successfully updated and saved!")
                    st.rerun()

        with tab_billing:
            render_staff_billing_verification_module()

    elif is_patient:
        # ----------------------------------------------------
        # PATIENT VIEW: VIEW PROCEDURES & SUBMIT REQUESTS
        # ----------------------------------------------------
        st.subheader("Your Assigned Medical Procedures")
        st.caption(
            "Review procedures, timelines, and submit date/time change or cancellation requests for staff verification.")

        current_username = st.session_state.get("current_username", "")
        current_user_id = st.session_state.get("patient_uid", "")

        df_procs = st.session_state.procedures_db

        if df_procs.empty:
            st.info("You have no procedures currently scheduled.")
        else:
            my_procs = pd.DataFrame()
            if "Patient_UID" in df_procs.columns and current_user_id:
                my_procs = df_procs[df_procs["Patient_UID"] == current_user_id]
            if my_procs.empty and current_username:
                my_procs = df_procs[df_procs["Patient_Name"].str.lower() == current_username.lower()]

            if my_procs.empty:
                st.info("No procedures found under your profile registry.")
            else:
                for idx, row in my_procs.iterrows():
                    with st.expander(f"{row['Procedure_Name']} — {row['Date']} ({row['Status']})"):
                        st.write(f"**Procedure ID**: `{row['Procedure_ID']}`")
                        st.write(f"**Performing Specialist**: {row['Performing_Doctor']}")
                        st.write(f"**Current Time Slot**: {row['Time_Slot']}")
                        st.write(f"**Clinical Notes**: {row['Clinical_Notes']}")
                        st.write(f"**Status**: `{row['Status']}`")

                        req_status = str(row.get("Request_Status", "None"))
                        if req_status in ["Pending Reschedule", "Pending Cancellation"]:
                            st.info(f"⏳ Status of Request: **{req_status}** (Awaiting staff verification)")

                        st.markdown("---")
                        st.markdown("#### Request Modification or Cancellation")

                        action_type = st.radio(
                            "Select Action",
                            ["None", "Reschedule Date/Time", "Cancel Procedure"],
                            key=f"action_{row['Procedure_ID']}"
                        )

                        if action_type == "Reschedule Date/Time":
                            with st.form(key=f"form_resched_{row['Procedure_ID']}"):
                                new_date = st.date_input("New Proposed Date", min_value=date.today())
                                new_time = st.selectbox("New Proposed Time Slot",
                                                        ["09:30 AM - 10:30 AM", "10:30 AM - 11:30 AM",
                                                         "11:30 AM - 12:30 PM",
                                                         "02:00 PM - 03:00 PM", "03:00 PM - 04:00 PM",
                                                         "04:00 PM - 05:00 PM"])
                                submit_res = st.form_submit_button("Submit Reschedule Request")

                                if submit_res:
                                    target_idx = df_procs[df_procs["Procedure_ID"] == row["Procedure_ID"]].index
                                    if not target_idx.empty:
                                        df_procs.at[target_idx[0], "Request_Status"] = "Pending Reschedule"
                                        df_procs.at[target_idx[0], "Requested_New_Date"] = new_date.strftime("%Y-%m-%d")
                                        df_procs.at[target_idx[0], "Requested_New_Time"] = new_time
                                        save_procedures_db(df_procs)

                                        # Notify staff regarding reschedule request
                                        add_notification("STAFF", "Procedure",
                                                         f"Reschedule request for procedure {row['Procedure_ID']} by {row.get('Patient_Name', 'Patient')}.")

                                        st.success("✅ Reschedule request sent to clinic staff for verification!")
                                        st.rerun()

                        elif action_type == "Cancel Procedure":
                            with st.form(key=f"form_cancel_{row['Procedure_ID']}"):
                                st.warning("Are you sure you want to request cancellation of this procedure?")
                                submit_can = st.form_submit_button("Submit Cancellation Request")

                                if submit_can:
                                    target_idx = df_procs[df_procs["Procedure_ID"] == row["Procedure_ID"]].index
                                    if not target_idx.empty:
                                        df_procs.at[target_idx[0], "Request_Status"] = "Pending Cancellation"
                                        save_procedures_db(df_procs)

                                        # Notify staff regarding cancellation request
                                        add_notification("STAFF", "Procedure",
                                                         f"Cancellation request for procedure {row['Procedure_ID']} by {row.get('Patient_Name', 'Patient')}.")

                                        st.success("✅ Cancellation request sent to clinic staff for verification!")
                                        st.rerun()
    else:
        st.error("❌ Access Denied: Unauthorized role context.")