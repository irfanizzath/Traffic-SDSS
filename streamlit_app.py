from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class Approach:
    name: str
    origin_lat: float
    origin_lon: float
    baseline_duration_min: float
    route_bias: float


INTERSECTION_CENTER = (25.238957662062077, 55.27264884409568)
APPROACHES = [
    Approach("2nd December St from Etihad Museum", 25.240403111239722, 55.26962252293249, 1.6, 0.10),
    Approach("2nd December St from Satwa", 25.236510554482432, 55.27685392208667, 1.4, 0.08),
    Approach("From Al Mina St", 25.242435925934902, 55.27581476033852, 1.5, 0.06),
    Approach("Al Wasl St (In)", 25.23482072689464, 55.27057671723187, 1.2, 0.05),
]


def _time_of_day_label(hour: int) -> str:
    if 7 <= hour <= 10:
        return "Morning Peak"
    if 11 <= hour <= 16:
        return "Midday"
    if 17 <= hour <= 20:
        return "Evening Peak"
    return "Off-Peak"


def _time_of_day_factor(label: str) -> float:
    return {
        "Morning Peak": 1.55,
        "Midday": 1.15,
        "Evening Peak": 1.75,
        "Off-Peak": 0.95,
    }[label]


def _congestion_label(delay_min: float) -> str:
    if delay_min <= 0.5:
        return "🟢 Light traffic"
    if delay_min <= 1.5:
        return "🟠 Moderate traffic"
    if delay_min <= 3:
        return "🔴 Heavy traffic"
    return "🚦 Very heavy congestion"


def _triangular_membership(x: float, a: float, b: float, c: float) -> float:
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def _fuzzy_signal_recommendation(delay_min: float, traffic_ratio: float, peak_factor: float) -> tuple[float, int]:
    delay_n = float(np.clip(delay_min / 4.5, 0.0, 1.0))
    pressure_n = float(np.clip((traffic_ratio - 1.0) / 1.2, 0.0, 1.0))
    peak_n = float(np.clip((peak_factor - 1.0) / 0.8, 0.0, 1.0))

    delay_low = max(0.0, 1.0 - delay_n / 0.45)
    delay_med = _triangular_membership(delay_n, 0.2, 0.5, 0.8)
    delay_high = min(1.0, max(0.0, (delay_n - 0.5) / 0.5))

    pressure_low = max(0.0, 1.0 - pressure_n / 0.45)
    pressure_med = _triangular_membership(pressure_n, 0.2, 0.5, 0.85)
    pressure_high = min(1.0, max(0.0, (pressure_n - 0.5) / 0.5))

    peak_low = max(0.0, 1.0 - peak_n / 0.5)
    peak_high = min(1.0, max(0.0, (peak_n - 0.4) / 0.6))

    urgent = max(
        min(delay_high, pressure_high),
        min(delay_high, peak_high),
        min(pressure_high, peak_high),
    )
    moderate = max(
        min(delay_med, pressure_med),
        min(delay_med, peak_high),
        min(pressure_med, peak_high),
    )
    normal = max(min(delay_low, pressure_low), min(delay_low, peak_low))

    score = np.clip((normal * 25) + (moderate * 62) + (urgent * 95), 0, 100)
    extension_sec = int(np.interp(score, [0, 35, 55, 75, 100], [0, 5, 10, 18, 30]))
    return float(round(score, 1)), extension_sec


def simulate_dataset(hours: int, incident_probability: float, seed: int) -> pd.DataFrame:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    rows: list[dict] = []
    rng = np.random.default_rng(seed)

    for i in range(hours):
        ts = now - timedelta(hours=(hours - i - 1))
        day_of_week = ts.strftime("%A")
        tod = _time_of_day_label(ts.hour)
        tod_factor = _time_of_day_factor(tod)

        for approach in APPROACHES:
            base = approach.baseline_duration_min
            stochastic = rng.normal(0, 0.12)
            incident = rng.uniform(0.8, 2.4) if rng.random() < incident_probability else 0.0

            duration_in_traffic = max(
                base * (tod_factor + approach.route_bias) + stochastic + incident,
                base * 0.85,
            )
            duration = base
            delay = max(duration_in_traffic - duration, 0.0)
            ratio = duration_in_traffic / duration
            fuzzy_score, extension_sec = _fuzzy_signal_recommendation(delay, ratio, tod_factor)

            rows.append(
                {
                    "timestamp_utc": ts.isoformat(),
                    "day_of_week": day_of_week,
                    "time_of_day": tod,
                    "approach_name": approach.name,
                    "origin_lat": approach.origin_lat,
                    "origin_lon": approach.origin_lon,
                    "destination_lat": INTERSECTION_CENTER[0],
                    "destination_lon": INTERSECTION_CENTER[1],
                    "estimated_travel_time_min": round(duration, 2),
                    "travel_time_in_traffic_min": round(duration_in_traffic, 2),
                    "traffic_delay_min": round(delay, 2),
                    "traffic_ratio": round(ratio, 3),
                    "congestion_label": _congestion_label(delay),
                    "fuzzy_priority_score": fuzzy_score,
                    "recommended_green_extension_sec": extension_sec,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(page_title="Traffic SDSS (Local Simulation)", layout="wide")
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  {
            font-family: "Dubai", "Dubai Regular", "Segoe UI", sans-serif;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Traffic SDSS — Local Simulated Decision Support")
    st.caption("Using approach-level travel time data, simulated locally, with fuzzy signal recommendations.")

    with st.sidebar:
        st.header("Simulation Controls")
        hours = st.slider("Lookback window (hours)", min_value=12, max_value=168, value=48, step=12)
        incident_probability = st.slider("Incident probability", min_value=0.00, max_value=0.35, value=0.08, step=0.01)
        seed = st.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1)

    df = simulate_dataset(hours=hours, incident_probability=incident_probability, seed=int(seed))
    latest_ts = df["timestamp_utc"].max()
    latest = df[df["timestamp_utc"] == latest_ts].copy()
    latest = latest.sort_values("traffic_delay_min", ascending=False)

    col1, col2, col3 = st.columns(3)
    col1.metric("Approaches", f"{latest['approach_name'].nunique()}")
    col2.metric("Average Delay (min)", f"{latest['traffic_delay_min'].mean():.2f}")
    col3.metric("Max Delay (min)", f"{latest['traffic_delay_min'].max():.2f}")

    st.subheader("Latest Snapshot by Approach")
    st.dataframe(
        latest[
            [
                "approach_name",
                "day_of_week",
                "time_of_day",
                "estimated_travel_time_min",
                "travel_time_in_traffic_min",
                "traffic_delay_min",
                "congestion_label",
                "fuzzy_priority_score",
                "recommended_green_extension_sec",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("Delay by Approach (Latest Snapshot)")
    st.bar_chart(latest.set_index("approach_name")["traffic_delay_min"], use_container_width=True)

    st.subheader("Delay Trend")
    trend = (
        df.pivot_table(index="timestamp_utc", columns="approach_name", values="traffic_delay_min", aggfunc="mean")
        .sort_index()
    )
    st.line_chart(trend, use_container_width=True)

    st.subheader("Fuzzy Priority Trend")
    priority_trend = (
        df.pivot_table(index="timestamp_utc", columns="approach_name", values="fuzzy_priority_score", aggfunc="mean")
        .sort_index()
    )
    st.line_chart(priority_trend, use_container_width=True)

    st.download_button(
        "Download simulated dataset (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="traffic_sdss_simulated_data.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
