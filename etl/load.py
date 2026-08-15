"""
ETL Step 5: Data Warehouse Loader
Extracts dimensional hierarchies, structures fact tables, and performs bulk loading into warehouse.
"""

from typing import Dict
import pandas as pd
import config
from warehouse.db import WarehouseManager
from warehouse.schema import init_database_schemas
from utils.logger import get_logger

logger = get_logger("etl_load")

class WarehouseLoader:
    """Loads cleaned data into relational dimension and fact warehouse tables."""

    @classmethod
    def extract_and_load_dimensions(cls, cleaned_sales: pd.DataFrame, cleaned_prices: pd.DataFrame) -> None:
        """Extracts and loads store, category, department, and product dimension tables."""
        logger.info("Extracting and loading dimension tables...")

        # 1. Stores Dimension
        store_map = {
            "CA_1": ("CA", "Sacramento Supercenter", "Pacific"),
            "CA_2": ("CA", "San Francisco Metro", "Pacific"),
            "TX_1": ("TX", "Dallas Supercenter", "South Central"),
            "TX_2": ("TX", "Austin Central", "South Central"),
            "WI_1": ("WI", "Milwaukee North", "Midwest"),
            "WI_2": ("WI", "Madison West", "Midwest"),
        }
        unique_stores = cleaned_sales[["store_id", "state_id"]].drop_duplicates()
        stores_records = []
        for _, r in unique_stores.iterrows():
            s_id = r["store_id"]
            st_id = r["state_id"]
            name, reg = store_map.get(s_id, (st_id, f"Store {s_id}", "General"))[1:]
            stores_records.append({
                "store_id": s_id,
                "state_id": st_id,
                "store_name": name,
                "region": reg
            })
        stores_df = pd.DataFrame(stores_records)
        WarehouseManager.write_dataframe(stores_df, "dim_stores", if_exists="replace")

        # 2. Categories Dimension
        unique_cats = cleaned_sales[["cat_id"]].drop_duplicates()
        unique_cats["category_name"] = unique_cats["cat_id"].str.replace("_", " ").str.title()
        WarehouseManager.write_dataframe(unique_cats, "dim_categories", if_exists="replace")

        # 3. Departments Dimension
        unique_depts = cleaned_sales[["dept_id", "cat_id"]].drop_duplicates()
        unique_depts["department_name"] = unique_depts["dept_id"].str.replace("_", " ").str.title()
        WarehouseManager.write_dataframe(unique_depts, "dim_departments", if_exists="replace")

        # 4. Products Dimension
        avg_prices = cleaned_prices.groupby("item_id")["sell_price"].mean().to_dict()
        unique_prods = cleaned_sales[["item_id", "dept_id", "cat_id"]].drop_duplicates()
        unique_prods["product_name"] = unique_prods["item_id"].apply(
            lambda x: f"{x.split('_')[0]} Product #{x.split('_')[-1]}"
        )
        unique_prods["unit_cost"] = unique_prods["item_id"].map(
            lambda x: round(avg_prices.get(x, 5.0) * 0.60, 2)
        )
        WarehouseManager.write_dataframe(unique_prods, "dim_products", if_exists="replace")

    @classmethod
    def load_calendar_dimension(cls, cleaned_calendar: pd.DataFrame) -> None:
        """Loads calendar dimension table."""
        logger.info("Loading dim_calendar...")
        cal_cols = [
            "date_str", "wm_yr_wk", "weekday", "wday", "month", "year", "d",
            "event_name_1", "event_type_1", "event_name_2", "event_type_2",
            "snap_CA", "snap_TX", "snap_WI", "is_holiday"
        ]
        cal_df = cleaned_calendar[[c for c in cal_cols if c in cleaned_calendar.columns]].copy()
        cal_df = cal_df.rename(columns={"d": "d_id"})
        WarehouseManager.write_dataframe(cal_df, "dim_calendar", if_exists="replace")

    @classmethod
    def load_fact_tables(cls, cleaned_sales: pd.DataFrame, cleaned_prices: pd.DataFrame) -> None:
        """Loads fact_sales and fact_prices."""
        logger.info("Loading fact_prices...")
        price_cols = ["store_id", "item_id", "wm_yr_wk", "sell_price"]
        WarehouseManager.write_dataframe(cleaned_prices[price_cols], "fact_prices", if_exists="replace")

        logger.info("Loading fact_sales...")
        sales_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id", "date_str", "sales_units"]
        WarehouseManager.write_dataframe(cleaned_sales[sales_cols], "fact_sales", if_exists="replace")

    @classmethod
    def seed_initial_users(cls) -> None:
        """Populates default system users."""
        users = []
        for username, udata in config.DEFAULT_USERS.items():
            users.append({
                "username": username,
                "password_hash": udata["password_hash"],
                "role": udata["role"],
                "full_name": udata["name"]
            })
        users_df = pd.DataFrame(users)
        WarehouseManager.write_dataframe(users_df, "sys_users", if_exists="replace")
        logger.info("Seeded initial users into sys_users.")

    @classmethod
    def run_loading_pipeline(cls, cleaned_datasets: Dict[str, pd.DataFrame]) -> None:
        """Orchestrates schema initialization and warehouse ingestion."""
        init_database_schemas()
        cls.extract_and_load_dimensions(cleaned_datasets["sales"], cleaned_datasets["prices"])
        cls.load_calendar_dimension(cleaned_datasets["calendar"])
        cls.load_fact_tables(cleaned_datasets["sales"], cleaned_datasets["prices"])
        cls.seed_initial_users()
        logger.info("Data Warehouse loading successfully completed.")
