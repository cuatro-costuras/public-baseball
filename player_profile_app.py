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
            pitcher_hand = player_data["p_throws"].iloc[0]  # Get the handedness of the pitcher

            st.header(f"Player Profile: {selected_player}")
            st.write(f"**Handedness**: {'Right-Handed (R)' if pitcher_hand == 'R' else 'Left-Handed (L)'}")

            # Display Metrics
            st.subheader("Top Metrics")
            k_rate = 30.5  # Example, replace with calculation
            bb_rate = 8.0  # Example, replace with calculation
            st.write(f"K%: {k_rate}%")
            st.write(f"BB%: {bb_rate}%")

            # Display Pitch Arsenal
            st.subheader("Pitch Arsenal")
            arsenal = player_data["pitch_type"].value_counts()
            for pitch, count in arsenal.items():
                st.write(f"- {pitch}: {count} pitches")

            # Plot Movement
            st.subheader("Movement Plot")
            movement_chart = alt.Chart(player_data).mark_circle(size=100).encode(
                x=alt.X("pfx_x", title="Horizontal Break (inches)"),
                y=alt.Y("pfx_z", title="Vertical Break (inches)"),
                color=alt.Color("pitch_type:N", legend=alt.Legend(title="Pitch Type"))
            ).properties(
                width=600,
                height=400
            )
            st.altair_chart(movement_chart, use_container_width=True)

            # Display Definitions
            st.subheader("Definitions")
            st.write("""
            - **K%**: Strikeout rate.
            - **BB%**: Walk rate.
            - **pfx_x**: Horizontal movement of the pitch in inches.
            - **pfx_z**: Vertical movement of the pitch in inches.
            """)

