import pandas as pd
import streamlit as st

from lib.api import ApiError, create_property, list_properties

st.title("Properties")

try:
    properties = list_properties()
except ApiError as e:
    st.error(str(e))
    properties = []

if properties:
    df = pd.DataFrame(properties).drop(columns=["id"])
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
        },
    )
else:
    st.info("No properties yet.")

with st.expander("Add a property"):
    with st.form("add_property", clear_on_submit=True):
        name = st.text_input("Name")
        address = st.text_input("Address")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add property")

if submitted:
    if not name:
        st.error("Name is required.")
    else:
        try:
            create_property(name=name, address=address or None, notes=notes or None)
            st.success(f"Added {name}.")
            st.rerun()
        except ApiError as e:
            st.error(str(e))
