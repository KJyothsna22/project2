"""
Helper functions for formatting, date math, and array computations.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import List, Union, Dict, Any

def format_currency(amount: Union[float, int, np.number]) -> str:
    """Formats numeric value to currency string e.g. $1,234,567.89 or $1.2M"""
    if pd.isna(amount):
        return "$0.00"
    amount = float(amount)
    if abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif abs(amount) >= 1_000:
        return f"${amount / 1_000:.1f}K"
    else:
        return f"${amount:,.2f}"

def format_number(value: Union[float, int, np.number], decimals: int = 0) -> str:
    """Formats numbers with comma separators."""
    if pd.isna(value):
        return "0"
    if decimals == 0:
        return f"{int(round(value)):,}"
    return f"{float(value):,.{decimals}f}"

def format_percentage(value: Union[float, int, np.number]) -> str:
    """Formats numeric value to percentage string e.g. 15.4%"""
    if pd.isna(value):
        return "0.0%"
    return f"{float(value) * 100:.1f}%" if abs(value) <= 1.0 else f"{float(value):.1f}%"

def calculate_date_range(start_date: str, days: int) -> List[str]:
    """Generates a list of date strings for a given start date and duration."""
    start_dt = pd.to_datetime(start_date)
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers without ZeroDivisionError."""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return default
    return numerator / denominator
