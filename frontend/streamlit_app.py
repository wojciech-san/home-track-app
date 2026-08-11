import streamlit as st

st.set_page_config(page_title="Home Track", page_icon="🏠", layout="wide")

home_page = st.Page("views/home.py", title="Overview", icon="🏠", default=True)
dashboard_page = st.Page("views/dashboard.py", title="Dashboard", icon="📈")
properties_page = st.Page("views/properties.py", title="Properties", icon="🏢")
utility_types_page = st.Page("views/utility_types.py", title="Utility Types", icon="⚡")
usage_page = st.Page("views/usage.py", title="Usage", icon="📝")
leases_page = st.Page("views/leases.py", title="Leases", icon="🔑")

nav = st.navigation(
    {
        "Overview": [home_page, dashboard_page],
        "Manage data": [properties_page, utility_types_page, usage_page, leases_page],
    }
)
nav.run()
