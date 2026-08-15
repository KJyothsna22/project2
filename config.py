"""
Retail Demand Forecasting & Inventory Optimization Platform
Global Configuration & Settings
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports" / "generated"
LOGS_DIR = BASE_DIR / "logs"

# Ensure essential directories exist
for path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database Configuration
# Default to SQLite/DuckDB for seamless local execution; configurable to PostgreSQL
DB_DIALECT = os.getenv("DB_DIALECT", "sqlite")  # options: sqlite, duckdb, postgresql, snowflake, bigquery
SQLITE_DB_PATH = BASE_DIR / "warehouse" / "retail_platform.db"
DUCKDB_PATH = BASE_DIR / "warehouse" / "retail_platform.duckdb"

# PostgreSQL connection params (if selected)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DATABASE = os.getenv("PG_DATABASE", "retail_warehouse")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

# Raw Dataset Files
SALES_TRAIN_FILE = RAW_DATA_DIR / "sales_train_validation.csv"
CALENDAR_FILE = RAW_DATA_DIR / "calendar.csv"
SELL_PRICES_FILE = RAW_DATA_DIR / "sell_prices.csv"

# Processed Files
CLEANED_SALES_FILE = PROCESSED_DATA_DIR / "cleaned_sales.parquet"
CLEANED_CALENDAR_FILE = PROCESSED_DATA_DIR / "cleaned_calendar.parquet"
CLEANED_PRICES_FILE = PROCESSED_DATA_DIR / "cleaned_prices.parquet"
DAILY_SALES_FILE = PROCESSED_DATA_DIR / "int_daily_sales.parquet"
FEATURE_DATASET_FILE = PROCESSED_DATA_DIR / "ml_features_dataset.parquet"

# Machine Learning & Forecasting Configurations
DEFAULT_HORIZONS = [7, 30, 90]  # Days
CONFIDENCE_LEVELS = [0.80, 0.95]
RANDOM_STATE = 42

# LightGBM Parameters
LGBM_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "boosting_type": "gbdt",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "n_estimators": 150,
    "verbose": -1,
    "random_state": RANDOM_STATE
}

# Inventory Engine Defaults
DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_SERVICE_LEVEL_Z = 1.65  # 95% service level
HOLDING_COST_RATE = 0.20        # 20% annual holding cost
STOCKOUT_PENALTY_MULTIPLIER = 1.5

# Role-Based Authentication
DEFAULT_USERS = {
    "admin": {
        "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # admin123
        "role": "Admin",
        "name": "Sarah Connor (VP of Supply Chain)"
    },
    "manager": {
        "password_hash": "866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5",  # manager123
        "role": "Inventory Manager",
        "name": "David Miller (Lead Inventory Planner)"
    },
    "viewer": {
        "password_hash": "65375049b9e4d7cad6c9ba286fdeb9394b28135a3e84136404cfccfdcc438894",  # viewer123
        "role": "Viewer",
        "name": "Alex Wong (Operations Analyst)"
    }
}
