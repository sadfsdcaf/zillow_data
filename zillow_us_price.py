import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Set page layout to wide
st.set_page_config(layout="wide")

st.title("Zillow Home Value Index Dashboard")

# Define file path for CSV in the GitHub repo
file_path = "Metro_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv"

# Initialize geolocator
geolocator = Nominatim(user_agent="zillow_dashboard")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Function to get coordinates with caching
@st.cache_data
def get_coordinates(city_state):
    try:
        location = geocode(city_state)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        st.error(f"Error fetching coordinates for {city_state}: {e}")
        return None, None

# Load Zillow data
if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    # Extract city and state from RegionName
    df[['City', 'State']] = df['RegionName'].str.split(', ', expand=True)

    # Get unique city-state pairs
    unique_locations = df[['City', 'State']].drop_duplicates()

    # Fetch coordinates for each unique city-state pair
    coords = unique_locations.apply(
        lambda row: pd.Series(get_coordinates(f"{row['City']}, {row['State']}")),
        axis=1
    )
    coords.columns = ['Latitude', 'Longitude']

    # Combine coordinates with location data
    location_data = pd.concat([unique_locations.reset_index(drop=True), coords], axis=1)

    # Merge coordinates back to the main dataframe
    df = pd.merge(df, location_data, on=['City', 'State'], how='left')

    # Reshape data: Convert wide format to long format
    df_melted = df.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "RegionType", "StateName", "City", "State", "Latitude", "Longitude"],
        var_name="Date",
        value_name="Home Value"
    )
    df_melted["Date"] = pd.to_datetime(df_melted["Date"])

    # User selects region
    region = st.selectbox("Select a Region", df_melted["RegionName"].unique())

    # Filter data
    region_data = df_melted[df_melted["RegionName"] == region]

    # Create layout with two equal columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Home Value Trends for {region}")
        st.line_chart(region_data.set_index("Date")["Home Value"])
    
    with col2:
        st.subheader("Locations with Zillow Data")
        latest_data = df_melted[df_melted["Date"] == df_melted["Date"].max()]
        fig = px.scatter_geo(
            latest_data.dropna(subset=['Latitude', 'Longitude']),
            lat="Latitude",
            lon="Longitude",
            hover_name="RegionName",
            size="Home Value",
            title="Latest Home Values by City",
            scope="usa"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Show raw data in full-width section below
    st.subheader("Raw Data")
    st.dataframe(region_data, use_container_width=True)

else:
    st.error("CSV file not found. Please ensure the file is in the correct directory.")
