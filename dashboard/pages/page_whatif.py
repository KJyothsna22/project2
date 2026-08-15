"""
Page 4: What-If Scenario Analysis & Supply Chain Simulation
Enables dynamic interactive simulation of:
- Price elasticity adjustments (-30% to +30%)
- Marketing & Promotional Campaigns (5% to 50% uplift)
- Holiday Demand Surges (10% to 100% surge)
- Supplier Lead Time Delays (+1 to +21 days)
Displays predicted impacts on Demand, Revenue, Working Capital, and Stockout Risk in real-time.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from warehouse.db import WarehouseManager
from dashboard.components import render_metric_card, render_section_header
from utils.helpers import format_currency, format_number, format_percentage

def render_whatif_page() -> None:
    """Renders the interactive scenario simulation engine."""
    st.markdown("### 🧪 What-If Scenario Simulation Engine")
    st.markdown("Stress-test demand elasticity, marketing promotions, holiday spikes, and supplier disruptions on retail inventory and financial capital.")

    # 1. Fetch baseline inventory and demand data
    inv_df = WarehouseManager.read_query("SELECT * FROM fact_inventory_recommendations")
    if inv_df.empty:
        st.warning("No baseline data available for scenario simulation.")
        return

    # 2. Interactive Scenario Controls Sidebar/Columns
    st.markdown("#### 🎛️ Simulation Parameters")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        price_change_pct = st.slider("🏷️ Price Adjustment (%)", min_value=-30, max_value=30, value=0, step=5, help="Estimated retail price elasticity of demand ~ -1.2")

    with c2:
        promo_uplift_pct = st.slider("📢 Promotion Campaign Uplift (%)", min_value=0, max_value=50, value=0, step=5, help="Marketing campaign customer acquisition uplift")

    with c3:
        holiday_surge_pct = st.slider("🎉 Holiday Surge Multiplier (%)", min_value=0, max_value=100, value=0, step=10, help="Anticipated peak holiday or event foot-traffic lift")

    with c4:
        lead_time_delay_days = st.slider("🚢 Supply Lead Time Delay (Days)", min_value=0, max_value=21, value=0, step=1, help="Port congestion or vendor fulfillment delay")

    st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # 3. Mathematical Simulation Logic
    # Price Elasticity: e = -1.2
    # % Change in Demand = Price Elasticity * % Change in Price + Promo Uplift + Holiday Surge
    elasticity_factor = -1.2 * (price_change_pct / 100.0)
    total_demand_multiplier = max(0.1, 1.0 + elasticity_factor + (promo_uplift_pct / 100.0) + (holiday_surge_pct / 100.0))
    price_multiplier = 1.0 + (price_change_pct / 100.0)

    # Baseline aggregates
    baseline_avg_demand = float(inv_df["average_daily_demand"].sum())
    baseline_safety_stock = int(inv_df["safety_stock"].sum())
    baseline_reorder_qty = int(inv_df["recommended_order_qty"].sum())
    baseline_daily_revenue = float((inv_df["average_daily_demand"] * 5.50).sum())
    baseline_order_cost = float(inv_df["estimated_order_cost"].sum())

    # Simulated aggregates
    sim_avg_demand = baseline_avg_demand * total_demand_multiplier
    sim_daily_revenue = baseline_daily_revenue * total_demand_multiplier * price_multiplier

    # Lead time impact on safety stock: SS ~ Z * sigma * sqrt(LT + delay)
    base_lt = 7
    sim_lt = base_lt + lead_time_delay_days
    lt_factor = np.sqrt(sim_lt / base_lt)
    sim_safety_stock = int(round(baseline_safety_stock * lt_factor * np.sqrt(total_demand_multiplier)))
    
    # Reorder requirements under scenario
    sim_reorder_qty = int(round(max(0, (sim_avg_demand * sim_lt) + sim_safety_stock - inv_df["current_inventory"].sum())))
    sim_order_cost = sim_reorder_qty * 5.00

    # Stockout risk shift
    base_stockout_risk = float(inv_df["stockout_risk_pct"].mean())
    sim_stockout_risk = min(100.0, max(0.0, base_stockout_risk * total_demand_multiplier * (1.0 + lead_time_delay_days / 10.0)))

    # 4. Simulation Impact Metrics
    demand_delta = ((sim_avg_demand - baseline_avg_demand) / baseline_avg_demand) * 100
    rev_delta = ((sim_daily_revenue - baseline_daily_revenue) / baseline_daily_revenue) * 100
    ss_delta = ((sim_safety_stock - baseline_safety_stock) / baseline_safety_stock) * 100
    risk_delta = sim_stockout_risk - base_stockout_risk

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        render_metric_card("Simulated Daily Demand", f"{sim_avg_demand:,.0f} units", f"{demand_delta:+.1f}% vs Base", "positive" if demand_delta >= 0 else "negative")
    with r2:
        render_metric_card("Simulated Daily Revenue", format_currency(sim_daily_revenue), f"{rev_delta:+.1f}% vs Base", "positive" if rev_delta >= 0 else "negative")
    with r3:
        render_metric_card("Required Safety Stock", f"{sim_safety_stock:,} units", f"{ss_delta:+.1f}% Buffer", "neutral")
    with r4:
        render_metric_card("Network Stockout Risk", f"{sim_stockout_risk:.1f}%", f"{risk_delta:+.1f}% Risk Shift", "negative" if risk_delta > 0 else "positive")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 5. Visual Comparison Charts: Baseline vs Scenario
    render_section_header("Scenario Comparative Analysis", "Side-by-side comparison of baseline operations versus simulated conditions")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_comp = go.Figure()
        categories = ["Daily Demand (Units)", "Required Safety Stock", "Reorder Qty (Units)"]
        fig_comp.add_trace(go.Bar(
            name="Baseline Operations",
            x=categories,
            y=[baseline_avg_demand, baseline_safety_stock, baseline_reorder_qty],
            marker_color="#94a3b8"
        ))
        fig_comp.add_trace(go.Bar(
            name="Simulated Scenario",
            x=categories,
            y=[sim_avg_demand, sim_safety_stock, sim_reorder_qty],
            marker_color="#3b82f6"
        ))
        fig_comp.update_layout(
            title="Operational Volume Impact",
            barmode="group",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_chart2:
        fig_fin = go.Figure()
        fin_cats = ["Daily Revenue ($)", "Replenishment Capital ($)"]
        fig_fin.add_trace(go.Bar(
            name="Baseline Operations",
            x=fin_cats,
            y=[baseline_daily_revenue, baseline_order_cost],
            marker_color="#cbd5e1"
        ))
        fig_fin.add_trace(go.Bar(
            name="Simulated Scenario",
            x=fin_cats,
            y=[sim_daily_revenue, sim_order_cost],
            marker_color="#10b981"
        ))
        fig_fin.update_layout(
            title="Financial Capital Impact",
            barmode="group",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig_fin, use_container_width=True)

    # 6. Strategic Takeaways & Sensitivity Insights
    render_section_header("Executive Strategic Recommendations for Scenario", "Actionable guidance based on simulation parameters")
    
    if price_change_pct > 0:
        st.info(f"📈 **Price Increase Impact**: Raising prices by {price_change_pct}% reduces volume demand by {abs(elasticity_factor)*100:.1f}%, but gross daily revenue changes by {rev_delta:+.1f}%. Recommended safety stocks decrease slightly due to lower velocity.")
    elif price_change_pct < 0:
        st.warning(f"📉 **Price Reduction Impact**: Discounting by {abs(price_change_pct)}% triggers a {abs(elasticity_factor)*100:.1f}% surge in unit volume. Reorder frequency and supplier replenishment buffers must increase by {ss_delta:.1f}% to avoid stockouts.")

    if lead_time_delay_days > 0:
        st.error(f"🚢 **Supply Chain Disruption**: A {lead_time_delay_days}-day supplier delay expands the inventory lead-time from {base_lt} to {sim_lt} days. Safety stock must expand by {ss_delta:+.1f}% ({sim_safety_stock - baseline_safety_stock:,} additional units) to prevent critical stockouts.")
