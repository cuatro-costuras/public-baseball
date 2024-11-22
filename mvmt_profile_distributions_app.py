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

# List of pitch types categorized for polarity adjustment
fastballs = ["Four-Seam Fastball", "Sinker", "Cutter", "Splitter", "Changeup"]
breaking_balls = ["Slider", "Curveball", "Knuckle Curve", "Sweeper", "Sweeping Curve", "Slow Curve"]

# Function to load 2024 Statcast data from GitHub (March to October)
@st.cache_data
def load_2024_data():
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/public-baseball/main/"
    combined_data = pd.DataFrame()
    columns_to_keep = ['player_name', 'pitch_type', 'pfx_x', 'pfx_z', 'release_speed', 'p_throws']

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

    # Convert movement profiles from feet to inches
    combined_data["pfx_x"] = combined_data["pfx_x"] * 12  # Horizontal movement in inches
    combined_data["pfx_z"] = combined_data["pfx_z"] * 12  # Vertical movement in inches

    return combined_data

# Load the data
data = load_2024_data()

# Ensure data is loaded before continuing
if not data.empty:
    st.title("MLB Movement Profile Distributions App")

    # Combine search bar and dropdown for pitcher selection
    all_pitchers = sorted(data["player_name"].dropna().unique())
    pitcher_name = st.selectbox(
        "Search or select a pitcher:",
        options=["Type a name or select..."] + all_pitchers
    )

    if pitcher_name and pitcher_name != "Type a name or select...":
        pitcher_data = data[data["player_name"] == pitcher_name]
        pitcher_hand = pitcher_data["p_throws"].iloc[0]  # Get the handedness of the pitcher

        # Display pitcher handedness beneath their name
        st.write(f"**Handedness**: {'Right-Handed (R)' if pitcher_hand == 'R' else 'Left-Handed (L)'}")

        # Adjust horizontal break (`pfx_x`) based on pitch type and handedness
        adjusted_pitcher_data = pitcher_data.copy()
        if pitcher_hand == "R":
            adjusted_pitcher_data.loc[adjusted_pitcher_data["pitch_type"].isin(fastballs), "pfx_x"] = np.abs(adjusted_pitcher_data["pfx_x"])
            adjusted_pitcher_data.loc[adjusted_pitcher_data["pitch_type"].isin(breaking_balls), "pfx_x"] = -np.abs(adjusted_pitcher_data["pfx_x"])
        elif pitcher_hand == "L":
            adjusted_pitcher_data.loc[adjusted_pitcher_data["pitch_type"].isin(fastballs), "pfx_x"] = -np.abs(adjusted_pitcher_data["pfx_x"])
            adjusted_pitcher_data.loc[adjusted_pitcher_data["pitch_type"].isin(breaking_balls), "pfx_x"] = np.abs(adjusted_pitcher_data["pfx_x"])

        st.write(f"### Movement Profiles for {pitcher_name}")

        # Create and display violin charts with legends on the right
        def create_violin_chart(data, field, title, y_label):
            base = alt.Chart(data).transform_density(
                density=field,
                groupby=["pitch_type"],
                as_=["value", "density"]
            )

            density = base.mark_area(opacity=0.6).encode(
                x=alt.X("value:Q", title=y_label),
                y=alt.Y("density:Q", stack="zero"),
                color=alt.Color("pitch_type:N", legend=alt.Legend(orient="right", title="Pitch Type")),
            )
            reflection = base.mark_area(opacity=0.6).encode(
                x=alt.X("value:Q", title=y_label),
                y=alt.Y("density:Q", stack="zero"),
                color=alt.Color("pitch_type:N", legend=None),
            ).transform_calculate(
                density="-datum.density"
            )

            return (density + reflection).properties(
                title=title,
                width=600,
                height=300
            )

        horizontal_violin = create_violin_chart(adjusted_pitcher_data, "pfx_x", "Horizontal Break (inches)", "Horizontal Break (inches)")
        vertical_violin = create_violin_chart(adjusted_pitcher_data, "pfx_z", "Vertical Break (inches)", "Vertical Break (inches)")
        velocity_violin = create_violin_chart(adjusted_pitcher_data, "release_speed", "Velocity (mph)", "Velocity (mph)")

        st.altair_chart(horizontal_violin, use_container_width=True)
        st.altair_chart(vertical_violin, use_container_width=True)
        st.altair_chart(velocity_violin, use_container_width=True)

        # Consistency Score Table
        all_pitchers_consistency = (
            data.groupby(["player_name", "pitch_type"])
            .apply(lambda x: np.sqrt(
                x["pfx_x"].std()**2 +
                x["pfx_z"].std()**2 +
                x["release_speed"].std()**2
            ))
            .reset_index(name="Consistency Score")
        )

        # Percentile for each pitch type
        def calculate_percentile(row):
            same_pitch_type = all_pitchers_consistency[all_pitchers_consistency["pitch_type"] == row["pitch_type"]]
            return (row["Consistency Score"] <= same_pitch_type["Consistency Score"]).mean() * 100

        all_pitchers_consistency["Percentile"] = all_pitchers_consistency.apply(calculate_percentile, axis=1)
        all_pitchers_consistency["Consistency Score"] = all_pitchers_consistency["Consistency Score"].map("{:.2f}".format)
        all_pitchers_consistency["Percentile"] = all_pitchers_consistency["Percentile"].map("{:.1f}".format)

        # Filter for the selected pitcher
        pitcher_consistency = all_pitchers_consistency[all_pitchers_consistency["player_name"] == pitcher_name]
        pitcher_consistency = pitcher_consistency.sort_values(by="Consistency Score").reset_index(drop=True)

        # Display table below the violin plots
        st.write("### Pitch Consistency Rankings")
        st.table(pitcher_consistency)

        # Consistency Score Definition
        st.write("### Consistency Score Definition")
        st.write(
            """
            **Consistency Score**: Measures how repeatable the movement and velocity of a pitch are.
            - Formula: `Consistency Score = sqrt(std_dev(pfx_x)^2 + std_dev(pfx_z)^2 + std_dev(velocity)^2)`
            - Lower scores indicate better repeatability.
            """
        )

        # Percentile Definition
        st.write(
            """
            **Percentile**: Represents where the pitch's consistency score ranks among all pitchers throwing the same pitch type.
            - A higher percentile means the pitch is more consistent compared to others of the same type.
            """
        )

        # Density Definition
        st.write("### What is Density?")
        st.write(
            """
            **Density**: A measure of how frequently certain movement or velocity values occur within the dataset.
            - Visualized by the "height" of the violin plot at a given value.
            """
        )
else:
    st.error("No data available. Please ensure the 2024 data files are uploaded to the repository.")
