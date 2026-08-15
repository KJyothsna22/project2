"""
Page 5: Forecast Accuracy Monitoring & Model Benchmarking
Displays MAE, RMSE, MAPE, and R2 metrics, head-to-head comparison of Prophet vs LightGBM,
residual error distributions, and automated champion model selection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from warehouse.db import WarehouseManager
from dashboard.components import render_metric_card, render_section_header
from utils.helpers import format_number

def render_accuracy_page() -> None:
    """Renders the forecast accuracy benchmarking and model monitoring dashboard."""
    st.markdown("### 🎯 Forecast Accuracy & Machine Learning Benchmarks")
    st.markdown("Continuous evaluation of predictive precision comparing Facebook Prophet (Additive GAM) and LightGBM GBDT models.")

    # 1. Fetch holdout evaluation results
    eval_query = """
    SELECT
        model_used,
        forecast_date,
        item_id,
        store_id,
        actual_demand,
        forecast_demand,
        forecast_error,
        horizon_days
    FROM fact_forecast_results
    WHERE actual_demand IS NOT NULL
    """
    eval_df = WarehouseManager.read_query(eval_query)

    if eval_df.empty:
        st.warning("No holdout evaluation data found in database. Running quick benchmark calculation...")
        return

    # 2. Compute aggregate metrics per model
    models = eval_df["model_used"].unique()
    metrics_summary = []

    for model in models:
        sub = eval_df[eval_df["model_used"] == model]
        y_true = sub["actual_demand"].values
        y_pred = sub["forecast_demand"].values
        
        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        
        non_zero = y_true > 0
        mape = float(np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100) if np.sum(non_zero) > 0 else 0.0
        
        # R2
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - (ss_res / (ss_tot + 1e-8)))

        metrics_summary.append({
            "Model": model,
            "MAE (Units)": round(mae, 2),
            "RMSE (Units)": round(rmse, 2),
            "MAPE (%)": f"{mape:.1f}%",
            "R² Score": round(r2, 3),
            "Evaluated Points": f"{len(sub):,}"
        })

    metrics_df = pd.DataFrame(metrics_summary)
    
    # Identify Champion
    champion_row = metrics_df.sort_values(by="RMSE (Units)").iloc[0]
    champion_name = champion_row["Model"]

    # 3. Champion Model Banner
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e293b, #0f172a); border-radius: 14px; padding: 18px 24px; color: white; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">Automated Production Champion Model</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #60a5fa; margin-top: 4px;">🏆 {champion_name}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.85rem; color: #cbd5e1;">Lowest Out-of-Time RMSE</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #10b981;">{champion_row['RMSE (Units)']} units (MAPE: {champion_row['MAPE (%)']})</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Metric Comparison Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Champion Model MAE", f"{champion_row['MAE (Units)']} units", "Mean Absolute Error", "positive")
    with c2:
        render_metric_card("Champion Model RMSE", f"{champion_row['RMSE (Units)']} units", "Root Mean Squared Error", "positive")
    with c3:
        render_metric_card("Champion Model MAPE", f"{champion_row['MAPE (%)']}", "Percentage Error", "positive")
    with c4:
        render_metric_card("Goodness-of-Fit (R²)", f"{champion_row['R² Score']}", "Variance Explained", "positive")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 5. Head-to-Head Model Comparison Table & Charts
    render_section_header("Prophet vs LightGBM Head-to-Head Scorecard", "Comprehensive accuracy and error tolerance benchmark across all evaluation points")
    col_scorecard, col_bar = st.columns([6, 6])

    with col_scorecard:
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        st.info("💡 **Model Insights**: LightGBM excels at multi-feature interactions (price elasticity, promotions, cross-product momentum), while Prophet captures smooth long-term annual seasonality and calendar event spikes.")

    with col_bar:
        fig_bar = px.bar(
            metrics_df,
            x="Model",
            y=["MAE (Units)", "RMSE (Units)"],
            barmode="group",
            title="Error Comparison by Model (Lower is Better)",
            color_discrete_sequence=["#3b82f6", "#ef4444"]
        )
        fig_bar.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(title=""),
            yaxis=dict(title="Error (Units)", showgrid=True, gridcolor="#f1f5f9"),
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # 6. Residual Error Distribution
    render_section_header("Residual Error Distribution & Diagnostic Plots", "Symmetry and dispersion of prediction residuals (Actual Demand - Forecast Demand)")
    col_hist, col_scatter = st.columns(2)

    with col_hist:
        fig_hist = px.histogram(
            eval_df,
            x="forecast_error",
            color="model_used",
            barmode="overlay",
            title="Residual Error Distribution (Target = 0)",
            nbins=35,
            color_discrete_sequence=["#3b82f6", "#10b981"]
        )
        fig_hist.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(title="Prediction Residual (Actual - Forecast)"),
            yaxis=dict(title="Frequency", showgrid=True, gridcolor="#f1f5f9"),
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_scatter:
        sample_scatter = eval_df.sample(n=min(500, len(eval_df)), random_state=42)
        fig_scatter = px.scatter(
            sample_scatter,
            x="actual_demand",
            y="forecast_demand",
            color="model_used",
            title="Actual vs Predicted Demand Scatter (Ideal = 45° Line)",
            trendline="ols",
            color_discrete_sequence=["#3b82f6", "#10b981"]
        )
        fig_scatter.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(title="Actual Demand (Units)", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Forecast Demand (Units)", showgrid=True, gridcolor="#f1f5f9"),
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
