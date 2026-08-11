from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.api import ApiError, list_leases, list_properties, list_usage, usage_summary


def shift_month(d: date, delta: int) -> date:
    """Return the 1st of the month that is `delta` months away from d's month."""
    total = d.year * 12 + (d.month - 1) + delta
    year, month = divmod(total, 12)
    return date(year, month + 1, 1)


def month_select(label: str, default: date, min_month: date, max_month: date) -> date:
    """A YYYY-MM dropdown, scoped to the range of months that actually have data."""
    options = pd.date_range(start=min_month, end=max_month, freq="MS").date.tolist()
    labels = [d.strftime("%Y-%m") for d in options]
    default_label = default.strftime("%Y-%m")
    index = labels.index(default_label) if default_label in labels else len(labels) - 1
    chosen = st.selectbox(label, labels, index=index)
    return datetime.strptime(chosen, "%Y-%m").date()


st.title("Dashboard")

try:
    properties = list_properties()
except ApiError as e:
    st.error(str(e))
    properties = []

if not properties:
    st.warning("Add a property and log some usage first.")
else:
    property_options = {"All properties": None}
    property_options.update({p["name"]: p["id"] for p in properties})

    col1, col2, col3 = st.columns(3)
    with col1:
        property_name = st.selectbox("Property", list(property_options.keys()))

    selected_property_id = property_options[property_name]

    # Scope the From/To dropdowns to months that actually have usage data for
    # this property (or across all properties, if "All properties" is picked).
    try:
        existing_records = list_usage(property_id=selected_property_id)
    except ApiError as e:
        st.error(str(e))
        existing_records = []

    if existing_records:
        record_months = sorted(datetime.strptime(r["month"], "%Y-%m-%d").date() for r in existing_records)
        data_min_month = record_months[0].replace(day=1)
        data_max_month = record_months[-1].replace(day=1)
    else:
        data_min_month = data_max_month = date.today().replace(day=1)

    default_from = max(data_min_month, shift_month(data_max_month, -6))

    with col2:
        month_from = month_select("From", default_from, data_min_month, data_max_month)
    with col3:
        month_to = month_select("To", data_max_month, data_min_month, data_max_month)

    try:
        summary = usage_summary(
            property_id=selected_property_id,
            month_from=str(month_from),
            month_to=str(month_to),
        )
    except ApiError as e:
        st.error(str(e))
        summary = []

    rows = []
    for entry in summary:
        for u in entry["utilities"]:
            rows.append(
                {
                    "property": entry["property_name"],
                    "month": entry["month"],
                    "utility_type": u["utility_type_name"],
                    "unit": u["unit"],
                    "value": u["total_value"],
                    "cost": u["total_cost"],
                }
            )

    try:
        active_leases = list_leases(property_id=selected_property_id, active_on=str(date.today()))
    except ApiError:
        active_leases = []

    # ---------- KPI row ----------
    total_cost = sum(r["cost"] for r in rows)
    monthly_rent_income = sum(l["monthly_rent"] for l in active_leases)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total cost (period)", f"{total_cost:,.2f}")
    k2.metric("Usage entries logged", len(rows))
    k3.metric("Active leases", len(active_leases))
    k4.metric("Monthly rent income", f"{monthly_rent_income:,.2f}")

    st.divider()

    if not rows:
        st.info("No usage data in this range yet.")
    else:
        df = pd.DataFrame(rows)
        df["month"] = pd.to_datetime(df["month"])
        # A clean, discrete "Aug 2026" label so every chart shows one bar/point
        # per calendar month, sorted chronologically rather than by day gaps.
        df["month_label"] = df["month"].dt.strftime("%b %Y")
        month_order = df.sort_values("month")["month_label"].unique().tolist()

        chart_theme = "plotly_white"

        st.subheader("Total monthly cost")
        monthly_total = df.groupby("month_label", as_index=False)["cost"].sum()
        total_fig = px.bar(
            monthly_total,
            x="month_label",
            y="cost",
            category_orders={"month_label": month_order},
            template=chart_theme,
            text_auto=".2f",
            labels={"month_label": "Month", "cost": "Total cost"},
        )
        total_fig.update_traces(marker_color="#4C78A8")
        total_fig.update_layout(xaxis_title=None)
        st.plotly_chart(total_fig, use_container_width=True)

        st.subheader("Monthly cost by utility type")
        monthly_by_utility = df.groupby(["month_label", "utility_type"], as_index=False)["cost"].sum()
        cost_fig = px.bar(
            monthly_by_utility,
            x="month_label",
            y="cost",
            color="utility_type",
            barmode="stack",
            category_orders={"month_label": month_order},
            template=chart_theme,
            labels={"month_label": "Month", "cost": "Cost", "utility_type": "Utility"},
        )
        cost_fig.update_layout(hovermode="x unified", legend_title_text="", xaxis_title=None)
        st.plotly_chart(cost_fig, use_container_width=True)

        st.subheader("Usage trend")
        monthly_usage = df.groupby(
            ["month_label", "utility_type", "property"], as_index=False
        )["value"].sum()
        usage_fig = px.line(
            monthly_usage,
            x="month_label",
            y="value",
            color="utility_type",
            line_dash="property" if df["property"].nunique() > 1 else None,
            markers=True,
            category_orders={"month_label": month_order},
            template=chart_theme,
            labels={"month_label": "Month", "value": "Usage", "utility_type": "Utility"},
        )
        usage_fig.update_layout(hovermode="x unified", legend_title_text="", xaxis_title=None)
        st.plotly_chart(usage_fig, use_container_width=True)

        st.subheader("Total cost per property")
        totals = (
            df.groupby("property", as_index=False)["cost"].sum().sort_values("cost", ascending=True)
        )
        totals_fig = px.bar(
            totals,
            x="cost",
            y="property",
            orientation="h",
            text_auto=".2f",
            template=chart_theme,
            labels={"cost": "Total cost", "property": ""},
        )
        totals_fig.update_traces(marker_color="#4C78A8")
        st.plotly_chart(totals_fig, use_container_width=True)

        st.subheader("Raw data")
        st.dataframe(
            df.sort_values("month", ascending=False),
            hide_index=True,
            use_container_width=True,
            column_config={
                "month": st.column_config.DateColumn("Month", format="MMM YYYY"),
                "value": st.column_config.NumberColumn("Value", format="%.2f"),
                "cost": st.column_config.NumberColumn("Cost", format="%.2f"),
            },
        )
