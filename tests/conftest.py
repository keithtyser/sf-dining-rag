import os
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

# Test client fixture
@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

# Mock data fixtures
@pytest.fixture
def sample_restaurant_data():
    """Sample restaurant data for testing"""
    return {
        "restaurant_name": "Test Restaurant",
        "rating": 4.5,
        "price_range": "$$",
        "cuisine_type": "Test Cuisine",
        "description": "A test restaurant description"
    }

@pytest.fixture
def sample_menu_item():
    """Sample menu item data for testing"""
    return {
        "item_name": "Test Item",
        "restaurant_name": "Test Restaurant",
        "category": "Test Category",
        "description": "A test menu item description",
        "price": 9.99
    }

@pytest.fixture
def mock_embedding():
    """Sample embedding vector for testing"""
    import numpy as np
    # Generate a random embedding vector of the correct dimension
    return list(np.random.rand(1536).astype(float))

# Environment setup
def pytest_configure(config):
    """Set up test environment variables if not already set"""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("OPENAI_API_KEY", "test_key")
    os.environ.setdefault("PINECONE_API_KEY", "test_key")
    os.environ.setdefault("PINECONE_ENVIRONMENT", "test") 