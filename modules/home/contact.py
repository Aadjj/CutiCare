# modules/home/contact.py
import streamlit as st
from modules.home.layout import render_common_header
from datetime import datetime


def render_contact_page():
    # Render the persistent top utility bar and navigation header
    render_common_header()

    st.markdown("""
        <style>
        .contact-hero {
            background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
            padding: 3rem 2.5rem;
            border-radius: 1.5rem;
            margin-bottom: 2.5rem;
            border: 1px solid #fed7aa;
            box-shadow: 0 10px 25px -5px rgba(234, 88, 12, 0.1);
        }
        .contact-hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 1rem;
        }
        .contact-hero-text {
            font-size: 1.05rem;
            color: #334155;
            line-height: 1.6;
        }
        .info-card {
            background: #ffffff;
            border: 2px solid #e2e8f0;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
            height: 100%;
        }
        .info-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 1rem;
        }
        .info-item {
            font-size: 0.95rem;
            color: #334155;
            margin-bottom: 0.8rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        </style>

        <div class="contact-hero">
            <div class="contact-hero-title">Get in Touch With Us</div>
            <div class="contact-hero-text">
                Have questions, need an appointment, or want to share feedback? Reach out to our team directly through our physical location or drop a confidential complaint/query below.
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_info, col_form = st.columns([1, 1.2], gap="large")

    with col_info:
        st.markdown("""
            <div class="info-card">
                <div class="info-title">📍 Clinic Location</div>
                <div class="info-item"><span>🏥</span> <b>Cuticare Center</b></div>
                <div class="info-item"><span>📌</span>  S.H.PLAZA, H.NO- 9-4, 86/224, above JOCKEY STORE, Salarjung Colony, Toli Chowki, Hyderabad, Telangana 500008</div>
                <div class="info-item"><span>📞</span> +91 8106109488</div>
                <div class="info-item"><span>✉️</span> support@cuticarecenter.com</div>
                <div class="info-item"><span>⏰</span> Open from 9 a.m to 7:30 p.m / Mon to Sat</div>
            </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown("""
            <div class="info-card">
                <div class="info-title">📢 Patient Complaint & Feedback Box</div>
                <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 1rem;">
                    Submit your grievances or direct reports. This will instantly show up in the Admin Control Panel and trigger an automated WhatsApp alert to administration.
                </p>
        """, unsafe_allow_html=True)

        with st.form("complaint_form", clear_on_submit=True):
            complainant_name = st.text_input("Your Full Name")
            complainant_contact = st.text_input("Phone Number / Email")
            complaint_category = st.selectbox(
                "Category",
                ["General Feedback", "Billing Grievance", "Staff Conduct", "Facility Issue", "Clinical Service Delay"]
            )
            complaint_message = st.text_area("Detailed Message / Complaint Description")

            submitted = st.form_submit_button("Submit Complaint & Send Alert", type="primary")

            if submitted:
                if not complainant_name or not complaint_message:
                    st.error("Please fill in your name and message description.")
                else:
                    # Save complaint to session state / global registry to simulate Admin Panel integration
                    if "admin_complaints_log" not in st.session_state:
                        st.session_state.admin_complaints_log = []

                    new_complaint = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "name": complainant_name,
                        "contact": complainant_contact,
                        "category": complaint_category,
                        "message": complaint_message,
                        "status": "Pending Review"
                    }
                    st.session_state.admin_complaints_log.append(new_complaint)

                    # Simulated WhatsApp Notification trigger to Admin
                    st.success("✅ Complaint logged successfully! Admin panel updated and WhatsApp notification dispatched to management (+91 8106109488).")

        st.markdown("</div>", unsafe_allow_html=True)