import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import requests
from io import BytesIO

# Function to load 2024 Statcast data from GitHub (March to October)
@st.cache_data
def load_2024_data():
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/shape-consistency-app/main/"
    combined_data = pd.DataFrame()
    for month in range(3, 11):  # March to October
        file_name = f'statcast_2024_{month:02d}.csv.gz'
        file_url = f"{base_url}{file_name}"
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            file_content = BytesIO(response.content)
            data = pd.read_csv(file_content, compression='gzip')
            combined_data = pd.concat([combined_data, data], ignore_index=True)
        except requests.exceptions.HTTPError as http_err:
            st.warning(f"HTTP Error for file: {file_name} - {http_err}")
        except Exception as e:
            st.error(f"Error loading file {file_name}: {e}")
    return combined_data

# Load the data
data = load_2024_data()

# Ensure data is loaded before continuing
if data.empty:
    st.error("No data available. Please ensure the 2024 data files are uploaded to the repository.")
else:
    st.title("MLB Pitch Movement Analysis App")

    # Step 1: Search bar for pitcher
    pitcher_name = st.text_input("Search for a pitcher by name:")
    if pitcher_name:
        filtered_pitchers = data[data["player_name"].str.contains(pitcher_name, case=False, na=False)]
        if filtered_pitchers.empty:
            st.warning("No pitcher found with that name.")
        else:
            pitcher_options = filtered_pitchers["player_name"].unique()
            selected_pitcher = st.selectbox("Select a pitcher:", pitcher_options)
            pitcher_data = data[data["player_name"] == selected_pitcher]

            # Step 2: Dropdown for pitch type
            arsenal = pitcher_data["pitch_type"].dropna().unique()
            pitch_type = st.selectbox("Select a pitch type from their arsenal:", arsenal)

            if pitch_type:
                pitch_data = pitcher_data[pitcher_data["pitch_type"] == pitch_type]
                if pitch_data.empty:
                    st.warning("No data available for the selected pitch type.")
                else:
                    # Step 3: Movement Plot using Altair
                    st.write(f"Movement Plot for {pitch_type} (Pitcher: {selected_pitcher})")
                    chart = alt.Chart(pitch_data).mark_circle(size=60, opacity=0.6).encode(
                        x=alt.X("pfx_x", title="Horizontal Break (pfx_x)"),
                        y=alt.Y("pfx_z", title="Vertical Break (pfx_z)"),
                        tooltip=["pfx_x", "pfx_z"]
                    ).properties(
                        title=f"{selected_pitcher} - {pitch_type} Movement",
                        width=600,
                        height=400
                    )
                    st.altair_chart(chart, use_container_width=True)

                    # Step 4: Consistency Score and Visualization
                    st.write("### Pitch Consistency")

                    # Calculate consistency metrics
                    horizontal_std = pitch_data["pfx_x"].std()
                    vertical_std = pitch_data["pfx_z"].std()
                    overall_consistency_score = np.sqrt(horizontal_std**2 + vertical_std**2)

                    st.write(f"Consistency Score: **{overall_consistency_score:.2f}**")

                    # Median and IQR
                    horizontal_median = pitch_data["pfx_x"].median()
                    vertical_median = pitch_data["pfx_z"].median()
                    horizontal_range = np.percentile(pitch_data["pfx_x"], [25, 75])
                    vertical_range = np.percentile(pitch_data["pfx_z"], [25, 75])

                    # Altair visualization for median and ranges
                    iqr_chart = alt.Chart(pitch_data).mark_circle(size=60, opacity=0.6).encode(
                        x=alt.X("pfx_x", title="Horizontal Break (pfx_x)"),
                        y=alt.Y("pfx_z", title="Vertical Break (pfx_z)")
                    ).properties(
                        title=f"{selected_pitcher} - {pitch_type} Consistency",
                        width=600,
                        height=400
                    ) + alt.Chart(pd.DataFrame({
                        "x": [horizontal_median],
                        "y": [vertical_median],
                        "color": ["Median"]
                    })).mark_point(size=120, shape="triangle", color="red").encode(
                        x="x",
                        y="y",
                        tooltip=["x", "y"]
                    )

                    st.altair_chart(iqr_chart, use_container_width=True)
