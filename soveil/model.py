"""Layer 2 (lightweight): physics-style soiling model.
Daily loss = carry-over + deposition. Deposition scales with forecast PM10.
Rain >= RAIN_CLEAN_MM or a cleaning crew resets the panel before that day's dust lands."""
import numpy as np

K_DEP = 0.004        # % efficiency loss per (ug/m3 PM10) per day  (calibrate on real data!)
RAIN_CLEAN_MM = 3.0  # rain that naturally cleans panels
PSH = 6.0            # equivalent peak sun hours per day


def daily_deposition(df, scale=1.0):
    return (df["pm10_mean"].values * K_DEP * scale)


def rain_flags(df):
    return (df["rain_mm"].values >= RAIN_CLEAN_MM)


def trajectory(initial, dep, rain, clean):
    """End-of-day soiling loss (%) for each day."""
    loss, prev = [], initial
    for d in range(len(dep)):
        base = 0.0 if (clean[d] or rain[d]) else prev
        prev = base + dep[d]
        loss.append(prev)
    return np.array(loss)


def uncertainty_band(initial, df):
    """P10/P50/P90 of the no-clean trajectory; spread grows with horizon."""
    dep, rain = daily_deposition(df), rain_flags(df)
    z = np.zeros(len(dep), dtype=bool)
    p50 = trajectory(initial, dep, rain, z)
    t = np.arange(1, len(dep) + 1)
    spread = 0.12 * np.sqrt(t)
    p10 = trajectory(initial, dep * (1 - spread), rain, z)
    p90 = trajectory(initial, dep * (1 + spread), rain, z)
    return p10, p50, p90
