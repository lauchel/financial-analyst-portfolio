"""
Generates a synthetic dataset modeling Amazon Hub Delivery Finance operations.

IMPORTANT: This is NOT real Amazon data. Amazon does not publish Hub Delivery
financials. This dataset is constructed to be *realistic* based on:
  - Publicly stated >100% YoY network growth (per job posting)
  - Typical last-mile delivery economics (per-package cost, driver payouts)
  - Standard FP&A plan-vs-actual structures

Assumptions are documented inline. Random seed is fixed for reproducibility.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

np.random.seed(42)

# --- Config / assumptions -----------------------------------------------
N_HUBS = 40                     # number of small-business hub partners
WEEKS = 26                      # 2 quarters of weekly data
START_DATE = date(2025, 1, 6)   # first Monday
REGIONS = ["Northeast", "Southeast", "Midwest", "West", "Southwest"]

# Planned (budget) assumptions set at start of period
PLAN_RATE_PER_PKG = 2.85        # $ paid to hub per package, per plan
PLAN_VOL_GROWTH_WK = 0.028      # ~2.8%/week compounding -> ~2x over 26wks

# Actual-world noise / drift assumptions
RATE_DRIFT_STD = 0.06           # week-to-week rate variance (fuel, labor mkt)
VOL_NOISE_STD = 0.09            # demand variance vs plan
CHURN_PROB = 0.015              # weekly probability a hub goes inactive
RAMP_HUBS_PER_QTR = 6           # new hubs onboarded mid-period

# --- Build hub roster -----------------------------------------------------
hubs = pd.DataFrame({
    "hub_id": [f"H{100+i}" for i in range(N_HUBS)],
    "region": np.random.choice(REGIONS, N_HUBS, p=[0.22, 0.22, 0.2, 0.22, 0.14]),
    "onboard_week": [0] * (N_HUBS - RAMP_HUBS_PER_QTR) +
                     list(np.random.choice(range(10, 20), RAMP_HUBS_PER_QTR, replace=False)),
    "base_daily_capacity": np.random.randint(80, 260, N_HUBS),  # packages/day capacity
})

records = []
for _, hub in hubs.iterrows():
    active = True
    base_vol = hub["base_daily_capacity"] * 6.5  # ~weekly volume at steady state, 6.5 active days
    plan_vol = base_vol * 0.55  # plan starts hubs below full capacity, ramps up
    for wk in range(WEEKS):
        if wk < hub["onboard_week"]:
            continue  # hub not yet onboarded
        if active and np.random.rand() < CHURN_PROB and wk > hub["onboard_week"] + 4:
            active = False

        week_start = START_DATE + timedelta(weeks=wk)

        # --- PLAN ---
        plan_vol *= (1 + PLAN_VOL_GROWTH_WK)
        plan_rate = PLAN_RATE_PER_PKG
        plan_packages = plan_vol
        plan_cost = plan_packages * plan_rate

        if not active:
            actual_packages = 0
            actual_rate = plan_rate
        else:
            # --- ACTUAL ---
            vol_noise = np.random.normal(0, VOL_NOISE_STD)
            capacity_cap = hub["base_daily_capacity"] * 6.5 * 1.15
            actual_packages = min(plan_packages * (1 + vol_noise), capacity_cap)
            actual_packages = max(actual_packages, 0)

            rate_noise = np.random.normal(0, RATE_DRIFT_STD)
            # Rates trend up slightly over time (driver market tightening)
            rate_trend = 0.0009 * wk
            actual_rate = plan_rate * (1 + rate_noise + rate_trend)

        actual_cost = actual_packages * actual_rate

        records.append({
            "hub_id": hub["hub_id"],
            "region": hub["region"],
            "week_start": week_start,
            "week_num": wk + 1,
            "plan_packages": round(plan_packages, 1),
            "plan_rate_per_pkg": round(plan_rate, 4),
            "plan_cost": round(plan_cost, 2),
            "actual_packages": round(actual_packages, 1),
            "actual_rate_per_pkg": round(actual_rate, 4),
            "actual_cost": round(actual_cost, 2),
            "active_flag": active,
        })

df = pd.DataFrame(records)
df.to_csv("/home/claude/hub-delivery-variance/data/hub_delivery_weekly.csv", index=False)
hubs.to_csv("/home/claude/hub-delivery-variance/data/hub_roster.csv", index=False)

print(f"Rows: {len(df)}, Hubs: {df.hub_id.nunique()}, Weeks: {df.week_num.max()}")
print(df.head())
