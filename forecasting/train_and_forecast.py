"""
Master Training, Forecasting, and Forecast Storage Pipeline
Trains Prophet and LightGBM models, evaluates holdout performance, generates multi-horizon
forecasts (7, 30, 90 days), and persists predictions into data warehouse `fact_forecast_results`.
"""

import time
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import config
from warehouse.db import WarehouseManager
from forecasting.feature_engineering import FeatureEngineer
from forecasting.prophet_model import ProphetDemandForecaster
from forecasting.lightgbm_model import LightGBMDemandForecaster
from forecasting.evaluation import ForecastEvaluator
from utils.logger import get_logger

logger = get_logger("train_and_forecast")

class ForecastingPipeline:
    """End-to-End Forecaster Orchestrator."""

    @classmethod
    def run(cls, test_days: int = 30) -> Dict[str, Any]:
        """Executes feature engineering, model training, evaluation, and forecast storage."""
        start_time = time.time()
        logger.info("================ STARTING DEMAND FORECASTING PIPELINE ================")

        # 1. Feature Engineering
        feature_df = FeatureEngineer.build_features()

        # 2. Train / Holdout Test Split
        unique_dates = sorted(feature_df["date_str"].unique())
        split_date = unique_dates[-test_days]
        logger.info(f"Splitting dataset: Train <= {split_date} | Holdout Test > {split_date}")

        train_df = feature_df[feature_df["date_str"] <= split_date].copy()
        test_df = feature_df[feature_df["date_str"] > split_date].copy()

        # 3. Train LightGBM
        lgbm_forecaster = LightGBMDemandForecaster()
        lgbm_forecaster.fit(train_df, target_col="sales_units")
        lgbm_test_preds = lgbm_forecaster.predict(test_df)
        lgbm_test_preds["actual_demand"] = test_df["sales_units"].values
        lgbm_test_preds["forecast_error"] = lgbm_test_preds["actual_demand"] - lgbm_test_preds["forecast_demand"]
        lgbm_test_preds["horizon_days"] = test_days

        # 4. Train Prophet per item-store sample series
        prophet_test_rows = []
        unique_series = train_df[["item_id", "store_id"]].drop_duplicates()
        
        logger.info(f"Training Prophet on {len(unique_series)} item-store series...")
        for _, series in unique_series.iterrows():
            item_id = series["item_id"]
            store_id = series["store_id"]
            
            sub_train = train_df[(train_df["item_id"] == item_id) & (train_df["store_id"] == store_id)]
            sub_test = test_df[(test_df["item_id"] == item_id) & (test_df["store_id"] == store_id)]
            
            if len(sub_train) < 14 or len(sub_test) == 0:
                continue
                
            p_model = ProphetDemandForecaster()
            p_model.fit(sub_train, target_col="sales_units")
            p_pred = p_model.predict(sub_test)
            p_pred["actual_demand"] = sub_test["sales_units"].values
            p_pred["forecast_error"] = p_pred["actual_demand"] - p_pred["forecast_demand"]
            p_pred["horizon_days"] = test_days
            prophet_test_rows.append(p_pred)

        prophet_test_df = pd.concat(prophet_test_rows, ignore_index=True) if prophet_test_rows else pd.DataFrame()

        # 5. Evaluate and Compare
        comparison = ForecastEvaluator.compare_models(
            prophet_test_df, lgbm_test_preds, actual_col="actual_demand", pred_col="forecast_demand"
        )
        logger.info(f"Model Evaluation Complete. Champion Model: {comparison['champion_model']}")

        # 6. Generate Forward Multi-Horizon Forecasts (7, 30, 90 Days)
        calendar_df = WarehouseManager.read_query("SELECT * FROM dim_calendar")
        last_date = pd.to_datetime(unique_dates[-1])

        forward_forecast_records = []
        # Create forward feature rows for LightGBM
        for horizon in config.DEFAULT_HORIZONS:
            logger.info(f"Generating forward {horizon}-day forecast across all products & stores...")
            future_dates = [(last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, horizon + 1)]
            
            for _, series in unique_series.iterrows():
                item_id = series["item_id"]
                store_id = series["store_id"]
                recent_history = feature_df[(feature_df["item_id"] == item_id) & (feature_df["store_id"] == store_id)].iloc[-28:]
                
                avg_recent_sales = recent_history["sales_units"].mean()
                std_recent_sales = recent_history["sales_units"].std()
                last_price = recent_history["sell_price"].iloc[-1]
                dept_id = recent_history["dept_id"].iloc[-1]
                cat_id = recent_history["cat_id"].iloc[-1]

                for d_str in future_dates:
                    dt = pd.to_datetime(d_str)
                    wday = dt.isoweekday() % 7 + 1
                    is_weekend = 1 if wday in [1, 2] else 0
                    
                    cal_row = calendar_df[calendar_df["date_str"] == d_str]
                    is_holiday = int(cal_row["is_holiday"].values[0]) if not cal_row.empty else 0
                    snap_col = f"snap_{store_id.split('_')[0]}"
                    snap_ind = int(cal_row[snap_col].values[0]) if (not cal_row.empty and snap_col in cal_row.columns) else 0

                    forward_forecast_records.append({
                        "item_id": item_id,
                        "store_id": store_id,
                        "dept_id": dept_id,
                        "cat_id": cat_id,
                        "date_str": d_str,
                        "forecast_date": d_str,
                        "day_of_week": dt.dayofweek,
                        "day_of_month": dt.day,
                        "month": dt.month,
                        "quarter": dt.quarter,
                        "is_weekend": is_weekend,
                        "is_holiday": is_holiday,
                        "snap_indicator": snap_ind,
                        "sell_price": last_price,
                        "price_change_pct": 0.0,
                        "price_rel_to_cat": 1.0,
                        "sales_lag_7": avg_recent_sales,
                        "sales_lag_14": avg_recent_sales,
                        "sales_lag_28": avg_recent_sales,
                        "sales_roll_mean_7": avg_recent_sales,
                        "sales_roll_mean_14": avg_recent_sales,
                        "sales_roll_mean_28": avg_recent_sales,
                        "sales_roll_std_7": std_recent_sales,
                        "sales_roll_std_28": std_recent_sales,
                        "horizon_days": horizon
                    })

        forward_features_df = pd.DataFrame(forward_forecast_records)
        forward_predictions = lgbm_forecaster.predict(forward_features_df)
        forward_predictions["actual_demand"] = np.nan
        forward_predictions["forecast_error"] = np.nan

        # 7. Persist to Fact Table: fact_forecast_results
        forecast_cols = [
            "forecast_date", "item_id", "store_id", "model_used",
            "actual_demand", "forecast_demand", "confidence_lower",
            "confidence_upper", "forecast_error", "horizon_days"
        ]

        # Combine holdout evaluation predictions and future forecasts
        eval_storage_lgbm = lgbm_test_preds.rename(columns={"date_str": "forecast_date"})[forecast_cols]
        eval_storage_prophet = prophet_test_df.rename(columns={"date_str": "forecast_date"})[forecast_cols]
        forward_storage = forward_predictions[forecast_cols]

        combined_forecasts = pd.concat([eval_storage_lgbm, eval_storage_prophet, forward_storage], ignore_index=True)
        WarehouseManager.write_dataframe(combined_forecasts, "fact_forecast_results", if_exists="replace")

        total_time = time.time() - start_time
        logger.info(f"================ DEMAND FORECASTING COMPLETED IN {total_time:.2f}s ================")

        return {
            "duration_seconds": total_time,
            "comparison": comparison,
            "total_forecast_rows": len(combined_forecasts)
        }

if __name__ == "__main__":
    ForecastingPipeline.run(test_days=30)
