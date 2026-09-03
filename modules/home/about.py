# modules/home/about.py
import streamlit as st
from modules.home.layout import render_common_header


def render_about_page():
    # Render the persistent header and top bar
    render_common_header()

    st.markdown("""
        <style>
        .about-hero {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 3rem 2.5rem;
            border-radius: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid #bae6fd;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.1);
        }
        .about-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 1rem;
        }
        .about-text {
            font-size: 1.05rem;
            color: #334155;
            line-height: 1.6;
            margin-bottom: 1rem;
        }
        .doctor-profile-card {
            background: #ffffff;
            border: 2px solid #bae6fd;
            padding: 2rem;
            border-radius: 1.25rem;
            box-shadow: 0 10px 20px -5px rgba(2, 132, 199, 0.08);
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        </style>

        <div class="about-hero">
            <div class="about-title">About Cuticare Centre</div>
            <div class="about-text">
                Located in Hyderabad, Telangana, Cuticare Centre is a specialized dermatology clinic dedicated to delivering world-class clinical, surgical, and cosmetic skin care. We combine advanced dermatological technology with compassionate patient-centered healing.
            </div>
            <div class="about-text">
                Equipped with an on-site diagnostic lab and an integrated pharmacy, we provide seamless, comprehensive care—from precise diagnosis to customized prescription management and specialized treatments—all under one roof.
            </div>
        </div>

        <div class="doctor-profile-card">
            <h3 style="margin-top: 0; color: #0f172a; font-weight: 700;">Meet Our Lead Consultant</h3>
            <h4 style="color: #0284c7; margin-bottom: 0.5rem;">Dr. Mir Mubashir Ali</h4>
            <p style="font-weight: 600; color: #475569; margin-top: 0; margin-bottom: 1rem;">Consultant Dermatologist, Cuticare Centre (Hyderabad, India)</p>
            <p style="color: #334155; line-height: 1.5; margin-bottom: 1.5rem;">
                Dr. Mir Mubashir Ali brings extensive expertise in medical and clinical dermatology, having completed his M.D. in Dermatology from the prestigious Kasturba Medical College, Mangalore (2002–2005) and his M.B.B.S. from M.R. Medical College. He is dedicated to offering evidence-based, personalized solutions for all complex skin, hair, and nail conditions.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.metric(label="Clinical Experience", value="20+ Years", delta="Expert Care")
    with col2:
        st.metric(label="Specialized Services", value="Derm, Lab & Pharmacy", delta="All-in-One")
    with col3:
        st.metric(label="Patient Commitment", value="100%", delta="Dedicated")