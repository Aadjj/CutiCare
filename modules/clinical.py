# modules/clinical.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.auth import check_role_access
from modules.notifications import add_notification


def render_clinical_module():
    st.title("🩺 Cuticare Clinical EHR & Consultation Suite")
    st.caption("Doctor Workstation — SOAP Consultation Notes, E-Prescriptions & Diagnostic Reviews")

    # 1. Enforce Role-Based Access Control (RBAC) — Restricted to DOCTOR & ADMIN
    if not check_role_access(["DOCTOR", "ADMIN"]):
        st.error("❌ Access Denied: Clinical EHR workstations are strictly restricted to DOCTORS and ADMINISTRATORS.")
        return

    # Ensure required system databases exist in session state
    if "patients_db" not in st.session_state or st.session_state.patients_db.empty:
        st.warning("⚠️ No registered patients found in the database. Please onboard a patient via Front Desk first.")
        return

    if "clinical_notes_db" not in st.session_state:
        st.session_state.clinical_notes_db = pd.DataFrame(columns=[
            "Note_ID", "Patient_UID", "Patient_Name", "Doctor_Name",
            "Subjective", "Objective", "Diagnosis", "Plan", "Timestamp"
        ])

    if "prescriptions_db" not in st.session_state:
        st.session_state.prescriptions_db = pd.DataFrame(columns=[
            "Rx_ID", "Patient_UID", "Patient_Name", "Doctor_Name",
            "Medication_Details", "Instructions", "Dispense_Status", "Timestamp"
        ])

    if "lab_reports_db" not in st.session_state:
        st.session_state.lab_reports_db = pd.DataFrame(columns=[
            "Report_ID", "Patient_UID", "Patient_Name", "Test_Name",
            "File_Name", "Uploaded_By", "Status", "Timestamp"
        ])

    if "lab_orders_queue" not in st.session_state:
        st.session_state.lab_orders_queue = pd.DataFrame(columns=[
            "Order_ID", "Patient_UID", "Patient_Name", "Test_Name", "Ordered_By", "Status", "Timestamp"
        ])

    # 2. Patient Selection Workspace Header
    patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

    col_select, col_info = st.columns([1, 2])
    with col_select:
        selected_uid = st.selectbox(
            "Select Active Patient for Consultation:",
            options=list(patient_map.keys()),
            format_func=lambda x: f"{x} - {patient_map[x]}"
        )

    patient_row = st.session_state.patients_db[st.session_state.patients_db["UID"] == selected_uid].iloc[0]

    with col_info:
        st.info(
            f"👤 **Patient Profile**: {patient_row['Full_Name']} | "
            f"**DOB**: {patient_row.get('DOB', 'N/A')} | "
            f"**Gender**: {patient_row.get('Gender', 'N/A')} | "
            f"**Allergies**: 🚨 `{patient_row.get('Allergies', 'None Recorded')}`"
        )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "📝 Clinical Encounter (SOAP Notes)",
        "💊 Issue E-Prescription & Lab Orders",
        "📂 Diagnostic & Lab Reports History"
    ])

    # TAB 1: SOAP CLINICAL NOTES
    with tab1:
        st.subheader("New Consultation Entry (SOAP Framework)")

        with st.form("soap_note_form", clear_on_submit=True):
            subj = st.text_area("Subjective (Chief Complaints, History of Present Illness):", placeholder="e.g. Patient presents with flare-up of facial acne and erythema for 3 weeks...")
            obj = st.text_area("Objective (Physical & Dermatological Exam Findings):", placeholder="e.g. Multiple inflammatory papules and comedones noted on bilateral cheeks...")
            diag = st.text_input("Diagnosis / ICD Classification:", placeholder="e.g. Acne Vulgaris (Grade II - Moderate)")
            plan = st.text_area("Assessment & Treatment Plan:", placeholder="e.g. Initiate topical Retinoid therapy, oral doxycycline for 4 weeks...")

            submit_soap = st.form_submit_button("Save Clinical SOAP Encounter", type="primary")

            if submit_soap:
                if not diag.strip():
                    st.error("Please enter a valid Diagnosis before saving the encounter note.")
                else:
                    note_id = f"NOTE-{100 + len(st.session_state.clinical_notes_db) + 1}"
                    doc_name = st.session_state.get("current_username", "Dr. Y. V. Rao")

                    new_note = {
                        "Note_ID": note_id,
                        "Patient_UID": selected_uid,
                        "Patient_Name": patient_row['Full_Name'],
                        "Doctor_Name": doc_name,
                        "Subjective": subj.strip(),
                        "Objective": obj.strip(),
                        "Diagnosis": diag.strip(),
                        "Plan": plan.strip(),
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    st.session_state.clinical_notes_db = pd.concat([
                        st.session_state.clinical_notes_db,
                        pd.DataFrame([new_note])
                    ], ignore_index=True)

                    # Send notification to patient
                    add_notification(selected_uid, "Clinical", f"New clinical consultation note (#{note_id}) added by {doc_name}.")

                    st.success(f"✅ Clinical SOAP Note `{note_id}` successfully committed to EHR!")
                    st.rerun()

        st.markdown("### Past Encounters for " + patient_row['Full_Name'])
        p_notes = st.session_state.clinical_notes_db[
            st.session_state.clinical_notes_db["Patient_UID"] == selected_uid
        ]

        if p_notes.empty:
            st.info("No prior clinical consultation notes recorded for this patient.")
        else:
            for idx, row in p_notes.iterrows():
                with st.expander(f"Encounter #{row['Note_ID']} — {row['Timestamp']} ({row['Diagnosis']})"):
                    st.write(f"**Consultant**: {row['Doctor_Name']}")
                    st.write(f"**Subjective**: {row['Subjective']}")
                    st.write(f"**Objective**: {row['Objective']}")
                    st.write(f"**Diagnosis**: {row['Diagnosis']}")
                    st.write(f"**Plan**: {row['Plan']}")

    # TAB 2: E-PRESCRIPTION & LAB ORDERS
    with tab2:
        st.subheader("Issue Electronic Prescription (E-Rx)")

        # Integration with Pharmacy Inventory if available
        available_meds = []
        if "pharmacy_inventory" in st.session_state and not st.session_state.pharmacy_inventory.empty:
            available_meds = st.session_state.pharmacy_inventory["Item_Name"].tolist()

        col_rx1, col_rx2 = st.columns(2)

        with col_rx1:
            if available_meds:
                selected_med = st.selectbox("Select Item from Pharmacy Inventory:", ["Custom / Unlisted Item"] + available_meds)
                if selected_med == "Custom / Unlisted Item":
                    med_name = st.text_input("Medication Name & Dosage Form:")
                else:
                    med_name = selected_med
            else:
                med_name = st.text_input("Medication Name & Dosage Form:", placeholder="e.g. Isotretinoin 20mg Capsule")

            dosage_freq = st.selectbox("Dosage Frequency:", [
                "Once Daily (OD)", "Twice Daily (BD)", "Thrice Daily (TDS)",
                "Four Times Daily (QDS)", "At Bedtime (HS)", "As Needed (PRN)"
            ])

        with col_rx2:
            duration = st.text_input("Duration:", value="14 Days")
            instructions = st.text_area("Special Instructions for Pharmacy / Patient:", placeholder="e.g. Take after meals. Apply topically at night.")

        if st.button("Issue & Queue E-Prescription", type="primary"):
            if not med_name or not med_name.strip():
                st.error("Please specify a medication name.")
            else:
                rx_id = f"RX-{1000 + len(st.session_state.prescriptions_db) + 1}"
                doc_name = st.session_state.get("current_username", "Dr. Y. V. Rao")

                med_summary = f"{med_name.strip()} — {dosage_freq} x {duration}"

                new_rx = {
                    "Rx_ID": rx_id,
                    "Patient_UID": selected_uid,
                    "Patient_Name": patient_row['Full_Name'],
                    "Doctor_Name": doc_name,
                    "Medication_Details": med_summary,
                    "Instructions": instructions.strip(),
                    "Dispense_Status": "Pending Pharmacy Dispense",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                st.session_state.prescriptions_db = pd.concat([
                    st.session_state.prescriptions_db,
                    pd.DataFrame([new_rx])
                ], ignore_index=True)

                # Send notification to patient
                add_notification(selected_uid, "Pharmacy", f"New e-prescription (#{rx_id}) issued by {doc_name}.")

                st.success(f"🎉 E-Prescription `{rx_id}` successfully generated and queued for Pharmacy!")
                st.rerun()

        st.markdown("---")
        st.subheader("🧪 Assign Laboratory Test")

        lab_test_options = [
            "--- Select Lab Test or Type Custom Below ---",
            "Skin Biopsy Pathology Analysis",
            "Complete Blood Count (CBC) + ESR",
            "Serum IgE Allergy Panel",
            "Fungal Culture & KOH Examination",
            "Hormonal Profile (PCOS / Acne Evaluation)",
            "Custom / Other Test"
        ]

        sel_lab_test = st.selectbox("Select Lab Test to Order *", options=lab_test_options, key="clinical_lab_select")

        if sel_lab_test == "Custom / Other Test" or sel_lab_test.startswith("---"):
            final_lab_test = st.text_input("Custom Lab Test Name", placeholder="e.g. Specific IgE Panel...")
        else:
            final_lab_test = sel_lab_test

        custom_lab_note = st.text_input("Clinical Instructions / Reason for Lab Test", placeholder="e.g. Rule out fungal infection...", key="clinical_lab_notes")

        if st.button("Order Lab Test for Patient", type="secondary"):
            if not final_lab_test or final_lab_test.startswith("---"):
                st.error("Please select or specify a valid lab test name.")
            else:
                test_to_save = custom_lab_note if final_lab_test == "Custom / Other Test" and custom_lab_note else final_lab_test
                new_order_id = f"L-{101 + len(st.session_state.lab_orders_queue)}"
                doc_name = st.session_state.get("current_username", "Dr. Y. V. Rao")

                new_lab_order = {
                    "Order_ID": new_order_id,
                    "Patient_UID": selected_uid,
                    "Patient_Name": patient_row['Full_Name'],
                    "Test_Name": test_to_save,
                    "Ordered_By": doc_name,
                    "Status": "Assigned by Doctor",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.lab_orders_queue = pd.concat([
                    st.session_state.lab_orders_queue,
                    pd.DataFrame([new_lab_order])
                ], ignore_index=True)

                # TRIGGER 1: Doctor assigns lab test notification for the patient
                add_notification(selected_uid, "Lab Assignment", f"Dr. {doc_name} has assigned a new lab test for you: {test_to_save}.")

                st.success(f"✅ Lab test order **{new_order_id}** ({test_to_save}) successfully assigned to {patient_row['Full_Name']}!")

        st.markdown("---")
        st.markdown("### Prescriptions Issued for Patient")
        p_rxs = st.session_state.prescriptions_db[
            st.session_state.prescriptions_db["Patient_UID"] == selected_uid
        ]
        if p_rxs.empty:
            st.info("No active or historical e-prescriptions found for this patient.")
        else:
            st.dataframe(p_rxs, use_container_width=True)

    # TAB 3: DIAGNOSTIC & LAB REPORTS HISTORY
    with tab3:
        st.subheader("Diagnostic & Laboratory Test Files")

        p_reports = st.session_state.lab_reports_db[
            st.session_state.lab_reports_db["Patient_UID"] == selected_uid
        ]

        if p_reports.empty:
            st.info("No diagnostic or pathology reports uploaded for this patient yet.")
        else:
            st.markdown("### Uploaded Diagnostic Documents")
            st.dataframe(p_reports, use_container_width=True)