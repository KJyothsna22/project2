-- Data Mart: mart_store_performance
-- Store-level revenue, category mix, and geographic velocity

WITH daily AS (
    SELECT * FROM int_daily_sales
),

stores AS (
    SELECT * FROM dim_stores
)

SELECT
    d.store_id,
    s.state_id,
    s.store_name,
    s.region,
    COUNT(DISTINCT d.item_id) AS total_skus_stocked,
    SUM(d.sales_units) AS total_units_sold,
    ROUND(SUM(d.daily_revenue), 2) AS total_gross_revenue,
    ROUND(AVG(d.daily_revenue), 2) AS avg_store_daily_revenue,
    ROUND(SUM(CASE WHEN d.cat_id = 'FOODS' THEN d.daily_revenue ELSE 0 END), 2) AS foods_revenue,
    ROUND(SUM(CASE WHEN d.cat_id = 'HOBBIES' THEN d.daily_revenue ELSE 0 END), 2) AS hobbies_revenue,
    ROUND(SUM(CASE WHEN d.cat_id = 'HOUSEHOLD' THEN d.daily_revenue ELSE 0 END), 2) AS household_revenue
FROM daily d
LEFT JOIN stores s ON d.store_id = s.store_id
GROUP BY
    d.store_id,
    s.state_id,
    s.store_name,
    s.region
