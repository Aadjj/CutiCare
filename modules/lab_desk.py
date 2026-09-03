# modules/lab_desk.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.auth import check_role_access
from modules.notifications import add_notification

UPLOAD_DIR = "uploaded_reports"


def ensure_upload_dir():
    """Ensures the temporary upload folder exists."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)


def render_lab_desk_module():
    st.title("🔬 Cuticare Pathology & Diagnostic Laboratory Workstation")
    st.caption("Diagnostic Orders Queue, Secure Result Entry & Patient Report Repository")

    ensure_upload_dir()

    # 1. Enforce Role-Based Access Control (RBAC) — Restricted to LAB, DOCTOR & ADMIN
    if not check_role_access(["LAB", "DOCTOR", "ADMIN"]):
        st.error(
            "❌ Access Denied: Diagnostic laboratory processing is strictly restricted to LAB TECHNICIANS, DOCTORS, and ADMINISTRATORS.")
        return

    # Ensure required databases exist in session state
    if "patients_db" not in st.session_state or st.session_state.patients_db.empty:
        st.warning("⚠️ No patient records found in the system. Onboard patients via Front Desk first.")
        return

    if "lab_reports_db" not in st.session_state:
        st.session_state.lab_reports_db = pd.DataFrame(columns=[
            "Report_ID", "Patient_UID", "Patient_Name", "Test_Name",
            "File_Name", "Uploaded_By", "Status", "Timestamp"
        ])

    # Pre-populate sample lab orders queue if not present
    if "lab_orders_queue" not in st.session_state:
        st.session_state.lab_orders_queue = pd.DataFrame([
            {
                "Order_ID": "L-101",
                "Patient_UID": st.session_state.patients_db.iloc[0]["UID"],
                "Patient_Name": st.session_state.patients_db.iloc[0]["Full_Name"],
                "Test_Name": "Complete Blood Count (CBC) + ESR",
                "Ordered_By": "Dr. Sarah Jenkins",
                "Status": "Pending Sample Collection",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "Order_ID": "L-102",
                "Patient_UID": st.session_state.patients_db.iloc[0]["UID"],
                "Patient_Name": st.session_state.patients_db.iloc[0]["Full_Name"],
                "Test_Name": "Skin Biopsy Pathology Analysis",
                "Ordered_By": "Dr. Sarah Jenkins",
                "Status": "In Processing",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ])

    tab1, tab2, tab3 = st.tabs([
        "📥 Pending Test Queue",
        "📤 Result Entry & Secure Report Upload",
        "📂 Diagnostic Repository Archive"
    ])

    # TAB 1: PENDING LAB QUEUE
    with tab1:
        st.subheader("Active Diagnostic Orders")

        if st.session_state.lab_orders_queue.empty:
            st.info("No active diagnostic orders currently queued.")
        else:
            st.dataframe(st.session_state.lab_orders_queue, use_container_width=True)

    # TAB 2: RESULT ENTRY & REPORT UPLOAD
    with tab2:
        st.subheader("Process Test & Securely Attach Diagnostic Report")

        patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

        with st.form("lab_report_upload_form", clear_on_submit=True):
            col_p, col_t = st.columns(2)

            with col_p:
                selected_uid = st.selectbox(
                    "Select Patient *",
                    options=list(patient_map.keys()),
                    format_func=lambda x: f"{x} - {patient_map[x]}"
                )

            with col_t:
                test_name = st.selectbox("Diagnostic Test Category *", [
                    "Skin Biopsy Pathology Analysis",
                    "Complete Blood Count (CBC) + ESR",
                    "Serum IgE Allergy Panel",
                    "Fungal Culture & KOH Examination",
                    "Hormonal Profile (PCOS / Acne Evaluation)",
                    "Custom / Other Test"
                ])

                if test_name == "Custom / Other Test":
                    test_name = st.text_input("Specify Test Name *")

            uploaded_file = st.file_uploader(
                "Upload Diagnostic Report / Pathology File (PDF, PNG, JPG):",
                type=["pdf", "png", "jpg", "jpeg"]
            )

            tech_notes = st.text_area("Lab Technician Observations / Summary Findings:",
                                      placeholder="e.g. Epidermal hyperkeratosis observed. Fungal elements negative...")

            submit_report = st.form_submit_button("Publish & Securely Attach Report", type="primary")

            if submit_report:
                if not test_name or not test_name.strip():
                    st.error("Please specify a valid test name.")
                else:
                    report_id = f"RPT-{100 + len(st.session_state.lab_reports_db) + 1}"

                    # Securely handle file storage tied strictly to Patient UID
                    stored_filename = "None"
                    if uploaded_file is not None:
                        orig_name = uploaded_file.name.replace(" ", "_")
                        stored_filename = f"{selected_uid}_{orig_name}"
                        file_path = os.path.join(UPLOAD_DIR, stored_filename)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    else:
                        stored_filename = f"{selected_uid}_Digital_Lab_Summary.txt"
                        file_path = os.path.join(UPLOAD_DIR, stored_filename)
                        with open(file_path, "w") as f:
                            f.write(f"Test: {test_name}\nNotes: {tech_notes}")

                    tech_username = st.session_state.get("current_username", "Pathology Lab Tech")
                    patient_full_name = patient_map.get(selected_uid, "Patient")

                    new_report = {
                        "Report_ID": report_id,
                        "Patient_UID": selected_uid,
                        "Patient_Name": patient_full_name,
                        "Test_Name": test_name.strip(),
                        "File_Name": stored_filename,
                        "Uploaded_By": tech_username,
                        "Status": "Completed & Verified",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    st.session_state.lab_reports_db = pd.concat([
                        st.session_state.lab_reports_db,
                        pd.DataFrame([new_report])
                    ], ignore_index=True)

                    # Update order status in queue if present
                    if not st.session_state.lab_orders_queue.empty:
                        st.session_state.lab_orders_queue.loc[
                            (st.session_state.lab_orders_queue["Patient_UID"] == selected_uid) &
                            (st.session_state.lab_orders_queue["Test_Name"] == test_name),
                            "Status"
                        ] = "Completed"

                    # -------------------------------------------------------------
                    # NOTIFICATIONS INTEGRATION
                    # -------------------------------------------------------------
                    # 1. Notify the specific patient
                    add_notification(selected_uid, "Lab",
                                     f"Your diagnostic report for {test_name} has been published (#{report_id}).")

                    # 2. Notify staff and doctors that a new lab report/test has been uploaded
                    add_notification("STAFF", "Lab",
                                     f"Patient {patient_full_name} ({selected_uid}) has uploaded/completed a new lab report: {test_name} (#{report_id}).")
                    add_notification("DOCTOR", "Lab",
                                     f"New diagnostic report uploaded for {patient_full_name}: {test_name} (#{report_id}).")
                    # -------------------------------------------------------------

                    st.success(f"✅ Diagnostic Report `{report_id}` securely attached to ID `{selected_uid}`!")
                    st.rerun()

    # TAB 3: DIAGNOSTIC REPOSITORY ARCHIVE
    with tab3:
        st.subheader("Master Laboratory Reports Archive & File Inspector")

        if st.session_state.lab_reports_db.empty:
            st.info("No published lab reports found in the repository archive.")
        else:
            st.dataframe(st.session_state.lab_reports_db, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🔍 Inspect Attached Files by Patient ID")

            patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()
            filter_uid = st.selectbox(
                "Select Patient ID to Review Attached Documents:",
                options=list(patient_map.keys()),
                format_func=lambda x: f"{x} - {patient_map[x]}",
                key="archive_patient_filter"
            )

            if os.path.exists(UPLOAD_DIR):
                all_files = os.listdir(UPLOAD_DIR)
                patient_files = [f for f in all_files if f.startswith(f"{filter_uid}_")]

                if not patient_files:
                    st.info(f"No files currently attached to patient ID `{filter_uid}`.")
                else:
                    for fname in patient_files:
                        display_name = fname.replace(f"{filter_uid}_", "")
                        fpath = os.path.join(UPLOAD_DIR, fname)

                        with st.container():
                            st.markdown(f"📄 **File:** `{display_name}`")
                            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                                st.image(fpath, caption=f"Attached Scan for {filter_uid}", width=400)
                            else:
                                with open(fpath, "rb") as file_download:
                                    st.download_button(
                                        label=f"Download / View {display_name}",
                                        data=file_download,
                                        file_name=display_name,
                                        mime="application/octet-stream",
                                        key=f"archive_dl_{fname}"
                                    )
                            st.markdown("---")