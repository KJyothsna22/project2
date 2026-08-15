"""
Unit Tests for Role-Based Authentication & Permissions
"""

import pytest
from auth.auth_manager import AuthManager

def test_password_hashing():
    h1 = AuthManager.hash_password("admin123")
    h2 = AuthManager.hash_password("admin123")
    assert h1 == h2
    assert len(h1) == 64

def test_authentication_success():
    session = AuthManager.authenticate("admin", "admin123")
    assert session is not None
    assert session["role"] == "Admin"
    assert "trigger_pipeline" in session["permissions"]

def test_authentication_failure():
    session = AuthManager.authenticate("admin", "wrong_password")
    assert session is None

def test_role_hierarchy():
    assert AuthManager.is_role_sufficient("Admin", "Viewer") is True
    assert AuthManager.is_role_sufficient("Viewer", "Admin") is False
