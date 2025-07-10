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

@st.cache_data
def load_shipments_from_api(params=None):
    res = requests.get(f"{API_BASE}/shipments", params=params)
    if res.status_code != 200:
        st.error("Could not fetch shipment data from API.")
        return pd.DataFrame()
    return pd.DataFrame(res.json())

@st.cache_data
def get_filter_options():
    res = requests.get(f"{API_BASE}/shipments")
    df = pd.DataFrame(res.json())
    if df.empty:
        return [], [], []
    return (
        sorted(df['status'].dropna().unique()),
        sorted(df['carrier'].dropna().unique()),
        sorted(df['current_city'].dropna().unique()),
    )

@st.cache_data
def get_analytics_from_api():
    res = requests.get(f"{API_BASE}/analytics")
    return res.json() if res.status_code == 200 else {}

st.title("📦 Delivery Dashboard")

# Get filter options
statuses, carriers, cities = get_filter_options()

if not statuses:
    st.warning('No shipment data found from API. Run your API server and producer.')
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
selected_status = st.sidebar.multiselect('Status', options=statuses, default=statuses)
selected_carrier = st.sidebar.multiselect('Carrier', options=carriers, default=carriers)
selected_city = st.sidebar.multiselect('Current City', options=cities, default=cities)

# Prepare params for API
params = {}
if selected_status != statuses:
    params['status'] = selected_status
if selected_carrier != carriers:
    params['carrier'] = selected_carrier
if selected_city != cities:
    params['city'] = selected_city

df = load_shipments_from_api(params)
if df.empty:
    st.warning("No shipments found for selected filters.")
    st.stop()

# Analytics for KPIs
analytics = get_analytics_from_api()
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Shipments", analytics.get('total_shipments', len(df)))
kpi2.metric("Delivered (Count)", analytics.get('delivered_shipments', int(df['delivered'].sum())))
kpi3.metric("On-Time Delivery (%)", f"{analytics.get('on_time_percent', 0):.1f}%")

st.subheader("Sample Shipments Data")
st.dataframe(df.head(10), use_container_width=True)

# Pie Chart: Shipment Status
st.subheader("Shipment Status Distribution")
status_counts = df['status'].value_counts()
fig_pie = px.pie(
    names=status_counts.index,
    values=status_counts.values,
    color=status_counts.index,
    color_discrete_sequence=px.colors.qualitative.Safe,
    title="Shipment Status"
)
st.plotly_chart(fig_pie, use_container_width=True)

# Bar Chart: Shipments by Source City
st.subheader("Shipments Count by Source City")
city_counts = df['source_city'].value_counts().reset_index()
city_counts.columns = ['City', 'Shipments']
fig_bar = px.bar(
    city_counts, x='City', y='Shipments',
    color='Shipments', color_continuous_scale='Blues',
    title="Shipments by Source City"
)
st.plotly_chart(fig_bar, use_container_width=True)

# Delay Reason Analysis
st.subheader("Delay Reason Comparison")
delay_counts = df['delay_reason'].dropna().value_counts()
fig_delay = px.bar(
    x=delay_counts.index, y=delay_counts.values,
    labels={'x': 'Delay Reason', 'y': 'Count'},
    color=delay_counts.values,
    color_continuous_scale='reds'
)
st.plotly_chart(fig_delay, use_container_width=True)

# Average Rating by Carrier
st.subheader("Average Customer Rating by Carrier")
avg_rating = df.groupby('carrier')['rating'].mean().reset_index()
fig_rating = px.bar(
    avg_rating, x='carrier', y='rating',
    color='rating', color_continuous_scale='Plasma',
    title="Avg. Rating by Carrier"
)
st.plotly_chart(fig_rating, use_container_width=True)

# City-level Map
st.subheader("Current Location of Shipments (City Map)")
df['latitude'] = df['current_city'].map(lambda x: city_coords.get(x, [None, None])[0])
df['longitude'] = df['current_city'].map(lambda x: city_coords.get(x, [None, None])[1])
map_df = df.dropna(subset=['latitude', 'longitude'])

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

st.info("🔄 Use the sidebar to filter the dashboard by status, carrier, or city! Data is now loaded via your Flask API for realism.")
