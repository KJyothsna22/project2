"""
Master Inventory Replenishment & Purchase Order Planning Pipeline
Orchestrates optimization, risk scoring, suggested replenishment schedules,
and persists recommendations to `fact_inventory_recommendations` table in the data warehouse.
"""

import time
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import config
from warehouse.db import WarehouseManager
from inventory.optimization_engine import InventoryOptimizer
from inventory.risk_analyzer import InventoryRiskAnalyzer
from utils.logger import get_logger

logger = get_logger("inventory_replenishment")

class ReplenishmentPlanner:
    """Master orchestrator for multi-store inventory replenishment recommendations."""

    @classmethod
    def generate_all_recommendations(
        cls,
        lead_time_days: int = config.DEFAULT_LEAD_TIME_DAYS
    ) -> pd.DataFrame:
        """
        Calculates inventory metrics and risk recommendations for all item-store series.
        """
        logger.info("================ STARTING INVENTORY OPTIMIZATION ENGINE ================")
        start_time = time.time()

        # 1. Fetch sales history and product catalog
        sales_query = """
        SELECT item_id, store_id, date_str, sales_units
        FROM fact_sales
        ORDER BY item_id, store_id, date_str ASC
        """
        sales_df = WarehouseManager.read_query(sales_query)

        products_query = "SELECT item_id, product_name, unit_cost FROM dim_products"
        prod_df = WarehouseManager.read_query(products_query).set_index("item_id")

        # 2. Fetch forecasted demand for next lead_time_days
        forecast_query = f"""
        SELECT item_id, store_id, SUM(forecast_demand) as forecast_lead_time_demand
        FROM fact_forecast_results
        WHERE actual_demand IS NULL
          AND horizon_days = {config.DEFAULT_HORIZONS[0]}
        GROUP BY item_id, store_id
        """
        forecast_df = WarehouseManager.read_query(forecast_query).set_index(["item_id", "store_id"])

        eval_date = sales_df["date_str"].max()
        records = []

        np.random.seed(config.RANDOM_STATE)
        unique_series = sales_df[["item_id", "store_id"]].drop_duplicates()

        logger.info(f"Optimizing inventory for {len(unique_series)} item-store series as of {eval_date}...")

        for _, row in unique_series.iterrows():
            item_id = row["item_id"]
            store_id = row["store_id"]

            sub_sales = sales_df[(sales_df["item_id"] == item_id) & (sales_df["store_id"] == store_id)]
            sales_arr = sub_sales["sales_units"].values[-90:]  # Recent 90 days
            avg_demand = float(np.mean(sales_arr)) if len(sales_arr) > 0 else 2.0

            # Simulate realistic current inventory on hand (some understocked, some balanced, some excess)
            # e.g. Randomly between 0.2x and 4x of lead time demand
            lt_base = avg_demand * lead_time_days
            rand_factor = np.random.choice([0.3, 0.7, 1.2, 1.8, 3.5], p=[0.15, 0.25, 0.35, 0.15, 0.10])
            current_inventory = max(0, int(round(lt_base * rand_factor)))

            # Unit Cost
            unit_cost = float(prod_df.loc[item_id, "unit_cost"]) if item_id in prod_df.index else 5.00

            # Forecasted Demand
            if (item_id, store_id) in forecast_df.index:
                forecast_demand_lt = float(forecast_df.loc[(item_id, store_id), "forecast_lead_time_demand"])
            else:
                forecast_demand_lt = avg_demand * lead_time_days

            # Optimization math
            opt_metrics = InventoryOptimizer.optimize_sku(
                item_id=item_id,
                store_id=store_id,
                current_inventory=current_inventory,
                historical_sales=sales_arr,
                forecast_demand_lt=forecast_demand_lt,
                unit_cost=unit_cost,
                lead_time_days=lead_time_days
            )

            # Risk evaluation
            risk_metrics = InventoryRiskAnalyzer.evaluate_risk(
                current_inventory=current_inventory,
                reorder_point=opt_metrics["reorder_point"],
                safety_stock=opt_metrics["safety_stock"],
                avg_daily_demand=opt_metrics["average_daily_demand"],
                lead_time_days=lead_time_days,
                evaluation_date=eval_date
            )

            record = {
                "evaluation_date": eval_date,
                **opt_metrics,
                **risk_metrics
            }
            records.append(record)

        recom_df = pd.DataFrame(records)

        # 3. Persist to warehouse
        logger.info(f"Persisting {len(recom_df)} inventory recommendations to 'fact_inventory_recommendations'...")
        WarehouseManager.write_dataframe(recom_df, "fact_inventory_recommendations", if_exists="replace")

        duration = time.time() - start_time
        logger.info(f"================ INVENTORY OPTIMIZATION COMPLETED IN {duration:.2f}s ================")
        return recom_df

if __name__ == "__main__":
    df_recom = ReplenishmentPlanner.generate_all_recommendations()
    print("Recommendations generated:", len(df_recom))
    print(df_recom["risk_level"].value_counts())
