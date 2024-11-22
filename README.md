# MLB Pitch Analysis Apps

## Overview
This repository hosts two Streamlit applications designed to analyze MLB pitchers' pitch movement and consistency using 2024 Statcast data.

1. **Shape Consistency App**:
   - Analyze a pitcher’s ability to consistently repeat the shape of their pitches.
   - Search for a pitcher, select a pitch type, and visualize its movement profile along with a consistency score.

2. **Movement Distribution App**:
   - View histograms of horizontal and vertical movement for each pitch type in a pitcher's arsenal.
   - Rank pitches by their shape consistency.

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

### **Movement Distribution App**
- **Search and Filter**:
  - Search or select a pitcher from the dataset.

- **Movement Histograms**:
  - View horizontal and vertical movement distributions for all pitch types in the arsenal.
  - Each pitch type is visualized in a unique color for clarity.

- **Shape Consistency Ranking**:
  - Rank pitches in a pitcher's arsenal based on their movement consistency (lowest standard deviation first).

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
