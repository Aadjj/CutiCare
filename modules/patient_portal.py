# modules/patient_portal.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from modules.auth import check_role_access
from modules.database import load_patients_db
from modules.billings import render_patient_billing_tab
from modules.notifications import add_notification
import os

PROCEDURES_FILE = "procedures.txt"
UPLOAD_DIR = "uploaded_reports"


def ensure_upload_dir():
    """Ensures the temporary upload folder exists."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)


def load_procedures_for_patient():
    """Loads procedures from procedures.txt if available."""
    if os.path.exists(PROCEDURES_FILE):
        try:
            df = pd.read_csv(PROCEDURES_FILE, sep="|")

            # Fill all NaN/missing values across the dataframe with empty strings first
            df = df.fillna("")

            # Ensure columns exist and are explicitly cast to string to prevent dtype/NaN errors
            for col, default_val in [
                ("Request_Status", "None"),
                ("Requested_New_Date", ""),
                ("Requested_New_Time", "")
            ]:
                if col not in df.columns:
                    df[col] = default_val
                df[col] = df[col].astype(str).replace(["nan", "None", ""], default_val)

            return df
        except Exception:
            pass

    return pd.DataFrame(
        columns=["Procedure_ID", "Patient_UID", "Patient_Name", "Procedure_Name", "Performing_Doctor", "Date",
                 "Time_Slot", "Status", "Clinical_Notes", "Request_Status", "Requested_New_Date", "Requested_New_Time"])


def save_procedures_for_patient(df):
    """Saves updated procedures back to procedures.txt."""
    try:
        df.to_csv(PROCEDURES_FILE, sep="|", index=False)
    except Exception as e:
        st.error(f"Error saving procedure updates: {e}")


def render_patient_portal_module():
    st.title("👤 Cuticare Patient Health Portal")
    st.caption(
        "Personal Health Records, Appointment Booking & Management, Prescriptions, Procedures, Report Uploader & Billings")

    ensure_upload_dir()

    # 1. Enforce Role-Based Access Control (RBAC)
    if not check_role_access(["PATIENT", "ADMIN"]):
        st.error("❌ Access Denied: The Patient Health Portal is reserved for patients.")
        return

    current_username = st.session_state.get("current_username", "Valued Patient")
    current_user_id = st.session_state.get("patient_uid", "")

    # Ensure patient database is loaded to find exact UIDs
    load_patients_db()

    # Resolve exact patient UID and Name from registry if available
    patient_uid = current_user_id
    patient_full_name = current_username
    patient_record = None

    if "patients_db" in st.session_state and not st.session_state.patients_db.empty:
        df_pat = st.session_state.patients_db
        matched = pd.DataFrame()
        if current_user_id:
            matched = df_pat[df_pat["UID"] == current_user_id]
        if matched.empty and current_username:
            matched = df_pat[df_pat["Full_Name"].str.lower() == current_username.lower()]

        if not matched.empty:
            patient_record = matched.iloc[0]
            patient_uid = patient_record["UID"]
            patient_full_name = patient_record["Full_Name"]

    # Ensure required databases exist in session state
    if "appointments_db" not in st.session_state:
        st.session_state.appointments_db = pd.DataFrame(columns=[
            "Appt_ID", "Patient_UID", "Patient_Name", "Consultant", "Date", "Time_Slot", "Classification", "Status"
        ])

    if "prescriptions_db" not in st.session_state:
        st.session_state.prescriptions_db = pd.DataFrame(columns=[
            "Rx_ID", "Patient_UID", "Patient_Name", "Doctor_Name",
            "Medication_Details", "Instructions", "Dispense_Status", "Timestamp"
        ])

    if "lab_reports_db" not in st.session_state:
        st.session_state.lab_reports_db = pd.DataFrame(columns=[
            "Report_ID", "Patient_UID", "Patient_Name", "Test_Name",
            "File_Name", "Uploaded_By", "Status", "Timestamp"
        ])

    # ----------------------------------------------------
    # TABS SETUP
    # ----------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 Medical Profile",
        "🗓️ Book Appointment",
        "📅 My Scheduled Visits",
        "📌 Clinic Schedule",
        "💊 My Prescriptions",
        "🩺 My Procedures",
        "📂 Diagnostic Reports",
        "💳 Billing & Payments"
    ])

    # ----------------------------------------------------
    # TAB 1: MEDICAL PROFILE & HISTORY OVERVIEW
    # ----------------------------------------------------
    with tab1:
        st.subheader("Your Personal & Clinical Overview")
        if patient_record is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Full Name", value=patient_record["Full_Name"], disabled=True)
                st.text_input("Date of Birth", value=str(patient_record["DOB"]).split(" ")[0], disabled=True)
                st.text_input("Gender", value=patient_record["Gender"], disabled=True)
                st.text_input("Contact Number", value=patient_record["Contact_Number"], disabled=True)
                st.text_input("Email", value=patient_record["Email"], disabled=True)

            with col2:
                st.text_area("Residential Address", value=patient_record["Address"], disabled=True)
                st.text_input("Emergency Contact", value=patient_record["Emergency_Contact"], disabled=True)
                st.text_input("Known Allergies", value=patient_record["Allergies"], disabled=True)
                st.text_input("Pre-existing Conditions", value=patient_record["Pre_existing_Conditions"], disabled=True)
        else:
            st.info("Detailed profile record not located in database registry.")

    # ----------------------------------------------------
    # TAB 2: BOOK NEW APPOINTMENT (CLIENT REQUEST)
    # ----------------------------------------------------
    with tab2:
        st.subheader("Schedule an Appointment with a Doctor")
        st.caption("Select your preferred consultant, date, time slot, and reason for visit.")

        with st.form("patient_self_booking_form"):
            doctor_choice = st.selectbox(
                "Select Doctor / Specialist *",
                [
                    "Dr. Sarah Jenkins (General Medicine)",
                    "Dr. Rajesh Rao (Dermatology)",
                    "Dr. Anita Sharma (Cardiology)"
                ]
            )

            appt_date = st.date_input("Preferred Appointment Date *", min_value=date.today())
            appt_time = st.selectbox("Preferred Time Slot *",
                                     ["09:30 AM", "10:30 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"])
            reason = st.text_area("Reason for Visit / Symptoms *",
                                  placeholder="Briefly describe your symptoms or reason for consultation")

            submit_booking = st.form_submit_button("Confirm & Book Appointment", type="primary")

            if submit_booking:
                if not reason.strip():
                    st.error("Please provide a reason for your visit.")
                else:
                    appts_df = st.session_state.appointments_db
                    active_uid = patient_uid if patient_uid else "PAT-SELF"
                    date_str = appt_date.strftime("%Y-%m-%d")

                    # Check for existing active bookings on the same date and time slot for this patient
                    duplicate_check = False
                    if not appts_df.empty:
                        matched_existing = appts_df[
                            (appts_df["Patient_UID"] == active_uid) &
                            (appts_df["Date"] == date_str) &
                            (appts_df["Time_Slot"] == appt_time) &
                            (appts_df["Status"].isin(["Scheduled", "Pending"]))
                        ]
                        if not matched_existing.empty:
                            duplicate_check = True

                    if duplicate_check:
                        st.error(f"❌ You already have an active appointment scheduled on **{date_str}** at **{appt_time}**. Please select a different date or time slot.")
                    else:
                        next_id = 5001 if appts_df.empty else len(appts_df) + 5001
                        appt_id = f"APT-{next_id}"

                        new_appt = {
                            "Appt_ID": appt_id,
                            "Patient_UID": active_uid,
                            "Patient_Name": patient_full_name,
                            "Consultant": doctor_choice,
                            "Date": date_str,
                            "Time_Slot": appt_time,
                            "Classification": "Consultation",
                            "Status": "Scheduled",
                            "Notes": reason.strip()
                        }

                        new_row = pd.DataFrame([new_appt])
                        st.session_state.appointments_db = pd.concat([appts_df, new_row], ignore_index=True)

                        # Notify staff regarding the new appointment booked by the patient
                        add_notification("STAFF", "Appointment",
                                         f"New self-booked appointment for {patient_full_name} with {doctor_choice} on {date_str}.")

                        st.success(f"🎉 Appointment successfully booked! Reference ID: **{appt_id}**")
                        st.balloons()

    # ----------------------------------------------------
    # TAB 3: PERSONAL SCHEDULED VISITS
    # ----------------------------------------------------
    with tab3:
        st.subheader(f"Scheduled Encounters for {patient_full_name}")

        appointments_df = st.session_state.appointments_db
        if appointments_df.empty:
            st.info("You currently have no scheduled appointments on file.")
        else:
            if "Patient_UID" in appointments_df.columns and patient_uid:
                my_appts = appointments_df[appointments_df["Patient_UID"] == patient_uid]
            else:
                my_appts = appointments_df[
                    appointments_df["Patient_Name"].str.contains(patient_full_name, case=False, na=False)
                ]

            if my_appts.empty:
                st.info(
                    "No personal appointments matched your profile. You can book an appointment using the 'Book Appointment' tab.")
            else:
                st.dataframe(my_appts, use_container_width=True)

    # ----------------------------------------------------
    # TAB 4: CLINIC-WIDE SCHEDULE OVERVIEW (VIEW-ONLY)
    # ----------------------------------------------------
    with tab4:
        st.subheader("General Clinic Consultation Schedule")
        st.caption("View available consultation timelines across providers.")

        if st.session_state.appointments_db.empty:
            st.info("No clinic bookings recorded in the system.")
        else:
            cols_to_show = [c for c in ["Appt_ID", "Consultant", "Date", "Time_Slot", "Classification", "Status"] if
                            c in st.session_state.appointments_db.columns]
            st.dataframe(
                st.session_state.appointments_db[cols_to_show],
                use_container_width=True
            )

    # ----------------------------------------------------
    # TAB 5: E-PRESCRIPTIONS & MEDICATIONS
    # ----------------------------------------------------
    with tab5:
        st.subheader("Your Active Prescriptions & Dosage Plans")

        prescriptions_df = st.session_state.prescriptions_db
        if prescriptions_df.empty:
            st.info("No active e-prescriptions on record.")
        else:
            if "Patient_UID" in prescriptions_df.columns and patient_uid:
                my_rxs = prescriptions_df[prescriptions_df["Patient_UID"] == patient_uid]
            else:
                my_rxs = prescriptions_df[
                    prescriptions_df["Patient_Name"].str.contains(patient_full_name, case=False, na=False)
                ]

            if my_rxs.empty:
                st.info("No prescriptions recorded under your name.")
            else:
                for idx, rx in my_rxs.iterrows():
                    with st.expander(
                            f"Prescription #{rx.get('Rx_ID', 'N/A')} — Issued by {rx.get('Doctor_Name', 'Doctor')} ({rx.get('Timestamp', '')})"):
                        st.write(f"**Medication**: {rx.get('Medication_Details', 'N/A')}")
                        st.write(f"**Instructions**: {rx.get('Instructions', 'N/A')}")
                        st.write(f"**Status**: `{rx.get('Dispense_Status', 'Active')}`")

    # ----------------------------------------------------
    # TAB 6: MY PROCEDURES (ASSIGNED PROCEDURES & REQUESTS)
    # ----------------------------------------------------
    with tab6:
        st.subheader("Your Assigned Medical & Clinical Procedures")
        st.caption(
            "Review procedures, timelines, and submit date/time change or cancellation requests for staff verification.")

        procs_df = load_procedures_for_patient()

        if procs_df.empty:
            st.info("No procedures currently recorded in the clinic registry.")
        else:
            my_procs = pd.DataFrame()
            if "Patient_UID" in procs_df.columns and patient_uid:
                my_procs = procs_df[procs_df["Patient_UID"] == patient_uid]
            if my_procs.empty and patient_full_name:
                my_procs = procs_df[procs_df["Patient_Name"].str.lower() == patient_full_name.lower()]

            if my_procs.empty:
                st.info("You have no procedures currently assigned to your profile.")
            else:
                for idx, row in my_procs.iterrows():
                    proc_id = row['Procedure_ID']
                    with st.expander(f"{row['Procedure_Name']} — {row['Date']} ({row['Status']})"):
                        st.write(f"**Procedure ID**: `{proc_id}`")
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
                            key=f"action_{proc_id}_{idx}"
                        )

                        if action_type == "Reschedule Date/Time":
                            with st.form(key=f"form_resched_{proc_id}_{idx}"):
                                new_date = st.date_input("New Proposed Date", min_value=date.today())
                                new_time = st.selectbox("New Proposed Time Slot",
                                                        ["10:00 AM", "11:30 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                                submit_res = st.form_submit_button("Submit Reschedule Request")

                                if submit_res:
                                    full_df = load_procedures_for_patient()
                                    target_idx = full_df[full_df["Procedure_ID"] == proc_id].index
                                    if not target_idx.empty:
                                        full_df.at[target_idx[0], "Request_Status"] = "Pending Reschedule"
                                        full_df.at[target_idx[0], "Requested_New_Date"] = new_date.strftime("%Y-%m-%d")
                                        full_df.at[target_idx[0], "Requested_New_Time"] = new_time
                                        save_procedures_for_patient(full_df)

                                        # Notify staff regarding reschedule request
                                        add_notification("STAFF", "Procedure",
                                                         f"Reschedule request for procedure {proc_id} by {patient_full_name}.")

                                        st.success("✅ Reschedule request sent to clinic staff for verification!")
                                        st.rerun()

                        elif action_type == "Cancel Procedure":
                            with st.form(key=f"form_cancel_{proc_id}_{idx}"):
                                st.warning("Are you sure you want to request cancellation of this procedure?")
                                submit_can = st.form_submit_button("Submit Cancellation Request")

                                if submit_can:
                                    full_df = load_procedures_for_patient()
                                    target_idx = full_df[full_df["Procedure_ID"] == proc_id].index
                                    if not target_idx.empty:
                                        full_df.at[target_idx[0], "Request_Status"] = "Pending Cancellation"
                                        save_procedures_for_patient(full_df)

                                        # Notify staff regarding cancellation request
                                        add_notification("STAFF", "Procedure",
                                                         f"Cancellation request for procedure {proc_id} by {patient_full_name}.")

                                        st.success("✅ Cancellation request sent to clinic staff for verification!")
                                        st.rerun()

    # ----------------------------------------------------
    # TAB 7: MEDICAL REPORTS & FILE UPLOADER
    # ----------------------------------------------------
    with tab7:
        st.subheader("Upload Personal Health Reports & View Lab Results")
        st.caption(
            "Documents uploaded here are immediately available to your attending physician and clinical team.")

        with st.form("patient_upload_form", clear_on_submit=True):
            report_title = st.text_input("Document / Report Title *",
                                         placeholder="e.g. Previous Dermatology Records / Blood Test")
            uploaded_file = st.file_uploader("Upload File (PDF or Image):", type=["pdf", "png", "jpg", "jpeg"])

            submit_upload = st.form_submit_button("Upload File to Medical History", type="primary")

            if submit_upload:
                if not report_title.strip():
                    st.error("Please specify a document title.")
                else:
                    rpt_id = f"RPT-{100 + len(st.session_state.lab_reports_db) + 1}"
                    active_uid = patient_uid if patient_uid else "PAT-SELF"

                    # Immediately tie uploaded file to patient ID in UPLOAD_DIR
                    if uploaded_file is not None:
                        orig_name = uploaded_file.name.replace(" ", "_")
                        file_name = f"{active_uid}_{orig_name}"
                        file_path = os.path.join(UPLOAD_DIR, file_name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    else:
                        file_name = f"{active_uid}_Patient_Uploaded_Document.txt"
                        file_path = os.path.join(UPLOAD_DIR, file_name)
                        with open(file_path, "w") as f:
                            f.write(f"Report Title: {report_title}\nUploaded by: {patient_full_name}")

                    new_rpt = {
                        "Report_ID": rpt_id,
                        "Patient_UID": active_uid,
                        "Patient_Name": patient_full_name,
                        "Test_Name": report_title.strip(),
                        "File_Name": file_name,
                        "Uploaded_By": f"Patient ({patient_full_name})",
                        "Status": "Uploaded by Patient",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    st.session_state.lab_reports_db = pd.concat([
                        st.session_state.lab_reports_db,
                        pd.DataFrame([new_rpt])
                    ], ignore_index=True)

                    # Notify staff regarding document upload
                    add_notification("STAFF", "Report",
                                     f"New medical report uploaded by patient {patient_full_name}: {report_title}.")

                    st.success(f"✅ Report `{rpt_id}` successfully uploaded and tied to ID `{active_uid}`!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### Your Document Repository & File Inspector")

        reports_df = st.session_state.lab_reports_db
        if reports_df.empty:
            my_docs = pd.DataFrame()
        else:
            if "Patient_UID" in reports_df.columns and patient_uid:
                my_docs = reports_df[reports_df["Patient_UID"] == patient_uid]
            else:
                my_docs = reports_df[
                    reports_df["Patient_Name"].str.contains(patient_full_name, case=False, na=False)
                ]

        if my_docs.empty:
            st.info("No documents or diagnostic reports uploaded yet.")
        else:
            st.dataframe(my_docs, use_container_width=True)

            # Direct file preview/download section for the patient
            st.markdown("#### 📁 View / Download Your Uploaded Files")
            target_uid = patient_uid if patient_uid else "PAT-SELF"
            if os.path.exists(UPLOAD_DIR):
                all_files = os.listdir(UPLOAD_DIR)
                patient_files = [f for f in all_files if f.startswith(f"{target_uid}_")]

                if not patient_files:
                    st.info("No files found in temporary storage directory.")
                else:
                    for fname in patient_files:
                        display_name = fname.replace(f"{target_uid}_", "")
                        fpath = os.path.join(UPLOAD_DIR, fname)

                        with st.container():
                            st.markdown(f"📄 **File:** `{display_name}`")
                            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                                st.image(fpath, caption=f"Uploaded Scan - {patient_full_name}", width=400)
                            else:
                                with open(fpath, "rb") as file_download:
                                    st.download_button(
                                        label=f"Download / View {display_name}",
                                        data=file_download,
                                        file_name=display_name,
                                        mime="application/octet-stream",
                                        key=f"patient_portal_view_{fname}"
                                    )
                            st.markdown("---")

    # ----------------------------------------------------
    # TAB 8: BILLING & PAYMENTS
    # ----------------------------------------------------
    with tab8:
        render_patient_billing_tab(patient_uid, patient_full_name)