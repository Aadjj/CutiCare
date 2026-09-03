# modules/pharmacy.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.auth import check_role_access
from modules.notifications import add_notification
from modules.medicine_inventory import load_medicine_inventory, update_medicine_stock


def render_pharmacy_module():
    st.title("💊 Cuticare Pharmacy Operations & E-Prescription Desk")
    st.caption("Fulfillment Queue, Dispensing Workflow, POS Counter Settlement & Inventory Monitor")

    # 1. Enforce Role-Based Access Control (RBAC) — Restricted to PHARMACY, STAFF & ADMIN
    if not check_role_access(["PHARMACY", "STAFF", "ADMIN"]):
        st.error("❌ Access Denied: The Pharmacy Desk is restricted to PHARMACY STAFF, FRONT DESK, and ADMINISTRATORS.")
        return

    current_role = st.session_state.get("current_role", "PHARMACY").upper()

    # Ensure required system databases exist in session state
    if "patients_db" not in st.session_state or st.session_state.patients_db.empty:
        st.warning(
            "⚠️ No registered patients found in the registry. Onboard a patient before processing prescriptions.")
        return

    if "prescriptions_db" not in st.session_state:
        st.session_state.prescriptions_db = pd.DataFrame(columns=[
            "Rx_ID", "Patient_UID", "Patient_Name", "Doctor_Name",
            "Medication_Details", "Instructions", "Dispense_Status", "Timestamp"
        ])

    # Synchronize pharmacy inventory with medicine.txt via medicine_inventory module
    med_df = load_medicine_inventory()
    if not med_df.empty:
        # Map medicine.txt columns to pharmacy format for backwards compatibility with the UI
        mapped_inv = pd.DataFrame({
            "Medication_ID": med_df["Med_ID"],
            "Item_Name": med_df["Medication_Name"],
            "Category": med_df["Category"],
            "Stock_Qty": pd.to_numeric(med_df["Stock_Quantity"], errors="coerce").fillna(0).astype(int),
            "Unit_Price": med_df["Unit_Price"].astype(str).str.replace("₹", "").str.strip().astype(float),
            "Reorder_Level": 20
        })
        st.session_state.pharmacy_inventory = mapped_inv
    elif "pharmacy_inventory" not in st.session_state:
        st.session_state.pharmacy_inventory = pd.DataFrame(columns=[
            "Medication_ID", "Item_Name", "Category", "Stock_Qty", "Unit_Price", "Reorder_Level"
        ])

    if "financial_ledger" not in st.session_state:
        st.session_state.financial_ledger = pd.DataFrame(columns=[
            "Invoice_No", "Patient_UID", "Patient_Name", "Billing_Type",
            "Gross_Amount", "Discount", "Net_Paid", "Settlement_Status", "Timestamp"
        ])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 E-Prescription Queue & Dispensing",
        "👤 Patient History Lookup",
        "💰 Pharmacy POS Checkout",
        "📦 View Inventory Levels"
    ])

    # TAB 1: E-PRESCRIPTION QUEUE & DISPENSING WORKFLOW
    with tab1:
        st.subheader("Doctor E-Prescriptions Pending Dispense")

        df_rx = st.session_state.prescriptions_db.copy()

        if df_rx.empty:
            st.info("No active e-prescriptions found in the clinic queue.")
        else:
            pending_rxs = df_rx[df_rx["Dispense_Status"] != "Dispensed"]
            completed_rxs = df_rx[df_rx["Dispense_Status"] == "Dispensed"]

            st.markdown(f"#### ⏳ Pending Orders ({len(pending_rxs)})")

            if pending_rxs.empty:
                st.success("🎉 All active e-prescriptions have been processed and dispensed!")
            else:
                for idx, rx in pending_rxs.iterrows():
                    with st.expander(f"Rx #{rx['Rx_ID']} — {rx['Patient_Name']} (Issued by {rx['Doctor_Name']})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Medication**: {rx['Medication_Details']}")
                            st.write(f"**Instructions**: {rx['Instructions']}")
                            st.write(f"**Timestamp**: {rx['Timestamp']}")
                            st.caption(f"Status: `{rx['Dispense_Status']}`")

                        with col2:
                            if st.button("Mark as Dispensed", key=f"dispense_{rx['Rx_ID']}", type="primary"):
                                st.session_state.prescriptions_db.loc[
                                    st.session_state.prescriptions_db["Rx_ID"] == rx["Rx_ID"],
                                    "Dispense_Status"
                                ] = "Dispensed"

                                # Automatically deduct stock from medicine.txt if medication name matches inventory
                                med_name_str = str(rx["Medication_Details"])
                                for _, m_row in med_df.iterrows():
                                    if m_row[
                                        "Medication_Name"].lower() in med_name_str.lower() or med_name_str.lower() in \
                                            m_row["Medication_Name"].lower():
                                        update_medicine_stock(m_row["Med_ID"], 1, is_addition=False)

                                # Send notification to patient
                                add_notification(rx["Patient_UID"], "Pharmacy",
                                                 f"Your prescription #{rx['Rx_ID']} has been marked as Dispensed.")

                                st.success(f"✅ Rx #{rx['Rx_ID']} updated to **Dispensed** and stock synchronized!")
                                st.rerun()

            if not completed_rxs.empty:
                st.markdown("---")
                st.markdown(f"#### ✅ Dispensed History ({len(completed_rxs)})")
                st.dataframe(completed_rxs, use_container_width=True)

    # TAB 2: PATIENT HISTORY LOOKUP
    with tab2:
        st.subheader("Patient Demographic & Medical History Reference")

        patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

        selected_uid = st.selectbox(
            "Select Patient to Inspect Medical Record:",
            options=list(patient_map.keys()),
            format_func=lambda x: f"{x} - {patient_map[x]}"
        )

        patient_row = st.session_state.patients_db[st.session_state.patients_db["UID"] == selected_uid].iloc[0]

        st.info(
            f"👤 **Patient Profile**: {patient_row['Full_Name']} | "
            f"**Contact**: {patient_row.get('Contact_Number', 'N/A')} | "
            f"**Allergies**: 🚨 `{patient_row.get('Allergies', 'None Recorded')}`"
        )

        st.markdown("### Prescriptions Issued for Patient")
        p_rxs = st.session_state.prescriptions_db[
            st.session_state.prescriptions_db["Patient_UID"] == selected_uid
            ]

        if p_rxs.empty:
            st.info("No prescription history found for this patient.")
        else:
            st.dataframe(p_rxs, use_container_width=True)

    # TAB 3: PHARMACY POS COUNTER BILLING
    with tab3:
        st.subheader("Pharmacy Point-of-Sale (POS) Counter Settlement")

        patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

        pharm_uid = st.selectbox(
            "Select Patient for Pharmacy Settlement:",
            options=list(patient_map.keys()),
            format_func=lambda x: f"{x} - {patient_map[x]}",
            key="pharm_pos_patient"
        )

        pharm_pname = patient_map.get(pharm_uid, "Valued Patient")

        st.markdown("#### Medication Line Items")

        inv_df = st.session_state.pharmacy_inventory

        if inv_df.empty:
            st.warning("Pharmacy stock inventory is empty. Stock items must be added by Administrator.")
        else:
            selected_meds = st.multiselect(
                "Select Prescribed Items to Bill:",
                options=inv_df["Medication_ID"].tolist(),
                format_func=lambda
                    x: f"{inv_df[inv_df['Medication_ID'] == x]['Item_Name'].values[0]} (₹{inv_df[inv_df['Medication_ID'] == x]['Unit_Price'].values[0]}/unit)"
            )

            total_pharm_gross = 0.0
            if selected_meds:
                st.markdown("##### Itemized Breakdown:")
                for med_id in selected_meds:
                    item_row = inv_df[inv_df["Medication_ID"] == med_id].iloc[0]
                    u_price = float(item_row["Unit_Price"])
                    max_stock = max(1, int(item_row["Stock_Qty"]))
                    qty = st.number_input(
                        f"Quantity for {item_row['Item_Name']} (In Stock: {max_stock}):",
                        min_value=1,
                        max_value=max_stock,
                        value=1,
                        key=f"pos_qty_{med_id}"
                    )
                    line_total = u_price * qty
                    total_pharm_gross += line_total
                    st.caption(f"Subtotal for {item_row['Item_Name']}: **₹{line_total:,.2f}**")

            pharm_discount = st.number_input("Pharmacy Discount (₹):", min_value=0.0,
                                             max_value=max(0.0, total_pharm_gross), value=0.0, key="pharm_pos_disc")
            pharm_net = total_pharm_gross - pharm_discount

            st.markdown(f"### Net Amount Payable: **₹{pharm_net:,.2f}**")

            payment_mode = st.selectbox("Payment Mode:", ["Cash", "UPI / QR Code", "Credit/Debit Card"])

            if st.button("Complete POS Settlement & Issue Receipt", type="primary"):
                if total_pharm_gross <= 0:
                    st.error("Please select at least one medication to process POS billing.")
                else:
                    inv_no = f"INV-{1000 + len(st.session_state.financial_ledger) + 1}"
                    pharm_invoice = {
                        "Invoice_No": inv_no,
                        "Patient_UID": pharm_uid,
                        "Patient_Name": pharm_pname,
                        "Billing_Type": "Pharmacy Dispensed Medicines",
                        "Gross_Amount": float(total_pharm_gross),
                        "Discount": float(pharm_discount),
                        "Net_Paid": float(pharm_net),
                        "Settlement_Status": "Settled",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Deduct inventory quantities immediately in medicine.txt and session state
                    for med_id in selected_meds:
                        item_idx = st.session_state.pharmacy_inventory[
                            st.session_state.pharmacy_inventory["Medication_ID"] == med_id].index[0]
                        purchased_qty = st.session_state.get(f"pos_qty_{med_id}", 1)
                        st.session_state.pharmacy_inventory.at[item_idx, "Stock_Qty"] -= purchased_qty

                        # Immediate update in medicine.txt
                        update_medicine_stock(med_id, purchased_qty, is_addition=False)

                    # Log to ledger
                    st.session_state.financial_ledger = pd.concat([
                        st.session_state.financial_ledger,
                        pd.DataFrame([pharm_invoice])
                    ], ignore_index=True)

                    # Send notification to patient
                    add_notification(pharm_uid, "Billing",
                                     f"Pharmacy POS Invoice #{inv_no} settled for ₹{pharm_net:,.2f}.")

                    st.success(
                        f"🎉 POS Receipt **#{inv_no}** generated for {pharm_pname}. Inventory quantities instantly updated in `medicine.txt`.")
                    st.balloons()

    # TAB 4: VIEW INVENTORY LEVELS (VIEW-ONLY FOR PHARMACY STAFF)
    with tab4:
        st.subheader("Pharmacy Stock Inventory Levels")
        st.caption("Synchronized in real-time with `medicine.txt` master stock registry.")

        # Reload latest from medicine.txt
        latest_med_df = load_medicine_inventory()
        if not latest_med_df.empty:
            inv_display = pd.DataFrame({
                "Medication_ID": latest_med_df["Med_ID"],
                "Item_Name": latest_med_df["Medication_Name"],
                "Category": latest_med_df["Category"],
                "Stock_Qty": pd.to_numeric(latest_med_df["Stock_Quantity"], errors="coerce").fillna(0).astype(int),
                "Unit_Price": latest_med_df["Unit_Price"],
                "Expiry_Date": latest_med_df["Expiry_Date"],
                "Last_Updated": latest_med_df["Last_Updated"]
            })

            low_stock = inv_display[inv_display["Stock_Qty"] <= 20]
            if not low_stock.empty:
                st.warning(f"⚠️ **Low Stock Alert**: {len(low_stock)} item(s) are running low!")
                st.dataframe(low_stock, use_container_width=True)

            st.markdown("### Master Stock Registry (`medicine.txt`)")
            st.dataframe(inv_display, use_container_width=True)
        else:
            st.info("No inventory records found in `medicine.txt`.")

        if current_role != "ADMIN":
            st.info("🔒 Stock additions and price edits are restricted to `ADMIN` users.")