import os
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

def is_streamlit_cloud():
    # Streamlit Cloud sets this env var; locally it won't be set.
    return os.environ.get('STREAMLIT_ENV') == 'cloud' or os.environ.get('STREAMPOD') == 'true'

@st.cache_data
def load_shipments_from_api(params=None):
    try:
        res = requests.get(f"{API_BASE}/shipments", params=params, timeout=6)
        if res.status_code != 200:
            return pd.DataFrame()
        return pd.DataFrame(res.json())
    except Exception as e:
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

if is_streamlit_cloud() or not os.path.exists("api.py"):
    st.info("🌐 Running in demo mode (Streamlit Cloud or no API detected). Data loaded from sample CSV.\n\nFor full analytics, run locally with your backend API.")
    df = process_csv()
    statuses = sorted(df['status'].dropna().unique())
    carriers = sorted(df['carrier'].dropna().unique())
    cities = sorted(df['current_city'].dropna().unique())
    analytics = {}  # No live analytics REST calls; use pandas below
else:
    statuses, carriers, cities = get_filter_options()
    if not statuses:
        st.warning('No shipment data found from API. Run your API server and producer, or use CSV for demo.')
        st.stop()
    analytics = get_analytics_from_api()

st.title("📦 Delivery Dashboard")

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

if is_streamlit_cloud() or not os.path.exists("api.py"):
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


if is_streamlit_cloud() or not analytics:
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

st.subheader("Sample Shipments Data")
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
    title="Shipments by Source City"
)
st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Delay Reason Comparison")
delay_counts = filtered_df['delay_reason'].dropna().value_counts()
fig_delay = px.bar(
    x=delay_counts.index, y=delay_counts.values,
    labels={'x': 'Delay Reason', 'y': 'Count'},
    color=delay_counts.values,
    color_continuous_scale='reds'
)
st.plotly_chart(fig_delay, use_container_width=True)

st.subheader("Average Customer Rating by Carrier")
avg_rating = filtered_df.groupby('carrier')['rating'].mean().reset_index()
fig_rating = px.bar(
    avg_rating, x='carrier', y='rating',
    color='rating', color_continuous_scale='Plasma',
    title="Avg. Rating by Carrier"
)
st.plotly_chart(fig_rating, use_container_width=True)

st.subheader("Current Location of Shipments (City Map)")
filtered_df['latitude'] = filtered_df['current_city'].map(lambda x: city_coords.get(x, [None, None])[0])
filtered_df['longitude'] = filtered_df['current_city'].map(lambda x: city_coords.get(x, [None, None])[1])
map_df = filtered_df.dropna(subset=['latitude', 'longitude'])

if not map_df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position='[longitude, latitude]',
        auto_highlight=True,
        get_radius=35000,
        get_fill_color="[230, 25, 75, 150]",
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=map_df['latitude'].mean(),
        longitude=map_df['longitude'].mean(),
        zoom=4,
        pitch=0,
    )
    tooltip = {"text": "City: {current_city}\nStatus: {status}\nCarrier: {carrier}"}
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))
else:
    st.info("No shipment location data available for mapping.")

