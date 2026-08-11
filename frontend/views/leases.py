from datetime import date

import pandas as pd
import streamlit as st

from lib.api import ApiError, create_lease, list_leases, list_properties, update_lease

st.title("Leases")

try:
    properties = list_properties()
except ApiError as e:
    st.error(str(e))
    properties = []

if not properties:
    st.warning("Add a property first.")
else:
    property_options = {p["name"]: p["id"] for p in properties}

    st.subheader("Add a lease")
    with st.form("add_lease", clear_on_submit=True):
        property_name = st.selectbox("Property", list(property_options.keys()))
        tenant_name = st.text_input("Tenant name")
        col1, col2 = st.columns(2)
        with col1:
            tenant_email = st.text_input("Tenant email")
            monthly_rent = st.number_input("Monthly rent", min_value=0.0, step=10.0)
            start_date = st.date_input("Start date", value=date.today())
        with col2:
            tenant_phone = st.text_input("Tenant phone")
            deposit = st.number_input("Deposit", min_value=0.0, step=10.0)
            ongoing = st.checkbox("Ongoing / no fixed end date", value=True)
            end_date = None if ongoing else st.date_input("End date", value=date.today())
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add lease")

    if submitted:
        if not tenant_name:
            st.error("Tenant name is required.")
        else:
            try:
                create_lease(
                    property_id=property_options[property_name],
                    tenant_name=tenant_name,
                    tenant_email=tenant_email or None,
                    tenant_phone=tenant_phone or None,
                    monthly_rent=monthly_rent,
                    deposit=deposit or None,
                    start_date=str(start_date),
                    end_date=str(end_date) if end_date else None,
                    notes=notes or None,
                )
                st.success(f"Added lease for {tenant_name}.")
                st.rerun()
            except ApiError as e:
                st.error(str(e))

    st.subheader("Current leases")
    show_active_only = st.checkbox("Show only active today", value=True)
    try:
        leases = list_leases(active_on=str(date.today()) if show_active_only else None)
    except ApiError as e:
        st.error(str(e))
        leases = []

    if leases:
        property_names = {v: k for k, v in property_options.items()}
        df = pd.DataFrame(leases)
        df["property"] = df["property_id"].map(property_names)
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["end_date"] = pd.to_datetime(df["end_date"])
        df = df.drop(columns=["id", "property_id"])
        df = df[["property"] + [c for c in df.columns if c != "property"]]
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "monthly_rent": st.column_config.NumberColumn("Monthly rent", format="%.2f"),
                "deposit": st.column_config.NumberColumn("Deposit", format="%.2f"),
                "start_date": st.column_config.DateColumn("Start date", format="YYYY-MM-DD"),
                "end_date": st.column_config.DateColumn("End date", format="YYYY-MM-DD"),
                "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
                "updated_at": st.column_config.DatetimeColumn("Updated", format="YYYY-MM-DD HH:mm"),
            },
        )

        st.subheader("End a lease")
        lease_options = {
            f"{l['tenant_name']} — {property_names.get(l['property_id'], '?')} (from {l['start_date']})": l
            for l in leases
        }
        choice = st.selectbox("Lease", list(lease_options.keys()))
        new_end = st.date_input("Move-out date", value=date.today(), key="end_lease_date")
        if st.button("Set end date"):
            try:
                update_lease(lease_options[choice]["id"], end_date=str(new_end))
                st.success("Lease updated.")
                st.rerun()
            except ApiError as e:
                st.error(str(e))
    else:
        st.info("No leases yet.")
