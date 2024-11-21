import pandas as pd
import numpy as np
import streamlit as st
import requests
from io import BytesIO
import matplotlib.pyplot as plt

# Function to load 2024 Statcast data from GitHub (March to October)
@st.cache_data
def load_2024_data():
    # Base URL for your GitHub repository
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/shape-consistency-app/main/"

    # Initialize an empty DataFrame
    combined_data = pd.DataFrame()

    # Loop through 2024 monthly files (March to October)
    for month in range(3, 11):  # Months 3 (March) to 10 (October)
        file_name = f'statcast_2024_{month:02d}.csv.gz'
        file_url = f"{base_url}{file_name}"

        try:
            # Download the file from GitHub
            response = requests.get(file_url)
            response.raise_for_status()  # Ensure the request was successful
            file_content = BytesIO(response.content)

            # Load the file content into a DataFrame
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
            # Get unique pitcher names for user selection
            pitcher_options = filtered_pitchers["player_name"].unique()
            selected_pitcher = st.selectbox("Select a pitcher:", pitcher_options)

            # Filter data for the selected pitcher
            pitcher_data = data[data["player_name"] == selected_pitcher]

            # Step 2: Dropdown for pitch type
            arsenal = pitcher_data["pitch_type"].dropna().unique()
            pitch_type = st.selectbox("Select a pitch type from their arsenal:", arsenal)

            if pitch_type:
                # Filter data for the selected pitch type
                pitch_data = pitcher_data[pitcher_data["pitch_type"] == pitch_type]

                if pitch_data.empty:
                    st.warning("No data available for the selected pitch type.")
                else:
                    # Step 3: Movement Plot
                    st.write(f"Movement Plot for {pitch_type} (Pitcher: {selected_pitcher})")
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.scatter(
                        pitch_data["pfx_x"], pitch_data["pfx_z"], alpha=0.6, label=f"{pitch_type} movement"
                    )
                    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
                    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
                    ax.set_title(f"{selected_pitcher} - {pitch_type} Movement", fontsize=14)
                    ax.set_xlabel("Horizontal Break (pfx_x)", fontsize=12)
                    ax.set_ylabel("Vertical Break (pfx_z)", fontsize=12)
                    ax.legend()
                    st.pyplot(fig)

                    # Step 4: Consistency Score and Visualization
                    st.write("### Pitch Consistency")
                    
                    # Calculate consistency metrics
                    horizontal_std = pitch_data["pfx_x"].std()
                    vertical_std = pitch_data["pfx_z"].std()
                    overall_consistency_score = np.sqrt(horizontal_std**2 + vertical_std**2)

                    st.write(f"Consistency Score: **{overall_consistency_score:.2f}**")

                    # Median, 25th, and 75th percent
