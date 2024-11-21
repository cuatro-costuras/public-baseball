# shape-consistency-app

## Overview
This Streamlit application allows users to analyze the movement of MLB pitchers' pitches using 2024 Statcast data. Users can:
1. Search for a specific MLB pitcher.
2. Select a pitch type from the pitcher's arsenal.
3. Visualize the movement of the selected pitch type.
4. See a consistency score and visualizations for pitch shape repeatability.

---

## Features
- **Search for MLB Pitchers**:
  - Quickly search the dataset to find your desired pitcher.
  
- **Pitch Arsenal Dropdown**:
  - Once a pitcher is selected, view and choose from the available pitch types in their arsenal.

- **Pitch Movement Plot**:
  - Visualize the horizontal (`pfx_x`) and vertical (`pfx_z`) movement of the selected pitch type.

- **Consistency Score**:
  - Calculate and display a consistency score based on the standard deviation of pitch movement.
  - View median movement and interquartile ranges (IQR) for added insights.

---

## Requirements
- **Python 3.8 or later**
- **Dependencies**:
  - 'pandas'
  - 'numpy'
  - 'altair'
  - 'streamlit'
  - 'requests'

