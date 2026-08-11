from datetime import date

import pandas as pd
import streamlit as st

from lib.api import ApiError, list_properties, list_usage, list_utility_types, upsert_usage

st.title("Usage")

try:
    properties = list_properties()
    utility_types = list_utility_types()
except ApiError as e:
    st.error(str(e))
    properties, utility_types = [], []

if not properties or not utility_types:
    st.warning("Add at least one property and one utility type first.")
else:
    property_options = {p["name"]: p["id"] for p in properties}
    utility_options = {u["name"]: u for u in utility_types}

    st.subheader("Log a monthly reading")
    with st.form("log_usage"):
        col1, col2 = st.columns(2)
        with col1:
            property_name = st.selectbox("Property", list(property_options.keys()))
            utility_name = st.selectbox("Utility type", list(utility_options.keys()))
        with col2:
            month_input = st.date_input(
                "Month", value=date.today().replace(day=1), help="Any date in the target month works"
            )
            value = st.number_input("Value (meter reading / usage amount)", min_value=0.0, step=0.1)

        override_cost = st.checkbox("Override calculated cost")
        cost = None
        if override_cost:
            cost = st.number_input("Cost", min_value=0.0, step=0.01)

        submitted = st.form_submit_button("Save")

    if submitted:
        utility_type = utility_options[utility_name]
        month = month_input.replace(day=1)
        try:
            upsert_usage(
                property_id=property_options[property_name],
                utility_type_id=utility_type["id"],
                month=month,
                value=value,
                cost=cost,
            )
            rate = utility_type.get("current_rate")
            if cost is None and rate:
                st.success(f"Saved. Cost auto-calculated as {value} x {rate} = {round(value * rate, 2)}.")
            else:
                st.success("Saved.")
            st.rerun()
        except ApiError as e:
            st.error(str(e))

    st.subheader("History")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_property = st.selectbox("Filter by property", ["All"] + list(property_options.keys()))
    with filter_col2:
        filter_utility = st.selectbox("Filter by utility type", ["All"] + list(utility_options.keys()))

    try:
        records = list_usage(
            property_id=property_options.get(filter_property) if filter_property != "All" else None,
            utility_type_id=(
                utility_options[filter_utility]["id"] if filter_utility != "All" else None
            ),
        )
    except ApiError as e:
        st.error(str(e))
        records = []

    if records:
        property_names = {v: k for k, v in property_options.items()}
        utility_names = {u["id"]: u["name"] for u in utility_types}

        df = pd.DataFrame(records)
        df["property"] = df["property_id"].map(property_names)
        df["utility_type"] = df["utility_type_id"].map(utility_names)
        df["month"] = pd.to_datetime(df["month"])
        df = df.drop(columns=["id", "property_id", "utility_type_id"])
        df = df[["property", "utility_type", "month", "value", "cost", "created_at", "updated_at"]]
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "month": st.column_config.DateColumn("Month", format="MMM YYYY"),
                "value": st.column_config.NumberColumn("Value", format="%.2f"),
                "cost": st.column_config.NumberColumn("Cost", format="%.2f"),
                "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
                "updated_at": st.column_config.DatetimeColumn("Updated", format="YYYY-MM-DD HH:mm"),
            },
        )
    else:
        st.info("No usage records yet.")
