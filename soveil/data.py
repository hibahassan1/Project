"""Layer 0/1 inputs: live dust + rain forecast from Open-Meteo (free, no API key).
Falls back to a synthetic (but realistic-looking) forecast if the API is unreachable,
so the demo never breaks on stage."""
import numpy as np
import pandas as pd
import requests

# Approximate coordinates; each site is a FICTIONAL 20 MW pilot sector.
# Generic, fictional sites (no real plant names or identities implied).
# Coordinates are illustrative points spread across the UAE, not tied to any named facility.
SITES = {
    "Solar Plant 1": dict(lat=24.76, lon=55.37, mw=20),
    "Solar Plant 2": dict(lat=24.46, lon=55.33, mw=20),
    "Solar Plant 3": dict(lat=23.65, lon=53.70, mw=20),
    "Solar Plant 4": dict(lat=24.20, lon=55.75, mw=20),
}
DEFAULT_INITIAL_LOSS = {  # % soiling loss today (simulated SCADA-derived value)
    "Solar Plant 1": 3.1,
    "Solar Plant 2": 6.4,
    "Solar Plant 3": 1.2,
    "Solar Plant 4": 8.7,
}
DAYS = 7
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WX_URL = "https://api.open-meteo.com/v1/forecast"


def _daily(hourly: pd.DataFrame) -> pd.DataFrame:
    hourly["date"] = hourly["time"].dt.date
    out = hourly.groupby("date").agg(
        pm10_mean=("pm10", "mean"), pm10_max=("pm10", "max"), rain_mm=("rain", "sum")
    ).reset_index()
    return out.head(DAYS)


def _live(lat, lon) -> pd.DataFrame:
    common = dict(latitude=lat, longitude=lon, forecast_days=DAYS, timezone="Asia/Dubai")
    aq = requests.get(AQ_URL, params={**common, "hourly": "pm10"}, timeout=10).json()["hourly"]
    wx = requests.get(WX_URL, params={**common, "hourly": "precipitation"}, timeout=10).json()["hourly"]
    h = pd.DataFrame({"time": pd.to_datetime(aq["time"]), "pm10": aq["pm10"]})
    h["rain"] = pd.Series(wx["precipitation"]).reindex(range(len(h))).fillna(0).values
    h["pm10"] = h["pm10"].astype(float).ffill().fillna(90.0)
    return _daily(h)


def _synthetic(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 90 + 30 * np.sin(np.linspace(0, 2, DAYS)) + rng.normal(0, 15, DAYS)
    base[rng.integers(2, 5)] += rng.uniform(150, 350)  # a dust event
    rain = np.zeros(DAYS)
    if seed % 2 == 0:
        rain[rng.integers(4, DAYS)] = rng.uniform(4, 9)
    dates = pd.date_range(pd.Timestamp.now(tz="Asia/Dubai").date(), periods=DAYS).date
    return pd.DataFrame({"date": dates, "pm10_mean": base.clip(30), "pm10_max": base.clip(30) * 1.4, "rain_mm": rain})


def get_forecast(site: str):
    """Returns (daily_df, source_label)."""
    s = SITES[site]
    try:
        return _live(s["lat"], s["lon"]), "live Open-Meteo (CAMS) forecast"
    except Exception:
        return _synthetic(sum(map(ord, site)) % 1000), "synthetic fallback (API unreachable)"


def inject_demo_storm(forecasts, site, day_idx, storm_pm10):
    """Guarantees a dust-storm approval scenario is on screen every time the app loads, instead
    of depending on whether that week's real/synthetic forecast happens to cross the threshold.
    Copies the site's dataframe (never mutates the cached forecast) and spikes PM10 on one day
    well above the storm threshold, with no rain that day so it doesn't get washed out instead."""
    out = {s_: df.copy() for s_, df in forecasts.items()}
    df = out[site]
    day_idx = min(day_idx, len(df) - 1)
    spike = max(storm_pm10 * 1.6, storm_pm10 + 120)
    df.loc[day_idx, "pm10_mean"] = spike * 0.85
    df.loc[day_idx, "pm10_max"] = spike
    df.loc[day_idx, "rain_mm"] = 0.0
    return out
