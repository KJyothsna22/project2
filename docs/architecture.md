# Enterprise Architecture Documentation
## Retail Demand Forecasting & Inventory Optimization Platform

### 1. System Overview
The platform provides an end-to-end automated analytics solution designed to ingest raw Walmart M5 multi-store retail sales datasets, execute automated data cleaning and validation, run dbt analytical transformations, train machine learning time-series models (Prophet and LightGBM), optimize inventory replenishment buffers, and present interactive analytics to business decision makers through a role-protected Streamlit dashboard.

---

### 2. End-to-End Architectural Pipeline

```mermaid
flowchart TD
    subgraph 1. Ingestion & Quality Layer
        RAW[M5 Raw Datasets / Synthetic Generator] --> EXT[ETL Extraction: etl/extract.py]
        EXT --> CLN[Data Cleaning & Standardization: etl/clean.py]
        CLN --> VAL[Quality Validator: etl/validate.py]
        VAL --> AUD[Audit Logger: etl/quality_checks.py]
        AUD --> WH[(Data Warehouse: SQLite / DuckDB / Postgres)]
    end

    subgraph 2. Analytical Transformation Layer
        WH --> STG[dbt Staging Models: stg_sales, stg_calendar, stg_prices]
        STG --> INT[dbt Intermediate Aggregations: int_daily, int_weekly, int_monthly]
        INT --> MARTS[dbt Data Marts: mart_product, mart_store, mart_inventory, mart_accuracy]
    end

    subgraph 3. Machine Learning & Feature Engineering
        MARTS --> FE[Feature Engineering: Lags 7/14/28/60, Rolling Stats, Price, SNAP]
        FE --> PROPHET[Prophet Forecaster: Additive GAM + Seasonality]
        FE --> LGBM[LightGBM Forecaster: GBDT Regressor]
        PROPHET & LGBM --> EVAL[Evaluation Engine: MAE, RMSE, MAPE, R2]
        EVAL --> FSTORE[(fact_forecast_results)]
    end

    subgraph 4. Inventory Optimization Engine
        FSTORE --> OPT[Inventory Optimizer: Safety Stock, ROP, Order Qty]
        OPT --> RISK[Risk Classifier: Stockout vs Overstock]
        RISK --> ISTORE[(fact_inventory_recommendations)]
    end

    subgraph 5. Presentation & Governance
        ISTORE & FSTORE --> AUTH[Role-Based Authentication: Admin, Manager, Viewer]
        AUTH --> DASH[Streamlit Multi-Page Dashboard: app.py]
        DASH --> REP[Reporting Module: CSV, Excel .xlsx, PDF Executive Briefs]
    end
```

---

### 3. Key Technology Stack
- **Data Engineering**: Python 3.10+, Pandas, DuckDB, SQLite, SQLAlchemy, PostgreSQL / Snowflake / BigQuery DDL.
- **Analytics Engineering**: dbt SQL transformations (Staging, Intermediate, Marts).
- **Machine Learning**: LightGBM (Gradient Boosted Trees), Facebook Prophet / Additive Seasonality GAMs, Scikit-Learn.
- **User Interface**: Streamlit with custom glassmorphic CSS, Plotly Interactive Charts.
- **Reporting & Security**: OpenPyXL, FPDF2, SHA-256 password hashing, Role-Based Access Control.
