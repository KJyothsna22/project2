"""
Inventory Optimization Engine
Calculates:
- Reorder Point (ROP): Average Demand * Lead Time + Safety Stock
- Safety Stock (SS): (Max Demand - Average Demand) * Lead Time & Z * std_dev * sqrt(Lead Time)
- Recommended Order Quantity (ROQ): Forecast Demand + Safety Stock - Current Inventory
"""

import math
from typing import Dict, Any
import numpy as np
import pandas as pd
import config
from utils.logger import get_logger

logger = get_logger("inventory_engine")

class InventoryOptimizer:
    """Computes mathematical inventory replenishment thresholds and order quantities."""

    @staticmethod
    def calculate_safety_stock(
        max_demand: float,
        avg_demand: float,
        demand_std: float,
        lead_time_days: int = config.DEFAULT_LEAD_TIME_DAYS,
        service_level_z: float = config.DEFAULT_SERVICE_LEVEL_Z,
        method: str = "statistical"
    ) -> int:
        """
        Calculates Safety Stock (SS).
        Methods:
        - 'statistical': Z * std_dev * sqrt(Lead Time)
        - 'max_min': (Max Demand - Average Demand) * Lead Time
        """
        if method == "max_min":
            ss = (max_demand - avg_demand) * lead_time_days
        else:
            # Standard statistical safety stock
            ss = service_level_z * demand_std * math.sqrt(lead_time_days)
            
        return max(1, int(math.ceil(ss)))

    @staticmethod
    def calculate_reorder_point(
        avg_demand: float,
        lead_time_days: int,
        safety_stock: int
    ) -> int:
        """
        Calculates Reorder Point (ROP).
        Formula: ROP = (Average Daily Demand * Lead Time) + Safety Stock
        """
        lead_time_demand = avg_demand * lead_time_days
        rop = lead_time_demand + safety_stock
        return max(1, int(math.ceil(rop)))

    @staticmethod
    def calculate_order_quantity(
        forecast_demand: float,
        safety_stock: int,
        current_inventory: int
    ) -> int:
        """
        Calculates Recommended Order Quantity (ROQ).
        Formula: Order Quantity = Forecast Demand + Safety Stock - Current Inventory
        """
        raw_order = forecast_demand + safety_stock - current_inventory
        return max(0, int(math.ceil(raw_order)))

    @classmethod
    def optimize_sku(
        cls,
        item_id: str,
        store_id: str,
        current_inventory: int,
        historical_sales: np.ndarray,
        forecast_demand_lt: float,
        unit_cost: float = 5.00,
        lead_time_days: int = config.DEFAULT_LEAD_TIME_DAYS
    ) -> Dict[str, Any]:
        """Calculates full optimization parameters for a single SKU-Store series."""
        avg_demand = float(np.mean(historical_sales)) if len(historical_sales) > 0 else 1.0
        max_demand = float(np.max(historical_sales)) if len(historical_sales) > 0 else avg_demand * 2.0
        demand_std = float(np.std(historical_sales)) if len(historical_sales) > 0 else 1.0

        # Safety stock and ROP
        safety_stock = cls.calculate_safety_stock(max_demand, avg_demand, demand_std, lead_time_days)
        reorder_point = cls.calculate_reorder_point(avg_demand, lead_time_days, safety_stock)
        recommended_order_qty = cls.calculate_order_quantity(forecast_demand_lt, safety_stock, current_inventory)

        # Days of Supply (Current Inventory / Average Daily Demand)
        days_of_supply = round(current_inventory / max(0.1, avg_demand), 1)

        return {
            "item_id": item_id,
            "store_id": store_id,
            "current_inventory": int(current_inventory),
            "average_daily_demand": round(avg_demand, 2),
            "demand_std_dev": round(demand_std, 2),
            "lead_time_days": lead_time_days,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "forecast_demand_lt": round(forecast_demand_lt, 2),
            "recommended_order_qty": recommended_order_qty,
            "days_of_supply": days_of_supply,
            "unit_cost": unit_cost,
            "estimated_order_cost": round(recommended_order_qty * unit_cost, 2)
        }
