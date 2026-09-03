# modules/scheduler.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from modules.auth import check_role_access
from modules.database import load_patients_db
from modules.notifications import add_notification


def init_scheduler_state():
    """Ensures the appointment database session state is permanently initialized once."""
    if "appointments_df" not in st.session_state or not isinstance(st.session_state.appointments_df, pd.DataFrame):
        st.session_state.appointments_df = pd.DataFrame(columns=[
            "Appt_ID", "Patient_UID", "Patient_Name", "Consultant",
            "Date", "Time_Slot", "Classification", "Status", "Booked_On"
        ])
    if "last_booking_hash" not in st.session_state:
        st.session_state.last_booking_hash = ""


def load_appointments_db():
    """Loads appointments safely from session cache."""
    init_scheduler_state()
    return st.session_state.appointments_df


def save_appointments_db(df):
    """Saves appointments DataFrame securely to session cache."""
    st.session_state.appointments_df = df


def check_appointment_conflict(target_uid, consultant, appt_date, time_slot, current_role):
    """
    Validates booking rules:
    1. No patient can book an appointment at the same time, same doc, or same date.
    2. Patients cannot book an appointment within 1 week of an existing active booking. Staff are exempt.
    """
    df = load_appointments_db()

    target_uid = str(target_uid).strip().lower()
    target_consultant = str(consultant).strip().lower()
    target_date_obj = appt_date if isinstance(appt_date, date) else datetime.strptime(str(appt_date), "%Y-%m-%d").date()
    target_slot = str(time_slot).strip().lower()
    is_patient = str(current_role).strip().upper() == "PATIENT"

    if not df.empty:
        for _, row in df.iterrows():
            status = str(row.get("Status", "")).strip().lower()
            if status not in ["scheduled", "in consultation"]:
                continue

            db_uid = str(row.get("Patient_UID", "")).strip().lower()
            db_consultant = str(row.get("Consultant", "")).strip().lower()
            db_date_str = str(row.get("Date", "")).strip()
            db_slot = str(row.get("Time_Slot", "")).strip().lower()

            try:
                db_date_obj = datetime.strptime(db_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            # 1. Exact Duplicate Check (Same Patient, Same Doctor, Same Date, Same Slot)
            if db_uid == target_uid and db_consultant == target_consultant and db_date_obj == target_date_obj and db_slot == target_slot:
                return True, f"Duplicate Booking Error: You already have an identical appointment booked with {consultant} for {time_slot} on {appt_date}."

            # 2. Doctor Double-Booking Check (Applies to everyone)
            if db_consultant == target_consultant and db_date_obj == target_date_obj and db_slot == target_slot:
                return True, f"Conflict: Consultant {consultant} is already booked for {time_slot} on {appt_date}."

            # 3. Patient Time Collision Check (Same time, different doctor)
            if is_patient and db_uid == target_uid and db_date_obj == target_date_obj and db_slot == target_slot:
                return True, f"Conflict: You already have an active appointment during {time_slot} on {appt_date}."

    # 4. Patient 1-Week Restriction Rule
    if is_patient and not df.empty:
        patient_appts = df[(df["Patient_UID"].astype(str).str.lower() == target_uid) & (
            df["Status"].astype(str).str.lower().isin(["scheduled", "in consultation"]))]

        for _, row in patient_appts.iterrows():
            try:
                existing_date = datetime.strptime(str(row["Date"]), "%Y-%m-%d").date()
                one_week_limit = existing_date + timedelta(days=7)

                if target_date_obj < one_week_limit:
                    formatted_limit = one_week_limit.strftime("%d/%m/%Y")
                    formatted_existing = existing_date.strftime("%d/%m/%Y")
                    return True, f"Restriction Notice: Because of your active appointment on {formatted_existing}, your next appointment can only be booked from **{formatted_limit}** onwards (1 week required between bookings)."
            except ValueError:
                continue

    return False, ""


def render_scheduler_module():
    init_scheduler_state()

    st.title("🗓️ Cuticare Clinic Scheduler & Appointment Desk")
    st.caption("Universal Consultant Slot Booking, Daily Appointment Rosters & Visit Management")

    if not check_role_access(["PATIENT", "STAFF", "DOCTOR", "ADMIN"]):
        st.error("❌ Access Denied: You do not have authorization to manage appointments.")
        return

    load_patients_db()

    if "patients_db" not in st.session_state or st.session_state.patients_db.empty:
        st.warning("⚠️ No registered patients found. Please onboard a patient in the Registration module first.")
        return

    current_role = st.session_state.get("current_role", "").upper()
    current_username = st.session_state.get("current_username", "")
    current_user_id = st.session_state.get("patient_uid", "")

    doctor_list = [
        "Dr. Sarah Jenkins (Dermatology)",
        "Dr. Rajesh Kumar (Cosmetology)",
        "Dr. Anita Roy (Trichology & Hair Loss)",
        "Dr. Suresh Menon (Pediatric Dermatology)"
    ]

    # ----------------------------------------------------
    # PATIENT PORTAL VIEW
    # ----------------------------------------------------
    if current_role == "PATIENT":
        st.subheader("👤 Patient Appointment Portal")

        patients_df = st.session_state.patients_db
        matched_patient = pd.DataFrame()

        if current_user_id:
            matched_patient = patients_df[patients_df["UID"] == current_user_id]

        if matched_patient.empty and current_username:
            matched_patient = patients_df[patients_df["Full_Name"].str.lower() == current_username.lower()]

        if not matched_patient.empty:
            patient_uid = matched_patient.iloc[0]["UID"]
            patient_name = matched_patient.iloc[0]["Full_Name"]
        else:
            patient_uid = patients_df.iloc[0]["UID"] if not patients_df.empty else "PAT-1001"
            patient_name = patients_df.iloc[0]["Full_Name"] if not patients_df.empty else (
                        current_username or "Valued Patient")

        tab_p1, tab_p2 = st.tabs(["📅 Book My Appointment", "📋 My Scheduled Visits"])

        with tab_p1:
            st.markdown("### Schedule Your Next Clinic Visit")

            consultant = st.selectbox("Select Attending Consultant *", doctor_list, key="pat_consultant")
            appt_date = st.date_input("Preferred Date *", min_value=date.today(), value=date.today(), key="pat_date")

            time_slots = [
                "09:00 AM - 09:30 AM", "09:30 AM - 10:00 AM",
                "10:00 AM - 10:30 AM", "10:30 AM - 11:00 AM",
                "11:30 AM - 12:00 PM", "12:00 PM - 12:30 PM",
                "02:00 PM - 02:30 PM", "02:30 PM - 03:00 PM",
                "04:00 PM - 04:30 PM", "04:30 PM - 05:00 PM"
            ]
            time_slot = st.selectbox("Preferred Time Slot *", time_slots, key="pat_timeslot")

            classification = st.selectbox("Visit Classification", [
                "Initial Consultation",
                "Follow-up Visit",
                "Minor Procedure / Chemical Peel",
                "Laser Therapy Session"
            ], key="pat_classification")

            if st.button("Confirm Booking", type="primary", key="pat_submit_btn"):
                # Create a unique hash for this exact submission attempt to block double-clicks
                current_hash = f"{patient_uid}_{consultant}_{appt_date}_{time_slot}"
                if st.session_state.last_booking_hash == current_hash:
                    st.warning("⚠️ This appointment has already been processed.")
                else:
                    has_conflict, error_msg = check_appointment_conflict(patient_uid, consultant, appt_date, time_slot,
                                                                         current_role)

                    if has_conflict:
                        st.error(f"❌ **Booking Blocked**: {error_msg}")
                    else:
                        st.session_state.last_booking_hash = current_hash
                        df_cache = load_appointments_db()
                        new_appt_id = f"APT-{101 + len(df_cache)}"
                        new_row = {
                            "Appt_ID": str(new_appt_id),
                            "Patient_UID": str(patient_uid),
                            "Patient_Name": str(patient_name),
                            "Consultant": str(consultant),
                            "Date": str(appt_date),
                            "Time_Slot": str(time_slot),
                            "Classification": str(classification),
                            "Status": "Scheduled",
                            "Booked_On": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        updated_df = pd.concat([df_cache, pd.DataFrame([new_row])], ignore_index=True)
                        save_appointments_db(updated_df)
                        add_notification("ALL", "Scheduler",
                                         f"New appointment booked: #{new_appt_id} for {patient_name} with {consultant} on {appt_date} at {time_slot}.")

                        st.success(f"🎉 Appointment ticket **{new_appt_id}** successfully booked with **{consultant}**!")
                        st.balloons()
                        st.rerun()

        with tab_p2:
            st.markdown("### Your Appointment History & Status")
            df_cache = load_appointments_db()
            my_appts = df_cache[df_cache["Patient_UID"] == patient_uid] if not df_cache.empty else pd.DataFrame()

            if my_appts.empty:
                st.info("You have no clinic bookings recorded in the session.")
            else:
                st.dataframe(my_appts, use_container_width=True)
                active_appts = my_appts[my_appts["Status"] == "Scheduled"]["Appt_ID"].tolist()
                if active_appts:
                    st.markdown("---")
                    cancel_id = st.selectbox("Select Appointment to Cancel", active_appts, key="pat_cancel_select")
                    if st.button("Cancel Selected Appointment", type="secondary", key="pat_cancel_btn"):
                        df_cache.loc[df_cache["Appt_ID"] == cancel_id, "Status"] = "Cancelled"
                        save_appointments_db(df_cache)
                        add_notification("ALL", "Scheduler",
                                         f"Appointment #{cancel_id} was cancelled by patient {patient_name}.")
                        st.success(f"Appointment {cancel_id} has been cancelled.")
                        st.rerun()
        return

    # ----------------------------------------------------
    # STAFF / DOCTOR / ADMIN VIEW
    # ----------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "📅 Book New Appointment",
        "📋 Master Daily Roster",
        "⚙️ Manage & Update Status"
    ])

    with tab1:
        st.subheader("Schedule Consultant Encounter")
        col1, col2 = st.columns(2)

        with col1:
            patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()
            selected_uid = st.selectbox(
                "Select Patient *",
                options=list(patient_map.keys()),
                format_func=lambda x: f"{x} - {patient_map[x]}",
                key="staff_selected_uid"
            )
            consultant = st.selectbox("Attending Consultant *", doctor_list, key="staff_consultant")
            appt_date = st.date_input("Appointment Date *", min_value=date.today(), value=date.today(),
                                      key="staff_date")

        with col2:
            time_slots = [
                "09:00 AM - 09:30 AM", "09:30 AM - 10:00 AM",
                "10:00 AM - 10:30 AM", "10:30 AM - 11:00 AM",
                "11:30 AM - 12:00 PM", "12:00 PM - 12:30 PM",
                "02:00 PM - 02:30 PM", "02:30 PM - 03:00 PM",
                "04:00 PM - 04:30 PM", "04:30 PM - 05:00 PM"
            ]
            time_slot = st.selectbox("Preferred Time Slot *", time_slots, key="staff_timeslot")
            classification = st.selectbox("Visit Classification", [
                "Initial Consultation",
                "Follow-up Visit",
                "Minor Procedure / Chemical Peel",
                "Laser Therapy Session",
                "Biopsy / Lab Sample Collection"
            ], key="staff_classification")

        st.markdown("---")
        if st.button("Confirm Booking & Issue Appointment Ticket", type="primary", key="staff_submit_booking"):
            current_hash = f"{selected_uid}_{consultant}_{appt_date}_{time_slot}"
            if st.session_state.last_booking_hash == current_hash:
                st.warning("⚠️ This appointment has already been processed.")
            else:
                has_conflict, error_msg = check_appointment_conflict(selected_uid, consultant, appt_date, time_slot,
                                                                     current_role)

                if has_conflict:
                    st.error(f"❌ **Booking Blocked**: {error_msg}")
                else:
                    st.session_state.last_booking_hash = current_hash
                    df_cache = load_appointments_db()
                    patient_row = st.session_state.patients_db[st.session_state.patients_db["UID"] == selected_uid]
                    patient_name = patient_row["Full_Name"].values[0] if not patient_row.empty else "Unknown Patient"

                    new_appt_id = f"APT-{101 + len(df_cache)}"
                    new_row = {
                        "Appt_ID": str(new_appt_id),
                        "Patient_UID": str(selected_uid),
                        "Patient_Name": str(patient_name),
                        "Consultant": str(consultant),
                        "Date": str(appt_date),
                        "Time_Slot": str(time_slot),
                        "Classification": str(classification),
                        "Status": "Scheduled",
                        "Booked_On": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    updated_df = pd.concat([df_cache, pd.DataFrame([new_row])], ignore_index=True)
                    save_appointments_db(updated_df)
                    add_notification("ALL", "Scheduler",
                                     f"New appointment booked by staff: #{new_appt_id} for {patient_name} with {consultant} on {appt_date} at {time_slot}.")
                    add_notification(selected_uid, "Scheduler",
                                     f"Your appointment #{new_appt_id} with {consultant} on {appt_date} at {time_slot} has been confirmed.")

                    st.success(
                        f"🎉 Appointment **{new_appt_id}** successfully booked for **{patient_name}** with **{consultant}**!")
                    st.balloons()
                    st.rerun()

    with tab2:
        st.subheader("Master Appointment Schedule")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_doctor = st.selectbox("Filter by Doctor:", ["All Doctors"] + doctor_list, key="roster_filter_doc")
        with col_f2:
            filter_status = st.selectbox("Filter by Status:",
                                         ["All Statuses", "Scheduled", "In Consultation", "Completed", "Cancelled"],
                                         key="roster_filter_status")
        with col_f3:
            filter_date = st.date_input("Filter by Date:", value=date.today(), key="roster_filter_date")

        df_appt = load_appointments_db()
        if not df_appt.empty:
            if current_role == "DOCTOR":
                df_appt = df_appt[
                    df_appt["Consultant"].astype(str).str.contains(current_username, case=False, na=False)]
            if filter_doctor != "All Doctors":
                df_appt = df_appt[df_appt["Consultant"].astype(str) == filter_doctor]
            if filter_status != "All Statuses":
                df_appt = df_appt[df_appt["Status"].astype(str) == filter_status]
            if filter_date:
                df_appt = df_appt[df_appt["Date"].astype(str) == str(filter_date)]

        st.markdown(f"**Total Encounters Displayed**: `{len(df_appt)}`")
        if df_appt.empty:
            st.info("No appointment bookings found matching the selected filters.")
        else:
            st.dataframe(df_appt, use_container_width=True)

    with tab3:
        st.subheader("Update Visit Status")
        df_cache = load_appointments_db()
        df_target = df_cache.copy()
        if not df_target.empty and current_role == "DOCTOR":
            df_target = df_target[
                df_target["Consultant"].astype(str).str.contains(current_username, case=False, na=False)]

        if df_target.empty:
            st.info("No appointments available for update under your profile.")
        else:
            appt_options = df_target["Appt_ID"].tolist()
            selected_appt_id = st.selectbox("Select Appointment Ticket to Update:", appt_options,
                                            key="manage_appt_select")

            match_indices = df_cache[df_cache["Appt_ID"].astype(str) == str(selected_appt_id)].index
            if not match_indices.empty:
                appt_idx = match_indices[0]
                appt_row = df_cache.loc[appt_idx]

                st.write(f"**Patient**: {appt_row['Patient_Name']} (`{appt_row['Patient_UID']}`)")
                st.write(f"**Consultant**: {appt_row['Consultant']}")
                st.write(f"**Slot**: {appt_row['Date']} @ {appt_row['Time_Slot']}")
                st.write(f"**Current Status**: `{appt_row['Status']}`")

                status_options = ["Scheduled", "In Consultation", "Completed", "Cancelled"]
                current_status_val = appt_row["Status"]
                default_idx = status_options.index(current_status_val) if current_status_val in status_options else 0

                new_status = st.selectbox("Update Encounter Status To:", status_options, index=default_idx,
                                          key="manage_new_status_select")

                if st.button("Apply Status Update", type="primary", key="manage_apply_btn"):
                    df_cache.at[appt_idx, "Status"] = str(new_status)
                    save_appointments_db(df_cache)
                    add_notification(appt_row["Patient_UID"], "Scheduler",
                                     f"Your appointment #{appt_row['Appt_ID']} status has been updated to: {new_status}.")
                    st.success(f"✅ Status for Appointment **{selected_appt_id}** updated to `{new_status}`!")
                    st.rerun()