import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from io import BytesIO
import requests

# Define pitch type mapping
pitch_type_mapping = {
    "FF": "Four-Seam Fastball",
    "SL": "Slider",
    "CU": "Curveball",
    "CH": "Changeup",
    "SI": "Sinker",
    "FC": "Cutter",
    "KC": "Knuckle Curve",
    "KN": "Knuckleball",
    "SV": "Sweeper",
}

# Columns to load
expected_columns = [
    'player_name', 'pitch_type', 'pfx_x', 'pfx_z', 'release_speed', 'p_throws', 
    'balls', 'strikes', 'events', 'zone', 'woba_value', 'year', 'month'
]

# Function to load monthly Statcast data
@st.cache_data
def load_monthly_statcast():
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/public-baseball/main/"
    combined_data = pd.DataFrame()

    for month in range(3, 11):  # March to October
        file_name = f"statcast_2024_{month:02d}.csv.gz"
        file_url = f"{base_url}{file_name}"
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            file_content = BytesIO(response.content)
            data = pd.read_csv(file_content, compression='gzip', usecols=expected_columns)
            combined_data = pd.concat([combined_data, data], ignore_index=True)
        except Exception as e:
            st.warning(f"Error loading file {file_name}: {e}")

    # Map pitch types to full text
    combined_data["pitch_type"] = combined_data["pitch_type"].map(pitch_type_mapping).fillna("Unknown")
    combined_data = combined_data[combined_data["pitch_type"] != "Unknown"]
    return combined_data

# Function to calculate player-specific metrics
def calculate_player_metrics(player_data):
    total_pitches = len(player_data)
    if total_pitches == 0:
        return None

    metrics = {
        "k_rate": round(player_data[player_data["events"] == "strikeout"].shape[0] / total_pitches * 100, 2),
        "bb_rate": round(player_data[player_data["events"] == "walk"].shape[0] / total_pitches * 100, 2),
        "kbb_rate": round(
            (player_data[player_data["events"] == "strikeout"].shape[0] / total_pitches -
             player_data[player_data["events"] == "walk"].shape[0] / total_pitches) * 100, 2
        ),
        "put_away_rate": round(player_data[player_data["balls"] + player_data["strikes"] == 4].shape[0] / total_pitches * 100, 2),
        "zone_rate": round(player_data[player_data["zone"].between(1, 9)].shape[0] / total_pitches * 100, 2),
        "race_to_2k_rate": round(player_data[player_data["strikes"] == 2].shape[0] / total_pitches * 100, 2),
    }

    return metrics

# Main App
data = load_monthly_statcast()

if data.empty:
    st.error("No data available. Please ensure the monthly Statcast data files are uploaded.")
else:
    st.title("MLB Player Profile App")
    
    # 1) Player Name (dropdown list combined with search bar)
    player_names = sorted(data["player_name"].dropna().unique())
    player_name = st.selectbox("Select a Player", [""] + player_names)

    if player_name:
        player_data = data[data["player_name"] == player_name]
        metrics = calculate_player_metrics(player_data)

        if metrics:
            # 2) 3 boxes across the top with raw score and percentile
            st.write("### Player Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("K-BB%", f"{metrics['kbb_rate']}%")
            col2.metric("Race to 2K%", f"{metrics['race_to_2k_rate']}%")
            col3.metric("Put Away Rate", f"{metrics['put_away_rate']}%")

            # 3) Box displaying each pitch type in their arsenal with a color code
            st.write("### Pitch Arsenal")
            pitch_types = player_data["pitch_type"].unique()
            st.write(", ".join(pitch_types))

            # 4) Flip "flash card" to show pitch metrics
            selected_pitch = st.selectbox("Select a Pitch Type", pitch_types)
            if selected_pitch:
                st.write(f"### Metrics for {selected_pitch}")
                pitch_metrics = player_data[player_data["pitch_type"] == selected_pitch][
                    ["release_speed", "pfx_x", "pfx_z"]
                ].mean().round(2)
                st.table(pitch_metrics)

            # 5) Stats Box
            st.write("### Stats Table")
            st.table(pd.DataFrame(metrics, index=["Value"]))

            # 6) Visuals: Pie Chart for Pitch Usage
            st.write("### Pitch Usage")
            usage_data = player_data["pitch_type"].value_counts(normalize=True).reset_index()
            usage_data.columns = ["Pitch Type", "Usage"]
            fig = px.pie(usage_data, values="Usage", names="Pitch Type", title="Pitch Usage")
            st.plotly_chart(fig)

            # Movement plot
            st.write("### Pitch Movement Plot")
            fig = px.scatter(
                player_data, x="pfx_x", y="pfx_z", color="pitch_type", 
                labels={"pfx_x": "Horizontal Break (inches)", "pfx_z": "Vertical Break (inches)"}
            )
            st.plotly_chart(fig)

            # 9) Definitions
            st.write("### Definitions")
            st.write("""
            **K-BB%**: Strikeout rate minus walk rate, indicating pitching dominance.
            **Race to 2K%**: How often a pitcher gets to two strikes before two balls.
            **Put Away Rate**: The rate at which a pitcher strikes out batters after reaching two strikes.
            **Zone%**: Percentage of pitches thrown in the strike zone.
            **Pitch Usage**: Percentage of each pitch type thrown by the pitcher.
            """)
