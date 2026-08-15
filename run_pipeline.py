"""
Master One-Click End-to-End Execution CLI
Executes the complete pipeline:
  1. ETL Pipeline & Data Validation
  2. dbt Data Transformations & Business Marts
  3. Machine Learning Forecasting (Prophet & LightGBM)
  4. Inventory Optimization & Replenishment Planning
  5. Executive Reporting Artifacts Generation
"""

import time
import argparse
from etl.pipeline import ETLPipeline
from dbt_project.dbt_runner import DBTRunner
from forecasting.train_and_forecast import ForecastingPipeline
from inventory.replenishment import ReplenishmentPlanner
from reports.report_generator import ReportGenerator
from utils.logger import get_logger

logger = get_logger("run_pipeline")

def run_full_platform_pipeline(test_days: int = 30) -> None:
    """Executes all stages of the platform sequentially."""
    overall_start = time.time()
    logger.info("================================================================================")
    logger.info("  RETAIL DEMAND FORECASTING & INVENTORY OPTIMIZATION PLATFORM - MASTER PIPELINE ")
    logger.info("================================================================================")

    # 1. ETL Pipeline
    logger.info("\n>>> STAGE 1: INGESTION, DATA CLEANING & QUALITY AUDIT")
    etl_results = ETLPipeline.run()

    # 2. dbt Transformations
    logger.info("\n>>> STAGE 2: dbt ANALYTICAL TRANSFORMATIONS & DATA MARTS")
    dbt_results = DBTRunner.run_transformations()

    # 3. ML Demand Forecasting
    logger.info("\n>>> STAGE 3: MACHINE LEARNING FORECASTING (PROPHET & LIGHTGBM)")
    ml_results = ForecastingPipeline.run(test_days=test_days)

    # 4. Inventory Optimization
    logger.info("\n>>> STAGE 4: INVENTORY OPTIMIZATION & REPLENISHMENT ENGINE")
    inv_results = ReplenishmentPlanner.generate_all_recommendations()

    # 5. Executive Reports Generation
    logger.info("\n>>> STAGE 5: REPORT GENERATION & COMPLIANCE ARTIFACTS")
    excel_bytes = ReportGenerator.generate_excel_report()
    pdf_bytes = ReportGenerator.generate_pdf_report()
    logger.info("Generated Excel (.xlsx) and PDF Executive Briefing reports successfully.")

    total_time = time.time() - overall_start
    logger.info("================================================================================")
    logger.info(f"  ALL PIPELINES EXECUTED SUCCESSFULLY IN {total_time:.2f}s")
    logger.info(f"  - Cleaned & Processed Records: {etl_results['quality_summary']['checks'][2]['total_records']:,} calendar days")
    logger.info(f"  - dbt Models Built: {dbt_results['models_executed']}")
    logger.info(f"  - Forecasting Champion Model: {ml_results['comparison']['champion_model']}")
    logger.info(f"  - Inventory SKUs Optimized: {len(inv_results):,}")
    logger.info("================================================================================")
    logger.info("\nTo launch the interactive Streamlit Dashboard, run:")
    logger.info("  python -m streamlit run app.py\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete Retail Demand & Inventory Platform pipeline.")
    parser.add_argument("--test-days", type=int, default=30, help="Number of holdout test days for forecast evaluation.")
    args = parser.parse_args()
    
    run_full_platform_pipeline(test_days=args.test_days)
