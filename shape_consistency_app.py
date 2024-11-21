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
                # Step 3: Calculate consistency score (unitless)
                horizontal_std = pitch_data["pfx_x"].std()
                vertical_std = pitch_data["pfx_z"].std()
                overall_consistency_score = np.sqrt(horizontal_std**2 + vertical_std**2)

                st.write(f"### Consistency Score for {pitch_type}: **{overall_consistency_score:.2f}** (unitless)")

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

                # Step 5: Movement Plot
                st.write(f"### Movement Plot for {pitch_type} (Pitcher: {pitcher_name})")

                # Convert movement to inches for plotting
                pitch_data["pfx_x_inches"] = pitch_data["pfx_x"] * 12  # Convert horizontal movement to inches
                pitch_data["pfx_z_inches"] = pitch_data["pfx_z"] * 12  # Convert vertical movement to inches
                mean_pfx_x_inches = pitch_data["pfx_x_inches"].mean()
                mean_pfx_z_inches = pitch_data["pfx_z_inches"].mean()
                horizontal_std_inches = pitch_data["pfx_x_inches"].std()
                vertical_std_inches = pitch_data["pfx_z_inches"].std()

                # Scatterplot for individual pitches
                movement_plot = alt.Chart(pitch_data).mark_circle(size=60, opacity=0.6).encode(
                    x=alt.X("pfx_x_inches", title="Horizontal Break (inches)"),
                    y=alt.Y("pfx_z_inches", title="Vertical Break (inches)"),
                    tooltip=["pfx_x_inches", "pfx_z_inches"]
                )

                # Mean marker
                mean_marker = alt.Chart(pd.DataFrame({
                    "pfx_x_inches": [mean_pfx_x_inches],
                    "pfx_z_inches": [mean_pfx_z_inches],
                })).mark_point(size=150, color="red", shape="diamond").encode(
                    x="pfx_x_inches",
                    y="pfx_z_inches",
                    tooltip=["pfx_x_inches", "pfx_z_inches"]
                )

                # Shaded rectangles for standard deviation (in inches)
                std_rect_x = alt.Chart(pd.DataFrame({
                    "x_start": [mean_pfx_x_inches - horizontal_std_inches],
                    "x_end": [mean_pfx_x_inches + horizontal_std_inches],
                    "y_start": [pitch_data["pfx_z_inches"].min()],
                    "y_end": [pitch_data["pfx_z_inches"].max()],
                })).mark_rect(opacity=0.2, color="blue").encode(
                    x="x_start:Q",
                    x2="x_end:Q",
                    y="y_start:Q",
                    y2="y_end:Q"
                )

                std_rect_y = alt.Chart(pd.DataFrame({
                    "x_start": [pitch_data["pfx_x_inches"].min()],
                    "x_end": [pitch_data["pfx_x_inches"].max()],
                    "y_start": [mean_pfx_z_inches - vertical_std_inches],
                    "y_end": [mean_pfx_z_inches + vertical_std_inches],
                })).mark_rect(opacity=0.2, color="blue").encode(
                    x="x_start:Q",
                    x2="x_end:Q",
                    y="y_start:Q",
                    y2="y_end:Q"
                )

                st.altair_chart(movement_plot + mean_marker + std_rect_x + std_rect_y, use_container_width=True)

                # Add a note below the chart
                st.write(
                    """
                    **Note:**
                    - The red diamond represents the **mean movement profile** of the selected pitch type.
                    - The blue shaded areas indicate ±1 standard deviation for horizontal and vertical break.
                    - The consistency score is a unitless value calculated as:
                      \n**Consistency Score = √(horizontal_std² + vertical_std²)**
                    """
                )
