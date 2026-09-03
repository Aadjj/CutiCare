# modules/equipment_scheduler.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
from modules.auth import check_role_access
from modules.database import load_patients_db
from modules.notifications import add_notification

EQUIPMENT_SCHEDULE_FILE = "equipment_schedule.txt"

# Procedure to Equipment/Suite Auto-Mapping Dictionary for CutiCare Centre
PROCEDURE_EQUIPMENT_MAP = {
    "Pico Q-Switch Laser (Pigmentation/Tattoo)": "Laser Suite A (Pico Q-Switch & CO2)",
    "CO2 Fractional Laser (Resurfacing/Scars)": "Laser Suite A (Pico Q-Switch & CO2)",
    "HydraFacial & Medical Clean-up": "Laser Suite B (Diode & HydraFacial Machine)",
    "Diode Laser Hair Reduction": "Laser Suite B (Diode & HydraFacial Machine)",
    "Chemical Peel": "Aesthetic Procedure Room 1",
    "Micro-needling / MNRF": "Aesthetic Procedure Room 1",
    "Botox & Fillers (Injectables)": "Aesthetic Procedure Room 2",
    "PRP Therapy (Hair/Skin)": "PRP Centrifuge Unit"
}


def get_suggested_equipment(procedure_name):
    """Returns the matching equipment suite for a given clinical procedure."""
    for proc_key, suite_name in PROCEDURE_EQUIPMENT_MAP.items():
        if proc_key.lower() in procedure_name.lower() or procedure_name.lower() in proc_key.lower():
            return suite_name
    return "Aesthetic Procedure Room 1"  # Default fallback


def load_equipment_schedule_db():
    """Loads resource bookings from equipment_schedule.txt into session state."""
    if "equipment_schedule_db" not in st.session_state:
        if os.path.exists(EQUIPMENT_SCHEDULE_FILE):
            try:
                st.session_state.equipment_schedule_db = pd.read_csv(EQUIPMENT_SCHEDULE_FILE, sep="|")
                for col, default_val in [
                    ("Booking_ID", ""),
                    ("Resource_Name", ""),
                    ("Resource_Type", ""),
                    ("Patient_UID", ""),
                    ("Patient_Name", ""),
                    ("Assigned_Staff", ""),
                    ("Date", ""),
                    ("Time_Slot", ""),
                    ("Status", "Confirmed")
                ]:
                    if col not in st.session_state.equipment_schedule_db.columns:
                        st.session_state.equipment_schedule_db[col] = default_val
            except Exception as e:
                st.error(f"Error loading {EQUIPMENT_SCHEDULE_FILE}: {e}")
                st.session_state.equipment_schedule_db = _get_empty_schedule_df()
        else:
            df = _get_empty_schedule_df()
            save_equipment_schedule_db(df)
            st.session_state.equipment_schedule_db = df
    return st.session_state.equipment_schedule_db


def save_equipment_schedule_db(df):
    """Saves the resource schedule DataFrame back to equipment_schedule.txt."""
    try:
        df.to_csv(EQUIPMENT_SCHEDULE_FILE, sep="|", index=False)
        st.session_state.equipment_schedule_db = df
    except Exception as e:
        st.error(f"Error saving to {EQUIPMENT_SCHEDULE_FILE}: {e}")


def _get_empty_schedule_df():
    """Returns an empty DataFrame with required schedule schema headers."""
    headers = [
        "Booking_ID", "Resource_Name", "Resource_Type", "Patient_UID",
        "Patient_Name", "Assigned_Staff", "Date", "Time_Slot", "Status"
    ]
    return pd.DataFrame(columns=headers)


def render_equipment_scheduler_module():
    st.title("⚡ Clinic Suite & Equipment Resource Scheduler")
    st.caption("Manage and prevent double-booking of specialized laser suites, aesthetic rooms, and clinical equipment.")

    # 1. Enforce Role Access: DOCTOR, STAFF, ADMIN only
    if not check_role_access(["DOCTOR", "STAFF", "ADMIN"]):
        st.error("❌ Access Denied: Unauthorized role context.")
        return

    load_equipment_schedule_db()
    patients_df = load_patients_db()

    tab_book, tab_calendar, tab_manage = st.tabs([
        "➕ Book Room / Equipment",
        "📅 Resource Calendar & Availability",
        "📋 Master Schedule Registry"
    ])

    # Predefined Clinical Resources at Cuticare Centre
    resource_inventory = {
        "Laser Suite A (Pico Q-Switch & CO2)": "Room / Suite",
        "Laser Suite B (Diode & HydraFacial Machine)": "Room / Suite",
        "Aesthetic Procedure Room 1": "Aesthetic Room",
        "Aesthetic Procedure Room 2": "Aesthetic Room",
        "Portable Wood's Lamp / Skin Analyzer": "Shared Equipment",
        "PRP Centrifuge Unit": "Shared Equipment"
    }

    with tab_book:
        st.subheader("Allocate Suite or Specialized Equipment")

        if patients_df.empty:
            st.warning("⚠️ No patient records found. Please register patients before booking resources.")
            return

        with st.form("resource_booking_form"):
            patient_options = [f"{row['Full_Name']} ({row['UID']})" for _, row in patients_df.iterrows()]
            selected_patient_str = st.selectbox("Select Patient *", patient_options)

            # Optional procedure selection hint for auto-suggestion
            procedure_hint = st.selectbox(
                "Link to Procedure Category (Optional Auto-Mapper)",
                ["-- Manual Selection --"] + list(PROCEDURE_EQUIPMENT_MAP.keys())
            )

            # Determine initial resource based on selection
            default_resource_idx = 0
            if procedure_hint != "-- Manual Selection --":
                suggested_suite = get_suggested_equipment(procedure_hint)
                if suggested_suite in list(resource_inventory.keys()):
                    default_resource_idx = list(resource_inventory.keys()).index(suggested_suite)

            resource_name = st.selectbox("Select Suite / Equipment *", list(resource_inventory.keys()), index=default_resource_idx)
            resource_type = resource_inventory[resource_name]

            staff_choice = st.selectbox(
                "Assigned Doctor / Aesthetician *",
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
                booking_date = st.date_input("Date *", min_value=date.today())
            with col2:
                time_slot = st.selectbox(
                    "Time Slot *",
                    ["09:30 AM - 10:30 AM", "10:30 AM - 11:30 AM", "11:30 AM - 12:30 PM",
                     "02:00 PM - 03:00 PM", "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM"]
                )

            submit_booking = st.form_submit_button("Confirm & Lock Resource", type="primary")

            if submit_booking:
                patient_uid = selected_patient_str.split("(")[-1].strip(")")
                patient_name = selected_patient_str.split("(")[0].strip()
                date_str = booking_date.strftime("%Y-%m-%d")

                # Double-Booking Prevention Check
                sched_df = st.session_state.equipment_schedule_db
                conflict_check = sched_df[
                    (sched_df["Resource_Name"] == resource_name) &
                    (sched_df["Date"] == date_str) &
                    (sched_df["Time_Slot"] == time_slot) &
                    (sched_df["Status"] == "Confirmed")
                ]

                if not conflict_check.empty:
                    st.error(f"❌ **Double-Booking Conflict!** '{resource_name}' is already booked for **{date_str}** during **{time_slot}**.")
                else:
                    next_id = 9001 if sched_df.empty else len(sched_df) + 9001
                    booking_id = f"RES-{next_id}"

                    new_booking = {
                        "Booking_ID": booking_id,
                        "Resource_Name": resource_name,
                        "Resource_Type": resource_type,
                        "Patient_UID": patient_uid,
                        "Patient_Name": patient_name,
                        "Assigned_Staff": staff_choice,
                        "Date": date_str,
                        "Time_Slot": time_slot,
                        "Status": "Confirmed"
                    }

                    updated_df = pd.concat([sched_df, pd.DataFrame([new_booking])], ignore_index=True)
                    save_equipment_schedule_db(updated_df)

                    # Send notification to patient
                    add_notification(patient_uid, "Scheduler", f"Your equipment/suite booking (#{booking_id}) for {resource_name} on {date_str} ({time_slot}) is confirmed.")

                    st.success(f"🎉 Resource successfully locked! Booking ID: **{booking_id}** for {resource_name}.")
                    st.balloons()

    with tab_calendar:
        st.subheader("Resource Availability Calendar")
        sched_df = load_equipment_schedule_db()

        if sched_df.empty:
            st.info("No resource bookings recorded.")
        else:
            selected_date = st.date_input("Filter by Date:", value=date.today(), key="calendar_date_filter")
            filtered_df = sched_df[sched_df["Date"] == selected_date.strftime("%Y-%m-%d")]

            if filtered_df.empty:
                st.info(f"No suites or equipment booked for {selected_date.strftime('%Y-%m-%d')}. All resources are fully available.")
            else:
                st.markdown(f"### Booked Resources on {selected_date.strftime('%Y-%m-%d')}")
                st.dataframe(
                    filtered_df[["Booking_ID", "Resource_Name", "Resource_Type", "Patient_Name", "Assigned_Staff", "Time_Slot", "Status"]],
                    use_container_width=True
                )

    with tab_manage:
        st.subheader("Master Resource Schedule Ledger")
        sched_df = load_equipment_schedule_db()

        if sched_df.empty:
            st.info("No schedule records available.")
        else:
            edited_schedule = st.data_editor(
                sched_df,
                use_container_width=True,
                num_rows="dynamic",
                key="equipment_master_editor"
            )
            if st.button("💾 Save Schedule Changes", type="secondary"):
                save_equipment_schedule_db(edited_schedule)
                st.success("✅ Resource schedule updated successfully!")
                st.rerun()