# modules/home/doctors.py
import base64
import streamlit as st
from modules.home.layout import render_common_header


def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""


def render_doctors_page():
    # Render the persistent top utility bar and navigation header
    render_common_header()

    img_base64 = get_image_base64(r"C:\Users\aadjj\Downloads\Dr.png")
    img_tag = (
        f'<img src="data:image/png;base64,{img_base64}" style="width: 150px; height: 150px; border-radius: 50%; object-fit: cover; border: 3px solid #0284c7; margin-bottom: 1rem;" />'
        if img_base64
        else '<div style="font-size: 4rem; margin-bottom: 1rem;">👨‍⚕️</div>'
    )

    st.markdown(
        f"""
        <style>
        .doctors-hero {{
            background: linear-gradient(135deg, #f0fdf4 100%, #dcfce7 0%);
            padding: 3rem 2.5rem;
            border-radius: 1.5rem;
            margin-bottom: 2.5rem;
            border: 1px solid #bbf7d0;
            box-shadow: 0 10px 25px -5px rgba(22, 163, 74, 0.1);
        }}
        .doctors-title {{
            font-size: 2.5rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 1rem;
        }}
        .doctors-text {{
            font-size: 1.05rem;
            color: #334155;
            line-height: 1.6;
        }}
        .doc-card-center {{
            background: #ffffff;
            border: 2px solid #bae6fd;
            padding: 2.5rem 2rem;
            border-radius: 1.25rem;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.1);
            max-width: 700px;
            margin: 0 auto 2rem auto;
        }}
        .doc-name {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.3rem;
        }}
        .doc-specialty {{
            font-size: 1.05rem;
            color: #0284c7;
            font-weight: 700;
            margin-bottom: 1.2rem;
        }}
        .doc-desc {{
            font-size: 0.95rem;
            color: #334155;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }}
        .credentials-box {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 1rem;
            border-radius: 0.75rem;
            font-size: 0.9rem;
            color: #475569;
            text-align: left;
            margin-top: 1rem;
        }}
        </style>

        <div class="doctors-hero">
            <div class="doctors-title">Meet Our Lead Specialist</div>
            <div class="doctors-text">
                At Cuticare Centre, our practice is anchored by expert dermatological proficiency, advanced skin therapies, and personalized patient care under one roof.
            </div>
        </div>

        <div class="doc-card-center">
            {img_tag}
            <div class="doc-name">Dr. Mir Mubashir Ali</div>
            <div class="doc-specialty">Consultant Dermatologist</div>
            <div class="doc-desc">
                Specializing in comprehensive clinical, medical, and cosmetic dermatology. Dedicated to providing evidence-based treatments for complex skin disorders, advanced aesthetic enhancements, hair conditions, and nail pathologies.
            </div>
            <div class="credentials-box">
                <b>🎓 Educational Background:</b><br>
                • <b>M.D. (Dermatology):</b> Kasturba Medical College, Mangalore (2002 – 2005)<br>
                • <b>M.B.B.S.:</b> M.R. Medical College<br><br>
                📍 <b>Practice Location:</b> Cuticare Centre, Hyderabad, Telangana, India
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )