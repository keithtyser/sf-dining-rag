"""
End-to-end tests for the chat functionality.

These tests verify the complete chat flow, including:
- Conversation creation and persistence
- Context handling
- Rate limiting
- Error scenarios
- Message history management
"""

import pytest
import time
from pathlib import Path
import shutil
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
    ErrorResponse,
    Message,
    Conversation,
    ConversationMetadata
)
from src.chat import conversation_manager
from openai import OpenAI
import httpx
import json
import os
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from tempfile import TemporaryDirectory
from src.api.dependencies import get_openai_client, get_pinecone_client
from src.conversation import conversation_manager, ConversationManager
from fastapi.responses import JSONResponse

@pytest.fixture
def mock_rate_limit():
    """Disable rate limiting for tests"""
    with patch("src.api.main.RATE_LIMIT_SECONDS", 0):
        yield

@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables"""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-key",
        "PINECONE_API_KEY": "test-key",
        "PINECONE_ENVIRONMENT": "test-env"
    }):
        yield

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client"""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="This is a test response"
                )
            )
        ]
    )
    return mock_client

@pytest.fixture
def mock_pinecone():
    """Create a mock Pinecone client"""
    mock_client = MagicMock()
    mock_client.query.return_value = MagicMock(
        matches=[
            {
                "id": "test_id",
                "score": 0.95,
                "metadata": {
                    "text": "Test restaurant information",
                    "restaurant_name": "Test Restaurant",
                    "rating": 4.5,
                    "price_range": "$$"
                }
            }
        ]
    )
    return mock_client

@pytest.fixture
def mock_http_client():
    """Mock HTTP client"""
    mock_client = MagicMock()
    mock_client.headers = {"Authorization": "Bearer test-key"}
    mock_client.post.return_value = MagicMock(status_code=200)
    return mock_client

@pytest.fixture
def test_storage_dir():
    """Create a temporary directory for conversation storage"""
    with TemporaryDirectory() as temp_dir:
        storage_dir = Path(temp_dir) / "test_conversations"
        storage_dir.mkdir(parents=True, exist_ok=True)
        # Create a new conversation manager with the test storage directory
        global conversation_manager
        conversation_manager = ConversationManager(str(storage_dir))
        # Ensure the storage directory is set correctly
        assert conversation_manager.storage_dir == storage_dir
        # Update the conversation manager in the chat module
        import src.chat
        src.chat.conversation_manager = conversation_manager
        # Update the conversation manager in the API module
        import src.api.main
        src.api.main.conversation_manager = conversation_manager
        yield storage_dir

@pytest.fixture
def mock_vector_search():
    """Create a mock vector search function"""
    async def mock_search(query: str, top_k: int = 3):
        # For the context window test, return no results to avoid message duplication
        if query.startswith("Message "):
            return []
            
        # For other tests, return the test restaurant data
        return [
            {
                "metadata": {
                    "text": "Test Restaurant is a popular dining spot known for its excellent service and diverse menu.",
                    "type": "restaurant_overview",
                    "restaurant_name": "Test Restaurant",
                    "rating": 4.5,
                    "price_range": "$$",
                    "restaurant_id": "123"
                },
                "score": 0.95
            }
        ]
    return mock_search

@pytest.fixture
def test_client(test_storage_dir, mock_openai, mock_pinecone):
    """Create a test client with mocked dependencies"""
    # Set up test app
    app.dependency_overrides[get_openai_client] = lambda: mock_openai
    app.dependency_overrides[get_pinecone_client] = lambda: mock_pinecone
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    conversation_manager.conversations = {}
    if test_storage_dir.exists():
        for file in test_storage_dir.glob("*.json"):
            file.unlink()

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
        result = data["results"][0]
        assert result["restaurant"] == "Test Restaurant"
        assert result["rating"] == "4.5"
        assert result["price_range"] == "$$"

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
        assert "conversation_id" in data
        assert data["conversation_id"] == "test_convo"

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
    
    # Second message in same conversation
    response2 = test_client.post(
        "/api/v1/chat",
        json={
            "query": "What are their popular dishes?",
            "conversation_id": "test_convo"
        }
    )
    assert response2.status_code == 200
    
    # Verify both messages are in conversation
    response3 = test_client.get("/api/v1/conversations/recent")
    assert response3.status_code == 200
    conversations = response3.json()
    assert len(conversations) > 0
    assert len(conversations[0]["messages"]) == 4  # 2 user messages + 2 assistant responses

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
    # Make multiple requests to exceed rate limit
    responses = []
    for _ in range(35):  # Exceeds the 30/minute limit
        response = test_client.post(
            "/api/v1/chat",
            json={
                "query": "Test query",
                "conversation_id": "test_convo"
            }
        )
        responses.append(response)
        time.sleep(0.01)  # Small delay to avoid overwhelming the test server
    
    # Count rate limited responses
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0
    
    # Verify rate limit response format
    rate_limited_response = rate_limited[0].json()
    assert "detail" in rate_limited_response
    detail = rate_limited_response["detail"]
    assert detail["error"] == "rate_limit_exceeded"
    assert "chat" in detail["message"].lower()
    assert detail["endpoint_type"] == "chat"
    assert detail["retry_after"] == 30

def test_error_handling(test_client, mock_openai):
    """Test error handling middleware"""
    # Reset rate limit state by creating a new storage
    test_client.app.state.limiter._storage._storage = {}
    
    # Simulate an error by passing invalid data
    response = test_client.post(
        "/api/v1/chat",
        json={"invalid": "data"}
    )
    
    assert response.status_code == 422
    error_response = response.json()
    assert "detail" in error_response

def test_rate_limiting_chat_endpoint(test_client):
    """Test rate limiting specifically for chat endpoints"""
    # Make multiple requests to chat endpoint
    responses = []
    for _ in range(35):  # Exceeds the 30/minute limit
        response = test_client.post(
            "/api/v1/chat",
            json={
                "query": "Test query",
                "conversation_id": "test_convo"
            }
        )
        responses.append(response)
        time.sleep(0.01)  # Small delay to avoid overwhelming the test server
    
    # Count rate limited responses
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0
    
    # Verify rate limit response format
    rate_limited_response = rate_limited[0].json()
    assert "detail" in rate_limited_response
    detail = rate_limited_response["detail"]
    assert detail["error"] == "rate_limit_exceeded"
    assert "chat" in detail["message"].lower()
    assert detail["endpoint_type"] == "chat"
    assert detail["retry_after"] == 30

def test_rate_limiting_conversation_endpoint(test_client):
    """Test rate limiting for conversation management endpoints"""
    # Make multiple requests to get recent conversations
    responses = []
    for _ in range(65):  # Exceeds the 60/minute limit
        response = test_client.get("/api/v1/conversations/recent")
        responses.append(response)
        time.sleep(0.01)  # Small delay to avoid overwhelming the test server
    
    # Count rate limited responses
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0
    
    # Verify rate limit response format
    rate_limited_response = rate_limited[0].json()
    assert "detail" in rate_limited_response
    detail = rate_limited_response["detail"]
    assert detail["error"] == "rate_limit_exceeded"
    assert "conversation" in detail["message"].lower()
    assert detail["endpoint_type"] == "conversation"
    assert detail["retry_after"] == 45

def test_rate_limiting_cleanup_endpoint(test_client):
    """Test rate limiting for cleanup endpoint"""
    # Make multiple requests to cleanup endpoint
    responses = []
    for _ in range(15):  # Exceeds the 10/minute limit
        response = test_client.post("/api/v1/chat/cleanup", json={"days_old": 30})
        responses.append(response)
        time.sleep(0.01)  # Small delay to avoid overwhelming the test server
    
    # Count rate limited responses
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0
    
    # Verify rate limit response format
    rate_limited_response = rate_limited[0].json()
    assert "detail" in rate_limited_response
    detail = rate_limited_response["detail"]
    assert detail["error"] == "rate_limit_exceeded"
    assert detail["retry_after"] == 60  # Default retry time 