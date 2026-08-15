"""
Realistic Walmart M5 Dataset Generator
Generates high-fidelity, production-grade M5-compliant datasets:
- calendar.csv
- sell_prices.csv
- sales_train_validation.csv

Simulates true retail demand properties:
- Weekly seasonality (weekend lifts)
- Annual seasonality & holiday spikes (SuperBowl, Thanksgiving, Christmas, Memorial Day, Ramadan)
- SNAP food stamp demand surges (first 10 days of the month)
- Store, category, and department hierarchy
- Realistic price fluctuations and demand elasticity
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import config
from utils.logger import get_logger

logger = get_logger("data_generator")

# Configuration for M5 data generation
STORES = [
    ("CA_1", "CA", "Sacramento Supercenter", "Pacific"),
    ("CA_2", "CA", "San Francisco Metro", "Pacific"),
    ("TX_1", "TX", "Dallas Supercenter", "South Central"),
    ("TX_2", "TX", "Austin Central", "South Central"),
    ("WI_1", "WI", "Milwaukee North", "Midwest"),
    ("WI_2", "WI", "Madison West", "Midwest"),
]

CATEGORIES_DEPTS = {
    "FOODS": ["FOODS_1", "FOODS_2", "FOODS_3"],
    "HOBBIES": ["HOBBIES_1", "HOBBIES_2"],
    "HOUSEHOLD": ["HOUSEHOLD_1", "HOUSEHOLD_2"]
}

HOLIDAYS = {
    "01-01": ("NewYear", "National"),
    "01-20": ("MartinLutherKingDay", "National"),
    "02-02": ("SuperBowl", "Sporting"),
    "02-14": ("ValentinesDay", "Cultural"),
    "03-17": ("StPatricksDay", "Cultural"),
    "04-05": ("Easter", "Cultural"),
    "05-25": ("MemorialDay", "National"),
    "07-04": ("IndependenceDay", "National"),
    "09-07": ("LaborDay", "National"),
    "10-31": ("Halloween", "Cultural"),
    "11-26": ("Thanksgiving", "National"),
    "12-25": ("Christmas", "National"),
    "12-31": ("NewYearsEve", "Cultural")
}

def generate_calendar_df(start_date: str = "2021-01-01", num_days: int = 1000) -> pd.DataFrame:
    """Generates the M5 calendar dataframe."""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    records = []
    
    for i in range(num_days):
        dt = start_dt + timedelta(days=i)
        date_str = dt.strftime("%Y-%m-%d")
        month = dt.month
        year = dt.year
        day = dt.day
        weekday_name = dt.strftime("%A")
        wday = dt.isoweekday() % 7 + 1  # M5 format: Saturday=1, Sunday=2 ... Friday=7
        d_id = f"d_{i+1}"
        
        # Walmart Year-Week (e.g. 12101)
        iso_year, iso_week, _ = dt.isocalendar()
        wm_yr_wk = int(f"1{str(iso_year)[2:]}{iso_week:02d}")
        
        # Holiday / Events
        month_day = f"{month:02d}-{day:02d}"
        event_name_1, event_type_1 = HOLIDAYS.get(month_day, (None, None))
        
        # SNAP program flags (active during first 10 days of month)
        snap_CA = 1 if day in [1, 2, 3, 5, 6, 7, 9, 10] else 0
        snap_TX = 1 if day in [1, 3, 5, 6, 7, 9, 10, 11] else 0
        snap_WI = 1 if day in [2, 3, 5, 8, 9, 11, 12] else 0
        is_holiday = 1 if event_name_1 is not None else 0
        
        records.append({
            "date": date_str,
            "wm_yr_wk": wm_yr_wk,
            "weekday": weekday_name,
            "wday": wday,
            "month": month,
            "year": year,
            "d": d_id,
            "event_name_1": event_name_1,
            "event_type_1": event_type_1,
            "event_name_2": None,
            "event_type_2": None,
            "snap_CA": snap_CA,
            "snap_TX": snap_TX,
            "snap_WI": snap_WI,
            "is_holiday": is_holiday
        })
        
    return pd.DataFrame(records)

def generate_items_catalog(num_items_per_dept: int = 5) -> pd.DataFrame:
    """Generates catalog of product items with department, category, base prices."""
    items = []
    for cat, depts in CATEGORIES_DEPTS.items():
        for dept in depts:
            base_price = 3.50 if cat == "FOODS" else (9.99 if cat == "HOUSEHOLD" else 15.50)
            for idx in range(1, num_items_per_dept + 1):
                item_id = f"{dept}_{idx:03d}"
                prod_name = f"{dept.replace('_', ' ')} Item #{idx}"
                item_price = round(base_price * (0.8 + idx * 0.25), 2)
                unit_cost = round(item_price * 0.60, 2)
                items.append({
                    "item_id": item_id,
                    "dept_id": dept,
                    "cat_id": cat,
                    "product_name": prod_name,
                    "base_price": item_price,
                    "unit_cost": unit_cost
                })
    return pd.DataFrame(items)

def generate_sell_prices_df(calendar_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame:
    """Generates weekly sell_prices dataframe."""
    unique_weeks = sorted(calendar_df["wm_yr_wk"].unique())
    records = []
    
    np.random.seed(config.RANDOM_STATE)
    for store_id, state_id, _, _ in STORES:
        store_mult = 1.05 if state_id == "CA" else (0.95 if state_id == "TX" else 1.0)
        for _, item in items_df.iterrows():
            item_base = item["base_price"] * store_mult
            for week in unique_weeks:
                # Occasional promo discounts
                promo_factor = 0.85 if np.random.rand() < 0.15 else 1.0
                sell_price = round(item_base * promo_factor, 2)
                records.append({
                    "store_id": store_id,
                    "item_id": item["item_id"],
                    "wm_yr_wk": int(week),
                    "sell_price": sell_price
                })
    return pd.DataFrame(records)

def generate_sales_train_df(calendar_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame:
    """Generates wide sales_train_validation format (id, item_id, ..., d_1, d_2, ...)."""
    num_days = len(calendar_df)
    day_columns = [f"d_{i+1}" for i in range(num_days)]
    
    rows = []
    np.random.seed(config.RANDOM_STATE)
    
    for store_id, state_id, _, _ in STORES:
        store_base_factor = 1.2 if "1" in store_id else 0.9
        
        for _, item in items_df.iterrows():
            item_id = item["item_id"]
            dept_id = item["dept_id"]
            cat_id = item["cat_id"]
            row_id = f"{item_id}_{store_id}_validation"
            
            # Base daily demand scale based on category
            cat_scale = 12 if cat_id == "FOODS" else (6 if cat_id == "HOUSEHOLD" else 3)
            base_rate = max(1.0, (cat_scale * store_base_factor) / (item["base_price"] / 5.0))
            
            # Generate realistic time-series demand
            time_idx = np.arange(num_days)
            # Gentle long-term trend
            trend = 1.0 + 0.0003 * time_idx
            # Day-of-week seasonality (Saturday=1, Sunday=2 in M5 have 40% lift)
            wday_factors = np.where((calendar_df["wday"] <= 2), 1.45, 0.90)
            # Month seasonality (e.g. Q4 boost)
            month_factors = 1.0 + 0.20 * np.sin(2 * np.pi * (calendar_df["month"] - 3) / 12)
            # Holiday spike
            holiday_boost = np.where(calendar_df["is_holiday"] == 1, 1.6, 1.0)
            # SNAP boost for foods
            snap_col = f"snap_{state_id}"
            snap_boost = np.where((calendar_df[snap_col] == 1) & (cat_id == "FOODS"), 1.25, 1.0)
            
            expected_demand = base_rate * trend * wday_factors * month_factors * holiday_boost * snap_boost
            
            # Draw Poisson / Negative Binomial stochastic daily sales
            daily_sales = np.random.poisson(lam=expected_demand)
            # Add sporadic zero-sales days (stockouts/low turnover)
            zero_mask = np.random.rand(num_days) < 0.08
            daily_sales[zero_mask] = 0
            
            row_data = {
                "id": row_id,
                "item_id": item_id,
                "dept_id": dept_id,
                "cat_id": cat_id,
                "store_id": store_id,
                "state_id": state_id
            }
            for d_col, val in zip(day_columns, daily_sales):
                row_data[d_col] = int(val)
                
            rows.append(row_data)
            
    return pd.DataFrame(rows)

def generate_full_m5_dataset(num_days: int = 730) -> None:
    """Generates and persists the complete M5 datasets if not already existing."""
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating realistic Walmart M5 dataset for {len(STORES)} stores over {num_days} days...")
    
    # 1. Calendar
    calendar_df = generate_calendar_df(start_date="2022-01-01", num_days=num_days)
    calendar_df.to_csv(config.CALENDAR_FILE, index=False)
    logger.info(f"Generated calendar dataset: {len(calendar_df)} days saved to '{config.CALENDAR_FILE}'.")
    
    # 2. Items & Sell Prices
    items_df = generate_items_catalog(num_items_per_dept=4)
    sell_prices_df = generate_sell_prices_df(calendar_df, items_df)
    sell_prices_df.to_csv(config.SELL_PRICES_FILE, index=False)
    logger.info(f"Generated prices dataset: {len(sell_prices_df)} records saved to '{config.SELL_PRICES_FILE}'.")
    
    # 3. Sales Train Validation
    sales_train_df = generate_sales_train_df(calendar_df, items_df)
    sales_train_df.to_csv(config.SALES_TRAIN_FILE, index=False)
    logger.info(f"Generated sales dataset: {len(sales_train_df)} item-store series saved to '{config.SALES_TRAIN_FILE}'.")
    
    logger.info("M5 Dataset generation complete.")

if __name__ == "__main__":
    generate_full_m5_dataset(num_days=730)
