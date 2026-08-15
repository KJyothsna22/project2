"""
Reusable Streamlit UI Components & Plotly Chart Builders
"""

from typing import Optional, List
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: str = "positive",
    help_text: Optional[str] = None
) -> None:
    """Renders a modern glassmorphic KPI metric tile."""
    delta_html = ""
    if delta:
        delta_class = f"delta-{delta_type}"
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'

    html = f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_risk_badge(risk_level: str) -> str:
    """Returns HTML for color-coded risk badge."""
    level_norm = risk_level.lower()
    if "high" in level_norm:
        cls_name = "risk-high"
    elif "med" in level_norm:
        cls_name = "risk-medium"
    else:
        cls_name = "risk-low"
    return f'<span class="risk-badge {cls_name}">{risk_level}</span>'

def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Renders a clean styled section header."""
    sub_html = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)

def plot_demand_forecast(
    history_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    title: str = "Demand Forecast with Confidence Intervals"
) -> go.Figure:
    """
    Plots historical daily demand along with forecasted demand and shaded 95% confidence bands.
    """
    fig = go.Figure()

    # 1. Historical Demand Line
    if not history_df.empty:
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(history_df["date_str"]),
            y=history_df["sales_units"],
            mode="lines+markers",
            name="Actual Demand",
            line=dict(color="#1e293b", width=2),
            marker=dict(size=4)
        ))

    # 2. Confidence Interval Shading (Upper and Lower bounds)
    if not forecast_df.empty and "confidence_upper" in forecast_df.columns:
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(forecast_df["forecast_date"]),
            y=forecast_df["confidence_upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            name="Upper 95% Bound"
        ))
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(forecast_df["forecast_date"]),
            y=forecast_df["confidence_lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(59, 130, 246, 0.18)",
            name="95% Confidence Interval"
        ))

    # 3. Forecast Demand Line
    if not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(forecast_df["forecast_date"]),
            y=forecast_df["forecast_demand"],
            mode="lines+markers",
            name="Forecast Demand",
            line=dict(color="#3b82f6", width=3, dash="dash"),
            marker=dict(size=6, color="#2563eb")
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Plus Jakarta Sans", color="#0f172a")),
        xaxis=dict(title="Date", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Units Demanded", showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def plot_category_breakdown(cat_df: pd.DataFrame) -> go.Figure:
    """Plots category revenue share donut chart."""
    fig = px.pie(
        cat_df,
        names="cat_id",
        values="total_revenue",
        hole=0.55,
        color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig

def plot_store_comparison(store_df: pd.DataFrame) -> go.Figure:
    """Plots store gross revenue bar chart."""
    fig = px.bar(
        store_df,
        x="store_name",
        y="total_gross_revenue",
        color="region",
        text_auto=".2s",
        color_discrete_sequence=["#2563eb", "#059669", "#d97706"]
    )
    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="Gross Revenue ($)", showgrid=True, gridcolor="#f1f5f9"),
        margin=dict(l=30, r=30, t=30, b=40)
    )
    return fig
