# modules/billing.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from modules.auth import check_role_access
from modules.notifications import add_notification

BILLINGS_FILE = "billings.txt"


def load_billings_db():
    """Loads billings data from billings.txt with complete schema defaults."""
    if "financial_ledger" not in st.session_state:
        if os.path.exists(BILLINGS_FILE):
            try:
                df = pd.read_csv(BILLINGS_FILE, sep="|")
                df = df.fillna("")
                for col, default_val in [
                    ("Invoice_No", ""),
                    ("Patient_UID", ""),
                    ("Patient_Name", ""),
                    ("Billing_Type", ""),
                    ("Gross_Amount", "0.0"),
                    ("Discount", "0.0"),
                    ("Net_Paid", "0.0"),
                    ("Payment_Method", "Cash"),
                    ("Transaction_Ref", "N/A"),
                    ("Settlement_Status", "Pending Verification"),
                    ("Timestamp", "")
                ]:
                    if col not in df.columns:
                        df[col] = default_val
                    df[col] = df[col].astype(str).replace(["nan", "None", ""], default_val)
                st.session_state.financial_ledger = df
            except Exception as e:
                st.error(f"Error loading {BILLINGS_FILE}: {e}")
                st.session_state.financial_ledger = _get_empty_ledger_df()
        else:
            df = _get_empty_ledger_df()
            save_billings_db(df)
            st.session_state.financial_ledger = df
    return st.session_state.financial_ledger


def save_billings_db(df):
    """Saves the financial ledger DataFrame back to billings.txt."""
    try:
        df.to_csv(BILLINGS_FILE, sep="|", index=False)
        st.session_state.financial_ledger = df
    except Exception as e:
        st.error(f"Error saving to {BILLINGS_FILE}: {e}")


def _get_empty_ledger_df():
    """Returns an empty ledger DataFrame with required columns."""
    headers = [
        "Invoice_No", "Patient_UID", "Patient_Name", "Billing_Type",
        "Gross_Amount", "Discount", "Net_Paid", "Payment_Method",
        "Transaction_Ref", "Settlement_Status", "Timestamp"
    ]
    return pd.DataFrame(columns=headers)


def render_billing_module():
    st.title("💰 Cuticare Billing & Financial Checkout Engine")
    st.caption("Point-of-Sale Invoicing, Counter Settlement, Online Payments & Financial Ledger Management")

    # 1. Enforce Role-Based Access Control (RBAC)
    is_authorized_staff = check_role_access(["STAFF", "PHARMACY", "ADMIN"])
    is_patient = check_role_access(["PATIENT"])

    load_billings_db()

    if is_authorized_staff:
        current_role = st.session_state.get("current_role", "STAFF").upper()

        if "patients_db" not in st.session_state or st.session_state.patients_db.empty:
            st.warning("⚠️ No registered patients found in the registry. Onboard a patient before issuing invoices.")
            return

        tab1, tab2, tab3, tab4 = st.tabs([
            "🧾 Generate Consultation/Procedure Invoice",
            "💊 Pharmacy Counter POS Settlement",
            "⏳ Payment Verifications",
            "📋 Master Financial Ledger & Audit"
        ])

        # TAB 1: CONSULTATION & PROCEDURE INVOICING
        with tab1:
            st.subheader("Front-Desk Patient Checkout & Invoice Compilation")

            if current_role == "PHARMACY":
                st.info(
                    "ℹ️ Pharmacy Staff: Please switch to the 'Pharmacy Counter POS Settlement' tab for medication billing.")
            else:
                patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

                selected_uid = st.selectbox(
                    "Select Patient for Checkout:",
                    options=list(patient_map.keys()),
                    format_func=lambda x: f"{x} - {patient_map[x]}",
                    key="billing_consult_patient"
                )

                p_name = patient_map.get(selected_uid, "Valued Patient")

                col1, col2 = st.columns(2)
                with col1:
                    consult_fee = st.number_input("Consultation Fee (₹):", min_value=0.0, step=50.0, value=500.0)

                    procedure_options = [
                        "None",
                        "Chemical Peel (Salicylic/Glycolic) - ₹1,500",
                        "HydraFacial Clinical Session - ₹3,500",
                        "Laser Toning / Pigmentation - ₹4,500",
                        "Microdermabrasion - ₹2,000",
                        "PRP Hair Therapy - ₹6,000",
                        "Other (Custom Procedure / Service)"
                    ]

                    procedure_type = st.selectbox(
                        "Procedure / Aesthetic Service Add-on:",
                        options=procedure_options,
                        key="billing_proc_select"
                    )

                    procedure_cost = 0.0
                    final_procedure_name = procedure_type

                    if procedure_type == "Other (Custom Procedure / Service)":
                        custom_proc_name = st.text_input(
                            "Specify Custom Procedure Name:",
                            placeholder="e.g. Specialized Laser Resurfacing Session",
                            key="billing_custom_proc_name"
                        )
                        custom_proc_fee = st.number_input(
                            "Custom Procedure Fee (₹):",
                            min_value=0.0,
                            step=100.0,
                            value=2000.0,
                            key="billing_custom_proc_fee"
                        )
                        final_procedure_name = custom_proc_name.strip() if custom_proc_name else "Custom Procedure"
                        procedure_cost = custom_proc_fee
                    elif "₹" in procedure_type:
                        try:
                            procedure_cost = float(procedure_type.split("₹")[-1].replace(",", ""))
                        except ValueError:
                            procedure_cost = 0.0

                with col2:
                    subtotal = consult_fee + procedure_cost
                    discount = st.number_input("Discount / Waiver Amount (₹):", min_value=0.0, max_value=subtotal,
                                               step=50.0, value=0.0)
                    net_payable = subtotal - discount

                    st.markdown("### Payment Summary")
                    st.write(f"• Gross Consultation & Services: **₹{subtotal:,.2f}**")
                    st.write(f"• Total Discount Applied: **₹{discount:,.2f}**")
                    st.markdown(f"### Net Amount Due: **₹{net_payable:,.2f}**")

                    payment_mode = st.selectbox("Payment Settlement Mode:",
                                                ["Cash Counter", "UPI / QR Code", "Credit/Debit Card",
                                                 "Insurance / TPA"])
                    txn_ref = st.text_input("Transaction / UPI Ref ID (if online):", placeholder="e.g., UPI/123456")

                if st.button("Generate Official Invoice & Process Settlement", type="primary"):
                    if procedure_type == "Other (Custom Procedure / Service)" and not final_procedure_name.strip():
                        st.error("Please specify a valid custom procedure name.")
                    else:
                        ledger_df = load_billings_db()
                        inv_no = f"INV-{1000 + len(ledger_df) + 1}"
                        billing_desc = f"Consultation + {final_procedure_name}" if procedure_type != "None" else "Consultation Only"

                        new_invoice = {
                            "Invoice_No": inv_no,
                            "Patient_UID": selected_uid,
                            "Patient_Name": p_name,
                            "Billing_Type": billing_desc,
                            "Gross_Amount": float(subtotal),
                            "Discount": float(discount),
                            "Net_Paid": float(net_payable),
                            "Payment_Method": payment_mode,
                            "Transaction_Ref": txn_ref.strip() if txn_ref.strip() else "Counter Cash",
                            "Settlement_Status": "Settled",
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        updated_ledger = pd.concat([ledger_df, pd.DataFrame([new_invoice])], ignore_index=True)
                        save_billings_db(updated_ledger)

                        # Notify patient regarding invoice generation
                        add_notification(selected_uid, "Billing",
                                         f"New invoice #{inv_no} generated for ₹{net_payable:,.2f}.")

                        st.success(
                            f"🎉 Invoice **#{inv_no}** successfully generated and marked as **Settled** via {payment_mode}!")
                        st.balloons()

        # TAB 2: PHARMACY POS COUNTER BILLING
        with tab2:
            st.subheader("Pharmacy Point-of-Sale (POS) Counter Billing")

            patient_map = st.session_state.patients_db.set_index("UID")["Full_Name"].to_dict()

            pharm_uid = st.selectbox(
                "Select Patient Profile for Medication Billing:",
                options=list(patient_map.keys()),
                format_func=lambda x: f"{x} - {patient_map[x]}",
                key="billing_pharm_patient"
            )

            pharm_pname = patient_map.get(pharm_uid, "Valued Patient")

            st.markdown("#### Medication Line Items")

            if "pharmacy_inventory" in st.session_state and not st.session_state.pharmacy_inventory.empty:
                inv_df = st.session_state.pharmacy_inventory

                selected_meds = st.multiselect(
                    "Select Prescribed Medications Dispensed:",
                    options=inv_df["Medication_ID"].tolist(),
                    format_func=lambda
                        x: f"{inv_df[inv_df['Medication_ID'] == x]['Item_Name'].values[0]} (₹{inv_df[inv_df['Medication_ID'] == x]['Unit_Price'].values[0]}/unit)"
                )

                total_pharm_gross = 0.0
                if selected_meds:
                    st.markdown("##### Selected Itemized Breakdown:")
                    for med_id in selected_meds:
                        item_row = inv_df[inv_df["Medication_ID"] == med_id].iloc[0]
                        u_price = float(item_row["Unit_Price"])
                        qty = st.number_input(f"Quantity for {item_row['Item_Name']}:", min_value=1,
                                              max_value=int(item_row["Stock_Qty"]), value=1, key=f"qty_{med_id}")
                        line_total = u_price * qty
                        total_pharm_gross += line_total
                        st.caption(f"Subtotal for {item_row['Item_Name']}: **₹{line_total:,.2f}**")

                pharm_discount = st.number_input("Pharmacy Discount (₹):", min_value=0.0,
                                                 max_value=max(0.0, total_pharm_gross), value=0.0, key="pharm_disc")
                pharm_net = total_pharm_gross - pharm_discount

                st.markdown(f"### Total Pharmacy Bill: **₹{pharm_net:,.2f}**")

                if st.button("Complete Pharmacy Transaction & Issue POS Receipt", type="primary"):
                    if total_pharm_gross <= 0:
                        st.error("Please select at least one medication to process pharmacy billing.")
                    else:
                        ledger_df = load_billings_db()
                        inv_no = f"INV-{1000 + len(ledger_df) + 1}"
                        pharm_invoice = {
                            "Invoice_No": inv_no,
                            "Patient_UID": pharm_uid,
                            "Patient_Name": pharm_pname,
                            "Billing_Type": "Pharmacy Dispensed Medicines",
                            "Gross_Amount": float(total_pharm_gross),
                            "Discount": float(pharm_discount),
                            "Net_Paid": float(pharm_net),
                            "Payment_Method": "Pharmacy Counter Cash/UPI",
                            "Transaction_Ref": "POS-COUNTER",
                            "Settlement_Status": "Settled",
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        updated_ledger = pd.concat([ledger_df, pd.DataFrame([pharm_invoice])], ignore_index=True)
                        save_billings_db(updated_ledger)

                        # Notify patient regarding pharmacy billing
                        add_notification(pharm_uid, "Billing",
                                         f"Pharmacy receipt #{inv_no} generated for ₹{pharm_net:,.2f}.")

                        st.success(
                            f"✅ Pharmacy POS Receipt **#{inv_no}** generated for {pharm_pname}. Payment settled.")
                        st.rerun()
            else:
                st.info("Pharmacy inventory data is currently empty. Initialize pharmacy stock in the Admin module.")

        # TAB 3: PAYMENT VERIFICATIONS (STAFF/ADMIN)
        with tab3:
            st.subheader("⏳ Patient Online Payment Confirmations & Verification Desk")
            st.caption("Review submitted online payments and transaction references awaiting staff clearance.")

            ledger_df = load_billings_db()
            pending_payments = ledger_df[ledger_df["Settlement_Status"] == "Pending Verification"]

            if pending_payments.empty:
                st.info("No pending payment verifications requiring staff attention.")
            else:
                for idx, row in pending_payments.iterrows():
                    with st.expander(f"Invoice: {row['Invoice_No']} | {row['Patient_Name']} (₹{row['Net_Paid']})"):
                        st.write(f"**Patient UID**: `{row['Patient_UID']}`")
                        st.write(f"**Billing Category**: {row['Billing_Type']}")
                        st.write(f"**Payment Method**: {row['Payment_Method']}")
                        st.write(f"**Transaction Ref / UPI ID**: `{row['Transaction_Ref']}`")
                        st.write(f"**Timestamp**: {row['Timestamp']}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Confirm Payment", key=f"conf_pay_{row['Invoice_No']}"):
                                full_ledger = load_billings_db()
                                target_idx = full_ledger[full_ledger["Invoice_No"] == row["Invoice_No"]].index
                                if not target_idx.empty:
                                    full_ledger.at[target_idx[0], "Settlement_Status"] = "Settled"
                                    save_billings_db(full_ledger)

                                    # Notify patient regarding payment confirmation
                                    add_notification(row["Patient_UID"], "Billing",
                                                     f"Your payment for invoice {row['Invoice_No']} has been verified and settled.")

                                    st.success(f"Invoice {row['Invoice_No']} verified and settled successfully!")
                                    st.rerun()
                        with col2:
                            if st.button("❌ Reject Payment", key=f"rej_pay_{row['Invoice_No']}"):
                                full_ledger = load_billings_db()
                                target_idx = full_ledger[full_ledger["Invoice_No"] == row["Invoice_No"]].index
                                if not target_idx.empty:
                                    full_ledger.at[target_idx[0], "Settlement_Status"] = "Rejected / Invalid"
                                    save_billings_db(full_ledger)

                                    # Notify patient regarding payment rejection
                                    add_notification(row["Patient_UID"], "Billing",
                                                     f"Your payment for invoice {row['Invoice_No']} was rejected. Please re-submit.")

                                    st.warning(f"Invoice {row['Invoice_No']} marked as rejected.")
                                    st.rerun()

        # TAB 4: MASTER FINANCIAL LEDGER & AUDIT
        with tab4:
            st.subheader("Central Clinic Financial & Invoice Ledger")

            ledger_df = load_billings_db()
            if ledger_df.empty:
                st.info("No invoice transactions logged in the financial ledger.")
            else:
                m1, m2, m3 = st.columns(3)
                settled_mask = ledger_df["Settlement_Status"] == "Settled"

                m1.metric("Total Generated Invoices", len(ledger_df))
                m2.metric("Total Net Collections", f"₹{ledger_df[settled_mask]['Net_Paid'].astype(float).sum():,.2f}")
                m3.metric("Total Discounts Granted", f"₹{ledger_df['Discount'].astype(float).sum():,.2f}")

                st.markdown("### Detailed Transaction Log")
                st.dataframe(ledger_df, use_container_width=True)

                st.markdown("---")
                if current_role == "ADMIN":
                    st.info(
                        "💡 As an Administrator, you can process invoice refunds or reversals directly in the Admin Module.")
                else:
                    st.caption(
                        "🔒 **Notice**: Financial reversals, refunds, or invoice cancellations require `ADMIN` authorization.")

    elif is_patient:
        # ----------------------------------------------------
        # PATIENT VIEW: VIEW INVOICES & SUBMIT ONLINE PAYMENTS
        # ----------------------------------------------------
        st.subheader("💳 Your Consultation & Procedure Invoices")
        st.caption("Review your medical invoices, settlement statuses, and submit online payment transaction receipts.")

        current_username = st.session_state.get("current_username", "")
        current_user_id = st.session_state.get("patient_uid", "")

        ledger_df = load_billings_db()

        if ledger_df.empty:
            st.info("No invoices found in the system.")
        else:
            my_invoices = pd.DataFrame()
            if "Patient_UID" in ledger_df.columns and current_user_id:
                my_invoices = ledger_df[ledger_df["Patient_UID"] == current_user_id]
            if my_invoices.empty and current_username:
                my_invoices = ledger_df[ledger_df["Patient_Name"].str.lower() == current_username.lower()]

            if my_invoices.empty:
                st.info("No invoices recorded under your patient profile.")
            else:
                st.dataframe(my_invoices[["Invoice_No", "Billing_Type", "Gross_Amount", "Discount", "Net_Paid",
                                          "Settlement_Status", "Timestamp"]], use_container_width=True)

                st.markdown("---")
                st.markdown("### Submit Online Payment / Receipt Details")
                with st.form("patient_online_payment_form"):
                    unsettled_invoices = my_invoices[my_invoices["Settlement_Status"] != "Settled"]
                    if unsettled_invoices.empty:
                        st.info("All your generated invoices are already fully settled!")
                        inv_to_pay = st.text_input("Invoice Number", value="INV-1001")
                        amount_to_pay = st.number_input("Amount (₹)", min_value=0.0, value=500.0)
                    else:
                        inv_to_pay = st.selectbox("Select Unsettled Invoice:",
                                                  unsettled_invoices["Invoice_No"].tolist())
                        selected_row = unsettled_invoices[unsettled_invoices["Invoice_No"] == inv_to_pay].iloc[0]
                        amount_to_pay = float(selected_row["Net_Paid"])
                        st.write(f"Amount Due for **{inv_to_pay}**: ₹{amount_to_pay:,.2f}")

                    gateway_method = st.selectbox("Payment Gateway Method",
                                                  ["UPI / QR Code Scan", "Credit / Debit Card", "NetBanking"])
                    txn_reference = st.text_input("Transaction / UPI Reference Number *",
                                                  placeholder="e.g., UPI123456789")

                    submit_online_pay = st.form_submit_button("Submit Payment for Verification", type="primary")

                    if submit_online_pay:
                        if not txn_reference.strip():
                            st.error("Please enter a valid transaction reference or receipt code.")
                        else:
                            full_ledger = load_billings_db()
                            target_idx = full_ledger[full_ledger["Invoice_No"] == inv_to_pay].index

                            if not target_idx.empty:
                                full_ledger.at[target_idx[0], "Payment_Method"] = gateway_method
                                full_ledger.at[target_idx[0], "Transaction_Ref"] = txn_reference.strip()
                                full_ledger.at[target_idx[0], "Settlement_Status"] = "Pending Verification"
                                save_billings_db(full_ledger)

                                # Notify staff regarding online payment submission
                                add_notification("STAFF", "Billing",
                                                 f"Online payment submitted for invoice {inv_to_pay} by {current_username}.")

                                st.success(
                                    f"🎉 Payment receipt for **{inv_to_pay}** submitted successfully! Awaiting clinic staff verification.")
                                st.rerun()
                            else:
                                st.error("Invoice reference not found.")
    else:
        st.error("❌ Access Denied: Unauthorized role context.")