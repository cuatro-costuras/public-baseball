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
def load_monthly_statcast():
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/public-baseball/main/"
    combined_data = pd.DataFrame()
    
    # Adjust these columns to match actual dataset
    relevant_columns = [
        "player_name", "pitch_type", "pfx_x", "pfx_z", "release_speed", "p_throws"
    ]

    for month in range(3, 11):  # March to October
        file_name = f'statcast_2024_{month:02d}.csv.gz'
        file_url = f"{base_url}{file_name}"
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            file_content = BytesIO(response.content)
            
            # Check available columns in each file
            data = pd.read_csv(file_content, compression="gzip")
            available_columns = [col for col in relevant_columns if col in data.columns]
            
            # Filter only necessary columns
            data = data[available_columns]
            combined_data = pd.concat([combined_data, data], ignore_index=True)
        except requests.exceptions.HTTPError as http_err:
            st.warning(f"HTTP Error for file: {file_name} - {http_err}")
        except Exception as e:
            st.error(f"Error loading file {file_name}: {e}")

    # Map pitch types to full text
    if "pitch_type" in combined_data.columns:
        combined_data["pitch_type"] = combined_data["pitch_type"].map(pitch_type_mapping).fillna("Unknown")
        combined_data = combined_data[combined_data["pitch_type"] != "Unknown"]  # Remove unknown pitch types

    return combined_data

# Load the data
data = load_monthly_statcast()

# Ensure data is loaded before continuing
if data.empty:
    st.error("No data available. Please ensure the monthly Statcast data files are uploaded to the repository.")
else:
    st.title("MLB Player Profile App")

    # Combine search bar and dropdown for player selection
    if "player_name" in data.columns:
        all_players = sorted(data["player_name"].dropna().unique())
        selected_player = st.selectbox(
            "Search or select a player:",
            options=["Type a name or select..."] + all_players
        )

        if selected_player and selected_player != "Type a name or select...":
            player_data = data[data["player_name"] == selected_player]

            # Metrics Section
            st.header(f"Player Profile: {selected_player}")
            st.write("Metrics display will depend on available data.")
