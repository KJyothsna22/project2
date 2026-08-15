-- Google BigQuery Enterprise Warehouse Schema
-- Retail Demand Forecasting & Inventory Optimization Platform

CREATE SCHEMA IF NOT EXISTS `retail_dw`;

CREATE TABLE IF NOT EXISTS `retail_dw.dim_stores` (
    store_id STRING,
    state_id STRING,
    store_name STRING,
    region STRING
);

CREATE TABLE IF NOT EXISTS `retail_dw.dim_categories` (
    cat_id STRING,
    category_name STRING
);

CREATE TABLE IF NOT EXISTS `retail_dw.dim_departments` (
    dept_id STRING,
    cat_id STRING,
    department_name STRING
);

CREATE TABLE IF NOT EXISTS `retail_dw.dim_products` (
    item_id STRING,
    dept_id STRING,
    cat_id STRING,
    product_name STRING,
    unit_cost NUMERIC
);

CREATE TABLE IF NOT EXISTS `retail_dw.dim_calendar` (
    date_str STRING,
    wm_yr_wk INT64,
    weekday STRING,
    wday INT64,
    month INT64,
    year INT64,
    d_id STRING,
    event_name_1 STRING,
    event_type_1 STRING,
    event_name_2 STRING,
    event_type_2 STRING,
    snap_CA INT64,
    snap_TX INT64,
    snap_WI INT64,
    is_holiday INT64
);

CREATE TABLE IF NOT EXISTS `retail_dw.fact_sales` (
    id STRING,
    item_id STRING,
    dept_id STRING,
    cat_id STRING,
    store_id STRING,
    state_id STRING,
    date_str STRING,
    sales_units INT64
)
PARTITION BY PARSE_DATE('%Y-%m-%d', date_str)
CLUSTER BY store_id, cat_id, item_id;

CREATE TABLE IF NOT EXISTS `retail_dw.fact_prices` (
    store_id STRING,
    item_id STRING,
    wm_yr_wk INT64,
    sell_price NUMERIC
)
CLUSTER BY store_id, item_id;

CREATE TABLE IF NOT EXISTS `retail_dw.fact_forecast_results` (
    forecast_date STRING,
    item_id STRING,
    store_id STRING,
    model_used STRING,
    actual_demand NUMERIC,
    forecast_demand NUMERIC,
    confidence_lower NUMERIC,
    confidence_upper NUMERIC,
    forecast_error NUMERIC,
    horizon_days INT64,
    created_at TIMESTAMP
)
PARTITION BY PARSE_DATE('%Y-%m-%d', forecast_date)
CLUSTER BY store_id, item_id, model_used;

CREATE TABLE IF NOT EXISTS `retail_dw.fact_inventory_recommendations` (
    evaluation_date STRING,
    item_id STRING,
    store_id STRING,
    current_inventory INT64,
    average_daily_demand NUMERIC,
    demand_std_dev NUMERIC,
    lead_time_days INT64,
    safety_stock INT64,
    reorder_point INT64,
    forecast_demand_lt NUMERIC,
    recommended_order_qty INT64,
    days_of_supply NUMERIC,
    inventory_status STRING,
    risk_level STRING,
    stockout_risk_pct NUMERIC,
    overstock_risk_pct NUMERIC,
    suggested_replenishment_date STRING,
    estimated_order_cost NUMERIC,
    created_at TIMESTAMP
)
PARTITION BY PARSE_DATE('%Y-%m-%d', evaluation_date)
CLUSTER BY store_id, item_id, risk_level;
