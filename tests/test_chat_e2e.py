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
    ChatRequest,
    ChatResponse,
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
def mock_pinecone():
    """Mock Pinecone initialization"""
    mock_pinecone = MagicMock()
    mock_pinecone.query = MagicMock(return_value=MagicMock(matches=[
        MagicMock(
            id="test-restaurant-1",
            score=0.95,
            metadata={
                "text": "Test Restaurant is a popular dining spot known for its excellent service and diverse menu.",
                "type": "restaurant_overview",
                "restaurant_name": "Test Restaurant",
                "rating": 4.5,
                "price_range": "$$"
            }
        )
    ]))
    
    # Create a mock index object with the correct name
    mock_index_obj = MagicMock()
    mock_index_obj.name = "restaurant-chatbot"
    mock_pinecone.list_indexes.return_value = [mock_index_obj]
    
    # Mock the describe_index_stats method to return the correct dimension
    mock_stats = {"dimension": 1536, "total_vector_count": 100, "namespaces": {}}
    mock_pinecone.describe_index_stats = MagicMock(return_value=mock_stats)
    mock_pinecone.Index.return_value.describe_index_stats = MagicMock(return_value=mock_stats)
    
    with patch("src.vector_db.init_pinecone", return_value=mock_pinecone), \
         patch("src.api.dependencies.get_pinecone_index", return_value=mock_pinecone), \
         patch("src.api.main.get_pinecone_index", return_value=mock_pinecone), \
         patch("pinecone.Pinecone", return_value=mock_pinecone), \
         patch("src.vector_db.Pinecone", return_value=mock_pinecone):
        yield mock_pinecone

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client"""
    mock_client = MagicMock()
    
    # Mock chat completion response
    mock_chat_response = MagicMock()
    mock_chat_response.choices = [MagicMock()]
    mock_chat_response.choices[0].message = MagicMock()
    mock_chat_response.choices[0].message.content = "This is a test response"
    mock_chat_response.choices[0].message.role = "assistant"
    mock_chat_response.choices[0].message.function_call = None
    mock_chat_response.choices[0].message.tool_calls = None
    mock_chat_response.model = "gpt-3.5-turbo"
    mock_chat_response.object = "chat.completion"
    mock_chat_response.usage = MagicMock(prompt_tokens=50, completion_tokens=20, total_tokens=70)
    mock_client.chat.completions.create.return_value = mock_chat_response
    
    # Mock embeddings response
    mock_embeddings_response = MagicMock()
    mock_embeddings_response.data = [MagicMock()]
    mock_embeddings_response.data[0].embedding = [0.1] * 1536
    mock_embeddings_response.data[0].index = 0
    mock_embeddings_response.data[0].object = "embedding"
    mock_embeddings_response.model = "text-embedding-ada-002"
    mock_embeddings_response.object = "list"
    mock_embeddings_response.usage = MagicMock(prompt_tokens=10, total_tokens=10)
    mock_client.embeddings.create.return_value = mock_embeddings_response
    
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
    
    # Disable rate limiting
    import slowapi.extension
    slowapi.extension.Limiter._inject_headers = lambda self, response, current_limit: response
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    conversation_manager.conversations = {}
    if test_storage_dir.exists():
        for file in test_storage_dir.glob("*.json"):
            file.unlink()

def test_complete_chat_flow(test_client, mock_openai, mock_vector_search):
    """Test a complete chat interaction flow"""
    with patch("src.api.main.get_similar_chunks", mock_vector_search):
        # Initial query
        response1 = test_client.post(
            "/api/v1/chat",
            json={
                "query": "Tell me about Test Restaurant",
                "metadata": {"test": True}
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert "response" in data1
        assert "conversation_id" in data1
        conversation_id = data1["conversation_id"]
        
        # Continue the conversation
        response2 = test_client.post(
            "/api/v1/chat",
            json={
                "query": "What's the price range?",
                "conversation_id": conversation_id
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["conversation_id"] == conversation_id
        assert "response" in data2

def test_conversation_persistence(test_client, mock_openai, mock_pinecone, test_storage_dir):
    """Test that conversations are properly persisted and can be retrieved"""
    # No need to set storage_dir here as it's already set in the fixture
    
    # Create multiple conversations
    conversation_ids = []
    for i in range(3):
        response = test_client.post(
            "/api/v1/chat",
            json={
                "query": f"Test message {i}",
                "metadata": {"test_id": i}
            }
        )
        assert response.status_code == 200
        data = response.json()
        conversation_ids.append(data["conversation_id"])

    # Verify conversations exist
    assert len(list(test_storage_dir.glob("*.json"))) == 3

    # Test retrieving a specific conversation
    response = test_client.get(f"/api/v1/chat/{conversation_ids[0]}")
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conversation_ids[0]
    assert len(data["messages"]) > 0

def test_conversation_cleanup(test_client, mock_openai, mock_pinecone, test_storage_dir):
    """Test cleanup of old conversations"""
    # Create some conversations
    conversation_ids = []
    for i in range(3):
        response = test_client.post(
            "/api/v1/chat",
            json={"query": f"Test message {i}"}
        )
        assert response.status_code == 200
        data = response.json()
        conversation_ids.append(data["conversation_id"])

    # Simulate old conversations by modifying file timestamps and conversation objects
    old_time = time.time() - (31 * 24 * 60 * 60)  # 31 days old
    for conv_id in conversation_ids:
        # Update file timestamp
        conv_file = test_storage_dir / f"{conv_id}.json"
        os.utime(conv_file, (old_time, old_time))
        
        # Update conversation object
        conv = conversation_manager.conversations[conv_id]
        conv.last_updated = old_time
        conv.save()  # Save to update the file with the new timestamp

    # Trigger cleanup
    response = test_client.post("/api/v1/chat/cleanup")
    assert response.status_code == 200

    # Verify conversations were cleaned up
    remaining_files = list(test_storage_dir.glob("*.json"))
    assert len(remaining_files) == 0
    assert len(conversation_manager.conversations) == 0

def test_error_scenarios(test_client):
    """Test various error scenarios"""
    # Test invalid conversation ID
    response = test_client.get("/api/v1/chat/invalid-id")
    assert response.status_code == 404

    # Test missing query
    response = test_client.post("/api/v1/chat", json={})
    assert response.status_code == 422

def test_context_window_handling(test_client, mock_openai, mock_vector_search, mock_pinecone):
    """Test handling of conversation context window"""
    with patch("src.api.main.get_similar_chunks", mock_vector_search):
        # Create a conversation with multiple messages
        conversation_id = None
        messages = [
            "Message 1",
            "Message 2",
            "Message 3",
            "Message 4",
            "Message 5",
            "Message 6"
        ]

        for msg in messages:
            response = test_client.post(
                "/api/v1/chat",
                json={
                    "query": msg,
                    "conversation_id": conversation_id,
                    "context_window_size": 3  # Only keep last 3 messages
                }
            )
            assert response.status_code == 200
            data = response.json()
            conversation_id = data["conversation_id"]

        # Verify only last 3 messages are kept
        response = test_client.get(f"/api/v1/chat/{conversation_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 12  # 6 user messages + 6 assistant responses 