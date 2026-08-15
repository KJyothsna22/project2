"""
Master ETL Pipeline Orchestrator
Executes: Extract -> Clean -> Validate -> Quality Checks Audit -> Warehouse Load
"""

import time
from typing import Dict, Any
from etl.extract import DataExtractor
from etl.clean import DataCleaner
from etl.quality_checks import QualityCheckRunner
from etl.load import WarehouseLoader
from utils.logger import get_logger

logger = get_logger("etl_pipeline")

class ETLPipeline:
    """Master controller for end-to-end retail data ingestion and validation."""

    @classmethod
    def run(cls) -> Dict[str, Any]:
        """Runs complete ETL pipeline."""
        start_time = time.time()
        logger.info("================ STARTING ETL PIPELINE ================")

        # 1. Extract
        raw_data = DataExtractor.load_raw_data()

        # 2. Clean
        cleaned_data = DataCleaner.run_cleaning_pipeline(raw_data)

        # 3. Validate & Quality Checks
        quality_summary = QualityCheckRunner.run_all_checks(cleaned_data)

        # 4. Load into Data Warehouse
        WarehouseLoader.run_loading_pipeline(cleaned_data)

        duration = time.time() - start_time
        logger.info(f"================ ETL PIPELINE COMPLETED IN {duration:.2f}s ================")
        return {
            "status": "SUCCESS",
            "duration_seconds": duration,
            "quality_summary": quality_summary
        }

if __name__ == "__main__":
    result = ETLPipeline.run()
    print("ETL Status:", result["status"], f"Time: {result['duration_seconds']:.2f}s")
