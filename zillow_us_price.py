import streamlit as st
import pandas as pd
import os

st.title("Zillow Home Value Index Dashboard")

# Define file path for CSV in the GitHub repo
file_path = "Metro_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv"

# Check if file exists
if os.path.exists(file_path):
    df = pd.read_csv(file_path)

    # Reshape data: Convert wide format to long format
    df_melted = df.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"],
        var_name="Date",
        value_name="Home Value"
    )
    df_melted["Date"] = pd.to_datetime(df_melted["Date"])

    # User selects region
    region = st.selectbox("Select a Region", df_melted["RegionName"].unique())

    # Filter data
    region_data = df_melted[df_melted["RegionName"] == region]

    # Display Data
    st.subheader(f"Home Value Trends for {region}")
    st.line_chart(region_data.set_index("Date")["Home Value"])

    # Show raw data
    st.subheader("Raw Data")
    st.dataframe(region_data)

else:
    st.error("CSV file not found. Please ensure the file is in the same directory as this script.")
