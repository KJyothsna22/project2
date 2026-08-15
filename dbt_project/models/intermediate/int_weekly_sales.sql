-- Intermediate model: int_weekly_sales
-- Aggregates sales at weekly store-item grain

WITH daily AS (
    SELECT * FROM int_daily_sales
)

SELECT
    store_id,
    item_id,
    dept_id,
    cat_id,
    wm_yr_wk,
    year,
    SUM(sales_units) AS weekly_sales_units,
    ROUND(SUM(daily_revenue), 2) AS weekly_revenue,
    ROUND(AVG(sell_price), 2) AS avg_weekly_price,
    MAX(is_holiday) AS had_holiday,
    MAX(is_snap_day) AS had_snap_day
FROM daily
GROUP BY
    store_id,
    item_id,
    dept_id,
    cat_id,
    wm_yr_wk,
    year
