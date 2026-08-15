"""
ETL Step 3: Data Quality Validation & Anomaly Detection
Checks for missing values, duplicates, pricing anomalies, sales outliers, and date sequence continuity.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from utils.logger import get_logger

logger = get_logger("etl_validate")

class DataValidator:
    """Executes rule-based data quality checks across cleaned datasets."""

    @classmethod
    def check_missing_records(cls, df: pd.DataFrame, dataset_name: str, key_cols: List[str]) -> Dict[str, Any]:
        """Checks for nulls or missing entries in mandatory key columns."""
        null_counts = df[key_cols].isna().sum().to_dict()
        total_nulls = sum(null_counts.values())
        status = "PASSED" if total_nulls == 0 else "FAILED"
        return {
            "dataset": dataset_name,
            "check": "Missing Key Records",
            "status": status,
            "total_records": len(df),
            "failed_records": total_nulls,
            "details": f"Null counts per column: {null_counts}"
        }

    @classmethod
    def check_duplicate_records(cls, df: pd.DataFrame, dataset_name: str, unique_subset: List[str]) -> Dict[str, Any]:
        """Checks for duplicate records based on primary key constraints."""
        duplicate_count = int(df.duplicated(subset=unique_subset).sum())
        status = "PASSED" if duplicate_count == 0 else "FAILED"
        return {
            "dataset": dataset_name,
            "check": "Duplicate Key Records",
            "status": status,
            "total_records": len(df),
            "failed_records": duplicate_count,
            "details": f"Duplicates on {unique_subset}: {duplicate_count}"
        }

    @classmethod
    def check_pricing_integrity(cls, prices_df: pd.DataFrame) -> Dict[str, Any]:
        """Validates sell prices are positive, non-null, and within standard commercial thresholds."""
        invalid_count = int(((prices_df["sell_price"] <= 0) | (prices_df["sell_price"] > 1000.0) | (prices_df["sell_price"].isna())).sum())
        status = "PASSED" if invalid_count == 0 else "FAILED"
        return {
            "dataset": "sell_prices",
            "check": "Pricing Integrity",
            "status": status,
            "total_records": len(prices_df),
            "failed_records": invalid_count,
            "details": f"Records with price <= 0 or > $1000: {invalid_count}"
        }

    @classmethod
    def check_sales_outliers(cls, sales_df: pd.DataFrame) -> Dict[str, Any]:
        """Detects sales unit anomalies using IQR method."""
        q75 = sales_df["sales_units"].quantile(0.75)
        q25 = sales_df["sales_units"].quantile(0.25)
        iqr = q75 - q25
        upper_bound = q75 + 4.0 * iqr
        
        outliers = int((sales_df["sales_units"] > upper_bound).sum())
        return {
            "dataset": "sales",
            "check": "Sales Outlier Detection",
            "status": "INFO",
            "total_records": len(sales_df),
            "failed_records": outliers,
            "details": f"Sales units > {upper_bound:.1f} ({outliers} high spikes flagged for awareness)"
        }

    @classmethod
    def check_date_completeness(cls, calendar_df: pd.DataFrame) -> Dict[str, Any]:
        """Verifies date continuity with 0 missing intermediate days."""
        dates = pd.to_datetime(calendar_df["date_str"]).sort_values()
        expected_days = (dates.max() - dates.min()).days + 1
        actual_days = len(dates.unique())
        missing_days = expected_days - actual_days
        status = "PASSED" if missing_days == 0 else "FAILED"
        return {
            "dataset": "calendar",
            "check": "Date Continuity & Completeness",
            "status": status,
            "total_records": actual_days,
            "failed_records": max(0, missing_days),
            "details": f"Date span {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}, missing days: {missing_days}"
        }
