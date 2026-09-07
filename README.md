# Real-Time Traffic Signal Decision Support System Using Google Maps API in Dubai

This project provides a **real-time traffic signal decision support system** using the Google Maps API. It calculates traffic delays from multiple origin points to a target intersection in Dubai and visualizes congestion levels to aid traffic management and decision-making.

---

## Features

- Fetches real-time traffic data from Google Maps for multiple origin points.
- Calculates:
  - Estimated travel time
  - Travel time in current traffic
  - Traffic delay
- Categorizes congestion levels with intuitive traffic indicators:
  - 🟢 Light traffic
  - 🟠 Moderate traffic
  - 🔴 Heavy traffic
  - 🚦 Very heavy congestion
- Visualizes traffic delays with a color-coded horizontal bar chart for easy interpretation.

![Traffic SDS](https://github.com/user-attachments/assets/68f65cb0-e85c-441a-8b0c-1109d281b9ab)

---

## Local Interactive Build (Simulated Data, No API Needed)

Because API quota may be unavailable, this repository now includes a **local Python interactive app** that uses **simulated traffic data** built from the same approach names and coordinates.

### Data points used

- Approach/route name  
- Origin/destination coordinates  
- Estimated travel time  
- Travel time in current traffic (simulated)  
- Timestamp/day/time-of-day  

Derived fields:
- Traffic delay
- Congestion level
- Fuzzy priority score
- Recommended green extension (seconds)

### Fixed approach names used in simulation

- 2nd December St from Etihad Museum
- 2nd December St from Satwa
- From Al Mina St
- Al Wasl St (In)

### Run locally

```bash
python -m pip install -r /home/runner/work/Traffic-SDSS/Traffic-SDSS/requirements.txt
streamlit run /home/runner/work/Traffic-SDSS/Traffic-SDSS/streamlit_app.py
```

### Dubai font

The app UI is configured to prefer **Dubai** font:

```text
font-family: "Dubai", "Dubai Regular", "Segoe UI", sans-serif
```

If Dubai is installed on your system, it will be used automatically.
