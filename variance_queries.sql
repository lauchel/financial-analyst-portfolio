-- ============================================================
-- Hub Delivery Finance — Variance & Bridge Analysis Queries
-- ============================================================

-- 1. Network-level plan vs. actual cost, by week
SELECT
    week_num,
    week_start,
    SUM(plan_cost)   AS plan_cost,
    SUM(actual_cost) AS actual_cost,
    SUM(actual_cost) - SUM(plan_cost) AS cost_variance,
    ROUND(100.0 * (SUM(actual_cost) - SUM(plan_cost)) / SUM(plan_cost), 2) AS variance_pct
FROM hub_delivery_weekly
GROUP BY week_num, week_start
ORDER BY week_num;

-- 2. Volume vs. Rate bridge (classic FP&A decomposition)
-- Variance = Volume Effect + Rate Effect + Volume*Rate Interaction
--   Volume Effect = (Actual Vol - Plan Vol) * Plan Rate
--   Rate Effect   = (Actual Rate - Plan Rate) * Plan Vol
--   Interaction   = (Actual Vol - Plan Vol) * (Actual Rate - Plan Rate)
SELECT
    week_num,
    week_start,
    SUM((actual_packages - plan_packages) * plan_rate_per_pkg)                         AS volume_effect,
    SUM((actual_rate_per_pkg - plan_rate_per_pkg) * plan_packages)                      AS rate_effect,
    SUM((actual_packages - plan_packages) * (actual_rate_per_pkg - plan_rate_per_pkg))  AS interaction_effect,
    SUM(actual_cost) - SUM(plan_cost)                                                    AS total_variance
FROM hub_delivery_weekly
GROUP BY week_num, week_start
ORDER BY week_num;

-- 3. Worst variance hubs (last 4 weeks) — candidates for action plans
SELECT
    hub_id,
    region,
    SUM(actual_cost) - SUM(plan_cost) AS cost_variance,
    SUM(actual_packages) - SUM(plan_packages) AS volume_variance,
    ROUND(AVG(actual_rate_per_pkg - plan_rate_per_pkg), 4) AS avg_rate_variance
FROM hub_delivery_weekly
WHERE week_num > (SELECT MAX(week_num) FROM hub_delivery_weekly) - 4
GROUP BY hub_id, region
ORDER BY cost_variance DESC
LIMIT 10;

-- 4. Churned hubs (went inactive) — revenue/cost impact
SELECT
    hub_id,
    region,
    MAX(week_num) AS last_active_week,
    SUM(plan_cost) AS lost_plan_cost_opportunity
FROM hub_delivery_weekly
WHERE active_flag = 0
GROUP BY hub_id, region;

-- 5. Regional rate trend — is driver/labor cost inflation regional or network-wide?
SELECT
    region,
    week_num,
    ROUND(AVG(actual_rate_per_pkg), 4) AS avg_actual_rate,
    ROUND(AVG(plan_rate_per_pkg), 4)   AS avg_plan_rate
FROM hub_delivery_weekly
GROUP BY region, week_num
ORDER BY region, week_num;

-- 6. New hub ramp performance (onboarded mid-period) vs. plan
SELECT
    w.hub_id,
    r.onboard_week,
    w.week_num,
    w.week_num - r.onboard_week AS weeks_since_onboard,
    w.actual_packages,
    w.plan_packages,
    ROUND(100.0 * w.actual_packages / NULLIF(w.plan_packages, 0), 1) AS pct_of_plan
FROM hub_delivery_weekly w
JOIN hub_roster r ON w.hub_id = r.hub_id
WHERE r.onboard_week > 0
ORDER BY w.hub_id, w.week_num;
