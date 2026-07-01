"""
Hub Delivery Finance — Variance Bridge Analysis

Loads the synthetic weekly dataset into SQLite, runs the volume/rate bridge
decomposition, flags underperforming hubs, and generates a WBR-style chart
+ narrative summary — mirroring the "actuals vs. plan, bridge variance,
build action plans" workflow described in the job posting.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = "/home/claude/hub-delivery-variance"
conn = sqlite3.connect(":memory:")

# --- Load CSVs into SQLite using the schema -------------------------------
weekly = pd.read_csv(f"{BASE}/data/hub_delivery_weekly.csv", parse_dates=["week_start"])
roster = pd.read_csv(f"{BASE}/data/hub_roster.csv")

weekly.to_sql("hub_delivery_weekly", conn, index=False, if_exists="replace")
roster.to_sql("hub_roster", conn, index=False, if_exists="replace")

# --- Query 1: network plan vs actual ---------------------------------------
q_network = """
SELECT week_num, week_start,
       SUM(plan_cost) AS plan_cost,
       SUM(actual_cost) AS actual_cost
FROM hub_delivery_weekly
GROUP BY week_num, week_start
ORDER BY week_num
"""
network = pd.read_sql(q_network, conn, parse_dates=["week_start"])
network["variance"] = network["actual_cost"] - network["plan_cost"]

# --- Query 2: volume/rate bridge -------------------------------------------
q_bridge = """
SELECT week_num, week_start,
    SUM((actual_packages - plan_packages) * plan_rate_per_pkg) AS volume_effect,
    SUM((actual_rate_per_pkg - plan_rate_per_pkg) * plan_packages) AS rate_effect,
    SUM((actual_packages - plan_packages) * (actual_rate_per_pkg - plan_rate_per_pkg)) AS interaction_effect
FROM hub_delivery_weekly
GROUP BY week_num, week_start
ORDER BY week_num
"""
bridge = pd.read_sql(q_bridge, conn, parse_dates=["week_start"])

# --- Query 3: worst variance hubs, last 4 weeks -----------------------------
q_worst = """
SELECT hub_id, region,
       SUM(actual_cost) - SUM(plan_cost) AS cost_variance,
       SUM(actual_packages) - SUM(plan_packages) AS volume_variance,
       ROUND(AVG(actual_rate_per_pkg - plan_rate_per_pkg), 4) AS avg_rate_variance
FROM hub_delivery_weekly
WHERE week_num > (SELECT MAX(week_num) FROM hub_delivery_weekly) - 4
GROUP BY hub_id, region
ORDER BY cost_variance DESC
LIMIT 5
"""
worst_hubs = pd.read_sql(q_worst, conn)

# =============================================================================
# CHART 1: Plan vs Actual cost trend (WBR-style)
# =============================================================================
fig, axes = plt.subplots(2, 1, figsize=(11, 9), height_ratios=[1, 1])

ax1 = axes[0]
ax1.plot(network["week_num"], network["plan_cost"], label="Plan", color="#232F3E", linewidth=2)
ax1.plot(network["week_num"], network["actual_cost"], label="Actual", color="#FF9900", linewidth=2)
ax1.fill_between(network["week_num"], network["plan_cost"], network["actual_cost"],
                  where=(network["actual_cost"] >= network["plan_cost"]),
                  color="#D13212", alpha=0.15, label="Unfavorable")
ax1.fill_between(network["week_num"], network["plan_cost"], network["actual_cost"],
                  where=(network["actual_cost"] < network["plan_cost"]),
                  color="#1D8102", alpha=0.15, label="Favorable")
ax1.set_title("Hub Delivery Network — Weekly Cost: Plan vs. Actual", fontsize=13, fontweight="bold")
ax1.set_xlabel("Week")
ax1.set_ylabel("Weekly Delivery Cost ($)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax1.legend(loc="upper left", fontsize=9)
ax1.grid(alpha=0.3)

# =============================================================================
# CHART 2: Cumulative variance bridge (Volume vs Rate vs Interaction)
# =============================================================================
ax2 = axes[1]
cum_vol = bridge["volume_effect"].sum()
cum_rate = bridge["rate_effect"].sum()
cum_inter = bridge["interaction_effect"].sum()
cum_total = cum_vol + cum_rate + cum_inter

labels = ["Plan Cost", "Volume\nEffect", "Rate\nEffect", "Interaction\nEffect", "Actual Cost"]
plan_total = network["plan_cost"].sum()
values = [plan_total, cum_vol, cum_rate, cum_inter, plan_total + cum_total]

# waterfall positions
bottoms = [0, plan_total, plan_total + cum_vol, plan_total + cum_vol + cum_rate, 0]
bar_vals = [plan_total, cum_vol, cum_rate, cum_inter, plan_total + cum_total]
colors = ["#232F3E",
          "#D13212" if cum_vol > 0 else "#1D8102",
          "#D13212" if cum_rate > 0 else "#1D8102",
          "#D13212" if cum_inter > 0 else "#1D8102",
          "#FF9900"]

for i, (label, bottom, val, color) in enumerate(zip(labels, bottoms, bar_vals, colors)):
    if i in (0, 4):
        ax2.bar(i, val, color=color, width=0.6)
    else:
        ax2.bar(i, val, bottom=bottom, color=color, width=0.6)
    y_text = (bottom + val) if i not in (0, 4) else val
    ax2.text(i, y_text + plan_total * 0.01, f"${val:,.0f}", ha="center", fontsize=9, fontweight="bold")

ax2.set_xticks(range(5))
ax2.set_xticklabels(labels)
ax2.set_title("H1 Cumulative Cost Bridge: Plan → Actual (Volume vs. Rate Drivers)",
              fontsize=13, fontweight="bold")
ax2.set_ylabel("Cumulative Cost ($)")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax2.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(f"{BASE}/output/variance_bridge.png", dpi=150, bbox_inches="tight")
print("Saved chart to output/variance_bridge.png")

# =============================================================================
# WRITTEN SUMMARY (mirrors WBR narrative / action-plan format)
# =============================================================================
pct_var = 100 * cum_total / plan_total
direction = "unfavorable (over plan)" if cum_total > 0 else "favorable (under plan)"

summary = f"""
HUB DELIVERY — H1 VARIANCE BRIDGE SUMMARY
==========================================
Plan cost (26 wks):    ${plan_total:,.0f}
Actual cost (26 wks):  ${plan_total + cum_total:,.0f}
Total variance:        ${cum_total:,.0f}  ({pct_var:+.1f}%, {direction})

Decomposition:
  Volume effect:       ${cum_vol:,.0f}   ({'higher' if cum_vol>0 else 'lower'} volume than planned)
  Rate effect:         ${cum_rate:,.0f}   ({'higher' if cum_rate>0 else 'lower'} per-package rate than planned)
  Interaction effect:  ${cum_inter:,.0f}

Top 5 hubs driving unfavorable variance (last 4 weeks):
"""
for _, row in worst_hubs.iterrows():
    summary += (f"  {row['hub_id']} ({row['region']}): "
                f"${row['cost_variance']:,.0f} cost variance, "
                f"rate variance ${row['avg_rate_variance']:+.3f}/pkg\n")

summary += """
Recommended action plan:
  1. If rate effect dominates -> escalate to Ops for per-hub rate card review,
     particularly in regions with the steepest rate drift (see regional trend query).
  2. If volume effect dominates and favorable -> validate hub capacity can sustain
     demand without service degradation; consider raising plan targets next cycle.
  3. Deep-dive top 5 variance hubs individually; determine if driven by local labor
     market, onboarding ramp delays, or one-off operational disruption.
"""

print(summary)
with open(f"{BASE}/output/wbr_summary.txt", "w") as f:
    f.write(summary)
print("Saved summary to output/wbr_summary.txt")
