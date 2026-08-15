-- Data Mart: mart_inventory_health
-- Aggregated inventory risks, stockout alerts, and replenishment requirements

SELECT
    store_id,
    COUNT(DISTINCT item_id) AS total_monitored_skus,
    SUM(current_inventory) AS total_inventory_units,
    ROUND(SUM(current_inventory * 5.0), 2) AS estimated_inventory_value,
    SUM(CASE WHEN risk_level = 'High Risk' THEN 1 ELSE 0 END) AS high_risk_sku_count,
    SUM(CASE WHEN risk_level = 'Medium Risk' THEN 1 ELSE 0 END) AS medium_risk_sku_count,
    SUM(CASE WHEN risk_level = 'Low Risk' THEN 1 ELSE 0 END) AS low_risk_sku_count,
    SUM(CASE WHEN inventory_status = 'Critical Stockout Risk' THEN 1 ELSE 0 END) AS stockout_alert_count,
    SUM(CASE WHEN inventory_status = 'Excess Overstock' THEN 1 ELSE 0 END) AS overstock_alert_count,
    SUM(recommended_order_qty) AS total_recommended_replenishment_units,
    ROUND(SUM(estimated_order_cost), 2) AS total_replenishment_cost
FROM fact_inventory_recommendations
GROUP BY
    store_id
