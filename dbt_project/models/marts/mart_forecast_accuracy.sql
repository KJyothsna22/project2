-- Data Mart: mart_forecast_accuracy
-- Aggregates forecast error metrics by model and horizon

SELECT
    model_used,
    horizon_days,
    COUNT(*) AS total_forecast_points,
    ROUND(AVG(ABS(actual_demand - forecast_demand)), 3) AS mae,
    ROUND(SQRT(AVG((actual_demand - forecast_demand) * (actual_demand - forecast_demand))), 3) AS rmse,
    ROUND(AVG(ABS(actual_demand - forecast_demand) / NULLIF(actual_demand, 0)) * 100, 2) AS mape_pct
FROM fact_forecast_results
WHERE actual_demand IS NOT NULL
GROUP BY
    model_used,
    horizon_days
