"""
Unit Tests for Inventory Optimization Engine & Risk Analyzer
"""

import numpy as np
import pytest
from inventory.optimization_engine import InventoryOptimizer
from inventory.risk_analyzer import InventoryRiskAnalyzer

def test_safety_stock_calculation():
    ss = InventoryOptimizer.calculate_safety_stock(
        max_demand=25.0,
        avg_demand=10.0,
        demand_std=3.0,
        lead_time_days=7,
        service_level_z=1.65
    )
    assert ss > 0
    assert isinstance(ss, int)

def test_reorder_point_calculation():
    rop = InventoryOptimizer.calculate_reorder_point(
        avg_demand=10.0,
        lead_time_days=7,
        safety_stock=15
    )
    # ROP = (10 * 7) + 15 = 85
    assert rop == 85

def test_order_quantity_calculation():
    roq = InventoryOptimizer.calculate_order_quantity(
        forecast_demand=70.0,
        safety_stock=15,
        current_inventory=20
    )
    # Order Qty = 70 + 15 - 20 = 65
    assert roq == 65

def test_risk_analyzer_classification():
    # Scenario: Low inventory (below safety stock) -> High Risk
    risk_info = InventoryRiskAnalyzer.evaluate_risk(
        current_inventory=5,
        reorder_point=85,
        safety_stock=15,
        avg_daily_demand=10.0,
        lead_time_days=7,
        evaluation_date="2023-12-31"
    )
    assert risk_info["risk_level"] == "High Risk"
    assert risk_info["inventory_status"] == "Critical Stockout Risk"
