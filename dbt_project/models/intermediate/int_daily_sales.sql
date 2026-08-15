-- Intermediate model: int_daily_sales
-- Joins daily sales with calendar attributes and pricing to compute daily revenue

WITH sales AS (
    SELECT * FROM stg_sales
),

cal AS (
    SELECT * FROM stg_calendar
),

prices AS (
    SELECT * FROM stg_prices
)

SELECT
    s.id,
    s.item_id,
    s.dept_id,
    s.cat_id,
    s.store_id,
    s.state_id,
    s.date_str,
    c.wm_yr_wk,
    c.weekday,
    c.wday,
    c.month,
    c.year,
    c.event_name_1,
    c.event_type_1,
    c.is_holiday,
    c.is_weekend,
    CASE
        WHEN s.state_id = 'CA' THEN c.snap_CA
        WHEN s.state_id = 'TX' THEN c.snap_TX
        WHEN s.state_id = 'WI' THEN c.snap_WI
        ELSE 0
    END AS is_snap_day,
    s.sales_units,
    COALESCE(p.sell_price, 5.00) AS sell_price,
    ROUND(s.sales_units * COALESCE(p.sell_price, 5.00), 2) AS daily_revenue
FROM sales s
INNER JOIN cal c ON s.date_str = c.date_str
LEFT JOIN prices p ON s.store_id = p.store_id
                   AND s.item_id = p.item_id
                   AND c.wm_yr_wk = p.wm_yr_wk
