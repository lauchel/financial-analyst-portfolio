-- ============================================================
-- Acme Co. — SQL Portfolio Queries | FY 2024
-- Author: Financial Analyst Work Sample
-- Database: Acme Co. Financial Database
-- Description: 6 analyst-level queries covering revenue
--              trending, expense analysis, AR aging,
--              and variance reporting.
-- ============================================================


-- ============================================================
-- TABLE SCHEMAS (for reference)
-- ============================================================

-- monthly_revenue  (month_num INT, month TEXT, revenue INT)
-- expenses         (month_num INT, expense_category TEXT, amount INT)
-- monthly_expenses (month_num INT, total_exp INT)
-- ar_invoices      (customer TEXT, invoice_no TEXT, amount INT, days_overdue INT)
-- quarterly_forecast (quarter TEXT, actual_revenue INT, forecast_revenue INT)


-- ============================================================
-- QUERY 1: Monthly Revenue Trend with MoM Growth
-- Purpose : Track revenue momentum month-over-month
-- Concepts: Window function (LAG), calculated field, ORDER BY
-- ============================================================

SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month_num)              AS prev_month_revenue,
    revenue - LAG(revenue) OVER (ORDER BY month_num)    AS mom_change,
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month_num))
        * 100.0 / LAG(revenue) OVER (ORDER BY month_num)
    , 1)                                                AS mom_growth_pct
FROM monthly_revenue
ORDER BY month_num;

-- Insight: Revenue grew 77% Jan–Dec. H2 outpaced H1 by 34%.
-- Feb dip is a recurring seasonal pattern worth flagging to leadership.


-- ============================================================
-- QUERY 2: Full-Year Expense Breakdown by Category
-- Purpose : Identify largest cost drivers
-- Concepts: GROUP BY, SUM, window function for % of total
-- ============================================================

SELECT
    expense_category,
    SUM(amount)                                         AS total_amount,
    ROUND(
        SUM(amount) * 100.0
        / SUM(SUM(amount)) OVER ()
    , 1)                                                AS pct_of_total
FROM expenses
GROUP BY expense_category
ORDER BY total_amount DESC;

-- Insight: Payroll (38%) + COGS (32%) = 70% of all expenses.
-- Marketing ROI is strong — only ~11% spend drove 77% revenue growth.


-- ============================================================
-- QUERY 3: Net Profit Margin by Month
-- Purpose : Monitor profitability health across the year
-- Concepts: JOIN, calculated fields, aliasing
-- ============================================================

SELECT
    r.month,
    r.revenue,
    e.total_exp                                         AS total_expenses,
    r.revenue - e.total_exp                             AS net_profit,
    ROUND(
        (r.revenue - e.total_exp) * 100.0 / r.revenue
    , 1)                                                AS net_margin_pct
FROM monthly_revenue r
JOIN monthly_expenses e
    ON r.month_num = e.month_num
ORDER BY r.month_num;

-- Insight: Margins stable at 26–38%. No margin compression despite
-- scaling — expenses growing proportionally is a controllership positive.


-- ============================================================
-- QUERY 4: AR Aging Bucket Analysis
-- Purpose : Categorize outstanding invoices by overdue period
-- Concepts: CASE WHEN, GROUP BY, aggregation
-- ============================================================

SELECT
    CASE
        WHEN days_overdue <= 0  THEN 'Current'
        WHEN days_overdue <= 30 THEN '1-30 Days'
        WHEN days_overdue <= 60 THEN '31-60 Days'
        WHEN days_overdue <= 90 THEN '61-90 Days'
        ELSE                         '90+ Days'
    END                                                 AS aging_bucket,
    COUNT(*)                                            AS invoice_count,
    SUM(amount)                                         AS total_amount,
    ROUND(SUM(amount) * 100.0 / SUM(SUM(amount)) OVER (), 1)
                                                        AS pct_of_total_ar
FROM ar_invoices
GROUP BY aging_bucket
ORDER BY MIN(days_overdue);

-- Insight: $100k+ is 60+ days overdue. Immediate escalation recommended
-- for 90+ day bucket — represents significant cash flow risk.


-- ============================================================
-- QUERY 5: High-Risk Customers with Overdue AR > $10,000
-- Purpose : Prioritize collections outreach by dollar exposure
-- Concepts: WHERE, GROUP BY, HAVING, ORDER BY
-- ============================================================

SELECT
    customer,
    COUNT(*)                                            AS open_invoices,
    SUM(amount)                                         AS total_owed,
    MAX(days_overdue)                                   AS max_days_overdue,
    CASE
        WHEN MAX(days_overdue) > 90 THEN 'Critical'
        WHEN MAX(days_overdue) > 60 THEN 'High'
        WHEN MAX(days_overdue) > 30 THEN 'Medium'
        ELSE                              'Low'
    END                                                 AS risk_level
FROM ar_invoices
WHERE days_overdue > 0
GROUP BY customer
HAVING SUM(amount) > 10000
ORDER BY total_owed DESC;

-- Insight: Ironclad Manufacturing ($57.5k, 183 days) and Delta Systems
-- ($45.5k, 108 days) are critical — refer to collections immediately.


-- ============================================================
-- QUERY 6: Quarterly Actual vs. Forecast Variance
-- Purpose : Measure forecast accuracy and explain variances
-- Concepts: Calculated fields, variance analysis, aliasing
-- ============================================================

SELECT
    quarter,
    actual_revenue,
    forecast_revenue,
    actual_revenue - forecast_revenue                   AS variance_abs,
    ROUND(
        (actual_revenue - forecast_revenue) * 100.0
        / forecast_revenue
    , 1)                                                AS variance_pct,
    CASE
        WHEN actual_revenue >= forecast_revenue THEN 'Beat'
        ELSE                                         'Missed'
    END                                                 AS vs_forecast
FROM quarterly_forecast
ORDER BY quarter;

-- Insight: Q1 missed by $8k (seasonal weakness). Q2-Q4 all beat forecast.
-- Q3 had the strongest positive surprise (+$12k). Full-year beat by $26k.


-- ============================================================
-- BONUS: Cumulative Revenue (Running Total)
-- Purpose : Show year-to-date revenue at any point in the year
-- Concepts: Window function (SUM OVER), running total
-- ============================================================

SELECT
    month,
    revenue                                             AS monthly_revenue,
    SUM(revenue) OVER (
        ORDER BY month_num
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                                   AS ytd_revenue
FROM monthly_revenue
ORDER BY month_num;

-- ============================================================
-- END OF PORTFOLIO QUERIES
-- ============================================================
