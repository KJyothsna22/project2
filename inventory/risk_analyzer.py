"""
Inventory Risk Classification & Anomaly Detection
Classifies products into High, Medium, and Low risk based on forecast demand,
current inventory, lead times, and reorder points. Computes stockout and overstock probabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from utils.logger import get_logger

logger = get_logger("risk_analyzer")

class InventoryRiskAnalyzer:
    """Classifies inventory health risks and evaluates replenishment urgency."""

    @classmethod
    def evaluate_risk(
        cls,
        current_inventory: int,
        reorder_point: int,
        safety_stock: int,
        avg_daily_demand: float,
        lead_time_days: int,
        evaluation_date: str
    ) -> Dict[str, Any]:
        """
        Classifies SKU into:
        - High Risk: Stockout Imminent (inventory < safety_stock) OR Severe Overstock (days_of_supply > 4 * lead_time)
        - Medium Risk: Reorder Needed (safety_stock <= inventory <= reorder_point)
        - Low Risk: Healthy Balance (reorder_point < inventory <= 3 * lead_time)
        """
        eval_dt = datetime.strptime(evaluation_date, "%Y-%m-%d")
        daily_demand = max(0.1, avg_daily_demand)
        days_of_supply = current_inventory / daily_demand

        # Stockout Risk % (Higher when inventory is low relative to lead time demand)
        lt_demand = daily_demand * lead_time_days
        stockout_risk_pct = min(100.0, max(0.0, ((lt_demand + safety_stock - current_inventory) / max(1.0, (lt_demand + safety_stock))) * 100.0))

        # Overstock Risk % (Higher when days of supply exceed 30+ days)
        overstock_threshold_days = lead_time_days * 3.5
        overstock_risk_pct = min(100.0, max(0.0, ((days_of_supply - overstock_threshold_days) / overstock_threshold_days) * 100.0)) if days_of_supply > overstock_threshold_days else 0.0

        # Classification logic
        if current_inventory < safety_stock:
            risk_level = "High Risk"
            status = "Critical Stockout Risk"
            # Imminent replenishment date
            replenishment_date = (eval_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        elif current_inventory <= reorder_point:
            risk_level = "Medium Risk"
            status = "Reorder Needed"
            # Replenishment within buffer days
            buffer_days = max(1, int((current_inventory - safety_stock) / daily_demand))
            replenishment_date = (eval_dt + timedelta(days=buffer_days)).strftime("%Y-%m-%d")
        elif days_of_supply > overstock_threshold_days:
            risk_level = "High Risk" if days_of_supply > overstock_threshold_days * 1.5 else "Medium Risk"
            status = "Excess Overstock"
            replenishment_date = (eval_dt + timedelta(days=int(days_of_supply))).strftime("%Y-%m-%d")
        else:
            risk_level = "Low Risk"
            status = "Healthy Buffer"
            days_to_rop = max(1, int((current_inventory - reorder_point) / daily_demand))
            replenishment_date = (eval_dt + timedelta(days=days_to_rop)).strftime("%Y-%m-%d")

        return {
            "inventory_status": status,
            "risk_level": risk_level,
            "stockout_risk_pct": round(stockout_risk_pct, 1),
            "overstock_risk_pct": round(overstock_risk_pct, 1),
            "suggested_replenishment_date": replenishment_date
        }
