# Hub Delivery Finance — Variance Bridge Analysis

A finance analytics project modeled on Amazon's **Hub Delivery** program (last-mile delivery via small-business partners), built to demonstrate the core workflow of a Hub Delivery Finance analyst: **track actuals vs. plan, decompose the variance, and produce action plans.**

> **Data disclosure:** Amazon does not publish Hub Delivery financials. All data here is **synthetic**, generated to be realistic based on public information (the >100% YoY network growth cited in Amazon's own job postings, typical last-mile per-package economics, and standard FP&A plan structures). See `data/generate_data.py` for every assumption used. This is a modeling exercise, not real Amazon data.

## What this project does

1. **Generates a synthetic network** of 40 hub partners across 5 regions, 26 weeks of plan vs. actual data (packages, rate per package, cost), including hub onboarding ramps and churn.
2. **Loads it into SQL** (`sql/schema.sql`) and runs finance queries (`sql/variance_queries.sql`) covering plan-vs-actual, regional rate trends, worst-variance hubs, and new-hub ramp performance.
3. **Runs a volume/rate bridge decomposition** in Python — the standard FP&A technique for explaining *why* actual cost diverged from plan:

   ```
   Total Variance = Volume Effect + Rate Effect + Interaction Effect
   Volume Effect = (Actual Volume − Plan Volume) × Plan Rate
   Rate Effect   = (Actual Rate − Plan Rate) × Plan Volume
   ```
4. **Outputs a WBR-style chart and written summary** with a recommended action plan — mirroring the weekly business review cadence described in the role.

## Project structure

```
hub-delivery-variance/
├── data/
│   ├── generate_data.py       # synthetic data generator (documented assumptions)
│   ├── hub_delivery_weekly.csv
│   └── hub_roster.csv
├── sql/
│   ├── schema.sql              # table definitions
│   └── variance_queries.sql    # 6 finance queries (plan/actual, bridge, ramp, churn, regional)
├── analysis/
│   └── bridge_analysis.py      # loads SQL, runs bridge calc, generates chart + summary
└── output/
    ├── variance_bridge.png     # plan vs actual trend + waterfall bridge chart
    └── wbr_summary.txt         # narrative variance summary + action plan
```

## Key finding (from this run)

Actual H1 cost came in **13.8% under plan**, driven almost entirely by a **volume shortfall** (fewer packages routed through hubs than planned), partially offset by **higher per-package rates** — a classic sign of tightening driver/labor market conditions even as demand ran below forecast. Five hubs, concentrated in the Southwest and Midwest, account for a disproportionate share of the unfavorable rate variance and are flagged for individual deep-dive.

![Variance Bridge](output/variance_bridge.png)

## How to run

```bash
pip install pandas numpy matplotlib
python data/generate_data.py        # regenerate the dataset
python analysis/bridge_analysis.py  # run the analysis, produce chart + summary
```

SQL queries can be run against any SQLite/Postgres instance loaded from the schema, or directly via `sqlite3` using the CSVs.

## Why this project

Built to reflect the core responsibilities in Amazon's Senior Finance Analyst, Hub Delivery Finance posting: weekly plan-vs-actual tracking, variance bridging, cross-functional action planning, and SQL-based data analysis.
