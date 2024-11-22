import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import requests
from io import BytesIO

# Mapping pitch type abbreviations to full text
pitch_type_mapping = {
    "FF": "Four-Seam Fastball",
    "SL": "Slider",
    "CU": "Curveball",
    "CH": "Changeup",
    "FS": "Splitter",
    "SI": "Sinker",
    "FC": "Cutter",
    "KC": "Knuckle Curve",
    "KN": "Knuckleball",
    "SV": "Sweeper",
    "ST": "Sweeping Curve",
    "CS": "Slow Curve",
}

# Function to load 2024 Statcast data from GitHub (March to October)
@st.cache_data
def load_2024_data():
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/public-baseball/main/"
    combined_data = pd.DataFrame()
    columns_to_keep = ['player_name', 'pitch_type', 'pfx_x', 'pfx_z']  # Relevant columns to keep

    for month in range(3, 11):  # March to October
        file_name = f'statcast_2024_{month:02d}.csv.gz'
        file_url = f"{base_url}{file_name}"
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            file_content = BytesIO(response.content)
            data = pd.read_csv(file_content, compression='gzip', usecols=columns_to_keep)  # Keep only necessary columns
            combined_data = pd.concat([combined_data, data], ignore_index=True)
        except requests.exceptions.HTTPError as http_err:
            st.warning(f"HTTP Error for file: {file_name} - {http_err}")
        except Exception as e:
            st.error(f"Error loading file {file_name}: {e}")

    # Map pitch types to full text
    combined_data["pitch_type"] = combined_data["pitch_type"].map(pitch_type_mapping).fillna("Unknown")
    combined_data = combined_data[combined_data["pitch_type"] != "Unknown"]  # Remove unknown pitch types
    return combined_data

# Load the data
data = load_2024_data()

# Ensure data is loaded before continuing
if data.empty:
    st.error("No data available. Please ensure the 2024 data files are uploaded to the repository.")
else:
    st.title("MLB Movement Profile Distributions App")

    # Step 1: Combine search bar and dropdown for pitcher selection
    all_pitchers = sorted(data["player_name"].dropna().unique())
    pitcher_name = st.selectbox(
        "Search or select a pitcher:",
        options=["Type a name or select..."] + all_pitchers
    )

    # Filter data for the selected pitcher
    if pitcher_name and pitcher_name != "Type a name or select...":
        pitcher_data = data[data["player_name"] == pitcher_name]

        # Step 2: Calculate consistency and rank pitches
        st.write(f"### Movement Distributions for {pitcher_name}")

        # Calculate standard deviations for each pitch type
        pitch_consistency = (
            pitcher_data.groupby("pitch_type")
            .apply(lambda x: np.sqrt(x["pfx_x"].std()**2 + x["pfx_z"].std()**2))
            .reset_index(name="Consistency Score")
        )

        # Sort pitches by consistency (ascending)
        pitch_consistency = pitch_consistency.sort_values(by="Consistency Score")
        ranked_pitch_types = pitch_consistency["pitch_type"].values

        # Step 3: Plot histograms
        for pitch_type in ranked_pitch_types:
            pitch_data = pitcher_data[pitcher_data["pitch_type"] == pitch_type]

            # Create histogram for horizontal and vertical movement
            hist = alt.Chart(pitch_data).mark_bar(opacity=0.6).encode(
                alt.X("pfx_x", bin=alt.Bin(maxbins=30), title="Horizontal Break (ft)"),
                alt.Y("count()", title="Frequency"),
                color=alt.value("#1f77b4")  # Change this color as needed
            ).properties(title=f"{pitch_type} - Horizontal Movement")

            st.altair_chart(hist, use_container_width=True)

            hist_vertical = alt.Chart(pitch_data).mark_bar(opacity=0.6).encode(
                alt.X("pfx_z", bin=alt.Bin(maxbins=30), title="Vertical Break (ft)"),
                alt.Y("count()", title="Frequency"),
                color=alt.value("#ff7f0e")  # Change this color as needed
            ).properties(title=f"{pitch_type} - Vertical Movement")

            st.altair_chart(hist_vertical, use_container_width=True)

        # Display pitch consistency table
        st.write("### Pitch Consistency Rankings")
        st.table(pitch_consistency)
