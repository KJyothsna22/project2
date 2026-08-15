-- Data Mart: mart_product_performance
-- Granular product performance metrics, revenue contribution, and sales velocity

WITH daily AS (
    SELECT * FROM int_daily_sales
)

SELECT
    item_id,
    cat_id,
    dept_id,
    COUNT(DISTINCT store_id) AS stores_count,
    SUM(sales_units) AS total_units_sold,
    ROUND(SUM(daily_revenue), 2) AS total_revenue,
    ROUND(AVG(sales_units), 2) AS avg_daily_units,
    ROUND(AVG(sell_price), 2) AS avg_selling_price,
    ROUND(MAX(sales_units), 2) AS max_single_day_units,
    ROUND(MIN(sales_units), 2) AS min_single_day_units
FROM daily
GROUP BY
    item_id,
    cat_id,
    dept_id
