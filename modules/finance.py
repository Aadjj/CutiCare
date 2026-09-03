# modules/finance.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.auth import check_role_access
from modules.notifications import add_notification


def render_finance_module():
    st.title("📊 Cuticare Executive Financial Analytics & Accounting")
    st.caption("Revenue Intelligence, Service-wise Billing Breakdown & Audit Governance")

    # 1. Enforce Role-Based Access Control (RBAC) — Restricted to ADMIN & STAFF
    if not check_role_access(["ADMIN", "STAFF"]):
        st.error(
            "❌ Access Denied: Financial analytics and revenue management are strictly restricted to authorized staff and administrators.")
        return

    current_role = st.session_state.get("current_role", "STAFF").upper()

    # Ensure required state database exists
    if "financial_ledger" not in st.session_state or st.session_state.financial_ledger.empty:
        st.info(
            "ℹ️ No active billing or invoice records found in the financial ledger. Revenue analytics will populate as transactions are settled.")
        return

    df_ledger = st.session_state.financial_ledger.copy()

    # Convert timestamp to datetime for filtering
    if "Timestamp" in df_ledger.columns:
        df_ledger["Timestamp"] = pd.to_datetime(df_ledger["Timestamp"], errors="coerce")

    # 2. Executive KPI Cards
    settled_df = df_ledger[df_ledger["Settlement_Status"] == "Settled"]
    refunded_df = df_ledger[df_ledger["Settlement_Status"] == "Refunded / Reversed"]

    total_gross = settled_df["Gross_Amount"].astype(float).sum() if not settled_df.empty else 0.0
    total_discounts = settled_df["Discount"].astype(float).sum() if not settled_df.empty else 0.0
    total_net = settled_df["Net_Paid"].astype(float).sum() if not settled_df.empty else 0.0
    total_refunds = refunded_df["Net_Paid"].astype(float).sum() if not refunded_df.empty else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Billed Revenue", f"₹{total_gross:,.2f}")
    m2.metric("Total Discounts Allowed", f"₹{total_discounts:,.2f}")
    m3.metric("Net Cash Collections", f"₹{total_net:,.2f}")
    m4.metric("Reversals & Refunds", f"₹{total_refunds:,.2f}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "📈 Revenue Breakdown Analytics",
        "📑 Detailed Transaction Audit Ledger",
        "⚙️ Financial Controls & Reports"
    ])

    # TAB 1: REVENUE BREAKDOWN ANALYTICS
    with tab1:
        st.subheader("Revenue Streams by Billing Category")

        if not settled_df.empty:
            cat_summary = settled_df.groupby("Billing_Type")["Net_Paid"].agg(lambda x: x.astype(float).sum(),
                                                                             "count").reset_index()
            # Fix manual aggregation for sum and count safely
            cat_summary = settled_df.groupby("Billing_Type").agg(
                Net_Revenue=("Net_Paid", lambda x: x.astype(float).sum()),
                Transaction_Count=("Net_Paid", "count")
            ).reset_index()
            cat_summary.columns = ["Billing Category", "Net Revenue (₹)", "Transaction Count"]

            col_chart, col_table = st.columns([3, 2])

            with col_chart:
                st.markdown("#### Collections Distribution")
                st.bar_chart(cat_summary.set_index("Billing Category")["Net Revenue (₹)"])

            with col_table:
                st.markdown("#### Category Metrics")
                st.dataframe(cat_summary, use_container_width=True)
        else:
            st.info("No settled transactions available for category breakdown.")

    # TAB 2: DETAILED TRANSACTION AUDIT LEDGER
    with tab2:
        st.subheader("Filterable Financial Audit Trail")

        # Filters
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            status_filter = st.multiselect(
                "Filter by Settlement Status:",
                options=df_ledger["Settlement_Status"].unique().tolist(),
                default=df_ledger["Settlement_Status"].unique().tolist()
            )
        with filter_col2:
            type_filter = st.multiselect(
                "Filter by Billing Type:",
                options=df_ledger["Billing_Type"].unique().tolist(),
                default=df_ledger["Billing_Type"].unique().tolist()
            )

        filtered_df = df_ledger[
            (df_ledger["Settlement_Status"].isin(status_filter)) &
            (df_ledger["Billing_Type"].isin(type_filter))
            ]

        st.dataframe(filtered_df, use_container_width=True)

    # TAB 3: FINANCIAL CONTROLS & EXPORTS
    with tab3:
        st.subheader("Financial Reporting & Export Governance")

        st.markdown("#### 📥 Export Audit Ledger")
        csv_data = df_ledger.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Master Financial Ledger (CSV)",
            data=csv_data,
            file_name=f"Cuticare_Financial_Ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.markdown("#### 🔒 Administrative Financial Overrides")
        if current_role == "ADMIN":
            st.success(
                "✅ Executive Administrator Access Verified: You have full privilege to manage billing reversals and inventory cost structures in the **Admin Module**.")

            # Quick Action inside Finance Module for Admin convenience
            with st.expander("⚡ Quick Invoice Refund / Reversal Utility"):
                settled_invs = df_ledger[df_ledger["Settlement_Status"] == "Settled"]
                if settled_invs.empty:
                    st.info("No settled invoices available for quick reversal.")
                else:
                    rev_inv_no = st.selectbox("Select Settled Invoice to Reverse:", settled_invs["Invoice_No"].tolist(),
                                              key="fin_quick_rev")
                    rev_reason = st.text_input("Reversal Reason:", placeholder="e.g., Service cancellation/refund",
                                               key="fin_quick_reason")
                    if st.button("Process Quick Refund", type="primary", key="fin_quick_btn"):
                        if not rev_reason.strip():
                            st.error("Please enter a reversal reason.")
                        else:
                            full_ledger = st.session_state.financial_ledger
                            target_idx = full_ledger[full_ledger["Invoice_No"] == rev_inv_no].index
                            if not target_idx.empty:
                                patient_uid = full_ledger.at[target_idx[0], "Patient_UID"]
                                full_ledger.at[target_idx[0], "Settlement_Status"] = "Refunded / Reversed"
                                full_ledger.at[target_idx[0], "Net_Paid"] = 0.0
                                st.session_state.financial_ledger = full_ledger

                                # Save back to file using imported billings save helper if available or standard file write
                                from modules.billings import save_billings_db
                                save_billings_db(full_ledger)

                                # Send notification
                                if patient_uid:
                                    add_notification(patient_uid, "Billing",
                                                     f"Invoice #{rev_inv_no} has been refunded/reversed. Reason: {rev_reason}")

                                st.success(f"Successfully processed refund for invoice **{rev_inv_no}**!")
                                st.rerun()
        else:
            st.warning("🔒 Financial reversals, refunds, or fee overrides require `ADMIN` role clearance.")