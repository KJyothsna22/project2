"""
Retail Demand Forecasting & Inventory Optimization Platform
Main Streamlit Application Entrypoint
"""

import streamlit as st
import pandas as pd
import config
from auth.auth_manager import AuthManager
from dashboard.styles import get_custom_css
from dashboard.pages.page_executive import render_executive_page
from dashboard.pages.page_forecasting import render_forecasting_page
from dashboard.pages.page_inventory import render_inventory_page
from dashboard.pages.page_whatif import render_whatif_page
from dashboard.pages.page_accuracy import render_accuracy_page
from reports.report_generator import ReportGenerator
from etl.pipeline import ETLPipeline
from dbt_project.dbt_runner import DBTRunner
from forecasting.train_and_forecast import ForecastingPipeline
from inventory.replenishment import ReplenishmentPlanner
from warehouse.schema import init_database_schemas

# Page Configuration
st.set_page_config(
    page_title="Retail Demand Forecasting & Inventory Optimization",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS Design System
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Session State Initialization
if "user_session" not in st.session_state:
    st.session_state["user_session"] = None

def render_login_screen():
    """Renders authentication screen."""
    st.markdown("""
    <div style="max-width: 480px; margin: 40px auto; padding: 32px; background: white; border-radius: 20px; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; text-align: center;">
        <div style="font-size: 2.8rem; margin-bottom: 8px;">🛒</div>
        <div style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">Retail Demand & Inventory AI</div>
        <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 24px;">Enterprise Supply Chain Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("##### 🔐 Sign In to Your Workspace")
            username = st.text_input("Username", placeholder="e.g. admin, manager, viewer").strip()
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Sign In to Platform", use_container_width=True)

            if submit:
                session = AuthManager.authenticate(username, password)
                if session:
                    st.session_state["user_session"] = session
                    st.success(f"Welcome, {session['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please verify your username and password.")

        st.markdown("""
        <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 14px 18px; margin-top: 20px; font-size: 0.82rem; color: #475569;">
            <strong>Demo Credentials (Role-Based Access Control):</strong><br>
            • <strong>Admin:</strong> <code>admin</code> / <code>admin123</code> (Full pipeline trigger & management)<br>
            • <strong>Inventory Manager:</strong> <code>manager</code> / <code>manager123</code> (Forecasting & replenishment)<br>
            • <strong>Viewer:</strong> <code>viewer</code> / <code>viewer123</code> (Read-only analytics & reports)
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Renders persistent navigation sidebar with reports export and role management."""
    session = st.session_state["user_session"]
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <span style="font-size: 1.8rem;">🛒</span>
            <div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff;">RETAIL AI PLATFORM</div>
                <div style="font-size: 0.72rem; color: #94a3b8; letter-spacing: 0.05em;">SUPPLY CHAIN OPTIMIZATION</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User Profile Pill
        role_color = "#3b82f6" if session["role"] == "Admin" else ("#10b981" if session["role"] == "Inventory Manager" else "#8b5cf6")
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; margin-bottom: 20px;">
            <div style="font-size: 0.75rem; color: #94a3b8;">ACTIVE SESSION</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-top: 2px;">{session['name']}</div>
            <div style="display: inline-block; background: {role_color}; color: white; font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 12px; margin-top: 6px;">
                {session['role']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation Options
        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 6px;'>Navigation</p>", unsafe_allow_html=True)
        nav_pages = [
            "📊 Executive Dashboard",
            "📈 Demand Forecasting",
            "📦 Inventory Optimization",
            "🧪 What-If Scenario Analysis",
            "🎯 Forecast Accuracy Monitoring"
        ]
        selected_page = st.radio("Navigation Menu", nav_pages, label_visibility="collapsed")

        st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)

        # Automated Reports Downloads
        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px;'>Executive Reports</p>", unsafe_allow_html=True)
        
        # 1. Download Multi-Tab Excel Report
        try:
            excel_bytes = ReportGenerator.generate_excel_report()
            st.download_button(
                label="📊 Download Excel Report (.xlsx)",
                data=excel_bytes,
                file_name=f"retail_inventory_forecast_report_{pd.to_datetime('today').strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"Excel report builder: {e}")

        # 2. Download PDF Briefing
        try:
            pdf_bytes = ReportGenerator.generate_pdf_report()
            st.download_button(
                label="📄 Download PDF Executive Brief",
                data=pdf_bytes,
                file_name=f"executive_briefing_{pd.to_datetime('today').strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"PDF generator: {e}")

        # Admin Controls: Trigger Pipeline
        if session["role"] == "Admin":
            st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px;'>Admin Operations</p>", unsafe_allow_html=True)
            if st.button("🚀 Re-Run End-to-End Pipeline", use_container_width=True):
                with st.spinner("Executing full pipeline (ETL -> dbt -> ML Training -> Inventory Optimization)..."):
                    ETLPipeline.run()
                    DBTRunner.run_transformations()
                    ForecastingPipeline.run()
                    ReplenishmentPlanner.generate_all_recommendations()
                st.success("Pipeline executed successfully!")
                st.rerun()

        # Logout Button
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["user_session"] = None
            st.rerun()

        return selected_page

def main():
    """Main application dispatcher."""
    if st.session_state["user_session"] is None:
        render_login_screen()
        return

    selected_page = render_sidebar()

    # Route to selected page
    if "Executive Dashboard" in selected_page:
        render_executive_page()
    elif "Demand Forecasting" in selected_page:
        render_forecasting_page()
    elif "Inventory Optimization" in selected_page:
        render_inventory_page()
    elif "What-If Scenario" in selected_page:
        render_whatif_page()
    elif "Forecast Accuracy" in selected_page:
        render_accuracy_page()

if __name__ == "__main__":
    main()
