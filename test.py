import os
import pytest
from dotenv import load_dotenv
from api_agents.env_loader import get_required_environ

# Load a test .env file (optional, or mock os.environ)
load_dotenv(".env.test")  # You can create a .env.test file for testing

def test_existing_variable(monkeypatch):
    # Patch environment variable
    monkeypatch.setenv("TEST_VAR", "hello")
    assert get_required_environ("TEST_VAR") == "hello"

def test_missing_variable(monkeypatch):
    # Ensure variable is not in environment
    monkeypatch.delenv("MISSING_VAR", raising=False)
    with pytest.raises(KeyError):
        get_required_environ("MISSING_VAR")

def test_empty_variable(monkeypatch):
    # Set variable to empty string
    monkeypatch.setenv("EMPTY_VAR", "   ")
    with pytest.raises(ValueError):
        get_required_environ("EMPTY_VAR")
