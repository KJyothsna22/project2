"""
Custom CSS & UI Styling for Streamlit Dashboard
Implements executive glassmorphism, modern typography, responsive cards, and vibrant accents.
"""

def get_custom_css() -> str:
    """Returns custom CSS injected into Streamlit."""
    return """
    <style>
        /* Import Modern Typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Main Container Padding */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
            max-width: 1400px;
        }

        /* Glassmorphic Metric Cards */
        .metric-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.85));
            border: 1px solid rgba(226, 232, 240, 0.8);
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.05), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
            backdrop-filter: blur(12px);
            transition: all 0.25s ease-in-out;
            margin-bottom: 15px;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 20px 30px -10px rgba(15, 23, 42, 0.1);
            border-color: #3b82f6;
        }

        .metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 6px;
        }

        .metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
        }

        .metric-delta {
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 6px;
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            border-radius: 20px;
        }

        .delta-positive {
            color: #059669;
            background-color: #ecfdf5;
        }

        .delta-negative {
            color: #dc2626;
            background-color: #fef2f2;
        }

        .delta-neutral {
            color: #475569;
            background-color: #f1f5f9;
        }

        /* Risk Badges */
        .risk-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .risk-high {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #f87171;
        }

        .risk-medium {
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fcd34d;
        }

        .risk-low {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
        }

        /* Section Headers */
        .section-header {
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 0.5rem;
        }

        .section-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: #0f172a;
        }

        .section-subtitle {
            font-size: 0.9rem;
            color: #64748b;
        }

        /* User Profile Pill */
        .user-pill {
            background: #1e293b;
            color: #f8fafc;
            padding: 8px 16px;
            border-radius: 30px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 15px;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0f172a;
            color: #f8fafc;
        }
        
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: #cbd5e1 !important;
        }
    </style>
    """
