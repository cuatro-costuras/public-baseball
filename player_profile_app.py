import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from io import BytesIO
import requests

# Mapping pitch type abbreviations to full text for color-coding
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

# Function to load the grouped Statcast 2024 data
@st.cache_data
def load_statcast_data():
    file_url = "https://raw.githubusercontent.com/cuatro-costuras/public-baseball/main/statcast_2024_grouped.csv"
    response = requests.get(file_url)
    response.raise_for_status()
    data = pd.read_csv(BytesIO(response.content))
    
    # Convert pitch type to full text
    data["pitch_type"] = data["pitch_type"].map(pitch_type_mapping).fillna("Unknown")
    return data

# Load data
data = load_statcast_data()

# Ensure data loaded successfully
if data.empty:
    st.error("No data available. Please check the dataset.")
else:
    # UI Layout
    st.title("MLB Player Profile")
    st.write("Analyze MLB pitchers' profiles based on Statcast 2024 data.")

    # 1) Player Name Dropdown with Search
    player_names = sorted(data["player_name"].dropna().unique())
    selected_player = st.selectbox("Search or Select a Player:", ["Select a Player"] + player_names)
    
    if selected_player != "Select a Player":
        player_data = data[data["player_name"] == selected_player]

        # 2) K-BB%, Race to 2K, and Put Away Rate (Top Boxes)
        col1, col2, col3 = st.columns(3)
        k_bb_percent = player_data["k_bb_percent"].iloc[0]
        race_to_2k = player_data["race_to_2k"].iloc[0]
        put_away = player_data["put_away_rate"].iloc[0]
        k_bb_percentile = player_data["k_bb_percentile"].iloc[0]
        race_to_2k_percentile = player_data["race_to_2k_percentile"].iloc[0]
        put_away_percentile = player_data["put_away_percentile"].iloc[0]

        col1.metric("K-BB%", f"{k_bb_percent:.2f}%", f"{k_bb_percentile}th Percentile")
        col2.metric("Race to 2K", f"{race_to_2k:.2f}%", f"{race_to_2k_percentile}th Percentile")
        col3.metric("Put Away", f"{put_away:.2f}%", f"{put_away_percentile}th Percentile")

        # 3) Pitch Type Box with Color Coding
        st.subheader("Pitch Arsenal")
        pitch_types = player_data["pitch_type"].unique()
        pitch_type_colors = alt.Scale(
            domain=list(pitch_types),
            range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        )
        selected_pitch_type = st.selectbox("Select a Pitch Type:", ["Select a Pitch"] + list(pitch_types))

        if selected_pitch_type != "Select a Pitch":
            st.write(f"### {selected_pitch_type} Metrics")
            metrics_table = player_data[player_data["pitch_type"] == selected_pitch_type][[
                "velocity", "vb", "hb", "extension", "vaa", "haa"
            ]]
            st.table(metrics_table)

        # 4) Stats Box
        st.subheader("Season Stats")
        stats = player_data[[
            "innings_pitched", "k_percent", "bb_percent", "k_bb_percent", 
            "hr_percent", "woba", "fip", "xfip", "war"
        ]]
        st.table(stats)

        # 5) Pie Chart and Trie for Usage
        st.subheader("Pitch Usage")
        pie_chart = alt.Chart(player_data).mark_arc().encode(
            theta="usage:Q",
            color=alt.Color("pitch_type:N", scale=pitch_type_colors),
            tooltip=["pitch_type", "usage"]
        )
        st.altair_chart(pie_chart, use_container_width=True)

        # Trie visualization can be implemented in a similar way with custom diagrams

        # 6) Movement Plot
        st.subheader("Movement Plot")
        movement_chart = alt.Chart(player_data).mark_circle(size=100).encode(
            x="horizontal_break:Q",
            y="vertical_break:Q",
            color=alt.Color("pitch_type:N", scale=pitch_type_colors),
            tooltip=["pitch_type", "horizontal_break", "vertical_break"]
        ).properties(
            width=600, height=400
        )
        st.altair_chart(movement_chart, use_container_width=True)

        # 7) Pitch Results Table
        st.subheader("Pitch Results")
        pitch_results = player_data[[
            "zone_percent", "called_strike_percent", "swing_rate", "chase_rate", 
            "whiff_rate", "in_zone_whiff_rate", "hard_hit_percent", "groundball_percent", "pop_fly_percent"
        ]]
        st.table(pitch_results)

        # 8) Definitions
        st.subheader("Metric Definitions")
        st.write("""
        **K-BB%**: Strikeout rate minus walk rate.
        **Race to 2K**: Frequency of getting to 2 strikes before 2 balls.
        **Put Away**: Rate of putting hitters away once getting to 2 strikes.
        **VB (Vertical Break)**: Vertical movement of a pitch.
        **HB (Horizontal Break)**: Horizontal movement of a pitch.
        **Zone%**: Percentage of pitches in the strike zone.
        **wOBA**: Weighted On-Base Average.
        **WAR**: Wins Above Replacement.
        """)
