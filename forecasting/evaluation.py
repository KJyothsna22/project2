"""
Forecast Evaluation & Model Comparison Engine
Calculates:
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- MAPE (Mean Absolute Percentage Error)
- R2 Score
- Automated Champion Model Identification (Prophet vs LightGBM)
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from utils.logger import get_logger

logger = get_logger("evaluation")

class ForecastEvaluator:
    """Computes forecast error metrics and benchmarks models."""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculates MAE, RMSE, MAPE, and R2."""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)

        # Drop NaNs
        mask = (~np.isnan(y_true)) & (~np.isnan(y_pred))
        y_t = y_true[mask]
        y_p = y_pred[mask]

        if len(y_t) == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0, "r2": 0.0}

        mae = float(mean_absolute_error(y_t, y_p))
        rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
        
        # MAPE with epsilon to avoid division by zero
        non_zero_mask = y_t > 0
        if np.sum(non_zero_mask) > 0:
            mape = float(np.mean(np.abs((y_t[non_zero_mask] - y_p[non_zero_mask]) / y_t[non_zero_mask])) * 100)
        else:
            mape = 0.0

        r2 = float(r2_score(y_t, y_p)) if len(y_t) > 1 else 0.0

        return {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "mape": round(mape, 2),
            "r2": round(r2, 3)
        }

    @classmethod
    def compare_models(
        cls,
        prophet_df: pd.DataFrame,
        lgbm_df: pd.DataFrame,
        actual_col: str = "actual_demand",
        pred_col: str = "forecast_demand"
    ) -> Dict[str, Any]:
        """Performs head-to-head comparison between Prophet and LightGBM."""
        prophet_metrics = cls.calculate_metrics(prophet_df[actual_col].values, prophet_df[pred_col].values)
        lgbm_metrics = cls.calculate_metrics(lgbm_df[actual_col].values, lgbm_df[pred_col].values)

        # Champion model selection (based on RMSE and MAE)
        best_model = "LightGBM" if lgbm_metrics["rmse"] <= prophet_metrics["rmse"] else "Prophet"

        logger.info(f"Model Comparison -> Prophet RMSE: {prophet_metrics['rmse']:.2f}, LightGBM RMSE: {lgbm_metrics['rmse']:.2f} => Champion: {best_model}")
        return {
            "champion_model": best_model,
            "prophet": prophet_metrics,
            "lightgbm": lgbm_metrics
        }
