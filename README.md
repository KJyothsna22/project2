# 🛒 Retail Demand Forecasting & Inventory Optimization Platform

An enterprise-grade, end-to-end automated analytics platform for retail and supply chain teams built upon the **Walmart M5 Forecasting Dataset** architecture.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LightGBM](https://img.shields.io/badge/LightGBM-4.7%2B-brightgreen)
![Streamlit](https://img.shields.io/badge/Streamlit-1.61%2B-red)
![dbt](https://img.shields.io/badge/dbt-Transformations-orange)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-blueviolet)

---

## 🌟 Executive Summary & Key Capabilities

This platform replicates production-scale retail supply chain intelligence systems used by **Walmart, Target, Amazon, Costco, and Reliance Retail**:

- **Automated Data Architecture & ETL Pipeline**: Ingestion and cleaning of raw sales, prices, and calendar events with 9 automated data quality validation rules and audit logging.
- **dbt Transformation DAG & Data Marts**: Standardized staging, intermediate, and dimensional business data marts (`mart_product_performance`, `mart_store_performance`, `mart_inventory_health`, `mart_forecast_accuracy`).
- **Feature Engineering Engine**: Temporal signals, holiday regressors, SNAP food stamp indicators, multi-day lag features (7, 14, 28, 60), rolling window statistics, and pricing dynamics.
- **Dual Machine Learning Forecasters**:
  - **Facebook Prophet (Additive GAM)**: Piecewise linear trend with changepoints, weekly/yearly Fourier seasonality, holiday spikes, and 95% Bayesian uncertainty intervals.
  - **LightGBM (GBDT Regressor)**: Granular item-store regression model with recursive multi-horizon forecast generation (7, 30, and 90 days).
  - **Automated Champion Selector**: Out-of-time evaluation benchmarking MAE, RMSE, MAPE, and $R^2$.
- **Inventory Optimization & Replenishment Engine**:
  - Reorder Point ($ROP = \mu_d \times LT + SS$)
  - Safety Stock ($SS = Z \times \sigma_d \times \sqrt{LT}$)
  - Recommended Order Quantity ($ROQ = \max(0, D_{\text{forecast}} + SS - I_{\text{current}})$)
  - Risk Classification (Critical Stockout, Excess Overstock, Healthy Buffer)
- **Interactive Multi-Page Streamlit Dashboard**: Glassmorphism UI theme with role-based access control (Admin, Manager, Viewer), scenario simulation sliders, and downloadable CSV, Excel (.xlsx), and PDF reports.

---

## 📁 Repository Structure

```
project2/
├── app.py                          # Streamlit application entrypoint
├── config.py                       # Global configuration & environment settings
├── run_pipeline.py                 # Master CLI script for end-to-end execution
├── requirements.txt                # Python dependencies
├── README.md                       # Platform documentation
│
├── auth/                           # Role-based authentication (Admin, Manager, Viewer)
├── data/
│   ├── raw/                        # M5 CSV files (or generated high-fidelity sample)
│   ├── processed/                  # Cleaned parquet datasets
│   └── sample_generator.py         # M5 synthetic data generator
│
├── etl/                            # Extract, clean, validate, quality checks & warehouse loader
├── warehouse/                      # SQLite/DuckDB/PostgreSQL connection & DDL schemas
│   └── migrations/                 # PostgreSQL, BigQuery, Snowflake DDL migration scripts
│
├── dbt_project/                    # dbt project, profiles, staging, intermediate & mart models
├── forecasting/                    # Feature engineering, Prophet, LightGBM, evaluation engine
├── inventory/                      # Safety stock, ROP, ROQ, risk analyzer & replenishment planner
├── dashboard/                      # Glassmorphic UI styles, components, and 5 interactive pages
├── reports/                        # CSV, Multi-tab Excel (.xlsx), and Executive PDF generator
├── utils/                          # Structured logger & date/numeric helpers
├── tests/                          # Pytest suite for ETL, ML, Inventory, and Auth
└── docs/                           # Architecture, lineage, setup & deployment guides
```

---

## 🚀 Quick Start Guide

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Master Pipeline
Executes data ingestion, quality validation, dbt transforms, ML training, and inventory optimization in ~10 seconds:
```bash
python run_pipeline.py
```

### 3. Launch Interactive Dashboard
```bash
python -m streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🔐 Role-Based Demo Credentials

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access, one-click pipeline re-run, inventory approvals, all exports |
| **Inventory Manager** | `manager` | `manager123` | Demand forecasting explorer, inventory optimization, what-if simulations |
| **Viewer** | `viewer` | `viewer123` | Executive dashboard overview, model accuracy metrics, report downloads |

---

## 🧪 Running Automated Tests
```bash
python -m pytest tests/ -v
```

---

## ☁️ Enterprise Cloud Migration
Pre-configured schemas for enterprise data warehouses are located in `warehouse/migrations/`:
- `warehouse/migrations/postgresql_schema.sql` (Amazon RDS, Aurora, Cloud SQL)
- `warehouse/migrations/snowflake_schema.sql` (Snowflake Data Cloud)
- `warehouse/migrations/bigquery_schema.sql` (Google Cloud BigQuery)
