"""
dbt Transformation Runner & Lineage Engine
Executes staging, intermediate, and marts transformation DAG in the data warehouse.
"""

import time
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from warehouse.db import WarehouseManager
from utils.logger import get_logger

logger = get_logger("dbt_runner")

DBT_MODELS_DIR = Path(__file__).resolve().parent / "models"

class DBTRunner:
    """Orchestrates SQL transformations corresponding to the dbt project DAG."""

    DAG_ORDER = [
        # Staging
        ("stg_sales", DBT_MODELS_DIR / "staging" / "stg_sales.sql", "view"),
        ("stg_calendar", DBT_MODELS_DIR / "staging" / "stg_calendar.sql", "view"),
        ("stg_prices", DBT_MODELS_DIR / "staging" / "stg_prices.sql", "view"),
        # Intermediate
        ("int_daily_sales", DBT_MODELS_DIR / "intermediate" / "int_daily_sales.sql", "table"),
        ("int_weekly_sales", DBT_MODELS_DIR / "intermediate" / "int_weekly_sales.sql", "table"),
        ("int_monthly_sales", DBT_MODELS_DIR / "intermediate" / "int_monthly_sales.sql", "table"),
        # Marts
        ("mart_product_performance", DBT_MODELS_DIR / "marts" / "mart_product_performance.sql", "table"),
        ("mart_store_performance", DBT_MODELS_DIR / "marts" / "mart_store_performance.sql", "table"),
        ("mart_inventory_health", DBT_MODELS_DIR / "marts" / "mart_inventory_health.sql", "table"),
        ("mart_forecast_accuracy", DBT_MODELS_DIR / "marts" / "mart_forecast_accuracy.sql", "table"),
    ]

    @classmethod
    def run_transformations(cls) -> Dict[str, Any]:
        """Executes all dbt models in topological dependency order."""
        logger.info("================ STARTING dbt TRANSFORMATIONS ================")
        start_time = time.time()
        results = []

        for model_name, sql_path, mat_type in cls.DAG_ORDER:
            if not sql_path.exists():
                logger.warning(f"SQL file not found for {model_name} at {sql_path}")
                continue

            with open(sql_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Materialize as View or Table
            logger.info(f"Building dbt model '{model_name}' as {mat_type.upper()}...")
            t0 = time.time()
            try:
                if mat_type == "view":
                    create_sql = f"CREATE VIEW IF NOT EXISTS {model_name} AS\n{sql_content}"
                    # Drop existing view if needed
                    WarehouseManager.execute_query(f"DROP VIEW IF EXISTS {model_name};")
                    WarehouseManager.execute_query(create_sql)
                else:
                    create_sql = f"CREATE TABLE IF NOT EXISTS {model_name} AS\n{sql_content}"
                    # Drop existing table if needed
                    WarehouseManager.execute_query(f"DROP TABLE IF EXISTS {model_name};")
                    WarehouseManager.execute_query(create_sql)

                elapsed = time.time() - t0
                logger.info(f"Model '{model_name}' built successfully ({elapsed:.2f}s).")
                results.append({"model": model_name, "status": "SUCCESS", "time_sec": elapsed})
            except Exception as e:
                logger.error(f"Error compiling dbt model '{model_name}': {e}")
                results.append({"model": model_name, "status": "FAILED", "error": str(e)})

        total_time = time.time() - start_time
        logger.info(f"================ dbt TRANSFORMATIONS COMPLETED IN {total_time:.2f}s ================")
        return {
            "total_time_seconds": total_time,
            "models_executed": len(results),
            "results": results
        }

if __name__ == "__main__":
    DBTRunner.run_transformations()
