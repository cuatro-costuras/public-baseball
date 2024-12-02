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

def calculate_percentile(value, all_values):
    return np.percentile(all_values, 100 * (value <= all_values))

# Function to calculate pitch-specific metrics
def calculate_pitch_metrics(pitch_data):
    metrics = {}
    metrics["Velocity"] = pitch_data["release_speed"].mean()
    metrics["VB"] = pitch_data["pfx_z"].mean()  # Vertical break
    metrics["HB"] = pitch_data["pfx_x"].mean()  # Horizontal break
    metrics["Extension"] = pitch_data["release_extension"].mean()
    metrics["VAA"] = pitch_data["plate_z"].mean()  # Approximation for VAA
    metrics["HAA"] = pitch_data["plate_x"].mean()  # Approximation for HAA
    metrics["Release Height"] = pitch_data["release_pos_y"].mean()
    metrics["Release Side"] = pitch_data["plate_x"].mean()
    return pd.DataFrame(metrics, index=["Value"])

# Main App
data = load_monthly_statcast()

if data.empty:
    st.error("No data available. Please ensure the monthly Statcast data files are uploaded.")
else:
    st.set_page_config(layout="wide")  # Set layout to wide
    st.title("MLB Player Profile App")

    # 1) Player Name Dropdown/Search Bar
    player_names = sorted(data["player_name"].dropna().unique())
    player_name = st.selectbox("Select a Player", [""] + player_names)

    if player_name:
        player_data = data[data["player_name"] == player_name]
        
        # 2) Metrics Boxes with Percentile Rankings
        kbb_rate = calculate_kbb_rate(player_data)
        race_to_2k_rate = calculate_percentile(kbb_rate, data["kbb_rate"])
        put_away_rate = calculate_percentile(kbb_rate, data["put_away_rate"])

        col1, col2, col3 = st.columns(3)
        col1.metric("K-BB%", f"{kbb_rate:.2f}%", f"{race_to_2k_rate:.1f} percentile")
        col2.metric("Race to 2K%", f"{race_to_2k_rate:.2f}%", f"{put_away_rate:.1f} percentile")
        col3.metric("Put Away Rate", f"{put_away_rate:.2f}%", f"{race_to_2k_rate:.1f} percentile")

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
            "Innings Pitched": len(player_data) / 3,  # Approximation
            "K%": kbb_rate,
            "BB%": 0,  # Placeholder
            "K-BB%": kbb_rate,  # Same as K-BB%
            "HR%": 0,  # Placeholder
            "wOBA": player_data["woba_value"].mean(),
            "FIP": 0,  # Placeholder
            "xFIP": 0,  # Placeholder
            "WAR": 0,  # Placeholder
        }
        st.table(pd.DataFrame(stats, index=["Value"]))

         # 6) Pitch Usage Visualization
        st.write("### Pitch Usage Overview")
        usage_data = player_data["pitch_type"].value_counts(normalize=True).reset_index()
        usage_data.columns = ["Pitch Type", "Usage"]
        pie_chart = px.pie(
            usage_data, values="Usage", names="Pitch Type", 
            color="Pitch Type", 
            title="Overall Pitch Usage",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(pie_chart, use_container_width=True)

        st.write("### Pitch Usage by Count")
        # Generate a count tree for pitch usage visualization
        count_tree = player_data.groupby(["balls", "strikes", "pitch_type"]).size().reset_index(name="Count")
        count_tree["Count %"] = count_tree["Count"] / count_tree["Count"].sum() * 100

        for count in sorted(count_tree["balls"].unique()):
            st.write(f"#### Count: {count}-0")
            sub_data = count_tree[count_tree["balls"] == count]
            count_pie = px.pie(
                sub_data, values="Count %", names="pitch_type", 
                color="pitch_type", title=f"Pitch Usage at Count {count}-0",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(count_pie, use_container_width=True)

        # 7) Movement Plot with Quadrants
        st.write("### Pitch Movement Plot")
        movement_plot = px.scatter(
            player_data, x="pfx_x", y="pfx_z", color="pitch_type", 
            labels={"pfx_x": "Horizontal Break (inches)", "pfx_z": "Vertical Break (inches)"},
            title="Pitch Movement Profile",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        movement_plot.update_layout(
            shapes=[
                {"type": "line", "x0": 0, "x1": 0, "y0": player_data["pfx_z"].min(), "y1": player_data["pfx_z"].max(), "line": {"color": "Black", "width": 2}},
                {"type": "line", "x0": player_data["pfx_x"].min(), "x1": player_data["pfx_x"].max(), "y0": 0, "y1": 0, "line": {"color": "Black", "width": 2}}
            ]
        )
        st.plotly_chart(movement_plot, use_container_width=True)

        # 8) Results Table
        st.write("### Pitch Results")
        results = {
            "Zone%": player_data["zone"].mean(),
            "Called Strike%": 0,  # Placeholder
            "Swing Rate": 0,  # Placeholder
            "Chase Rate": 0,  # Placeholder
            "Whiff Rate": 0,  # Placeholder
            "In-Zone Whiff Rate": 0,  # Placeholder
            "Hard Hit%": 0,  # Placeholder
            "Groundball%": 0,  # Placeholder
            "Pop Fly%": 0,  # Placeholder
        }
        st.table(pd.DataFrame(results, index=["Value"]))

        # 9) Definitions and Calculations
        st.write("### Definitions and Calculations")
        st.write("""
        **K-BB%**: Strikeout rate minus walk rate.
        **Race to 2K%**: How often a pitcher reaches 2 strikes before 2 balls.
        **Put Away Rate**: Rate at which a pitcher strikes out hitters once they reach 2 strikes.
        **Zone%**: Percentage of pitches in the strike zone.
        **Velocity (mph)**: Average velocity of a pitch.
        **VB (Vertical Break)**: The vertical movement of the pitch caused by spin and gravity.
        **HB (Horizontal Break)**: The horizontal movement of the pitch caused by spin.
        **Extension**: The distance from the mound at which the ball is released.
        **VAA**: Vertical approach angle as the ball crosses the plate.
        **HAA**: Horizontal approach angle as the ball crosses the plate.
        **Release Height**: The height of the pitcher's release point.
        **Release Side**: The side-to-side position of the pitcher's release point relative to the mound.
        **WAR**: Wins Above Replacement, an advanced metric evaluating a player's total contributions.
        **Percentile**: How a player's metric compares to others in the dataset, expressed as a percentage.
        """)
