# modules/home/blog.py
import streamlit as st
from modules.home.layout import render_common_header


def render_blog_page():
    # Render the persistent top utility bar and navigation header
    render_common_header()

    st.markdown("""
        <style>
        .blog-hero {
            background: linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%);
            padding: 3rem 2.5rem;
            border-radius: 1.5rem;
            margin-bottom: 2.5rem;
            border: 1px solid #f5d0fe;
            box-shadow: 0 10px 25px -5px rgba(217, 70, 239, 0.1);
        }
        .blog-hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 1rem;
        }
        .blog-hero-text {
            font-size: 1.05rem;
            color: #334155;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        .doctor-spotlight {
            background: #ffffff;
            border: 2px solid #e879f9;
            padding: 1.5rem 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 20px -5px rgba(217, 70, 239, 0.1);
            margin-top: 1.5rem;
        }
        .blog-card {
            background: #ffffff;
            border: 2px solid #e2e8f0;
            padding: 2rem 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            height: 100%;
        }
        .blog-card:hover {
            transform: translateY(-5px);
            border-color: #0284c7;
            box-shadow: 0 20px 25px -5px rgba(2, 132, 199, 0.15);
        }
        .blog-badge {
            display: inline-block;
            background: #e0f2fe;
            color: #0369a1;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .blog-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }
        .blog-desc {
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.5;
        }
        </style>

        <div class="blog-hero">
            <div class="blog-hero-title">Dermatology Insights & Clinical Expertise</div>
            <div class="blog-hero-text">
                Explore expert skin care advice, advanced aesthetic breakthroughs, and clinical perspectives written by <b>Dr. Mir Mubashir Ali</b>. With years of specialized experience across premier medical institutions, international global conferences, and award-winning research, Dr. Ali brings world-class knowledge directly to Cuticare Centre.
            </div>
            <div class="doctor-spotlight">
                <h4 style="margin: 0 0 0.5rem 0; color: #701a75; font-weight: 700;">🌟 Leadership & Global Recognition</h4>
                <p style="margin: 0; font-size: 0.95rem; color: #475569; line-height: 1.5;">
                    Backed by over a decade of clinical practice at <b>CARE Hospital</b>, collaborative work with top experts at <b>Star Hospitals</b>, and multiple international awards won across worldwide dermatology conferences, Dr. Ali ensures Cuticare Centre features state-of-the-art machinery, advanced lasers, and a properly sealed, sterile operation theater for ultimate patient safety.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Blog cards grid layout
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown("""
            <div class="blog-card">
                <span class="blog-badge">Aesthetic Technology</span>
                <div class="blog-title">The Evolution of Advanced Lasers in Skin Rejuvenation</div>
                <div class="blog-desc">An inside look at how next-generation laser machinery transforms scar revision, pigmentation correction, and anti-aging treatments safely.</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="blog-card">
                <span class="blog-badge">Clinical Dermatology</span>
                <div class="blog-title">Managing Chronic Eczema & Psoriasis with Modern Therapeutics</div>
                <div class="blog-desc">Dr. Mir Mubashir Ali shares evidence-based approaches combining targeted topical regimens, lab diagnostics, and long-term flare prevention.</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="blog-card">
                <span class="blog-badge">Surgical Safety</span>
                <div class="blog-title">Why a Sealed Sterile Operation Theater Matters in Dermatology</div>
                <div class="blog-desc">Discover the critical safety standards and advanced surgical protocols maintained at Cuticare Centre for minor dermatological procedures.</div>
            </div>
        """, unsafe_allow_html=True)