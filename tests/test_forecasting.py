"""
Unit Tests for Time-Series Forecasting Models & Evaluation
"""

import pandas as pd
import numpy as np
import pytest
from forecasting.prophet_model import ProphetDemandForecaster
from forecasting.lightgbm_model import LightGBMDemandForecaster
from forecasting.evaluation import ForecastEvaluator

def test_prophet_model_fit_predict():
    dates = pd.date_range("2023-01-01", periods=60, freq="D")
    df = pd.DataFrame({
        "item_id": ["ITEM_001"] * 60,
        "store_id": ["CA_1"] * 60,
        "date_str": dates.strftime("%Y-%m-%d"),
        "sales_units": np.random.poisson(lam=10, size=60),
        "is_holiday": [0] * 60,
        "snap_indicator": [1 if d.day <= 10 else 0 for d in dates],
        "sell_price": [4.99] * 60
    })

    model = ProphetDemandForecaster()
    model.fit(df, target_col="sales_units")
    assert model.fitted is True

    preds = model.predict(df)
    assert len(preds) == 60
    assert "forecast_demand" in preds.columns
    assert "confidence_lower" in preds.columns
    assert "confidence_upper" in preds.columns
    assert (preds["forecast_demand"] >= 0).all()

def test_forecast_evaluator():
    y_true = np.array([10.0, 20.0, 30.0, 40.0])
    y_pred = np.array([12.0, 18.0, 33.0, 38.0])
    metrics = ForecastEvaluator.calculate_metrics(y_true, y_pred)
    assert metrics["mae"] == 2.25
    assert metrics["rmse"] > 0
    assert metrics["mape"] > 0
    assert metrics["r2"] > 0.9
