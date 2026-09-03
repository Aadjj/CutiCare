# modules/registration.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.database import save_patients_db, load_patients_db
from modules.auth import check_role_access


def render_registration_module():
    st.title("📋 Patient Registration Desk")
    st.markdown("Register new patients or review the live patient database synced with `patients.txt`.")

    # Enforce role access for staff/admin
    if not check_role_access(["STAFF", "ADMIN"]):
        st.error("❌ Access Denied: You do not have authorization to access the Patient Registration module.")
        return

    # Ensure database is loaded into session state
    load_patients_db()
    if "patients_db" not in st.session_state:
        st.warning("⚠️ Patient database could not be initialized.")
        return

    # Use tabs to separate registration from directory viewing
    tab1, tab2 = st.tabs(["➕ Register New Patient", "📋 Live Patient Directory & Database"])

    # ----------------------------------------------------
    # TAB 1: REGISTER NEW PATIENT
    # ----------------------------------------------------
    with tab1:
        st.subheader("New Patient Onboarding Form")

        with st.form("patient_registration_form"):
            col1, col2 = st.columns(2)

            with col1:
                full_name = st.text_input("Full Name *")
                dob = st.date_input("Date of Birth *", value=datetime(1995, 1, 1))
                gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
                contact_number = st.text_input("Contact Number *", placeholder="+91 98765 43210")
                email = st.text_input("Email Address *", placeholder="patient@example.com")

            with col2:
                address = st.text_area("Residential Address *", placeholder="Apt, Street, City")
                emergency_contact = st.text_input("Emergency Contact *", placeholder="Name (+91 Phone)")
                allergies = st.text_input("Known Allergies", value="None", placeholder="e.g., Penicillin, Dust")
                pre_existing_conditions = st.text_input(
                    "Pre-existing Conditions", value="None", placeholder="e.g., Hypertension, Asthma"
                )

            submitted = st.form_submit_button("Register Patient & Save to File", type="primary")

            if submitted:
                if not full_name.strip() or not contact_number.strip() or not email.strip() or not address.strip():
                    st.error("Please fill in all mandatory fields marked with an asterisk (*).")
                else:
                    df = st.session_state.patients_db
                    next_id_num = 1001 if df.empty else len(df) + 1001
                    uid = f"PAT-{next_id_num}"

                    new_patient_dict = {
                        "UID": uid,
                        "Full_Name": full_name.strip(),
                        "DOB": dob.strftime("%Y-%m-%d"),
                        "Gender": gender,
                        "Contact_Number": contact_number.strip(),
                        "Email": email.strip(),
                        "Address": address.strip(),
                        "Emergency_Contact": emergency_contact.strip(),
                        "Allergies": allergies.strip(),
                        "Pre_existing_Conditions": pre_existing_conditions.strip(),
                        "Registration_Date": datetime.now().strftime("%Y-%m-%d")
                    }

                    new_row_df = pd.DataFrame([new_patient_dict])
                    st.session_state.patients_db = pd.concat([st.session_state.patients_db, new_row_df],
                                                             ignore_index=True)

                    # Persist immediately to text file
                    save_patients_db(st.session_state.patients_db)

                    st.success(f"🎉 Patient successfully registered with ID: **{uid}** and saved to `patients.txt`!")
                    st.balloons()

    # ----------------------------------------------------
    # TAB 2: VIEW & EDIT LIVE DATABASE
    # ----------------------------------------------------
    with tab2:
        st.subheader("Master Patient Directory (`patients.txt`)")

        df_current = st.session_state.patients_db

        if df_current.empty:
            st.info("No patient records found in the database.")
        else:
            st.metric("Total Active Patient Records", len(df_current))

            # Allow staff to view and optionally edit records with instant file saving
            st.markdown("### Patient Records Table")
            edited_df = st.data_editor(
                df_current,
                use_container_width=True,
                num_rows="dynamic",
                key="patient_database_editor"
            )

            if st.button("💾 Save Table Changes to `patients.txt`", type="secondary"):
                save_patients_db(edited_df)
                st.success("✅ Changes successfully written and saved to `patients.txt`!")
                st.rerun()