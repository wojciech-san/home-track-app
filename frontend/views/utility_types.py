import pandas as pd
import streamlit as st

from lib.api import ApiError, create_utility_type, list_utility_types, update_utility_type

st.title("Utility Types")

try:
    utility_types = list_utility_types()
except ApiError as e:
    st.error(str(e))
    utility_types = []

if utility_types:
    df = pd.DataFrame(utility_types).drop(columns=["id"])
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "current_rate": st.column_config.NumberColumn("Current rate", format="%.4f"),
        },
    )
else:
    st.info(
        "No utility types yet. Add water / energy / gas / rent below, "
        "or run scripts/seed_utility_types.py on the backend."
    )

with st.expander("Add a utility type"):
    with st.form("add_utility_type", clear_on_submit=True):
        name = st.text_input("Name (e.g. water, energy, gas, rent)")
        unit = st.text_input("Unit (e.g. m3, kWh, PLN)")
        current_rate = st.number_input(
            "Current rate (price per unit)", min_value=0.0, step=0.01, format="%.4f"
        )
        submitted = st.form_submit_button("Add utility type")

if submitted:
    if not name:
        st.error("Name is required.")
    else:
        try:
            create_utility_type(name=name, unit=unit or None, current_rate=current_rate or None)
            st.success(f"Added {name}.")
            st.rerun()
        except ApiError as e:
            st.error(str(e))

with st.expander("Update a rate"):
    if utility_types:
        options = {u["name"]: u for u in utility_types}
        choice = st.selectbox("Utility type", list(options.keys()))
        selected = options[choice]
        new_rate = st.number_input(
            "New current rate",
            min_value=0.0,
            step=0.01,
            format="%.4f",
            value=float(selected["current_rate"] or 0.0),
            key="update_rate",
        )
        if st.button("Update rate"):
            try:
                update_utility_type(selected["id"], current_rate=new_rate)
                st.success("Rate updated.")
                st.rerun()
            except ApiError as e:
                st.error(str(e))
    else:
        st.caption("Add a utility type first.")
