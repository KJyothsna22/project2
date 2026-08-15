"""
ETL Step 4: Quality Checks Runner & Audit Logging
Executes comprehensive validation suite and logs audit metrics to data warehouse.
"""

import json
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import config
from etl.validate import DataValidator
from warehouse.db import WarehouseManager
from utils.logger import get_logger

logger = get_logger("quality_checks")

class QualityCheckRunner:
    """Orchestrates all validation checks and logs audit records."""

    @classmethod
    def run_all_checks(cls, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Executes full test suite across datasets and writes logs."""
        logger.info("Executing comprehensive data quality validation suite...")
        
        calendar_df = datasets["calendar"]
        prices_df = datasets["prices"]
        sales_df = datasets["sales"]
        
        results: List[Dict[str, Any]] = []

        # 1. Calendar Checks
        results.append(DataValidator.check_missing_records(calendar_df, "calendar", ["date_str", "wm_yr_wk", "wday"]))
        results.append(DataValidator.check_duplicate_records(calendar_df, "calendar", ["date_str"]))
        results.append(DataValidator.check_date_completeness(calendar_df))

        # 2. Prices Checks
        results.append(DataValidator.check_missing_records(prices_df, "sell_prices", ["store_id", "item_id", "wm_yr_wk", "sell_price"]))
        results.append(DataValidator.check_duplicate_records(prices_df, "sell_prices", ["store_id", "item_id", "wm_yr_wk"]))
        results.append(DataValidator.check_pricing_integrity(prices_df))

        # 3. Sales Checks
        results.append(DataValidator.check_missing_records(sales_df, "sales", ["item_id", "store_id", "date_str", "sales_units"]))
        results.append(DataValidator.check_duplicate_records(sales_df, "sales", ["item_id", "store_id", "date_str"]))
        results.append(DataValidator.check_sales_outliers(sales_df))

        # Log into warehouse
        log_records = []
        for r in results:
            log_records.append({
                "dataset_name": r["dataset"],
                "check_name": r["check"],
                "status": r["status"],
                "records_evaluated": r["total_records"],
                "failed_records": r["failed_records"],
                "details": r["details"]
            })
            logger.info(f"[{r['status']}] {r['dataset']}.{r['check']} - Failed: {r['failed_records']:,} | {r['details']}")

        log_df = pd.DataFrame(log_records)
        try:
            WarehouseManager.write_dataframe(log_df, "sys_validation_logs", if_exists="append", index=False)
        except Exception as e:
            logger.warning(f"Could not persist validation logs to DB: {e}")

        summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r["status"] == "PASSED"),
            "failed_checks": sum(1 for r in results if r["status"] == "FAILED"),
            "info_checks": sum(1 for r in results if r["status"] == "INFO"),
            "checks": results
        }

        # Save JSON report
        report_path = config.REPORTS_DIR / "data_quality_report.json"
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Data Quality report written to '{report_path}'.")

        return summary
