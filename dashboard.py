import os
import socket
import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import requests

API_BASE = "http://localhost:5000"

city_coords = {
    'Delhi': [28.6139, 77.2090],
    'Mumbai': [19.0760, 72.8777],
    'Bangalore': [12.9716, 77.5946],
    'Hyderabad': [17.3850, 78.4867],
    'Chennai': [13.0827, 80.2707],
    'Ahmedabad': [23.0225, 72.5714],
    'Pune': [18.5204, 73.8567],
    'Kolkata': [22.5726, 88.3639],
    'Surat': [21.1702, 72.8311],
    'Jaipur': [26.9124, 75.7873]
}

def running_on_streamlit_cloud():
    if os.environ.get('STREAMLIT_ENV') == 'cloud' or os.environ.get('STREAMPOD') == 'true':
        return True
    try:
        socket.create_connection(("localhost", 5000), timeout=1)
        return False
    except Exception:
        return True

USE_CSV_DATA = running_on_streamlit_cloud()

def process_csv():
    df = pd.read_csv("kafka_shipments.csv")
    df = df.rename(columns={
        "ID": "shipment_id",
        "timestamp": "timestamp",
        "source_city": "source_city",
        "destination_city": "destination_city",
        "current_city": "current_city",
        "Mode_of_Shipment": "status",
        "Weight_in_gms": "weight_kg",
        "carrier": "carrier",
        "estimated_delivery": "estimated_delivery",
        "delay_reason": "delay_reason",
        "Customer_rating": "rating",
        "Reached.on.Time_Y.N": "delivered"
    })
    df["delivered"] = df["delivered"] == 1
    df["weight_kg"] = round(df["weight_kg"] / 1000, 2)
    return df

@st.cache_data
def load_shipments_from_api(params=None):
    try:
        res = requests.get(f"{API_BASE}/shipments", params=params, timeout=6)
        if res.status_code != 200:
            return pd.DataFrame()
        return pd.DataFrame(res.json())
    except Exception:
        return pd.DataFrame()

@st.cache_data
def get_filter_options():
    try:
        res = requests.get(f"{API_BASE}/shipments", timeout=6)
        df = pd.DataFrame(res.json())
        if df.empty:
            return [], [], []
        return (
            sorted(df['status'].dropna().unique()),
            sorted(df['carrier'].dropna().unique()),
            sorted(df['current_city'].dropna().unique()),
        )
    except Exception:
        return [], [], []

@st.cache_data
def get_analytics_from_api():
    try:
        res = requests.get(f"{API_BASE}/analytics", timeout=6)
        return res.json() if res.status_code == 200 else {}
    except Exception:
        return {}

st.title("📦 Delivery Dashboard")

if USE_CSV_DATA:
    df = process_csv()
    statuses = sorted(df['status'].dropna().unique())
    carriers = sorted(df['carrier'].dropna().unique())
    cities = sorted(df['current_city'].dropna().unique())
    analytics = {}
else:
    statuses, carriers, cities = get_filter_options()
    if not statuses:
        st.warning('No shipment data found from API. Run your API server and producer, or use CSV for demo.')
        st.stop()
    analytics = get_analytics_from_api()

st.sidebar.header("Filters")
selected_status = st.sidebar.multiselect('Status', options=statuses, default=statuses)
selected_carrier = st.sidebar.multiselect('Carrier', options=carriers, default=carriers)
selected_city = st.sidebar.multiselect('Current City', options=cities, default=cities)

params = {}
if selected_status != statuses:
    params['status'] = selected_status
if selected_carrier != carriers:
    params['carrier'] = selected_carrier
if selected_city != cities:
    params['city'] = selected_city

if USE_CSV_DATA:
    filtered_df = df[
        df['status'].isin(selected_status) &
        df['carrier'].isin(selected_carrier) &
        df['current_city'].isin(selected_city)
    ]
else:
    filtered_df = load_shipments_from_api(params)
    if filtered_df.empty:
        st.warning("No shipments found for selected filters.")
        st.stop()

if USE_CSV_DATA or not analytics:
    total_shipments = len(filtered_df)
    delivered_count = filtered_df['delivered'].sum()
    on_time_pct = 100 * delivered_count / total_shipments if total_shipments else 0
else:
    total_shipments = analytics.get('total_shipments', len(filtered_df))
    delivered_count = analytics.get('delivered_shipments', int(filtered_df['delivered'].sum()))
    on_time_pct = analytics.get('on_time_percent', 0)

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Shipments", total_shipments)
kpi2.metric("Delivered (Count)", delivered_count)
kpi3.metric("On-Time Delivery (%)", f"{on_time_pct:.1f}%")

st.subheader("Shipments Data")
st.dataframe(filtered_df.head(10), use_container_width=True)

st.subheader("Shipment Status Distribution")
status_counts = filtered_df['status'].value_counts()
fig_pie = px.pie(
    names=status_counts.index,
    values=status_counts.values,
    color=status_counts.index,
    color_discrete_sequence=px.colors.qualitative.Safe,
    title="Shipment Status"
)
st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Shipments Count by Source City")
city_counts = filtered_df['source_city'].value_counts().reset_index()
city_counts.columns = ['City', 'Shipments']
fig_bar = px.bar(
    city_counts, x='City', y='Shipments',
    color='Shipments', color_continuous_scale='Blues',
)
st.plotly_chart(fig_bar, use_container_width=True)
