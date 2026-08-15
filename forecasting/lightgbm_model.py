"""
LightGBM Granular Item-Level Demand Forecaster
Utilizes Gradient Boosted Decision Trees trained on:
- Historical Sales Lags (7, 14, 28, 60 days)
- Rolling Window Statistics (7, 14, 28 day means, 7, 28 day std)
- Sell Price & Price Momentum
- Promotions (SNAP) & Holiday Indicators
- Store, Category, and Department Categorical Features
- Multi-horizon forecast generation (7, 30, 90 days)
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
import config
from utils.logger import get_logger

logger = get_logger("lightgbm_model")

class LightGBMDemandForecaster:
    """Item-Level LightGBM Regressor for retail demand forecasting."""

    FEATURE_COLS = [
        "day_of_week", "day_of_month", "month", "quarter", "is_weekend",
        "is_holiday", "snap_indicator", "sell_price", "price_change_pct",
        "price_rel_to_cat", "sales_lag_7", "sales_lag_14", "sales_lag_28",
        "sales_roll_mean_7", "sales_roll_mean_14", "sales_roll_mean_28",
        "sales_roll_std_7", "sales_roll_std_28", "store_code", "cat_code", "dept_code"
    ]

    def __init__(self, custom_params: Optional[Dict] = None):
        self.params = config.LGBM_PARAMS.copy()
        if custom_params:
            self.params.update(custom_params)
        self.model: Optional[lgb.LGBMRegressor] = None
        self.encoders: Dict[str, LabelEncoder] = {}
        self.residual_std: float = 1.0
        self.fitted: bool = False

    def _encode_categoricals(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Encodes store, category, and department strings to integer codes."""
        df = df.copy()
        for col, code_col in [("store_id", "store_code"), ("cat_id", "cat_code"), ("dept_id", "dept_code")]:
            if col in df.columns:
                if fit:
                    le = LabelEncoder()
                    df[code_col] = le.fit_transform(df[col].astype(str))
                    self.encoders[col] = le
                else:
                    le = self.encoders.get(col)
                    if le is not None:
                        # Handle unseen categories gracefully
                        known_classes = set(le.classes_)
                        safe_series = df[col].astype(str).map(lambda s: s if s in known_classes else le.classes_[0])
                        df[code_col] = le.transform(safe_series)
                    else:
                        df[code_col] = 0
            else:
                df[code_col] = 0
        return df

    def fit(self, train_df: pd.DataFrame, target_col: str = "sales_units") -> "LightGBMDemandForecaster":
        """Trains LightGBM model on feature matrix."""
        logger.info(f"Training LightGBM on {len(train_df):,} samples...")
        df_encoded = self._encode_categoricals(train_df, fit=True)
        
        # Ensure all required features exist
        for col in self.FEATURE_COLS:
            if col not in df_encoded.columns:
                df_encoded[col] = 0.0

        X = df_encoded[self.FEATURE_COLS]
        y = df_encoded[target_col].values

        self.model = lgb.LGBMRegressor(**self.params)
        self.model.fit(X, y)

        preds = self.model.predict(X)
        residuals = y - preds
        self.residual_std = float(np.std(residuals)) if len(residuals) > 1 else 1.0
        self.fitted = True
        logger.info(f"LightGBM training complete. Residual Std Dev: {self.residual_std:.3f}")
        return self

    def predict(self, feature_df: pd.DataFrame, confidence_level: float = 0.95) -> pd.DataFrame:
        """Generates predictions with uncertainty intervals."""
        if not self.fitted or self.model is None:
            raise ValueError("Model is not fitted.")

        df_encoded = self._encode_categoricals(feature_df, fit=False)
        for col in self.FEATURE_COLS:
            if col not in df_encoded.columns:
                df_encoded[col] = 0.0

        X = df_encoded[self.FEATURE_COLS]
        preds = self.model.predict(X)
        preds = np.maximum(0, preds)

        z = 1.96 if confidence_level >= 0.95 else 1.28
        lower = np.maximum(0, preds - z * self.residual_std)
        upper = preds + z * self.residual_std

        result = feature_df.copy()
        result["forecast_demand"] = np.round(preds, 2)
        result["confidence_lower"] = np.round(lower, 2)
        result["confidence_upper"] = np.round(upper, 2)
        result["model_used"] = "LightGBM"
        return result

    def get_feature_importances(self) -> pd.DataFrame:
        """Returns sorted feature importance dataframe."""
        if not self.fitted or self.model is None:
            return pd.DataFrame()
        importances = self.model.feature_importances_
        return pd.DataFrame({
            "feature": self.FEATURE_COLS,
            "importance": importances
        }).sort_values(by="importance", ascending=False).reset_index(drop=True)
