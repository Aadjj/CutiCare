# modules/home/layout.py
import base64
import os
import streamlit as st


def get_image_base64(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    except Exception:
        pass
    return ""


def render_common_header():
    """Renders the persistent top utility bar and navigation header used across public pages."""
    st.markdown("""
        <style>
        header.stAppHeader {
            background-color: transparent !important;
        }
        .block-container {
            padding-top: 4rem !important;
            padding-bottom: 2rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            max-width: 100% !important;
        }
        [data-testid="column"] {
            padding: 0px 1px !important;
        }
        .top-bar-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: #ffffff;
            padding: 18px 32px !important;
            min-height: 60px !important;
            height: auto !important;
            font-size: 0.9rem;
            border-radius: 0.75rem;
            margin-top: 10px !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            width: 100%;
            box-sizing: border-box;
        }
        .top-bar-left, .top-bar-right {
            display: flex;
            align-items: center;
            gap: 25px;
            color: #ffffff !important;
        }
        .top-bar-right div, .top-bar-right b {
            color: #ffffff !important;
        }
        /* Navbar button styling */
        div.stButton > button:not([kind="primary"]) {
            background-color: transparent !important;
            border: none !important;
            color: inherit !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 2px 2px !important;
            box-shadow: none !important;
            min-height: unset !important;
            height: auto !important;
            width: auto !important;
        }
        div.stButton > button:not([kind="primary"]):hover {
            color: #0284c7 !important;
            background-color: transparent !important;
        }
        div[data-baseweb="select"] {
            max-width: 120px !important;
            margin-left: auto;
        }
        </style>

        <div class="top-bar-container">
            <div class="top-bar-left">
                <span> Developed By Syed Adnan Ahmed </span>
            </div>
            <div class="top-bar-right">
                <div>📞 <b>+91 8106109488</b></div>
                <div>✉️ <b>support@cuticarecenter.com</b></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_logo, nav_home, nav_about, nav_doctors, nav_services, nav_blog, nav_contact, col_login = st.columns(
        [3.0, 0.18, 0.18, 0.25, 0.25, 0.22, 0.25, 0.6], vertical_alignment="center", gap="small"
    )

    with col_logo:
        st.markdown("<h3 style='margin: 0; font-weight: 800;'>🏥 Cuticare Center</h3>",
                    unsafe_allow_html=True)

    with nav_home:
        if st.button("Home", key="nav_home_btn"):
            st.session_state.show_classic_login = False
            st.session_state.login_tab_focus = None
            st.session_state.selected_nav = "Home"
            st.rerun()
    with nav_about:
        if st.button("About", key="nav_about_btn"):
            st.session_state.show_classic_login = False
            st.session_state.login_tab_focus = None
            st.session_state.selected_nav = "About"
            st.rerun()
    with nav_doctors:
        if st.button("Doctors", key="nav_doc_btn"):
            st.session_state.show_classic_login = False
            st.session_state.login_tab_focus = None
            st.session_state.selected_nav = "Doctors"
            st.rerun()
    with nav_services:
        if st.button("Services", key="nav_serv_btn"):
            st.session_state.show_classic_login = False
            st.session_state.login_tab_focus = None
            st.session_state.selected_nav = "Services"
            st.rerun()
    with nav_blog:
        if st.button("Blog", key="nav_blog_btn"):
            st.session_state.show_classic_login = False
            st.session_state.login_tab_focus = None
            st.session_state.selected_nav = "Blog"
            st.rerun()
    with nav_contact:
        if st.button("Contact", key="nav_contact_btn"):
            st.session_state.show_classic_login = False
            st.session_state.login_tab_focus = None
            st.session_state.selected_nav = "Contact"
            st.rerun()
    with col_login:
        login_action = st.selectbox(
            "Account",
            ["👤 Login", "Patient", "Clinic", "Admin"],
            label_visibility="collapsed",
            key="layout_account_selectbox"
        )
        if login_action != "👤 Login":
            st.session_state.show_classic_login = True
            st.session_state.login_tab_focus = login_action
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)


def render_home_page():
    render_common_header()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "..", "..", "Dr.png")
    img_base64 = get_image_base64(image_path)

    img_tag = f'<img src="data:image/png;base64,{img_base64}" style="width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 3px solid #86efac; margin-bottom: 0.75rem;" />' if img_base64 else '<div style="font-size: 3rem;">👨‍⚕️</div>'

    st.markdown(f"""
        <style>
        .hero-container {{
            background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 50%, #7dd3fc 100%) !important;
            padding: 3.5rem 3rem;
            border-radius: 1.5rem;
            margin-bottom: 2.5rem;
            box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.15);
            border: 1px solid #7dd3fc;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 2rem;
        }}
        .hero-left-content {{
            flex: 1.3;
        }}
        .hero-right-card {{
            flex: 0.8;
            background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%) !important;
            padding: 2rem;
            border-radius: 1.5rem;
            text-align: center;
            box-shadow: 0 20px 25px -5px rgba(2, 132, 199, 0.12);
            border: 2px solid #86efac;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .hero-title {{
            font-size: 2.8rem;
            font-weight: 800;
            color: #0f172a !important;
            line-height: 1.15;
            margin-bottom: 1.2rem;
        }}
        .hero-subtitle {{
            font-size: 1.0rem;
            color: #334155 !important;
            line-height: 1.6;
            margin-bottom: 1.8rem;
            font-weight: 500;
        }}
        .hero-btn-link {{
            display: inline-block;
            background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
            border: 1px solid #d8b4fe;
            color: #7e22ce !important;
            font-weight: 700;
            padding: 0.75rem 1.75rem;
            border-radius: 0.75rem;
            text-decoration: none;
            box-shadow: 0 4px 6px -1px rgba(147, 51, 234, 0.1);
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }}
        .hero-btn-link:hover {{
            background: linear-gradient(135deg, #e9d5ff 0%, #ddd6fe 100%);
            border-color: #c084fc;
            color: #6b21a8 !important;
        }}
        .services-header {{
            text-align: center;
            margin-bottom: 2.5rem;
            margin-top: 3rem;
        }}
        .services-title {{
            font-size: 2.2rem;
            font-weight: 700;
            color: inherit;
            margin-bottom: 0.5rem;
        }}
        .services-subtitle {{
            font-size: 0.95rem;
            color: #64748b;
            max-width: 600px;
            margin: 0 auto;
        }}
        .dept-card {{
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
            border: 2px solid #e2e8f0;
            padding: 1.75rem 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04);
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }}
        .dept-card:hover {{
            transform: translateY(-6px);
            border-color: #0284c7;
            background: linear-gradient(145deg, #ffffff 0%, #f0f9ff 100%);
            box-shadow: 0 20px 25px -5px rgba(2, 132, 199, 0.15);
        }}
        .dept-icon-box {{
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: #ffffff;
            width: 55px;
            height: 55px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
            flex-shrink: 0;
            box-shadow: 0 6px 12px rgba(2, 132, 199, 0.25);
        }}
        .dept-content h4 {{
            margin: 0 0 0.4rem 0;
            font-size: 1.15rem;
            font-weight: 700;
            color: #0f172a !important;
        }}
        .dept-content p {{
            margin: 0;
            font-size: 0.85rem;
            color: #64748b !important;
            line-height: 1.4;
        }}

        /* Mobile responsive adjustments */
        @media (max-width: 768px) {{
            .hero-container {{
                flex-direction: column !important;
                padding: 2rem 1.5rem !important;
                text-align: center;
            }}
            .hero-right-card {{
                width: 100% !important;
                margin-top: 1.5rem;
            }}
            .hero-title {{
                font-size: 2.1rem !important;
            }}
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
            .top-bar-container {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
                padding: 12px 16px !important;
            }}
            .top-bar-left, .top-bar-right {{
                justify-content: center;
                gap: 15px;
            }}
        }}
        </style>

        <div class="hero-container">
            <div class="hero-left-content">
                <div class="hero-title">Your Partner In Health and Wellness</div>
                <div class="hero-subtitle">It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. Cuticare delivers top-tier clinical care and management with state-of-the-art facilities.</div>
                <a href="?action=book_appointment" target="_self" class="hero-btn-link" onclick="window.location.reload();">BOOK AN APPOINTMENT</a>
            </div>
            <div class="hero-right-card">
                {img_tag}
                <p style="font-weight: 700; color: #0f172a !important; margin: 0 0 0.3rem 0; font-size: 1.15rem;">Advanced Medical Staff</p>
                <p style="font-size: 0.85rem; color: #16a34a !important; margin: 0; font-weight: 600;">🟢 Dedicated professionals at your service 24/7.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.query_params.get("action") == "book_appointment":
        st.query_params.clear()
        st.session_state.show_classic_login = True
        st.session_state.login_tab_focus = "Patient"
        st.rerun()

    st.markdown("""
            <div class="services-header">
                <div class="services-title">Our Healthcare Services</div>
                <div class="services-subtitle">Explore our specialized dermatological care, advanced skin diagnostics, and integrated pharmacy solutions.</div>
            </div>
        """, unsafe_allow_html=True)

    dcol1, dcol2, dcol3 = st.columns(3, gap="medium")
    with dcol1:
        st.markdown("""
                <div class="dept-card">
                    <div class="dept-icon-box">🩺</div>
                    <div class="dept-content">
                        <h4>Medical Dermatology</h4>
                        <p>Expert clinical care and advanced treatment plans for acne, eczema, psoriasis, and chronic skin conditions.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    with dcol2:
        st.markdown("""
                <div class="dept-card">
                    <div class="dept-icon-box">✨</div>
                    <div class="dept-content">
                        <h4>Cosmetic Dermatology</h4>
                        <p>State-of-the-art aesthetic treatments, anti-aging therapies, laser resurfacing, and skin rejuvenation.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    with dcol3:
        st.markdown("""
                <div class="dept-card">
                    <div class="dept-icon-box">🛡️</div>
                    <div class="dept-content">
                        <h4>Pediatric & Specialized Care</h4>
                        <p>Gentle, specialized dermatological care tailored safely for infants, children, and sensitive skin types.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    dcol4, dcol5 = st.columns(2, gap="medium")
    with dcol4:
        st.markdown("""
                <div class="dept-card">
                    <div class="dept-icon-box">🔬</div>
                    <div class="dept-content">
                        <h4>In-House Diagnostic Lab</h4>
                        <p>Advanced skin scrapings, biopsies, allergy testing, and pathology diagnostics processed right on-site.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    with dcol5:
        st.markdown("""
                <div class="dept-card">
                    <div class="dept-icon-box">💊</div>
                    <div class="dept-content">
                        <h4>Integrated Pharmacy</h4>
                        <p>Fully stocked prescription pharmacy providing specialized dermatological topicals, compounded medications, and skincare regimens.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
