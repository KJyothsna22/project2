"""
Role-Based Authentication & Session Management
Roles:
- Admin: Full access (ETL trigger, model retraining, inventory approval, scenario simulation, user management)
- Inventory Manager: Operational access (Forecasting explorer, inventory optimization, what-if simulations, report downloads)
- Viewer: Read-only access (Executive dashboard, aggregate trends, report downloads)
"""

import hashlib
import time
from typing import Optional, Dict, Any
import config
from utils.logger import get_logger

logger = get_logger("auth_manager")

class AuthManager:
    """Manages role-based authentication and user sessions."""

    ROLE_HIERARCHY = {
        "Admin": 3,
        "Inventory Manager": 2,
        "Viewer": 1
    }

    ROLE_PERMISSIONS = {
        "Admin": [
            "view_executive", "view_forecasting", "view_inventory",
            "view_whatif", "view_accuracy", "trigger_pipeline",
            "modify_inventory_parameters", "export_reports", "manage_users"
        ],
        "Inventory Manager": [
            "view_executive", "view_forecasting", "view_inventory",
            "view_whatif", "view_accuracy", "export_reports",
            "modify_inventory_parameters"
        ],
        "Viewer": [
            "view_executive", "view_forecasting", "view_accuracy", "export_reports"
        ]
    }

    @staticmethod
    def hash_password(password: str) -> str:
        """Computes SHA-256 hash of a plain text password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Validates credentials. Returns user session dict if valid, None otherwise.
        """
        username = username.strip().lower()
        user_info = config.DEFAULT_USERS.get(username)
        if not user_info:
            logger.warning(f"Authentication failed: user '{username}' not found.")
            return None

        password_hash = cls.hash_password(password)
        if password_hash == user_info["password_hash"]:
            logger.info(f"User '{username}' successfully authenticated with role '{user_info['role']}'.")
            return {
                "username": username,
                "name": user_info["name"],
                "role": user_info["role"],
                "authenticated_at": time.time(),
                "permissions": cls.ROLE_PERMISSIONS.get(user_info["role"], [])
            }
        
        logger.warning(f"Authentication failed: invalid password for user '{username}'.")
        return None

    @classmethod
    def has_permission(cls, user_role: str, required_permission: str) -> bool:
        """Checks if a given role has a specific capability."""
        permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
        return required_permission in permissions

    @classmethod
    def is_role_sufficient(cls, user_role: str, min_role: str) -> bool:
        """Verifies if user's role meets or exceeds the minimum required role."""
        return cls.ROLE_HIERARCHY.get(user_role, 0) >= cls.ROLE_HIERARCHY.get(min_role, 0)
