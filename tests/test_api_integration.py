import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.main import app
from src.api.models import (
    QueryRequest,
    QueryResponse,
    ChatRequest,
    ChatResponse,
    RestaurantSearchRequest,
    RestaurantSearchResponse,
    ErrorResponse
)

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client"""
    mock_client = MagicMock()
    
    # Mock the chat completions create method
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response"
    
    mock_client.chat.completions.create.return_value = mock_response
    
    # Mock the client in the dependencies
    with patch("src.api.dependencies.OpenAI", return_value=mock_client):
        yield mock_client

@pytest.fixture
def mock_vector_search():
    """Create a mock vector search function"""
    return MagicMock(return_value=[{
        "restaurant": "Test Restaurant",
        "rating": "4.5",
        "price_range": "$$",
        "description": "A cozy restaurant known for its delicious food",
        "score": 0.95
    }])

def test_query_endpoint_success(test_client, mock_vector_search):
    """Test successful query processing"""
    with patch("src.api.main.get_similar_chunks", mock_vector_search):
        response = test_client.post(
            "/api/v1/query",
            json={"query": "Tell me about Test Restaurant"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert data["results"][0]["restaurant"] == "Test Restaurant"

def test_query_endpoint_empty_query(test_client):
    """Test query endpoint with empty query"""
    response = test_client.post(
        "/api/v1/query",
        json={"query": ""}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_chat_endpoint_success(test_client, mock_openai, mock_vector_search):
    """Test successful chat completion"""
    with patch("src.api.main.get_similar_chunks", mock_vector_search):
        response = test_client.post(
            "/api/v1/chat",
            json={
                "query": "What's good at Test Restaurant?",
                "conversation_id": "test_convo"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "This is a test response"
        assert "conversation_id" in data

def test_chat_endpoint_with_history(test_client, mock_openai):
    """Test chat endpoint with conversation history"""
    # First message
    response1 = test_client.post(
        "/api/v1/chat",
        json={
            "query": "Tell me about Test Restaurant",
            "conversation_id": "test_convo"
        }
    )
    assert response1.status_code == 200
    
    # Follow-up message
    response2 = test_client.post(
        "/api/v1/chat",
        json={
            "query": "What's on their menu?",
            "conversation_id": "test_convo"
        }
    )
    assert response2.status_code == 200
    data = response2.json()
    assert data["conversation_id"] == "test_convo"

def test_restaurants_endpoint_success(test_client):
    """Test successful restaurant search"""
    response = test_client.post(
        "/api/v1/restaurants",
        json={
            "query": "Italian restaurants",
            "price_range": "$$",
            "min_rating": 4.0,
            "page": 1,
            "page_size": 10
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "restaurants" in data
    assert "total_results" in data
    assert "total_pages" in data
    assert "page" in data
    assert "page_size" in data

def test_restaurants_endpoint_invalid_params(test_client):
    """Test restaurant search with invalid parameters"""
    response = test_client.post(
        "/api/v1/restaurants",
        json={
            "query": "Italian restaurants",
            "price_range": "invalid",
            "min_rating": 6.0,  # Invalid rating
            "page": 0,  # Invalid page
            "page_size": 100  # Too large
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_rate_limiting(test_client):
    """Test rate limiting middleware"""
    # Make multiple requests in quick succession
    responses = []
    for _ in range(100):  # Increase number of requests
        response = test_client.get("/api/v1/health")
        responses.append(response)
    
    # At least one response should be rate limited
    assert any(r.status_code == 429 for r in responses)

def test_error_handling(test_client, mock_openai):
    """Test error handling middleware"""
    # Make OpenAI client raise an exception
    mock_openai.chat.completions.create.side_effect = Exception("Test error")
    
    response = test_client.post(
        "/api/v1/chat",
        json={
            "query": "This should fail",
            "conversation_id": "test_convo"
        }
    )
    
    assert response.status_code == 500
    data = response.json()
    assert "error" in data["detail"]
    assert "message" in data["detail"] 