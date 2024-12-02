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
    columns_to_keep = [
        "player_name", "pitch_type", "pfx_x", "pfx_z", "release_speed", "p_throws",
        "k_rate", "bb_rate", "kbb_rate", "put_away_rate", "race_to_2k_rate",
        "pitch_usage", "zone_rate", "swing_rate", "whiff_rate", "hard_hit_rate",
        "groundball_rate", "flyball_rate", "called_strike_rate", "chase_rate"
    ]  # Adjust to include only relevant columns

    for month in range(3, 11):  # March to October
        file_name = f'statcast_2024_{month:02d}.csv.gz'
        file_url = f"{base_url}{file_name}"
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            file_content = BytesIO(response.content)
            data = pd.read_csv(file_content, compression='gzip', usecols=columns_to_keep)
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
data = load_monthly_statcast()

# Ensure data is loaded before continuing
if data.empty:
    st.error("No data available. Please ensure the monthly Statcast data files are uploaded to the repository.")
else:
    st.title("MLB Player Profile App")

    # Combine search bar and dropdown for player selection
    all_players = sorted(data["player_name"].dropna().unique())
    selected_player = st.selectbox(
        "Search or select a player:",
        options=["Type a name or select..."] + all_players
    )

    if selected_player and selected_player != "Type a name or select...":
        player_data = data[data["player_name"] == selected_player]

        # Display player name
        st.header(f"Player Profile: {selected_player}")

        # Metrics Section
        metrics = {
            "K-BB%": ("kbb_rate", "Percentile: K-BB%"),
            "Race to 2K%": ("race_to_2k_rate", "Percentile: Race to 2K%"),
            "Put Away%": ("put_away_rate", "Percentile: Put Away%")
        }

        cols = st.columns(len(metrics))
        for i, (metric_name, (metric_column, percentile_column)) in enumerate(metrics.items()):
            metric_value = player_data[metric_column].mean()
            metric_percentile = player_data[percentile_column].mean()
            cols[i].metric(metric_name, f"{metric_value:.2f}", f"{metric_percentile:.1f} Percentile")

        # Pitch Type Arsenal
        pitch_types = player_data["pitch_type"].unique()
        st.subheader("Pitch Arsenal")
        selected_pitch = st.selectbox("Select a Pitch Type:", options=pitch_types)

        if selected_pitch:
            pitch_data = player_data[player_data["pitch_type"] == selected_pitch]
            st.write(f"### {selected_pitch} Metrics")
            st.table(pitch_data.describe().T)

        # Stats Table
        st.subheader("Player Stats")
        stats_table = player_data[[
            "k_rate", "bb_rate", "kbb_rate", "put_away_rate", "race_to_2k_rate",
            "zone_rate", "swing_rate", "whiff_rate", "hard_hit_rate",
            "groundball_rate", "flyball_rate", "called_strike_rate", "chase_rate"
        ]].mean().reset_index(name="Value")
        st.table(stats_table)

        # Pie Chart for Pitch Usage
        st.subheader("Pitch Usage")
        pitch_usage = player_data.groupby("pitch_type")["pitch_usage"].mean().reset_index()
        pitch_usage_chart = alt.Chart(pitch_usage).mark_arc().encode(
            theta=alt.Theta("pitch_usage", type="quantitative"),
            color=alt.Color("pitch_type", legend=None),
            tooltip=["pitch_type", "pitch_usage"]
        )
        st.altair_chart(pitch_usage_chart, use_container_width=True)

        # Movement Plot
        st.subheader("Pitch Movement Plot")
        movement_chart = alt.Chart(player_data).mark_circle().encode(
            x=alt.X("pfx_x", title="Horizontal Break (inches)"),
            y=alt.Y("pfx_z", title="Vertical Break (inches)"),
            color="pitch_type",
            tooltip=["pitch_type", "pfx_x", "pfx_z"]
        )
        st.altair_chart(movement_chart, use_container_width=True)

        # Definitions
        st.subheader("Stat Definitions")
        st.write(
            """
            **K-BB%**: Strikeouts minus walks as a percentage of batters faced.
            **Race to 2K%**: How often a pitcher reaches two strikes before two balls.
            **Put Away%**: Rate of strikeouts after reaching two strikes.
            **Zone%**: Percentage of pitches thrown in the strike zone.
            **Chase Rate**: Swings at pitches outside the strike zone.
            **Whiff Rate**: Swings and misses as a percentage of swings.
            **Hard Hit%**: Batted balls hit at 95 mph or higher.
            **Groundball%**: Percentage of batted balls that are groundballs.
            **Flyball%**: Percentage of batted balls that are flyballs.
            """
        )
