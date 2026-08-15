"""
Page 3: Inventory Optimization & Replenishment Planning
Displays stock levels, safety stocks, reorder points, order quantities, and risk alerts with interactive PO export.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from warehouse.db import WarehouseManager
from dashboard.components import render_metric_card, render_section_header, render_risk_badge
from utils.helpers import format_currency, format_number

def render_inventory_page() -> None:
    """Renders the inventory optimization and replenishment planner page."""
    st.markdown("### 📦 Inventory Optimization & Replenishment Engine")
    st.markdown("Automated safety stock calculation, dynamic reorder points (ROP), and risk-adjusted purchase orders.")

    # 1. Fetch inventory recommendations
    inv_df = WarehouseManager.read_query("SELECT * FROM fact_inventory_recommendations")
    if inv_df.empty:
        st.warning("No inventory recommendations found. Please trigger the pipeline or check warehouse tables.")
        return

    # 2. Filters
    col_store_filter, col_risk_filter, col_status_filter = st.columns([3, 3, 4])
    with col_store_filter:
        stores = ["All Stores"] + sorted(inv_df["store_id"].unique().tolist())
        selected_store = st.selectbox("🏬 Store Filter", stores, index=0)

    with col_risk_filter:
        risks = ["All Risk Levels", "High Risk", "Medium Risk", "Low Risk"]
        selected_risk = st.selectbox("⚠️ Risk Filter", risks, index=0)

    with col_status_filter:
        statuses = ["All Statuses"] + sorted(inv_df["inventory_status"].unique().tolist())
        selected_status = st.selectbox("🏷️ Inventory Status", statuses, index=0)

    # Filter dataframe
    filtered_df = inv_df.copy()
    if selected_store != "All Stores":
        filtered_df = filtered_df[filtered_df["store_id"] == selected_store]
    if selected_risk != "All Risk Levels":
        filtered_df = filtered_df[filtered_df["risk_level"] == selected_risk]
    if selected_status != "All Statuses":
        filtered_df = filtered_df[filtered_df["inventory_status"] == selected_status]

    st.markdown("<hr style='margin: 10px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # 3. Macro KPI Row
    total_on_hand = int(filtered_df["current_inventory"].sum())
    total_reorder_qty = int(filtered_df["recommended_order_qty"].sum())
    total_po_cost = float(filtered_df["estimated_order_cost"].sum())
    high_risk_items = int((filtered_df["risk_level"] == "High Risk").sum())
    avg_dos = float(filtered_df["days_of_supply"].mean()) if not filtered_df.empty else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card("Current On-Hand Units", f"{total_on_hand:,}", f"Avg DOS: {avg_dos:.1f} days", "neutral")
    with k2:
        render_metric_card("Recommended Replenishment", f"{total_reorder_qty:,} units", f"Target Order Size", "positive")
    with k3:
        render_metric_card("Estimated PO Capital", format_currency(total_po_cost), f"{len(filtered_df)} SKUs Filtered", "neutral")
    with k4:
        render_metric_card("High-Risk Stock Alerts", f"{high_risk_items} Items", f"Urgent Attention Needed" if high_risk_items > 0 else "All Balanced", "negative" if high_risk_items > 0 else "positive")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 4. Interactive Charts: Risk Distribution & Stock Level Breakdown
    render_section_header("Inventory Risk & Days-of-Supply Diagnostics", "Breakdown of inventory position across risk tiers and depletion rates")
    col_c1, col_c2 = st.columns([5, 7])

    with col_c1:
        risk_counts = filtered_df["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        color_map = {"High Risk": "#ef4444", "Medium Risk": "#f59e0b", "Low Risk": "#10b981"}
        fig_risk = px.pie(
            risk_counts,
            names="risk_level",
            values="count",
            color="risk_level",
            color_discrete_map=color_map,
            hole=0.5,
            title="Catalog Risk Distribution"
        )
        fig_risk.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_risk, use_container_width=True)

    with col_c2:
        # Top items by replenishment urgency
        top_reorders = filtered_df.sort_values(by="recommended_order_qty", ascending=False).head(10)
        fig_reorder = px.bar(
            top_reorders,
            x="item_id",
            y=["current_inventory", "safety_stock", "recommended_order_qty"],
            barmode="group",
            title="Top 10 Order Priority SKUs (On-Hand vs Safety Stock vs Order Qty)",
            color_discrete_sequence=["#94a3b8", "#f59e0b", "#3b82f6"]
        )
        fig_reorder.update_layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(title=""),
            yaxis=dict(title="Units", showgrid=True, gridcolor="#f1f5f9"),
            margin=dict(l=30, r=30, t=40, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_reorder, use_container_width=True)

    # 5. Inventory Recommendations Grid & Export
    render_section_header("Comprehensive Replenishment Action Plan", "Real-time parameters, mathematical buffers, and target replenishment dates")
    
    display_cols = [
        "item_id", "store_id", "current_inventory", "average_daily_demand",
        "safety_stock", "reorder_point", "recommended_order_qty",
        "days_of_supply", "inventory_status", "risk_level",
        "stockout_risk_pct", "suggested_replenishment_date", "estimated_order_cost"
    ]
    table_view = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()
    table_view["estimated_order_cost"] = table_view["estimated_order_cost"].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(table_view, use_container_width=True, hide_index=True)

    # 6. Purchase Order Generator & Actions
    col_po_gen, col_po_info = st.columns([6, 6])
    with col_po_gen:
        st.markdown("#### 📑 Purchase Order (PO) Export")
        po_csv = filtered_df[filtered_df["recommended_order_qty"] > 0].to_csv(index=False)
        st.download_button(
            label="📦 Generate & Download Official Purchase Order (CSV)",
            data=po_csv,
            file_name=f"purchase_orders_{selected_store}_{pd.to_datetime('today').strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_po_info:
        st.info("📌 **Optimization Logic**: Reorder Point ($ROP$) combines average lead-time demand with statistical 95% service-level safety buffer. Recommended orders proactively avoid stockouts while minimizing holding costs.")
