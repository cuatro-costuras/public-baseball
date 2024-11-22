# MLB Pitch Analysis Apps

## Overview
This repository hosts two Streamlit applications designed to analyze MLB pitchers' pitch movement and consistency using 2024 Statcast data.

1. **Shape Consistency App**:
   - Analyze a pitcher’s ability to consistently repeat the shape of their pitches.
   - Search for a pitcher, select a pitch type, and visualize its movement profile along with a consistency score.

2. **Movement Profile Distributions App**:
   - View violin plots of horizontal and vertical movement, as well as velocity distributions, for each pitch type in a pitcher's arsenal.
   - Rank pitches by their shape consistency and compare them to other pitchers throwing the same pitch type.

Both apps utilize the 2024 Statcast monthly data files.

---

## Features

### **Shape Consistency App**
- **Search for MLB Pitchers**:
  - Find and select a pitcher from the dataset.
  
- **Pitch Arsenal Dropdown**:
  - Choose from the available pitch types in the pitcher's arsenal.

- **Pitch Movement Visualization**:
  - Display a movement plot of the selected pitch type (horizontal and vertical break).

- **Consistency Score**:
  - View a calculated consistency score for each pitch type based on its movement repeatability.

---

### **Movement Profile Distributions App**
- **Search and Filter**:
  - Search or select a pitcher from the dataset.

- **Violin Plots**:
  - View horizontal break, vertical break, and velocity distributions for all pitch types in the pitcher's arsenal.
  - Each pitch type is color-coded for clarity, with a key displayed next to the graphs.

- **Shape Consistency Ranking**:
  - Rank pitches in a pitcher's arsenal based on their movement and velocity consistency (lowest standard deviation first).
  - Includes percentile rankings for each pitch type compared to other pitchers in the dataset.

- **Definitions**:
  - Clear definitions for consistency score, density, and percentile are provided to aid interpretation.

---

## Requirements

- **Python 3.8 or later**
- **Dependencies**:
  - `pandas`
  - `numpy`
  - `altair`
  - `streamlit`
  - `requests`

Install dependencies with:
```bash
pip install -r requirements.txt
