# Data Lineage & Transformation Guide
## Retail Demand Forecasting & Inventory Optimization Platform

### 1. Lineage DAG

```mermaid
graph LR
    subgraph Raw Layer
        R1[sales_train_validation.csv]
        R2[calendar.csv]
        R3[sell_prices.csv]
    end

    subgraph Warehouse Dimensions & Facts
        D1[dim_calendar]
        D2[dim_stores]
        D3[dim_categories]
        D4[dim_departments]
        D5[dim_products]
        F1[fact_sales]
        F2[fact_prices]
    end

    subgraph dbt Staging
        S1[stg_sales]
        S2[stg_calendar]
        S3[stg_prices]
    end

    subgraph dbt Intermediate
        I1[int_daily_sales]
        I2[int_weekly_sales]
        I3[int_monthly_sales]
    end

    subgraph dbt Marts
        M1[mart_product_performance]
        M2[mart_store_performance]
        M3[mart_inventory_health]
        M4[mart_forecast_accuracy]
    end

    subgraph Machine Learning & Analytics
        ML1[ml_features_dataset]
        ML2[fact_forecast_results]
        ML3[fact_inventory_recommendations]
    end

    R1 --> F1
    R2 --> D1
    R3 --> F2
    F1 --> D2 & D3 & D4 & D5
    F1 --> S1
    D1 --> S2
    F2 --> S3

    S1 & S2 & S3 --> I1
    I1 --> I2 & I3
    I1 --> M1 & M2
    I1 --> ML1
    ML1 --> ML2
    ML2 --> ML3
    ML3 --> M3
    ML2 --> M4
```

---

### 2. Transformation Descriptions

| Model Name | Layer | Source | Granularity | Key Transformation Logic |
| :--- | :--- | :--- | :--- | :--- |
| **stg_sales** | Staging | `fact_sales` | Store-Item-Date | Type casting, negative sale zero-clipping |
| **stg_calendar** | Staging | `dim_calendar` | Date | Holiday indicator flag, is_weekend calculation |
| **stg_prices** | Staging | `fact_prices` | Store-Item-Week | Price validation, null handling |
| **int_daily_sales** | Intermediate | `stg_sales`, `stg_calendar`, `stg_prices` | Store-Item-Date | Joined daily revenue calculation ($units \times price$) |
| **int_weekly_sales** | Intermediate | `int_daily_sales` | Store-Item-Week | Weekly unit and revenue aggregations |
| **int_monthly_sales** | Intermediate | `int_daily_sales` | Store-Cat-Month | High-level monthly business velocity |
| **mart_product_performance** | Mart | `int_daily_sales` | Item | Lifetime product revenue, units, max daily spikes |
| **mart_store_performance** | Mart | `int_daily_sales`, `dim_stores` | Store | Store revenue rankings, regional category mix |
| **mart_inventory_health** | Mart | `fact_inventory_recommendations` | Store | Store-level stockout counts, total capital requirements |
| **mart_forecast_accuracy** | Mart | `fact_forecast_results` | Model-Horizon | MAE, RMSE, MAPE benchmark scorecard |
