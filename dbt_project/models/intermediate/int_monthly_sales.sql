-- Intermediate model: int_monthly_sales
-- Aggregates sales at monthly grain for high-level business trend analysis

WITH daily AS (
    SELECT * FROM int_daily_sales
)

SELECT
    store_id,
    cat_id,
    dept_id,
    year,
    month,
    SUM(sales_units) AS monthly_sales_units,
    ROUND(SUM(daily_revenue), 2) AS monthly_revenue,
    COUNT(DISTINCT item_id) AS active_products_count,
    ROUND(AVG(daily_revenue), 2) AS avg_daily_revenue
FROM daily
GROUP BY
    store_id,
    cat_id,
    dept_id,
    year,
    month
