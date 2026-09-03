# modules/home/services.py
import streamlit as st
from modules.home.layout import render_common_header


def render_services_page():
    # Render the persistent top utility bar and navigation header
    render_common_header()

    st.markdown("""
        <style>
        .services-hero {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            padding: 3rem 2.5rem;
            border-radius: 1.5rem;
            margin-bottom: 2.5rem;
            border: 1px solid #bfdbfe;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.1);
        }
        .services-hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 1rem;
        }
        .services-hero-text {
            font-size: 1.05rem;
            color: #334155;
            line-height: 1.6;
        }
        .service-card {
            background: #ffffff;
            border: 2px solid #e2e8f0;
            padding: 2rem 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            height: 100%;
        }
        .service-card:hover {
            transform: translateY(-5px);
            border-color: #0284c7;
            box-shadow: 0 20px 25px -5px rgba(2, 132, 199, 0.15);
        }
        .service-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        .service-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }
        .service-desc {
            font-size: 0.9rem;
            color: #64748b;
            line-height: 1.5;
        }
        </style>

        <div class="services-hero">
            <div class="services-hero-title">Specialized Dermatological & Clinical Services</div>
            <div class="services-hero-text">
                At Cuticare Centre, we provide comprehensive skin, hair, and nail care under one roof. Led by Dr. Mir Mubashir Ali, our clinic integrates expert medical treatments, an on-site diagnostic laboratory, and a fully stocked prescription pharmacy.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Detailed service cards grid layout
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown("""
            <div class="service-card">
                <div class="service-icon">🩺</div>
                <div class="service-title">Medical Dermatology</div>
                <div class="service-desc">Expert clinical care and tailored treatment plans for acne, eczema, psoriasis, chronic dermatitis, and other complex skin conditions.</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="service-card">
                <div class="service-icon">✨</div>
                <div class="service-title">Cosmetic & Aesthetic Care</div>
                <div class="service-desc">Advanced anti-aging therapies, skin rejuvenation, scar treatments, and aesthetic dermatology solutions for glowing health.</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="service-card">
                <div class="service-icon">🛡️</div>
                <div class="service-title">Hair & Nail Disorders</div>
                <div class="service-desc">Specialized diagnostics and clinical interventions for chronic hair fall, alopecia, scalp disorders, and complex nail pathologies.</div>
            </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3, gap="medium")

    with col4:
        st.markdown("""
            <div class="service-card">
                <div class="service-icon">🔬</div>
                <div class="service-title">In-House Diagnostic Lab</div>
                <div class="service-desc">Advanced dermatopathology services, skin scrapings, biopsies, and allergy screening processed rapidly on-site.</div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""
            <div class="service-card">
                <div class="service-icon">💊</div>
                <div class="service-title">Integrated Pharmacy POS</div>
                <div class="service-desc">Fully stocked prescription pharmacy providing specialized topical medications, customized compounding, and medical skincare regimens.</div>
            </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown("""
            <div class="service-card">
                <div class="service-icon">👶</div>
                <div class="service-title">Pediatric Dermatology</div>
                <div class="service-desc">Gentle, specialized dermatological evaluations and safe therapeutic care designed specifically for infants, children, and sensitive skin.</div>
            </div>
        """, unsafe_allow_html=True)