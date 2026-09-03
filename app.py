# app.py
import os
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Cuticare Clinic EMR & Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

from modules.auth import render_user_profile_bar, check_role_access, render_login
from modules.home import render_home_page
from modules.home.about import render_about_page
from modules.database import load_patients_db
from modules.registration import render_registration_module
from modules.scheduler import render_scheduler_module
from modules.patient_portal import render_patient_portal_module
from modules.pharmacy import render_pharmacy_module
from modules.procedures import render_procedure_management_module
from modules.equipment_scheduler import render_equipment_scheduler_module
from modules.notifications import render_notifications_page
from modules.home.doctors import render_doctors_page
from modules.home.services import render_services_page
from modules.home.blog import render_blog_page
from modules.home.contact import render_contact_page

# Import Doctor 4 distinct views
try:
    from modules.doctor_desk import (
        render_doctor_schedule,
        render_doctor_patient_directory,
        render_doctor_clinical_ehr,
        render_doctor_diagnostic_reports
    )
except ImportError:
    def render_doctor_schedule():
        st.error("Doctor Schedule module missing.")


    def render_doctor_patient_directory():
        st.error("Doctor Patient Directory module missing.")


    def render_doctor_clinical_ehr():
        st.error("Clinical EHR module missing.")


    def render_doctor_diagnostic_reports():
        st.error("Diagnostic Reports module missing.")

try:
    from modules.lab_desk import render_lab_desk_module
except ImportError:
    def render_lab_desk_module():
        st.title("🔬 Pathology & Lab Desk")
        st.info("Lab module loading...")

try:
    from modules.billing import render_billing_module
except ImportError:
    def render_billing_module():
        st.title("💳 Billing & Invoicing Desk")
        st.info("Billing module loading...")

try:
    from modules.admin import render_admin_module
except ImportError:
    def render_admin_module():
        st.title("⚙️ Admin Control Panel")
        st.info("Admin module loading...")


def main():
    # Load patient database directly from patients.txt via database module on startup
    load_patients_db()

    # Ensure navigation state defaults to Home if not set
    if "selected_nav" not in st.session_state:
        st.session_state.selected_nav = "Home"

    # If the user is not authenticated, check whether to show the home page, about page, or login form
    if not st.session_state.get("authenticated", False):
        if st.session_state.get("show_classic_login", False):
            col_back, _ = st.columns([1, 5])
            with col_back:
                if st.button("⬅️ Back to Home", type="secondary"):
                    st.session_state.show_classic_login = False
                    st.session_state.login_tab_focus = None
                    st.session_state.selected_nav = "Home"
                    st.rerun()
            render_login()
        else:
            if st.session_state.selected_nav == "About":
                render_about_page()
            elif st.session_state.selected_nav == "Doctors":
                render_doctors_page()
            elif st.session_state.selected_nav == "Services":
                render_services_page()
            elif st.session_state.selected_nav == "Blog":
                render_blog_page()
            elif st.session_state.selected_nav == "Contact":
                render_contact_page()
            else:
                render_home_page()
        return

    # Top profile bar for logged-in users
    render_user_profile_bar()

    current_role = st.session_state.get("current_role", "PATIENT").upper()

    # Use a static navigation label for Notifications to prevent Streamlit radio index reset on rerun
    notif_nav_label = "🔔 Notifications"

    nav_options = []

    # Patients do NOT have access to system notifications
    if current_role == "PATIENT":
        nav_options = ["👤 Patient Health Portal"]
    elif current_role == "STAFF":
        nav_options = [
            "📋 Patient Registration",
            "🗓️ Clinic Appointments",
            "⚡ Equipment & Suite Scheduler",
            "🩺 Procedure Management",
            "💳 Billing & Invoicing",
            notif_nav_label
        ]
    elif current_role == "DOCTOR":
        nav_options = [
            "🗓️ Doctor Schedule",
            "📋 Patient Directory",
            "🩺 Clinical EHR",
            "🔬 Diagnostic Reports",
            "⚡ Equipment & Suite Scheduler",
            "🩺 Procedure Management",
            notif_nav_label
        ]
    elif current_role == "PHARMACY":
        nav_options = [
            "💊 Pharmacy Operations & POS",
            notif_nav_label
        ]
    elif current_role == "LAB":
        nav_options = [
            "🔬 Lab & Pathology Desk",
            notif_nav_label
        ]
    elif current_role == "ADMIN":
        nav_options = [
            "⚙️ Admin Control Panel",
            "👤 Patient Health Portal",
            "📋 Patient Registration",
            "🗓️ Clinic Appointments",
            "🗓️ Doctor Schedule",
            "📋 Patient Directory",
            "🩺 Clinical EHR",
            "🔬 Diagnostic Reports",
            "⚡ Equipment & Suite Scheduler",
            "💊 Pharmacy Operations & POS",
            "🔬 Lab & Pathology Desk",
            "💳 Billing & Invoicing",
            "🩺 Procedure Management",
            notif_nav_label
        ]

    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Navigation")
    selected_page = st.sidebar.radio("Go to:", nav_options)

    st.sidebar.markdown("---")
    st.sidebar.caption("Cuticare Health EHR System v1")

    # Route Selected View Safely
    if "Notifications" in selected_page:
        render_notifications_page()

    elif "Patient Health Portal" in selected_page:
        render_patient_portal_module()

    elif "Patient Registration" in selected_page:
        render_registration_module()

    elif "Clinic Appointments" in selected_page:
        render_scheduler_module()

    elif "Equipment & Suite Scheduler" in selected_page:
        render_equipment_scheduler_module()

    elif "Procedure Management" in selected_page:
        render_procedure_management_module()

    elif "Doctor Schedule" in selected_page:
        render_doctor_schedule()

    elif "Patient Directory" in selected_page:
        render_doctor_patient_directory()

    elif "Clinical EHR" in selected_page:
        render_doctor_clinical_ehr()

    elif "Diagnostic Reports" in selected_page:
        render_doctor_diagnostic_reports()

    elif "Pharmacy Operations" in selected_page:
        render_pharmacy_module()

    elif "Lab & Pathology Desk" in selected_page:
        render_lab_desk_module()

    elif "Billing & Invoicing" in selected_page:
        render_billing_module()

    elif "Admin Control Panel" in selected_page:
        render_admin_module()


if __name__ == "__main__":
    main()