import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from io import BytesIO
import requests

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="MLB Player Profile App", page_icon="⚾")

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
    'balls', 'strikes', 'events', 'zone', 'woba_value', 'release_extension', 
    'release_pos_y', 'plate_x', 'plate_z', 'year', 'month'
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

# Utility functions for metric calculations
def calculate_kbb_rate(player_data):
    k_count = len(player_data[player_data["events"] == "strikeout"])
    bb_count = len(player_data[player_data["events"] == "walk"])
    total_pitches = len(player_data)
    return (k_count - bb_count) / total_pitches * 100 if total_pitches > 0 else 0

def calculate_race_to_2k(player_data):
    qualifying_pitches = player_data[(player_data["balls"] < 2) | (player_data["strikes"] < 2)]
    if qualifying_pitches.empty:
        return 0
    reached_two_strikes = qualifying_pitches[qualifying_pitches["strikes"] == 2]
    return len(reached_two_strikes) / len(qualifying_pitches) * 100

def calculate_put_away_rate(player_data):
    two_strike_appearances = player_data[player_data["strikes"] == 2]
    if two_strike_appearances.empty:
        return 0
    strikeouts = two_strike_appearances[two_strike_appearances["events"] == "strikeout"]
    return len(strikeouts) / len(two_strike_appearances) * 100

def calculate_pitch_metrics(pitch_data):
    metrics = {
        "Velocity": pitch_data["release_speed"].mean() if "release_speed" in pitch_data else None,
        "Vertical Break (VB)": pitch_data["pfx_z"].mean() if "pfx_z" in pitch_data else None,
        "Horizontal Break (HB)": pitch_data["pfx_x"].mean() if "pfx_x" in pitch_data else None,
        "Extension": pitch_data["release_extension"].mean() if "release_extension" in pitch_data else None,
        "VAA": pitch_data["plate_z"].mean() if "plate_z" in pitch_data else None,
        "HAA": pitch_data["plate_x"].mean() if "plate_x" in pitch_data else None,
        "Release Height": pitch_data["release_pos_y"].mean() if "release_pos_y" in pitch_data else None,
        "Release Side": pitch_data["plate_x"].mean() if "plate_x" in pitch_data else None,
    }
    return pd.DataFrame.from_dict(metrics, orient="index", columns=["Value"])

# Main App
data = load_monthly_statcast()

if data.empty:
    st.error("No data available. Please ensure the monthly Statcast data files are uploaded.")
else:
    st.title("MLB Player Profile App")

    # 1) Player Name Dropdown/Search Bar
    player_names = sorted(data["player_name"].dropna().unique())
    player_name = st.selectbox("Select a Player", [""] + player_names)

    if player_name:
        player_data = data[data["player_name"] == player_name]
        
        # 2) Metrics Boxes with Percentile Rankings
        kbb_rate = calculate_kbb_rate(player_data)
        race_to_2k_rate = calculate_race_to_2k(player_data)
        put_away_rate = calculate_put_away_rate(player_data)

        all_kbb_rates = data.groupby("player_name").apply(calculate_kbb_rate)
        all_race_to_2k_rates = data.groupby("player_name").apply(calculate_race_to_2k)
        all_put_away_rates = data.groupby("player_name").apply(calculate_put_away_rate)

        col1, col2, col3 = st.columns(3)
        col1.metric("K-BB%", f"{kbb_rate:.2f}%", f"{(kbb_rate - all_kbb_rates.mean()) / all_kbb_rates.std():.1f} SD")
        col2.metric("Race to 2K%", f"{race_to_2k_rate:.2f}%", f"{(race_to_2k_rate - all_race_to_2k_rates.mean()) / all_race_to_2k_rates.std():.1f} SD")
        col3.metric("Put Away Rate", f"{put_away_rate:.2f}%", f"{(put_away_rate - all_put_away_rates.mean()) / all_put_away_rates.std():.1f} SD")

        # 3) Pitch Type Arsenal
        st.sidebar.write("### Pitch Arsenal")
        arsenal = player_data["pitch_type"].value_counts()
        st.sidebar.table(arsenal)

        # 4) Flashcard for Selected Pitch
        selected_pitch = st.sidebar.selectbox("Select a Pitch Type", arsenal.index)
        if selected_pitch:
            pitch_data = player_data[player_data["pitch_type"] == selected_pitch]
            st.sidebar.write("### Metrics for Selected Pitch")
            st.sidebar.table(calculate_pitch_metrics(pitch_data))

        # 5) Stats Box
        st.write("### Player Stats")
        stats = {
            "Innings Pitched": len(player_data) / 3,
            "K%": kbb_rate,
            "BB%": 0,
            "K-BB%": kbb_rate,
            "HR%": 0,
            "wOBA": player_data["woba_value"].mean(),
            "FIP": 0,
            "xFIP": 0,
            "WAR": 0,
        }
        st.table(pd.DataFrame(stats, index=["Value"]))

        # 6) Pitch Usage Visualization
        st.write("### Pitch Usage Overview")
        usage_data = player_data["pitch_type"].value_counts(normalize=True).reset_index()
        usage_data.columns = ["Pitch Type", "Usage"]
        pie_chart = px.pie(
            usage_data, values="Usage", names="Pitch Type",
            title="Overall Pitch Usage", color="Pitch Type",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(pie_chart, use_container_width=True)

        # 7) Movement Plot
        st.write("### Pitch Movement Profile")
        movement_plot = px.scatter(
            player_data, x="pfx_x", y="pfx_z", color="pitch_type",
            title="Pitch Movement", labels={"pfx_x": "HB", "pfx_z": "VB"},
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(movement_plot, use_container_width=True)

        # 8) Results Table
        st.write("### Pitch Results")
        results = {
            "Zone%": player_data["zone"].mean(),
            "Called Strike%": 0,
            "Swing Rate": 0,
            "Chase Rate": 0,
            "Whiff Rate": 0,
            "In-Zone Whiff Rate": 0,
            "Hard Hit%": 0,
            "Groundball%": 0,
            "Pop Fly%": 0,
        }
        st.table(pd.DataFrame(results, index=["Value"]))

        # 9) Definitions
        st.write("""
        **K-BB%**: Strikeout rate minus walk rate.
        **Race to 2K%**: Reaching 2 strikes before 2 balls.
        """)
