import pandas as pd
import streamlit as st

from lib.api import API_BASE_URL, ApiError, list_properties

st.title("Home Track")
st.write(
    "Track monthly utility usage, cost, and tenant leases across your properties. "
    "Use the sidebar to enter data or view the dashboard."
)
st.caption(f"Backend: {API_BASE_URL}")

try:
    properties = list_properties()
except ApiError as e:
    st.error(str(e))
    properties = []

if properties:
    st.subheader("Properties")
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
    st.info("No properties yet — add one on the Properties page.")
