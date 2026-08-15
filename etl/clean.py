"""
ETL Step 2: Data Cleaning & Transformation
Implements:
- Missing value imputation and null handling
- Duplicate record removal
- Invalid date detection & normalization
- Invalid / negative price detection and correction
- Negative sales validation
- Data type casting and wide-to-long normalization
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
import config
from utils.logger import get_logger

logger = get_logger("etl_clean")

class DataCleaner:
    """Cleans and standardizes raw M5 datasets."""

    @classmethod
    def clean_calendar(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans calendar dataframe."""
        logger.info("Cleaning calendar data...")
        df = df.copy()

        # 1. Deduplicate
        initial_len = len(df)
        df = df.drop_duplicates(subset=["date"])
        if len(df) < initial_len:
            logger.info(f"Removed {initial_len - len(df)} duplicate calendar rows.")

        # 2. Date parsing & validation
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Found {invalid_dates} invalid dates in calendar; dropping.")
            df = df.dropna(subset=["date"])
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

        # 3. Data type conversions
        df["wm_yr_wk"] = pd.to_numeric(df["wm_yr_wk"], errors="coerce").fillna(0).astype(int)
        df["wday"] = pd.to_numeric(df["wday"], errors="coerce").fillna(1).astype(int)
        df["month"] = pd.to_numeric(df["month"], errors="coerce").fillna(1).astype(int)
        df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(2022).astype(int)

        # 4. Fill event nulls
        for col in ["event_name_1", "event_type_1", "event_name_2", "event_type_2"]:
            if col in df.columns:
                df[col] = df[col].fillna("None").astype(str)

        # 5. SNAP indicators
        for snap_col in ["snap_CA", "snap_TX", "snap_WI"]:
            if snap_col in df.columns:
                df[snap_col] = pd.to_numeric(df[snap_col], errors="coerce").fillna(0).astype(int)

        # Holiday indicator
        df["is_holiday"] = ((df["event_name_1"] != "None") & (df["event_name_1"] != "")).astype(int)

        logger.info(f"Cleaned calendar dataset: {len(df):,} valid rows.")
        return df

    @classmethod
    def clean_prices(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans weekly sell_prices dataframe."""
        logger.info("Cleaning sell_prices data...")
        df = df.copy()

        # 1. Deduplicate by store_id, item_id, wm_yr_wk
        initial_len = len(df)
        df = df.drop_duplicates(subset=["store_id", "item_id", "wm_yr_wk"])
        if len(df) < initial_len:
            logger.info(f"Removed {initial_len - len(df)} duplicate price records.")

        # 2. String standardization
        df["store_id"] = df["store_id"].astype(str).str.strip()
        df["item_id"] = df["item_id"].astype(str).str.strip()
        df["wm_yr_wk"] = pd.to_numeric(df["wm_yr_wk"], errors="coerce").fillna(0).astype(int)

        # 3. Numeric price validation (price must be positive)
        df["sell_price"] = pd.to_numeric(df["sell_price"], errors="coerce")
        invalid_prices = (df["sell_price"].isna()) | (df["sell_price"] <= 0)
        if invalid_prices.sum() > 0:
            logger.warning(f"Detected {invalid_prices.sum()} invalid prices <= 0 or NaN. Imputing with median.")
            median_price = df.loc[~invalid_prices, "sell_price"].median()
            df["sell_price"] = df["sell_price"].fillna(median_price)
            df.loc[df["sell_price"] <= 0, "sell_price"] = median_price

        df["sell_price"] = df["sell_price"].round(2)
        logger.info(f"Cleaned sell_prices dataset: {len(df):,} valid rows.")
        return df

    @classmethod
    def clean_and_melt_sales(
        cls, sales_df: pd.DataFrame, calendar_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Cleans sales dataset and unpivots from wide (d_1..d_n) to normalized long format.
        Maps d_x column names to actual date_str.
        """
        logger.info("Normalizing and cleaning sales data (wide to long format)...")
        sales_df = sales_df.copy()

        # Deduplicate
        sales_df = sales_df.drop_duplicates(subset=["id"])

        # Identify day columns
        id_vars = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
        day_cols = [c for c in sales_df.columns if c.startswith("d_")]

        logger.info(f"Unpivoting {len(sales_df):,} series across {len(day_cols)} days...")
        melted_df = pd.melt(
            sales_df,
            id_vars=id_vars,
            value_vars=day_cols,
            var_name="d",
            value_name="sales_units"
        )

        # Data type casting and negative sales validation
        melted_df["sales_units"] = pd.to_numeric(melted_df["sales_units"], errors="coerce").fillna(0)
        negative_count = (melted_df["sales_units"] < 0).sum()
        if negative_count > 0:
            logger.warning(f"Found {negative_count} negative sales values; clipping to 0.")
            melted_df["sales_units"] = melted_df["sales_units"].clip(lower=0)
        melted_df["sales_units"] = melted_df["sales_units"].astype(int)

        # Merge with calendar to get exact calendar dates
        d_to_date = calendar_df.set_index("d")["date_str"].to_dict()
        melted_df["date_str"] = melted_df["d"].map(d_to_date)
        melted_df = melted_df.dropna(subset=["date_str"])

        logger.info(f"Completed sales normalization: {len(melted_df):,} daily records.")
        return melted_df

    @classmethod
    def run_cleaning_pipeline(cls, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Runs end-to-end cleaning for all datasets and saves to processed parquet."""
        cleaned_calendar = cls.clean_calendar(raw_data["calendar"])
        cleaned_prices = cls.clean_prices(raw_data["prices"])
        cleaned_sales = cls.clean_and_melt_sales(raw_data["sales"], cleaned_calendar)

        # Persist processed datasets
        cleaned_calendar.to_parquet(config.CLEANED_CALENDAR_FILE, index=False)
        cleaned_prices.to_parquet(config.CLEANED_PRICES_FILE, index=False)
        cleaned_sales.to_parquet(config.CLEANED_SALES_FILE, index=False)
        logger.info("Saved cleaned datasets to data/processed/.")

        return {
            "calendar": cleaned_calendar,
            "prices": cleaned_prices,
            "sales": cleaned_sales
        }
