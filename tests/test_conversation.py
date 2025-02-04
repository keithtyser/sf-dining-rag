"""Tests for the conversation management system."""

import pytest
import time
import json
from pathlib import Path
from src.conversation import Message, Conversation, ConversationManager

@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary directory for conversation storage"""
    storage_dir = tmp_path / "conversations"
    storage_dir.mkdir()
    return storage_dir

@pytest.fixture
def conversation_manager(temp_storage_dir):
    """Create a conversation manager with temporary storage"""
    return ConversationManager(storage_dir=str(temp_storage_dir))

def test_message_creation():
    """Test creating a message with metadata"""
    metadata = {"source": "test", "context_chunks": 3}
    message = Message(role="user", content="Test message", metadata=metadata)
    
    assert message.role == "user"
    assert message.content == "Test message"
    assert message.metadata == metadata
    assert isinstance(message.timestamp, float)

def test_conversation_creation():
    """Test creating a conversation"""
    conv = Conversation(id="test_conv")
    
    assert conv.id == "test_conv"
    assert len(conv.messages) == 0
    assert isinstance(conv.created_at, float)
    assert isinstance(conv.last_updated, float)

def test_conversation_add_message():
    """Test adding messages to a conversation"""
    conv = Conversation(id="test_conv")
    
    # Add messages
    conv.add_message("user", "Hello", {"type": "greeting"})
    conv.add_message("assistant", "Hi there!", {"type": "response"})
    
    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[0].content == "Hello"
    assert conv.messages[0].metadata["type"] == "greeting"
    assert conv.messages[1].role == "assistant"
    assert conv.messages[1].content == "Hi there!"
    assert conv.messages[1].metadata["type"] == "response"

def test_conversation_get_messages():
    """Test getting formatted messages"""
    conv = Conversation(id="test_conv")
    
    # Add messages
    conv.add_message("user", "Hello")
    conv.add_message("assistant", "Hi there!")
    
    messages = conv.get_messages()
    assert len(messages) == 2
    assert all(isinstance(msg, dict) for msg in messages)
    assert all("role" in msg and "content" in msg for msg in messages)

def test_conversation_get_context_window():
    """Test getting context window"""
    conv = Conversation(id="test_conv")
    
    # Add multiple messages
    for i in range(10):
        conv.add_message("user", f"Message {i}")
    
    # Get context window
    window = conv.get_context_window(window_size=5)
    assert len(window) == 5
    assert window[-1]["content"] == "Message 9"

def test_conversation_pruning():
    """Test conversation history pruning"""
    conv = Conversation(id="test_conv", max_messages=5)
    
    # Add more messages than max_messages
    for i in range(10):
        conv.add_message("user", f"Message {i}")
    
    assert len(conv.messages) == 5
    assert conv.messages[-1].content == "Message 9"

def test_conversation_persistence(temp_storage_dir):
    """Test saving and loading conversations"""
    # Create conversation with storage directory
    conv = Conversation(id="test_conv", storage_dir=temp_storage_dir)
    conv.add_message("user", "Test message")
    
    # Save conversation
    conv.save()
    
    # Check file exists
    file_path = temp_storage_dir / "test_conv.json"
    assert file_path.exists()
    
    # Load and verify content
    with open(file_path) as f:
        data = json.load(f)
    
    assert data["id"] == "test_conv"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Test message"

def test_conversation_manager_operations(conversation_manager):
    """Test conversation manager operations"""
    # Create conversations
    conv1 = conversation_manager.get_conversation("conv1")
    conv2 = conversation_manager.get_conversation("conv2")
    
    # Add messages
    conversation_manager.add_message("conv1", "user", "Hello from conv1")
    conversation_manager.add_message("conv2", "user", "Hello from conv2")
    
    # Get recent conversations
    recent = conversation_manager.get_recent_conversations(limit=2)
    assert len(recent) == 2
    
    # Verify conversations were saved
    saved_files = list(Path(conversation_manager.storage_dir).glob("*.json"))
    assert len(saved_files) == 2

def test_conversation_cleanup(conversation_manager):
    """Test cleaning up old conversations"""
    # Create old and new conversations
    old_conv = conversation_manager.get_conversation("old_conv")
    new_conv = conversation_manager.get_conversation("new_conv")
    
    # Modify last_updated for old conversation
    old_conv.last_updated = time.time() - (31 * 24 * 60 * 60)  # 31 days old
    old_conv.save()
    
    # Add messages to new conversation
    conversation_manager.add_message("new_conv", "user", "Recent message")
    
    # Clean up old conversations
    conversation_manager.cleanup_old_conversations(days_old=30)
    
    # Verify old conversation was removed
    remaining_files = list(Path(conversation_manager.storage_dir).glob("*.json"))
    assert len(remaining_files) == 1
    assert remaining_files[0].stem == "new_conv"

def test_conversation_metadata():
    """Test conversation metadata handling"""
    conv = Conversation(
        id="test_conv",
        metadata={"user_id": "123", "session_data": {"browser": "Chrome"}}
    )
    
    assert conv.metadata["user_id"] == "123"
    assert conv.metadata["session_data"]["browser"] == "Chrome"
    
    # Add message with metadata
    conv.add_message(
        "user",
        "Test message",
        metadata={"timestamp": time.time(), "client_info": {"ip": "127.0.0.1"}}
    )
    
    assert "client_info" in conv.messages[0].metadata
    assert conv.messages[0].metadata["client_info"]["ip"] == "127.0.0.1" 