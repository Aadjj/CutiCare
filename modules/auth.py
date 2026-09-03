# modules/auth.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Pre-configured user registry for staff/admin role-based authentication
STAFF_USERS_DB = {
    "staff": {"password": "123", "role": "STAFF", "name": "Front Desk Reception"},
    "doctor": {"password": "123", "role": "DOCTOR", "name": "Dr. Sarah Jenkins"},
    "pharmacy": {"password": "123", "role": "PHARMACY", "name": "Chief Pharmacist"},
    "lab": {"password": "123", "role": "LAB", "name": "Pathology Lab Tech"},
    "admin": {"password": "123", "role": "ADMIN", "name": "System Administrator"},
}


def render_login():
    """Renders the login UI form based on dropdown selection and manages authentication state."""
    st.title("🏥 Cuticare Health EMR Portal")
    st.caption("Secure Clinical Information & Patient Portal")

    focus = st.session_state.get("login_tab_focus", "Patient")

    # If Admin selected, show focused Admin login interface
    if focus == "Admin":
        st.subheader("⚙️ System Administrator Sign-In")
        with st.form("admin_login_form"):
            admin_pass = st.text_input("Admin Password:", type="password", placeholder="Enter admin password", key="adm_pass")
            submitted = st.form_submit_button("Sign In (Admin)", type="primary", use_container_width=True)
            if submitted:
                if admin_pass == "123":
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = "admin"
                    st.session_state["current_role"] = STAFF_USERS_DB["admin"]["role"]
                    st.session_state["current_username"] = STAFF_USERS_DB["admin"]["name"]
                    st.success("✅ Welcome, System Administrator!")
                    st.rerun()
                else:
                    st.error("❌ Invalid admin password.")

    # If Clinic selected, show staff/clinical sign-in
    elif focus == "Clinic":
        st.subheader("👨‍⚕️ Staff & Clinical Sign-In")
        st.caption("For Doctors, Front Desk, Lab, Pharmacy & Admin")

        with st.form("staff_login_form"):
            staff_username = st.text_input("Username / Staff ID:", placeholder="e.g. doctor, pharmacy, lab, staff", key="staff_uname")
            staff_password = st.text_input("Password:", type="password", placeholder="Enter password", key="staff_pass")

            staff_submitted = st.form_submit_button("Sign In (Staff Portal)", type="primary", use_container_width=True)

            if staff_submitted:
                u_clean = staff_username.strip().lower()
                if u_clean in STAFF_USERS_DB and STAFF_USERS_DB[u_clean]["password"] == staff_password:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = u_clean
                    st.session_state["current_role"] = STAFF_USERS_DB[u_clean]["role"]
                    st.session_state["current_username"] = STAFF_USERS_DB[u_clean]["name"]
                    st.success(f"✅ Welcome back, {STAFF_USERS_DB[u_clean]['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid staff credentials.")

    # Default to Patient Portal
    else:
        st.subheader("👤 Patient Portal Sign-In")
        st.caption("Username = Full Name | Password = DOB (ddmmyyyy)")

        with st.form("patient_login_form"):
            patient_username = st.text_input("Full Name:", key="pat_uname")
            patient_password = st.text_input("Password (DOB as ddmmyyyy):", type="password", key="pat_pass")

            patient_submitted = st.form_submit_button("Sign In (Patient Portal)", type="secondary", use_container_width=True)

            if patient_submitted:
                p_uname_clean = patient_username.strip().lower()

                if p_uname_clean == "patient" and patient_password == "123":
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = "patient"
                    st.session_state["current_role"] = "PATIENT"
                    st.session_state["current_username"] = "Ananya Sharma"
                    st.session_state["patient_uid"] = "PAT-1001"
                    st.success("✅ Welcome to the Patient Portal, Ananya!")
                    st.rerun()
                elif "patients_db" in st.session_state and not st.session_state.patients_db.empty:
                    patients_df = st.session_state.patients_db
                    match = patients_df[patients_df["Full_Name"].str.lower() == p_uname_clean]

                    if not match.empty:
                        patient_record = match.iloc[0]
                        raw_dob = str(patient_record["DOB"]).split(" ")[0]
                        try:
                            date_obj = datetime.strptime(raw_dob, "%Y-%m-%d")
                            expected_pw = date_obj.strftime("%d%m%Y")
                        except Exception:
                            expected_pw = "".join(filter(str.isdigit, raw_dob))[:8]

                        if patient_password.strip() == expected_pw:
                            st.session_state["authenticated"] = True
                            st.session_state["current_user"] = patient_record["UID"]
                            st.session_state["current_role"] = "PATIENT"
                            st.session_state["current_username"] = patient_record["Full_Name"]
                            st.session_state["patient_uid"] = patient_record["UID"]
                            st.success(f"✅ Welcome, {patient_record['Full_Name']}!")
                            st.rerun()
                        else:
                            st.error("❌ Incorrect password (Date of Birth in ddmmyyyy format).")
                    else:
                        st.error("❌ Patient name not found in registry.")
                else:
                    st.error("❌ Patient registry is empty or credentials incorrect.")

    # Quick Access Demo Accounts Reference
    st.markdown("---")
    st.markdown("### 💡 Quick Access Demo Accounts")

    d1, d2, d3, d4, d5, d6 = st.columns(6)
    d1.metric("Doctor", "doctor", "Pass: 123")
    d2.metric("Staff", "staff", "Pass: 123")
    d3.metric("Admin", "admin", "Pass: 123")
    d4.metric("Pharmacy", "pharmacy", "Pass: 123")
    d5.metric("Lab Tech", "lab", "Pass: 123")
    d6.metric("Patient", "patient", "Pass: 123")


def render_user_profile_bar():
    """Renders user info and logout button in the sidebar."""
    if st.session_state.get("authenticated", False):
        st.sidebar.markdown("### 👤 User Session")
        st.sidebar.write(f"**User**: {st.session_state.get('current_username', 'User')}")
        st.sidebar.write(f"**Role**: `{st.session_state.get('current_role', 'GUEST')}`")

        if st.sidebar.button("🚪 Logout", type="secondary"):
            st.session_state["authenticated"] = False
            st.session_state["current_user"] = None
            st.session_state["current_role"] = None
            st.session_state["current_username"] = None
            if "patient_uid" in st.session_state:
                del st.session_state["patient_uid"]
            st.rerun()


def check_role_access(allowed_roles):
    """Validates if current user role matches permitted roles."""
    if not st.session_state.get("authenticated", False):
        return False

    user_role = st.session_state.get("current_role", "").upper()
    allowed_roles_upper = [r.upper() for r in allowed_roles]

    return user_role in allowed_roles_upper