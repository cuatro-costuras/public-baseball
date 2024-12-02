import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import plotly.express as px

# Function to load 2024 Statcast data
@st.cache_data
def load_monthly_statcast():
    base_url = "https://raw.githubusercontent.com/cuatro-costuras/public-baseball/main/"
    combined_data = pd.DataFrame()
    columns_to_keep = [
        "player_name", "pitch_type", "pfx_x", "pfx_z", "release_speed", "innings_pitched",
        "k_rate", "bb_rate", "kbb_rate", "race_to_2k_rate", "put_away_rate", "woba", 
        "fip", "xfip", "war", "zone_rate", "called_strike_rate", "swing_rate", "chase_rate",
        "whiff_rate", "in_zone_whiff_rate", "hard_hit_rate", "groundball_rate", "flyball_rate"
    ]

    for month in range(3, 11):  # March to October
        file_name = f'statcast_2024_{month:02d}.csv.gz'
        file_url = f"{base_url}{file_name}"
        try:
            monthly_data = pd.read_csv(file_url, compression="gzip", usecols=columns_to_keep)
            combined_data = pd.concat([combined_data, monthly_data], ignore_index=True)
        except Exception as e:
            st.error(f"Error loading file {file_name}: {e}")
    return combined_data

# Load data
data = load_monthly_statcast()

# Ensure data is loaded
if data.empty:
    st.error("No data available. Please ensure the monthly Statcast data files are uploaded.")
else:
    st.title("MLB Player Profile App")

    # 1. Player Dropdown
    all_players = sorted(data["player_name"].dropna().unique())
    selected_player = st.selectbox("Select a Player:", options=["Type a name or select..."] + all_players)

    if selected_player and selected_player != "Type a name or select...":
        player_data = data[data["player_name"] == selected_player]
        
        # 2. Display top metrics
        st.header(f"Player Profile: {selected_player}")
        st.subheader("Top Metrics")
        col1, col2, col3 = st.columns(3)

        # Top Metrics
        col1.metric("K-BB%", f"{player_data['kbb_rate'].mean():.2f}%", f"{np.percentile(player_data['kbb_rate'], 75):.1f} percentile")
        col2.metric("Race to 2K", f"{player_data['race_to_2k_rate'].mean():.2f}%", f"{np.percentile(player_data['race_to_2k_rate'], 75):.1f} percentile")
        col3.metric("Put Away Rate", f"{player_data['put_away_rate'].mean():.2f}%", f"{np.percentile(player_data['put_away_rate'], 75):.1f} percentile")

        # 3. Pitch Arsenal
        st.subheader("Pitch Arsenal")
        arsenal = player_data["pitch_type"].value_counts().reset_index()
        arsenal.columns = ["Pitch Type", "Usage"]
        st.dataframe(arsenal)

        selected_pitch = st.selectbox("Select a Pitch Type:", options=arsenal["Pitch Type"])
        if selected_pitch:
            pitch_metrics = player_data[player_data["pitch_type"] == selected_pitch]
            st.write(f"Metrics for {selected_pitch}")
            metrics_table = pitch_metrics[["release_speed", "pfx_x", "pfx_z"]].describe().T
            st.dataframe(metrics_table)

        # 5. Player Stats
        st.subheader("Player Stats")
        stats = {
            "Innings Pitched": player_data["innings_pitched"].sum(),
            "K%": f"{player_data['k_rate'].mean():.2f}%",
            "BB%": f"{player_data['bb_rate'].mean():.2f}%",
            "K-BB%": f"{player_data['kbb_rate'].mean():.2f}%",
            "HR%": f"{player_data['flyball_rate'].mean():.2f}%",
            "wOBA": f"{player_data['woba'].mean():.3f}",
            "FIP": f"{player_data['fip'].mean():.2f}",
            "xFIP": f"{player_data['xfip'].mean():.2f}",
            "WAR": f"{player_data['war'].sum():.2f}"
        }
        stats_df = pd.DataFrame(stats.items(), columns=["Stat", "Value"])
        st.table(stats_df)

        # 6. Pie Chart for Pitch Usage
        st.subheader("Pitch Usage")
        pitch_usage_fig = px.pie(arsenal, values="Usage", names="Pitch Type", title="Overall Pitch Usage")
        st.plotly_chart(pitch_usage_fig)

        # 7. Movement Plot
        st.subheader("Pitch Movement Plot")
        movement_plot = alt.Chart(player_data).mark_circle(size=100).encode(
            x=alt.X("pfx_x", title="Horizontal Break (inches)"),
            y=alt.Y("pfx_z", title="Vertical Break (inches)"),
            color=alt.Color("pitch_type", legend=alt.Legend(title="Pitch Type")),
            tooltip=["pitch_type", "pfx_x", "pfx_z"]
        ).properties(width=600, height=400)
        st.altair_chart(movement_plot, use_container_width=True)

        # 8. Pitch Results Table
        st.subheader("Pitch Results")
        results = player_data[[
            "zone_rate", "called_strike_rate", "swing_rate", "chase_rate", 
            "whiff_rate", "in_zone_whiff_rate", "hard_hit_rate", 
            "groundball_rate", "flyball_rate"
        ]].mean()
        results_df = pd.DataFrame(results, columns=["Value"]).reset_index()
        results_df.columns = ["Metric", "Value"]
        st.table(results_df)

        # 9. Definitions
        st.subheader("Definitions")
        st.write("""
        - **K%**: Strikeout percentage.
        - **BB%**: Walk percentage.
        - **K-BB%**: Difference between strikeout and walk percentages.
        - **Race to 2K**: Percentage of times pitcher gets to two strikes before two balls.
        - **Put Away Rate**: Percentage of times pitcher gets an out after two strikes.
        """)
