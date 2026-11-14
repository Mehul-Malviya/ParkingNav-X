"""
Feature engineering for occupancy prediction.
Builds feature vectors from the synthetic_multi_year_demand.csv dataset.
"""

import numpy as np
import pandas as pd
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
# Prefer the dense 30-day synthetic dataset; fall back to the sparse hand-curated one.
DATA_PATH = (
    _DATA_DIR / "synthetic_demand.csv"
    if (_DATA_DIR / "synthetic_demand.csv").exists()
    else _DATA_DIR / "synthetic_multi_year_demand.csv"
)

LOT_IDS = [
    "vitap-lot-academic-main",
    "vitap-lot-hostel",
    "vitap-lot-admin-visitor",
    "vitap-lot-sports",
    "vitap-lot-overflow",
]

LOT_CAPACITIES = {
    "vitap-lot-academic-main": 108,
    "vitap-lot-hostel": 162,
    "vitap-lot-admin-visitor": 72,
    "vitap-lot-sports": 84,
    "vitap-lot-overflow": 46,
}


MIN_REAL_POINTS = 7 * 96   # a lot needs a week of real 15-minute readings before its model trains on them


def load_data(conn=None) -> pd.DataFrame:
    """Training data: synthetic demand, with real recorded occupancy replacing it for every lot that has
    at least MIN_REAL_POINTS real readings (needs `conn`). Rows carry a `data_source` column."""
    df = _load_synthetic()
    if conn is None:
        return df
    from digital_twin.observations import real_demand_frame
    real = real_demand_frame(conn)
    if real.empty:
        return df
    enough = [lot for lot, g in real.groupby("lot_id") if g["fill_rate"].notna().sum() >= MIN_REAL_POINTS]
    if not enough:
        return df
    return pd.concat([df[~df["lot_id"].isin(enough)], real[real["lot_id"].isin(enough)]], ignore_index=True)


def real_lots(df: pd.DataFrame) -> list:
    """Lots whose rows in `df` are real recorded occupancy."""
    if "data_source" not in df.columns:
        return []
    return sorted(df.loc[df["data_source"] == "real", "lot_id"].unique())


def _load_synthetic() -> pd.DataFrame:
    """Load the synthetic demand CSV; (re)generate if missing or stale."""
    _code_mtime = Path(__file__).stat().st_mtime
    if DATA_PATH.exists() and DATA_PATH.stat().st_mtime >= _code_mtime:
        df = pd.read_csv(DATA_PATH)
        if "datetime" in df.columns and "timestamp" not in df.columns:
            df = df.rename(columns={"datetime": "timestamp"})
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
        # Compute fill_rate from occupied_spaces / total_capacity if not present
        if "fill_rate" not in df.columns:
            if "occupied_spaces" in df.columns and "total_capacity" in df.columns:
                df["fill_rate"] = (df["occupied_spaces"] / df["total_capacity"].replace(0, np.nan)).clip(0, 1)
            elif "occupied" in df.columns and "capacity" in df.columns:
                df["fill_rate"] = (df["occupied"] / df["capacity"].replace(0, np.nan)).clip(0, 1)
        # Rename occupied_spaces → occupied for compatibility
        if "occupied_spaces" in df.columns and "occupied" not in df.columns:
            df["occupied"] = df["occupied_spaces"]
        # Extract time features if not present
        if "hour" not in df.columns and "timestamp" in df.columns:
            df["hour"] = df["timestamp"].dt.hour
            df["minute"] = df["timestamp"].dt.minute
            df["day_of_week"] = df["timestamp"].dt.dayofweek
            df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        # If lot_id column doesn't exist but there's a single-lot dataset, add it
        if "lot_id" not in df.columns:
            df["lot_id"] = LOT_IDS[0]
        return df
    # Generate and cache synthetic data
    df = _generate_synthetic_data()
    try:
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
    except Exception:
        pass
    return df


def _lot_fill(lot_id: str, hour: float, dow: int, rng) -> float:
    """
    Realistic VIT-AP-calibrated fill rate for each lot.
    hour: fractional hour (e.g. 8.25 = 08:15)
    dow: 0=Mon … 6=Sun
    Returns fill_rate in [0, 1].
    """
    is_weekend = dow >= 5
    # Friday is lighter than Mon-Thu; Mon has a slight rush
    weekday_scale = {0: 1.05, 1: 1.0, 2: 1.0, 3: 0.98, 4: 0.88}.get(dow, 0.5 if is_weekend else 1.0)

    def bell(h, peak, width, height):
        return height * np.exp(-0.5 * ((h - peak) / width) ** 2)

    if lot_id == "vitap-lot-academic-main":
        # Sharp morning rush 8-10am, secondary 2-4pm, dead by 7pm
        if is_weekend:
            base = bell(hour, 10, 1.5, 0.25) + 0.05
        else:
            base = (bell(hour, 9.0, 0.9, 0.82) + bell(hour, 14.5, 1.2, 0.60)
                    + bell(hour, 11.5, 0.8, 0.20) + 0.04)
        noise_sd = 0.04

    elif lot_id == "vitap-lot-hostel":
        # Always moderately full (residents park overnight); dips when everyone goes to class
        if is_weekend:
            base = 0.55 + bell(hour, 11, 2.0, 0.20) + bell(hour, 16, 2.5, 0.15)
        else:
            base = (0.45
                    - bell(hour, 9.5, 1.5, 0.20)   # students leave for class
                    + bell(hour, 13.0, 1.0, 0.15)  # lunch return
                    + bell(hour, 18.5, 1.5, 0.30)  # evening return
                    + bell(hour, 22.0, 2.0, 0.10))
        noise_sd = 0.05

    elif lot_id == "vitap-lot-admin-visitor":
        # 9-to-5 office pattern, closed weekends
        if is_weekend:
            base = 0.05 + bell(hour, 11, 2, 0.12)
        else:
            base = (bell(hour, 10.0, 1.5, 0.65) + bell(hour, 15.0, 1.5, 0.45)
                    + 0.05 * (8 <= hour <= 17))
        noise_sd = 0.04

    elif lot_id == "vitap-lot-sports":
        # Peaks on evenings and weekends (games, practice)
        if is_weekend:
            base = bell(hour, 10, 2, 0.60) + bell(hour, 16, 2, 0.70) + 0.08
        else:
            base = bell(hour, 17.5, 1.5, 0.65) + bell(hour, 12.5, 1.0, 0.20) + 0.05
        noise_sd = 0.06

    elif lot_id == "vitap-lot-overflow":
        # Spills over from academic during peak — correlated but delayed
        if is_weekend:
            base = 0.03 + bell(hour, 11, 2, 0.08)
        else:
            base = (bell(hour, 9.5, 1.0, 0.35) + bell(hour, 15.0, 1.5, 0.22)
                    + 0.02)
        noise_sd = 0.03

    else:
        base = 0.3
        noise_sd = 0.05

    fill = float(np.clip(base * weekday_scale + rng.normal(0, noise_sd), 0.0, 1.0))
    return fill


def _generate_synthetic_data() -> pd.DataFrame:
    """
    Generate 90 days of realistic VIT-AP-calibrated occupancy data.
    Each lot has a distinct daily shape, lot-specific peaks, and day-of-week variation
    so the prediction model learns real structure (not just a flat average).
    """
    rng = np.random.default_rng(42)
    # 90 days gives enough train/val/test split depth for the XGBoost model
    dates = pd.date_range("2024-07-01", periods=90 * 24 * 4, freq="15min")
    records = []
    for ts in dates:
        dow = ts.dayofweek
        hour_frac = ts.hour + ts.minute / 60.0
        is_weekend = dow >= 5
        for lot_id in LOT_IDS:
            cap = LOT_CAPACITIES[lot_id]
            fill = _lot_fill(lot_id, hour_frac, dow, rng)
            records.append({
                "timestamp": ts,
                "lot_id": lot_id,
                "occupied": int(fill * cap),
                "capacity": cap,
                "fill_rate": round(fill, 4),
                "day_of_week": dow,
                "hour": ts.hour,
                "minute": ts.minute,
                "is_weekend": int(is_weekend),
            })
    return pd.DataFrame(records)


def build_features(df: pd.DataFrame, lot_id: str, horizon_steps: int = 1) -> tuple:
    """
    Build (X, y) feature/target arrays for a given lot.

    horizon_steps: number of 15-min steps ahead to predict.
    Returns (X, y, timestamps).
    """
    lot_df = df[df["lot_id"] == lot_id].copy() if "lot_id" in df.columns else df.copy()
    lot_df = lot_df.sort_values("timestamp").reset_index(drop=True)

    if "fill_rate" not in lot_df.columns:
        cap = LOT_CAPACITIES.get(lot_id, 100)
        lot_df["fill_rate"] = lot_df.get("occupied", 0) / cap

    # Lag features
    for lag in [1, 2, 4, 8, 96]:  # 15m, 30m, 1h, 2h, 24h
        col = f"fill_lag_{lag}"
        lot_df[col] = lot_df["fill_rate"].shift(lag)

    # Rolling statistics
    lot_df["fill_roll_mean_4"] = lot_df["fill_rate"].shift(1).rolling(4).mean()
    lot_df["fill_roll_std_4"]  = lot_df["fill_rate"].shift(1).rolling(4).std().fillna(0)
    lot_df["fill_roll_mean_96"] = lot_df["fill_rate"].shift(1).rolling(96).mean()

    # Time features
    if "hour" not in lot_df.columns:
        lot_df["hour"] = lot_df["timestamp"].dt.hour
    if "minute" not in lot_df.columns:
        lot_df["minute"] = lot_df["timestamp"].dt.minute
    if "day_of_week" not in lot_df.columns:
        lot_df["day_of_week"] = lot_df["timestamp"].dt.dayofweek
    if "is_weekend" not in lot_df.columns:
        lot_df["is_weekend"] = (lot_df["day_of_week"] >= 5).astype(int)

    # Cyclical time encoding
    lot_df["hour_sin"] = np.sin(2 * np.pi * lot_df["hour"] / 24)
    lot_df["hour_cos"] = np.cos(2 * np.pi * lot_df["hour"] / 24)
    lot_df["dow_sin"]  = np.sin(2 * np.pi * lot_df["day_of_week"] / 7)
    lot_df["dow_cos"]  = np.cos(2 * np.pi * lot_df["day_of_week"] / 7)

    # Target: fill_rate at horizon steps ahead
    lot_df["target"] = lot_df["fill_rate"].shift(-horizon_steps)

    feature_cols = [
        "fill_lag_1", "fill_lag_2", "fill_lag_4", "fill_lag_8", "fill_lag_96",
        "fill_roll_mean_4", "fill_roll_std_4", "fill_roll_mean_96",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend",
        "hour", "minute", "day_of_week",
    ]

    lot_df = lot_df.dropna(subset=feature_cols + ["target"])
    X = lot_df[feature_cols].values
    y = lot_df["target"].values
    ts = lot_df["timestamp"].values

    return X, y, ts
