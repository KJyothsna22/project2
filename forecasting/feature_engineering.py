"""
Feature Engineering Engine for Time-Series Demand Forecasting
Generates:
- Temporal Features: day of week, day of month, month, quarter, year, is_weekend
- Event / Promotion Features: holiday_indicator, snap_indicator, event_type
- Lag Features: lag_7, lag_14, lag_28, lag_60
- Rolling Window Features: rolling_mean_7, rolling_mean_14, rolling_mean_28, rolling_std_7, rolling_std_28
- Pricing Features: price_change_pct, price_diff_cat_avg, relative_price
- Hierarchical Momentum: store_daily_mean, cat_daily_mean
"""

from typing import List, Tuple, Optional, Dict
import numpy as np
import pandas as pd
import config
from warehouse.db import WarehouseManager
from utils.logger import get_logger

logger = get_logger("feature_engineering")

class FeatureEngineer:
    """Computes high-signal tabular and time-series features from normalized daily sales data."""

    @classmethod
    def load_base_data(cls) -> pd.DataFrame:
        """Loads daily sales joined with calendar and pricing from data warehouse."""
        query = """
        SELECT
            s.id,
            s.item_id,
            s.dept_id,
            s.cat_id,
            s.store_id,
            s.state_id,
            s.date_str,
            s.sales_units,
            c.wm_yr_wk,
            c.weekday,
            c.wday,
            c.month,
            c.year,
            c.event_name_1,
            c.event_type_1,
            c.is_holiday,
            CASE
                WHEN s.state_id = 'CA' THEN c.snap_CA
                WHEN s.state_id = 'TX' THEN c.snap_TX
                WHEN s.state_id = 'WI' THEN c.snap_WI
                ELSE 0
            END AS snap_indicator,
            COALESCE(p.sell_price, 5.00) AS sell_price
        FROM fact_sales s
        INNER JOIN dim_calendar c ON s.date_str = c.date_str
        LEFT JOIN fact_prices p ON s.store_id = p.store_id
                               AND s.item_id = p.item_id
                               AND c.wm_yr_wk = p.wm_yr_wk
        ORDER BY s.item_id, s.store_id, s.date_str ASC
        """
        logger.info("Loading base time-series dataset from data warehouse...")
        df = WarehouseManager.read_query(query)
        df["date"] = pd.to_datetime(df["date_str"])
        return df

    @classmethod
    def build_features(cls, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Generates all temporal, event, lag, rolling, pricing, and hierarchical features."""
        if df is None:
            df = cls.load_base_data()

        logger.info(f"Engineering features for {len(df):,} records...")
        df = df.sort_values(by=["item_id", "store_id", "date"]).copy()

        # 1. Temporal Features
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_month"] = df["date"].dt.day
        df["quarter"] = df["date"].dt.quarter
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["day_of_year"] = df["date"].dt.dayofyear
        # Cyclical month encodings
        df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)

        # 2. Lag Features (grouped by item_id and store_id)
        grouped = df.groupby(["item_id", "store_id"])["sales_units"]
        for lag in [7, 14, 28, 60]:
            df[f"sales_lag_{lag}"] = grouped.shift(lag)

        # 3. Rolling Window Statistics (shifted by 1 to prevent data leakage)
        for window in [7, 14, 28]:
            df[f"sales_roll_mean_{window}"] = (
                df.groupby(["item_id", "store_id"])["sales_units"]
                .transform(lambda x: x.shift(1).rolling(window=window, min_periods=3).mean())
            )
        
        for window in [7, 28]:
            df[f"sales_roll_std_{window}"] = (
                df.groupby(["item_id", "store_id"])["sales_units"]
                .transform(lambda x: x.shift(1).rolling(window=window, min_periods=3).std())
            )

        # 4. Pricing Dynamics
        df["price_lag_7"] = df.groupby(["item_id", "store_id"])["sell_price"].shift(7)
        df["price_change_pct"] = (
            (df["sell_price"] - df["price_lag_7"]) / df["price_lag_7"].replace(0, np.nan)
        ).fillna(0.0)

        # Relative price to category mean
        cat_avg_price = df.groupby(["cat_id", "date_str"])["sell_price"].transform("mean")
        df["price_rel_to_cat"] = (df["sell_price"] / cat_avg_price).fillna(1.0)

        # 5. Hierarchical Momentum Metrics (Store-level and Category-level sales velocity)
        df["store_sales_momentum_7"] = (
            df.groupby(["store_id", "date_str"])["sales_units"]
            .transform("sum")
        )
        df["cat_sales_momentum_7"] = (
            df.groupby(["cat_id", "date_str"])["sales_units"]
            .transform("sum")
        )

        # 6. Clean nulls caused by shifting
        df = df.fillna(0.0)

        logger.info(f"Feature engineering complete. Total shape: {df.shape}")
        # Save feature dataset to parquet
        df.to_parquet(config.FEATURE_DATASET_FILE, index=False)
        return df

if __name__ == "__main__":
    df_feat = FeatureEngineer.build_features()
    print("Features engineered successfully! Columns:", len(df_feat.columns))
