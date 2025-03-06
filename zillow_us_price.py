import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Set page layout to wide
st.set_page_config(layout="wide")

st.title("Zillow Home Value Index Dashboard")

# Define file path for CSV in the GitHub repo
file_path = "Metro_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv"

# Cache function for loading data
@st.cache_data
def load_data():
    df = pd.read_csv(file_path)
    df_melted = df.melt(
        id_vars=["SizeRank", "RegionName"],
        var_name="Date",
        value_name="Home Value"
    )
    df_melted["Date"] = pd.to_datetime(df_melted["Date"], errors="coerce")
    
    # Drop invalid dates
    df_melted = df_melted.dropna(subset=["Date"])
    
    # Extract state from RegionName
    df_melted["StateName"] = df_melted["RegionName"].apply(lambda x: x.split(", ")[-1] if ", " in x else "United States")
    
    # Filter data to only include the past 10 years
    ten_years_ago = datetime.today().year - 10
    df_melted = df_melted[df_melted["Date"] >= f"{ten_years_ago}-01-01"]
    
    # Format Home Value as whole number with comma separator
    df_melted["Home Value"] = df_melted["Home Value"].fillna(0).astype(int)
    df_melted["Home Value Formatted"] = df_melted["Home Value"].apply(lambda x: f"{x:,}")
    
    # Calculate state average home value
    state_avg = df_melted.groupby(["StateName", "Date"])["Home Value"].mean().reset_index()
    
    # Sort data by most recent date
    df_melted = df_melted.sort_values(by="Date", ascending=False)
    
    return df_melted, state_avg

# Load data
if os.path.exists(file_path):
    df_melted, state_avg = load_data()
    
    # User selects region
    region = st.selectbox("Select a Region", df_melted["RegionName"].unique())
    
    # Filter data
    region_data = df_melted[df_melted["RegionName"] == region]
    state_data = state_avg[state_avg["StateName"] == region_data.iloc[0]["StateName"]]
    
    # Create layout with two equal columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Home Value Trends for {region} and {region_data.iloc[0]['StateName']} Average")
        combined_data = region_data.set_index("Date")["Home Value"].rename(region)
        combined_state_data = state_data.set_index("Date")["Home Value"].rename(f"{region_data.iloc[0]['StateName']} Avg")
        st.line_chart(pd.concat([combined_data, combined_state_data], axis=1))
    
    with col2:
        st.subheader("Locations with Zillow Data")
        latest_data = df_melted[df_melted["Date"] == df_melted["Date"].max()]
        fig = px.scatter_geo(
            latest_data,
            locations="StateName",
            locationmode="USA-states",
            hover_name="RegionName",
            size="Home Value",
            title="Latest Home Values by Region",
            scope="usa"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Show additional trend insights
    st.subheader("Market Trends")
    trend_col1, trend_col2 = st.columns(2)
    
    with trend_col1:
        st.metric("Highest Recent Value", f"${region_data['Home Value'].max():,}")
        st.metric("Lowest Recent Value", f"${region_data['Home Value'].min():,}")
    
    with trend_col2:
        price_change = region_data.iloc[0]["Home Value"] - region_data.iloc[-1]["Home Value"]
        st.metric("Price Change (Last 10 Years)", f"${price_change:,}", delta=int(price_change) if not pd.isna(price_change) else 0)
    
    # Show raw data in full-width section below
    st.subheader("Raw Data")
    st.dataframe(region_data[["Date", "RegionName", "StateName", "Home Value Formatted"]], use_container_width=True)

else:
    st.error("CSV file not found. Please ensure the file is in the correct directory.")
