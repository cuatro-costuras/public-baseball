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
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/shape-consistency-app/main/"
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
    st.title("MLB Shape Consistency App")

    # Step 1: Combine search bar and dropdown for pitcher selection
    all_pitchers = sorted(data["player_name"].dropna().unique())
    pitcher_name = st.selectbox(
        "Search or select a pitcher:",
        options=["Type a name or select..."] + all_pitchers
    )

    # Filter data for the selected pitcher
    if pitcher_name and pitcher_name != "Type a name or select...":
        pitcher_data = data[data["player_name"] == pitcher_name]

        # Step 2: Dropdown for pitch type
        arsenal = pitcher_data["pitch_type"].dropna().unique()
        pitch_type = st.selectbox("Select a pitch type from their arsenal:", arsenal)

        if pitch_type:
            pitch_data = pitcher_data[pitcher_data["pitch_type"] == pitch_type]
            if pitch_data.empty:
                st.warning("No data available for the selected pitch type.")
            else:
                # Step 3: Calculate consistency score
                horizontal_std = pitch_data["pfx_x"].std()
                vertical_std = pitch_data["pfx_z"].std()
                overall_consistency_score = np.sqrt(horizontal_std**2 + vertical_std**2)

                st.write(f"### Consistency Score for {pitch_type}: **{overall_consistency_score:.2f}**")

                # Step 4: Rank by consistency for the selected pitch type
                pitch_type_data = data[data["pitch_type"] == pitch_type]  # Filter all data by pitch type
                consistency_scores = (
                    pitch_type_data.groupby("player_name")
                    .apply(lambda x: np.sqrt(x["pfx_x"].std()**2 + x["pfx_z"].std()**2))
                    .reset_index(name="Consistency Score")
                )

                # Add rank
                consistency_scores["Rank"] = consistency_scores["Consistency Score"].rank()
                selected_pitcher_rank = consistency_scores.loc[
                    consistency_scores["player_name"] == pitcher_name, "Rank"
                ].values[0]

                st.write(f"### Rank: {int(selected_pitcher_rank)} out of {len(consistency_scores)} pitchers")

                # Step 5: Movement Plot with Mean and Standard Deviations
                st.write(f"### Movement Plot for {pitch_type} (Pitcher: {pitcher_name})")

                mean_pfx_x = pitch_data["pfx_x"].mean()
                mean_pfx_z = pitch_data["pfx_z"].mean()

                # Prepare data for plotting
                movement_plot = alt.Chart(pitch_data).mark_circle(size=60, opacity=0.6).encode(
                    x=alt.X("pfx_x", title="Horizontal Break (pfx_x)"),
                    y=alt.Y("pfx_z", title="Vertical Break (pfx_z)"),
                    tooltip=["pfx_x", "pfx_z"]
                )

                # Mean marker
                mean_marker = alt.Chart(pd.DataFrame({
                    "pfx_x": [mean_pfx_x],
                    "pfx_z": [mean_pfx_z],
                })).mark_point(size=150, color="red", shape="diamond").encode(
                    x="pfx_x",
                    y="pfx_z",
                    tooltip=["pfx_x", "pfx_z"]
                )

                # Ellipses for standard deviations
                std_ellipse = alt.Chart(pd.DataFrame({
                    "x": [mean_pfx_x - horizontal_std, mean_pfx_x + horizontal_std],
                    "y": [mean_pfx_z - vertical_std, mean_pfx_z + vertical_std]
                })).mark_circle(size=300, opacity=0.3, color="lightblue").encode(
                    x="x",
                    y="y"
                )

                st.altair_chart(movement_plot + mean_marker + std_ellipse, use_container_width=True)
