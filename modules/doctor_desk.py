# modules/doctor_desk.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
from modules.auth import check_role_access
from modules.notifications import add_notification
from modules.patient_logs import add_patient_log, load_patient_logs
from modules.medicine_inventory import load_medicine_inventory

UPLOAD_DIR = "uploaded_reports"


def _init_doctor_state():
    """Initializes shared memory data structures for doctor views."""
    if "appointments_db" not in st.session_state:
        st.session_state.appointments_db = pd.DataFrame([
            {
                "Appt_ID": "APT-101",
                "Patient_UID": "PAT-1001",
                "Patient_Name": "Ananya Sharma",
                "Consultant": "Dr. Sarah Jenkins (Dermatology)",
                "Date": str(date.today()),
                "Time_Slot": "10:00 AM - 10:30 AM",
                "Classification": "Initial Consultation",
                "Status": "Scheduled",
                "Booked_On": "2026-02-05 09:15:00"
            },
            {
                "Appt_ID": "APT-102",
                "Patient_UID": "PAT-1002",
                "Patient_Name": "Vikram Verma",
                "Consultant": "Dr. Rajesh Kumar (Cosmetology)",
                "Date": str(date.today()),
                "Time_Slot": "11:30 AM - 12:00 PM",
                "Classification": "Follow-up Visit",
                "Status": "Completed",
                "Booked_On": "2026-02-06 14:20:00"
            }
        ])

    if "consultations_db" not in st.session_state:
        st.session_state.consultations_db = pd.DataFrame(columns=[
            "Consult_ID", "Patient_UID", "Doctor_Name", "Date",
            "Subjective", "Objective", "Assessment", "Plan"
        ])

    if "prescriptions_db" not in st.session_state:
        st.session_state.prescriptions_db = pd.DataFrame(columns=[
            "Rx_ID", "Patient_UID", "Patient_Name", "Doctor_Name",
            "Medication_Details", "Instructions", "Dispense_Status", "Timestamp"
        ])

    if "lab_orders_queue" not in st.session_state:
        st.session_state.lab_orders_queue = pd.DataFrame(columns=[
            "Order_ID", "Patient_UID", "Patient_Name", "Test_Name", "Ordered_By", "Status", "Timestamp"
        ])

    if "lab_reports_db" not in st.session_state:
        st.session_state.lab_reports_db = pd.DataFrame(columns=[
            "Report_ID", "Patient_UID", "Patient_Name", "Test_Name",
            "File_Name", "Uploaded_By", "Status", "Timestamp"
        ])

    if "lab_orders_db" not in st.session_state:
        st.session_state.lab_orders_db = pd.DataFrame([
            {
                "Order_ID": "LAB-1001",
                "Patient_UID": "PAT-1001",
                "Patient_Name": "Ananya Sharma",
                "Test_Requested": "Skin Scraping KOH Mount",
                "Ordering_Doctor": "Dr. Sarah Jenkins",
                "Status": "Completed",
                "Lab_Notes": "Positive for fungal hyphae",
                "Source": "Lab Upload",
                "Timestamp": "2026-02-05 11:30:00"
            }
        ])


# 1. DOCTOR SCHEDULE
def render_doctor_schedule():
    st.title("🗓️ Master Appointment Schedule")
    st.caption("View scheduled encounters across all consultants")

    if not check_role_access(["DOCTOR", "ADMIN"]):
        st.error("❌ Access Denied.")
        return

    _init_doctor_state()

    df_appt = st.session_state.appointments_db.copy()

    col1, col2 = st.columns(2)
    with col1:
        doctors = ["All Doctors"] + sorted(df_appt["Consultant"].unique().tolist()) if not df_appt.empty else [
            "All Doctors"]
        filter_doc = st.selectbox("Filter by Doctor:", doctors)
    with col2:
        filter_date = st.date_input("Filter by Date:", value=date.today())

    if filter_doc != "All Doctors":
        df_appt = df_appt[df_appt["Consultant"] == filter_doc]

    if filter_date:
        df_appt = df_appt[df_appt["Date"] == str(filter_date)]

    st.markdown(f"**Total Appointments Found**: `{len(df_appt)}`")

    if df_appt.empty:
        st.info("No scheduled appointments found for the selected criteria.")
    else:
        st.dataframe(
            df_appt[["Appt_ID", "Time_Slot", "Patient_UID", "Patient_Name", "Consultant", "Classification", "Status"]],
            use_container_width=True
        )


# 2. PATIENT DIRECTORY
def render_doctor_patient_directory():
    st.title("📋 Patient Directory & Medical Demographics")
    st.caption("Read-only access to patient profiles, medical histories, and known allergies")

    if not check_role_access(["DOCTOR", "ADMIN"]):
        st.error("❌ Access Denied.")
        return

    _init_doctor_state()

    df_pat = st.session_state.patients_db.copy()

    search_term = st.text_input("🔍 Search Directory (Name, UID, or Phone):", placeholder="e.g. Ananya or PAT-1001")

    if search_term.strip():
        mask = (
                df_pat["Full_Name"].str.contains(search_term, case=False, na=False) |
                df_pat["UID"].str.contains(search_term, case=False, na=False) |
                df_pat["Contact_Number"].str.contains(search_term, case=False, na=False)
        )
        df_pat = df_pat[mask]

    st.dataframe(
        df_pat[["UID", "Full_Name", "DOB", "Gender", "Contact_Number", "Allergies", "Pre_existing_Conditions",
                "Emergency_Contact"]],
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### Historical Consultation Records")

    if not st.session_state.patients_db.empty:
        patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()
        selected_uid = st.selectbox(
            "Select Patient to Review Past Notes:",
            options=list(patient_map.keys()),
            format_func=lambda x: f"{x} - {patient_map[x]}"
        )

        logs_df = load_patient_logs()
        patient_history = pd.DataFrame()
        if not logs_df.empty:
            patient_history = logs_df[logs_df["Patient_UID"].astype(str).str.strip().str.upper() == str(selected_uid).strip().upper()]

        if patient_history.empty:
            p_consults = st.session_state.consultations_db[
                st.session_state.consultations_db["Patient_UID"] == selected_uid
            ]
            if p_consults.empty:
                st.info("No prior consultation notes logged for this patient.")
            else:
                for _, row in p_consults.iloc[::-1].iterrows():
                    with st.expander(f"🩺 Visit on {row['Date']} | Doctor: {row['Doctor_Name']}"):
                        st.write(f"**Subjective:** {row['Subjective']}")
                        st.write(f"**Objective:** {row['Objective']}")
                        st.write(f"**Assessment:** {row['Assessment']}")
                        st.write(f"**Plan:** {row['Plan']}")
        else:
            for _, row in patient_history.iloc[::-1].iterrows():
                with st.expander(f"🩺 Visit on {row['Timestamp']} | Doctor: {row['Doctor_Name']}"):
                    st.write(f"**Diagnosis:** {row['Diagnosis']}")
                    st.write(f"**Prescription:** {row['Prescription']}")
                    st.write(f"**Clinical Notes:** {row['Notes']}")


# 3. CLINICAL EHR
def render_doctor_clinical_ehr():
    st.title("🩺 Clinical EHR & Consultation Desk")
    st.caption("Record consultation notes, diagnoses, and queue e-prescriptions using dropdown selections")

    if not check_role_access(["DOCTOR", "ADMIN"]):
        st.error("❌ Access Denied.")
        return

    _init_doctor_state()

    if st.session_state.patients_db.empty:
        st.warning("No registered patients found in system.")
        return

    patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

    selected_uid = st.selectbox(
        "Select Active Patient for Encounter:",
        options=list(patient_map.keys()),
        format_func=lambda x: f"{x} - {patient_map[x]}"
    )

    p_info = st.session_state.patients_db[st.session_state.patients_db["UID"] == selected_uid].iloc[0]

    st.info(
        f"👤 **Patient**: {p_info['Full_Name']} (`{p_info['UID']}`) | **DOB**: {p_info['DOB']} | **Gender**: {p_info['Gender']}\n\n"
        f"🚨 **Allergies**: `{p_info['Allergies']}` | **Pre-existing Conditions**: `{p_info['Pre_existing_Conditions']}`"
    )

    current_doctor = st.session_state.get("current_username", "Dr. Sarah Jenkins")

    # Dropdown Options for SOAP & Plan
    subjective_options = [
        "--- Type Custom or Select Preset Below ---",
        "Patient reports persistent facial erythema and burning sensation for 2 weeks",
        "Complains of severe itching, scaling, and red patches on elbows and knees",
        "Reports sudden localized hair loss and patchy bald spots over 1 month",
        "Complains of recurrent inflammatory acne lesions on face and back"
    ]

    objective_options = [
        "--- Type Custom or Select Preset Below ---",
        "Erythematous papules and telangiectasia noted over malar and nasal regions",
        "Well-demarcated silvery-scaled plaques present on extensor surfaces",
        "Non-scarring alopecia with positive hair pull test in affected areas",
        "Multiple open/closed comedones, papules, and pustules with mild scarring"
    ]

    assessment_options = [
        "--- Type Custom or Select Preset Below ---",
        "Rosacea (Erythematotelangiectatic subtype)",
        "Psoriasis Vulgaris (Chronic plaque type)",
        "Alopecia Areata (Localized patchy hair loss)",
        "Acne Vulgaris (Moderate papulopustular)",
        "Atopic Dermatitis / Eczema flare-up"
    ]

    plan_options = [
        "--- Type Custom or Select Preset Below ---",
        "Topical Ivermectin 1% cream daily + strict sun protection and trigger avoidance",
        "Topical Clobetasol Propionate 0.05% ointment twice daily + emollient therapy",
        "Intralesional corticosteroid injection session + topical minoxidil 5%",
        "Oral Isotretinoin course + gentle cleanser and non-comedogenic moisturizer"
    ]

    # Load pharmacy options dynamically from medicine.txt via load_medicine_inventory()
    med_df = load_medicine_inventory()
    if not med_df.empty and "Medication_Name" in med_df.columns:
        pharmacy_options = ["--- Type Custom or Select Preset Below ---"] + med_df["Medication_Name"].dropna().unique().tolist()
    else:
        pharmacy_options = [
            "--- Type Custom or Select Preset Below ---",
            "Clobetasol Propionate 0.05% Ointment",
            "Tacrolimus 0.1% Topical Cream",
            "Cetirizine 10mg Tablets",
            "Ketoconazole 2% Antifungal Shampoo",
            "Isotretinoin 20mg Capsules",
            "Clindamycin 1% Topical Gel",
            "Mupirocin 2% Ointment",
            "Hydrocortisone 1% Cream"
        ]

    with st.form("clinical_ehr_form"):
        st.markdown("#### 📝 SOAP Consultation Notes")
        c1, c2 = st.columns(2)

        with c1:
            sel_subj = st.selectbox("Subjective Preset (Optional):", options=subjective_options, key="sel_subj")
            subj_default = "" if sel_subj.startswith("---") else sel_subj
            subj = st.text_area("Subjective (Chief Complaints):", value=subj_default,
                                placeholder="Type chief complaints here...")

            sel_obj = st.selectbox("Objective Preset (Optional):", options=objective_options, key="sel_obj")
            obj_default = "" if sel_obj.startswith("---") else sel_obj
            obj = st.text_area("Objective (Exam & Physical Findings):", value=obj_default,
                               placeholder="Type physical examination findings here...")

        with c2:
            sel_assess = st.selectbox("Assessment Preset (Optional):", options=assessment_options, key="sel_assess")
            assess_default = "" if sel_assess.startswith("---") else sel_assess
            assess = st.text_area("Assessment (Diagnosis):", value=assess_default, placeholder="Type diagnosis here...")

            sel_plan = st.selectbox("Plan Preset (Optional):", options=plan_options, key="sel_plan")
            plan_default = "" if sel_plan.startswith("---") else sel_plan
            plan = st.text_area("Plan (Treatment & Advice):", value=plan_default,
                                placeholder="Type treatment plan here...")

        st.markdown("---")
        st.markdown("#### 🗓️ Follow-up & Next Appointment")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            schedule_followup = st.checkbox("Schedule Follow-up Appointment", value=False)
            followup_date = st.date_input("Suggested Follow-up Date:", min_value=date.today())
        with col_f2:
            followup_time = st.selectbox(
                "Suggested Time Slot:",
                ["09:30 AM", "10:30 AM", "11:30 AM", "02:00 PM", "03:30 PM", "05:00 PM"]
            )

        st.markdown("---")
        st.markdown("#### 💊 Issue E-Prescription")

        sel_med = st.selectbox("Medication Preset (Optional):", options=pharmacy_options, key="sel_med")
        med_default = "" if sel_med.startswith("---") else sel_med
        final_meds = st.text_input("Medication Name & Strength:", value=med_default,
                                   placeholder="Type medication name and strength...")

        # Dosage Instructions Dropdown with Custom Message Option
        dosage_options = [
            "--- Select Dosage Instruction or Type Custom Below ---",
            "Take 1 tablet daily after food",
            "Take 1 tablet twice daily after meals",
            "Apply topically once daily at bedtime",
            "Apply twice daily to affected areas",
            "Take 1 capsule once a day in the morning",
            "Custom Message..."
        ]
        sel_dosage = st.selectbox("Dosage Instructions Preset:", options=dosage_options, key="sel_dosage")

        if sel_dosage == "Custom Message..." or sel_dosage.startswith("---"):
            instructions = st.text_input("Custom Dosage Instructions:", placeholder="e.g. Apply sparingly twice daily")
        else:
            instructions = sel_dosage

        issue_rx = st.checkbox("Queue E-Prescription to Pharmacy Desk", value=True)

        # 🧪 Diagnostic & Lab Test Orders Section inside Clinical EHR
        st.markdown("---")
        st.markdown("#### 🧪 Diagnostic & Lab Test Orders")

        lab_test_options = [
            "--- Select Lab Test or Type Custom Below ---",
            "Skin Biopsy Pathology Analysis",
            "Complete Blood Count (CBC) + ESR",
            "Serum IgE Allergy Panel",
            "Fungal Culture & KOH Examination",
            "Hormonal Profile (PCOS / Acne Evaluation)",
            "Custom / Other Test"
        ]

        sel_lab_test = st.selectbox("Select Lab Test to Order *", options=lab_test_options, key="consult_lab_select")

        if sel_lab_test == "Custom / Other Test" or sel_lab_test.startswith("---"):
            final_lab_test = st.text_input("Custom Lab Test Name", placeholder="e.g. Specific IgE Panel...")
        else:
            final_lab_test = sel_lab_test

        custom_lab_note = st.text_input("Clinical Instructions / Reason for Lab Test",
                                        placeholder="e.g. Rule out fungal infection...", key="consult_lab_notes")
        order_lab = st.checkbox("Assign Lab Test to Patient", value=False)

        if st.form_submit_button("Save Encounter & Issue E-Prescription", type="primary"):
            if issue_rx and not final_meds.strip():
                st.error("Please specify or select a valid medication.")
            else:
                c_id = f"CON-{1001 + len(st.session_state.consultations_db)}"
                new_consult = {
                    "Consult_ID": c_id,
                    "Patient_UID": selected_uid,
                    "Doctor_Name": current_doctor,
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Subjective": subj,
                    "Objective": obj,
                    "Assessment": assess,
                    "Plan": plan
                }
                st.session_state.consultations_db = pd.concat([
                    st.session_state.consultations_db,
                    pd.DataFrame([new_consult])
                ], ignore_index=True)

                # Persist to patient_logs.txt for Historical Consultation Records tracking
                add_patient_log(
                    patient_uid=selected_uid,
                    doctor_name=current_doctor,
                    diagnosis=assess,
                    prescription=final_meds.strip() if issue_rx else "None",
                    notes=f"Subjective: {subj} | Objective: {obj} | Plan: {plan} | Instructions: {instructions}"
                )

                if issue_rx and final_meds.strip():
                    rx_id = f"RX-{1001 + len(st.session_state.prescriptions_db)}"
                    new_rx = {
                        "Rx_ID": rx_id,
                        "Patient_UID": selected_uid,
                        "Patient_Name": p_info["Full_Name"],
                        "Doctor_Name": current_doctor,
                        "Medication_Details": final_meds.strip(),
                        "Instructions": instructions.strip(),
                        "Dispense_Status": "Pending",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.prescriptions_db = pd.concat([
                        st.session_state.prescriptions_db,
                        pd.DataFrame([new_rx])
                    ], ignore_index=True)

                    # Notify staff about new prescription queue
                    add_notification("STAFF", "Prescription",
                                     f"New e-prescription queued for {p_info['Full_Name']} by {current_doctor}.")

                # Handle Lab Test Order if checked
                if order_lab and final_lab_test and not final_lab_test.startswith("---"):
                    test_to_save = custom_lab_note if final_lab_test == "Custom / Other Test" and custom_lab_note else final_lab_test
                    new_order_id = f"L-{101 + len(st.session_state.lab_orders_queue)}"
                    new_lab_order = {
                        "Order_ID": new_order_id,
                        "Patient_UID": selected_uid,
                        "Patient_Name": p_info["Full_Name"],
                        "Test_Name": test_to_save,
                        "Ordered_By": current_doctor,
                        "Status": "Assigned by Doctor",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.lab_orders_queue = pd.concat([
                        st.session_state.lab_orders_queue,
                        pd.DataFrame([new_lab_order])
                    ], ignore_index=True)

                    add_notification(selected_uid, "Lab Assignment",
                                     f"Dr. {current_doctor} has assigned a new lab test for you: {test_to_save}.")

                # Sync follow-up appointment if checked
                if schedule_followup:
                    appts_df = st.session_state.appointments_db
                    next_id = 5001 if appts_df.empty else len(appts_df) + 5001
                    appt_id = f"APT-{next_id}"

                    new_appt = {
                        "Appt_ID": appt_id,
                        "Patient_UID": selected_uid,
                        "Patient_Name": p_info["Full_Name"],
                        "Consultant": current_doctor,
                        "Date": followup_date.strftime("%Y-%m-%d"),
                        "Time_Slot": followup_time,
                        "Classification": "Follow-up Visit",
                        "Status": "Scheduled",
                        "Booked_On": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.appointments_db = pd.concat([
                        appts_df,
                        pd.DataFrame([new_appt])
                    ], ignore_index=True)

                    add_notification("STAFF", "Appointment",
                                     f"Follow-up scheduled for {p_info['Full_Name']} on {followup_date} at {followup_time}.")

                st.success(f"✅ Encounter saved successfully for **{p_info['Full_Name']}**!")
                st.balloons()


# 4. DIAGNOSTIC REPORTS
def render_doctor_diagnostic_reports():
    st.title("🔬 Diagnostic & Lab Reports Workspace")
    st.caption("Inspect lab results and patient-uploaded medical reports")

    if not check_role_access(["DOCTOR", "ADMIN"]):
        st.error("❌ Access Denied.")
        return

    _init_doctor_state()

    df_labs = st.session_state.lab_orders_db.copy()

    t1, t2 = st.tabs(["🔬 Pathology Lab Results", "📄 Patient-Uploaded Reports"])

    with t1:
        st.subheader("Lab-Uploaded Diagnostic Results")
        if df_labs.empty:
            st.info("No lab-uploaded diagnostic results found.")
        else:
            lab_results = df_labs[df_labs["Source"] == "Lab Upload"]
            if lab_results.empty:
                st.info("No lab results recorded.")
            else:
                st.dataframe(lab_results, use_container_width=True)

    with t2:
        st.subheader("Patient-Uploaded Medical Reports & Scans")
        patients_df = st.session_state.get("patients_db", pd.DataFrame())

        if patients_df.empty:
            st.warning("No registered patient profiles available.")
            return

        patient_options = [f"{row['Full_Name']} ({row['UID']})" for _, row in patients_df.iterrows()]
        selected_patient_str = st.selectbox("Select Patient to Inspect Uploaded Files *", patient_options)
        target_uid = selected_patient_str.split("(")[-1].strip(")")
        target_name = selected_patient_str.split("(")[0].strip()

        st.markdown(f"### Attached Files for: **{target_name}** (`{target_uid}`)")

        if os.path.exists(UPLOAD_DIR):
            all_files = os.listdir(UPLOAD_DIR)
            patient_files = [f for f in all_files if f.startswith(f"{target_uid}_")]

            if not patient_files:
                st.info(f"No documents uploaded by {target_name} yet.")
            else:
                for fname in patient_files:
                    display_name = fname.replace(f"{target_uid}_", "")
                    fpath = os.path.join(UPLOAD_DIR, fname)

                    with st.container():
                        st.markdown(f"📄 **File:** `{display_name}`")
                        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                            st.image(fpath, caption=f"Uploaded Scan - {target_name}", width=400)
                        else:
                            with open(fpath, "rb") as file_download:
                                st.download_button(
                                    label=f"Download / View {display_name}",
                                    data=file_download,
                                    file_name=display_name,
                                    mime="application/octet-stream",
                                    key=f"doc_view_{fname}"
                                )
                        st.markdown("---")
        else:
            st.info("No upload directory initialized yet.")