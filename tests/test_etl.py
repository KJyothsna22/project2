"""
Unit Tests for ETL Data Extraction, Cleaning, and Validation
"""

import pandas as pd
import numpy as np
import pytest
from etl.clean import DataCleaner
from etl.validate import DataValidator

def test_clean_calendar():
    raw_calendar = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01", "invalid_date", "2023-01-02"],
        "wm_yr_wk": [12301, 12301, 12301, 12301],
        "weekday": ["Sunday", "Sunday", "None", "Monday"],
        "wday": [2, 2, 0, 3],
        "month": [1, 1, 1, 1],
        "year": [2023, 2023, 2023, 2023],
        "d": ["d_1", "d_1", "d_2", "d_3"],
        "event_name_1": [np.nan, np.nan, np.nan, "NewYear"],
        "snap_CA": [1, 1, 0, 1]
    })
    cleaned = DataCleaner.clean_calendar(raw_calendar)
    assert len(cleaned) == 2  # Deduplicated and dropped invalid date
    assert "date_str" in cleaned.columns
    assert cleaned["is_holiday"].iloc[1] == 1

def test_clean_prices():
    raw_prices = pd.DataFrame({
        "store_id": ["CA_1", "CA_1", "CA_1"],
        "item_id": ["FOODS_1_001", "FOODS_1_001", "FOODS_1_002"],
        "wm_yr_wk": [12301, 12301, 12301],
        "sell_price": [3.50, 3.50, -5.00]  # One duplicate, one negative price
    })
    cleaned = DataCleaner.clean_prices(raw_prices)
    assert len(cleaned) == 2  # Deduplicated
    assert (cleaned["sell_price"] > 0).all()  # Negative price corrected

def test_data_validator_integrity():
    df = pd.DataFrame({
        "store_id": ["CA_1", "CA_2"],
        "item_id": ["ITEM_1", "ITEM_2"],
        "wm_yr_wk": [12301, 12301],
        "sell_price": [5.0, 10.0]
    })
    check_res = DataValidator.check_pricing_integrity(df)
    assert check_res["status"] == "PASSED"
    assert check_res["failed_records"] == 0
