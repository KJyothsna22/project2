"""
ETL Step 1: Data Extraction
Reads raw M5 CSV datasets (or triggers high-fidelity generator if raw files are missing).
"""

from pathlib import Path
from typing import Tuple, Dict
import pandas as pd
import config
from data.sample_generator import generate_full_m5_dataset
from utils.logger import get_logger

logger = get_logger("etl_extract")

class DataExtractor:
    """Extracts raw files from local filesystem or generates realistic sample dataset."""

    @classmethod
    def ensure_data_exists(cls) -> None:
        """Verifies raw CSV files exist; generates them if absent."""
        if not (config.SALES_TRAIN_FILE.exists() and config.CALENDAR_FILE.exists() and config.SELL_PRICES_FILE.exists()):
            logger.warning("Raw M5 files not found in data/raw/. Generating realistic dataset...")
            generate_full_m5_dataset(num_days=730)

    @classmethod
    def load_raw_data(cls) -> Dict[str, pd.DataFrame]:
        """
        Loads raw sales, calendar, and sell prices datasets into memory.
        Returns dictionary of raw dataframes.
        """
        cls.ensure_data_exists()
        
        logger.info(f"Loading calendar dataset from '{config.CALENDAR_FILE}'...")
        calendar_df = pd.read_csv(config.CALENDAR_FILE)
        logger.info(f"Loaded calendar: {calendar_df.shape[0]:,} rows, {calendar_df.shape[1]} columns.")

        logger.info(f"Loading prices dataset from '{config.SELL_PRICES_FILE}'...")
        prices_df = pd.read_csv(config.SELL_PRICES_FILE)
        logger.info(f"Loaded sell_prices: {prices_df.shape[0]:,} rows, {prices_df.shape[1]} columns.")

        logger.info(f"Loading sales dataset from '{config.SALES_TRAIN_FILE}'...")
        sales_df = pd.read_csv(config.SALES_TRAIN_FILE)
        logger.info(f"Loaded sales_train: {sales_df.shape[0]:,} rows, {sales_df.shape[1]} columns.")

        return {
            "calendar": calendar_df,
            "prices": prices_df,
            "sales": sales_df
        }

if __name__ == "__main__":
    extractor = DataExtractor()
    dfs = extractor.load_raw_data()
    print({k: v.shape for k, v in dfs.items()})
