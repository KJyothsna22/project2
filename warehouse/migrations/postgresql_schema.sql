-- PostgreSQL Enterprise Warehouse Schema
-- Retail Demand Forecasting & Inventory Optimization Platform

CREATE SCHEMA IF NOT EXISTS retail_dw;
SET search_path TO retail_dw;

CREATE TABLE IF NOT EXISTS dim_stores (
    store_id VARCHAR(20) PRIMARY KEY,
    state_id VARCHAR(10) NOT NULL,
    store_name VARCHAR(100),
    region VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_categories (
    cat_id VARCHAR(30) PRIMARY KEY,
    category_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_departments (
    dept_id VARCHAR(30) PRIMARY KEY,
    cat_id VARCHAR(30) NOT NULL REFERENCES dim_categories(cat_id),
    department_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_products (
    item_id VARCHAR(50) PRIMARY KEY,
    dept_id VARCHAR(30) NOT NULL REFERENCES dim_departments(dept_id),
    cat_id VARCHAR(30) NOT NULL REFERENCES dim_categories(cat_id),
    product_name VARCHAR(150),
    unit_cost NUMERIC(10, 2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS dim_calendar (
    date_str VARCHAR(10) PRIMARY KEY,
    wm_yr_wk INT NOT NULL,
    weekday VARCHAR(15) NOT NULL,
    wday INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    d_id VARCHAR(10) NOT NULL,
    event_name_1 VARCHAR(50),
    event_type_1 VARCHAR(50),
    event_name_2 VARCHAR(50),
    event_type_2 VARCHAR(50),
    snap_CA INT DEFAULT 0,
    snap_TX INT DEFAULT 0,
    snap_WI INT DEFAULT 0,
    is_holiday INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fact_sales (
    id VARCHAR(80),
    item_id VARCHAR(50) NOT NULL REFERENCES dim_products(item_id),
    dept_id VARCHAR(30),
    cat_id VARCHAR(30),
    store_id VARCHAR(20) NOT NULL REFERENCES dim_stores(store_id),
    state_id VARCHAR(10),
    date_str VARCHAR(10) NOT NULL REFERENCES dim_calendar(date_str),
    sales_units INT NOT NULL,
    PRIMARY KEY (item_id, store_id, date_str)
);

CREATE TABLE IF NOT EXISTS fact_prices (
    store_id VARCHAR(20) NOT NULL REFERENCES dim_stores(store_id),
    item_id VARCHAR(50) NOT NULL REFERENCES dim_products(item_id),
    wm_yr_wk INT NOT NULL,
    sell_price NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (store_id, item_id, wm_yr_wk)
);

CREATE TABLE IF NOT EXISTS fact_forecast_results (
    id SERIAL PRIMARY KEY,
    forecast_date VARCHAR(10) NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    store_id VARCHAR(20) NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    actual_demand NUMERIC(10, 2),
    forecast_demand NUMERIC(10, 2) NOT NULL,
    confidence_lower NUMERIC(10, 2),
    confidence_upper NUMERIC(10, 2),
    forecast_error NUMERIC(10, 2),
    horizon_days INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_inventory_recommendations (
    id SERIAL PRIMARY KEY,
    evaluation_date VARCHAR(10) NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    store_id VARCHAR(20) NOT NULL,
    current_inventory INT NOT NULL,
    average_daily_demand NUMERIC(10, 2) NOT NULL,
    demand_std_dev NUMERIC(10, 2) NOT NULL,
    lead_time_days INT NOT NULL,
    safety_stock INT NOT NULL,
    reorder_point INT NOT NULL,
    forecast_demand_lt NUMERIC(10, 2) NOT NULL,
    recommended_order_qty INT NOT NULL,
    days_of_supply NUMERIC(10, 2) NOT NULL,
    inventory_status VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    stockout_risk_pct NUMERIC(5, 2) NOT NULL,
    overstock_risk_pct NUMERIC(5, 2) NOT NULL,
    suggested_replenishment_date VARCHAR(10),
    estimated_order_cost NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
