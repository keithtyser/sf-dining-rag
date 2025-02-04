import pytest
from unittest.mock import MagicMock, patch
from src.chat import ConversationHistory, generate_response

@pytest.fixture
def conversation_history():
    """Create a conversation history for testing"""
    return ConversationHistory(max_history=3)

def test_conversation_history_add_message(conversation_history):
    """Test adding messages to conversation history"""
    # Add user message
    conversation_history.add_message("user", "Hello")
    messages = conversation_history.get_messages()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    
    # Add assistant message
    conversation_history.add_message("assistant", "Hi there!")
    messages = conversation_history.get_messages()
    assert len(messages) == 2
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"

def test_conversation_history_max_length(conversation_history):
    """Test conversation history respects max length"""
    # Add more messages than max_history
    conversation_history.add_message("user", "Message 1")
    conversation_history.add_message("assistant", "Response 1")
    conversation_history.add_message("user", "Message 2")
    conversation_history.add_message("assistant", "Response 2")
    
    messages = conversation_history.get_messages()
    assert len(messages) == 3  # max_history is 3
    assert messages[0]["content"] == "Response 1"  # Oldest message within limit
    assert messages[-1]["content"] == "Response 2"  # Most recent message

def test_conversation_history_clear(conversation_history):
    """Test clearing conversation history"""
    conversation_history.add_message("user", "Test message")
    assert len(conversation_history.get_messages()) == 1
    
    conversation_history.clear()
    assert len(conversation_history.get_messages()) == 0

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client"""
    mock_client = MagicMock()
    
    # Mock the chat completions create method
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response"
    
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_query():
    """Create a mock query function"""
    return MagicMock()

def test_generate_response(mock_openai, mock_query, conversation_history):
    """Test response generation"""
    query = "Tell me about Test Restaurant"
    response = generate_response(
        query=query,
        conversation_history=conversation_history,
        client=mock_openai
    )

    # Verify response
    assert response is not None
    assert response == "This is a test response"
    
    # Verify the OpenAI API was called correctly
    mock_openai.chat.completions.create.assert_called_once()
    call_args = mock_openai.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-3.5-turbo"
    assert call_args["temperature"] == 0.7
    assert call_args["max_tokens"] == 150

def test_generate_response_with_context(mock_openai, mock_query, conversation_history):
    """Test response generation with context from vector search"""
    # Mock the query response
    mock_query.return_value = [{
        "restaurant": "Test Restaurant",
        "rating": "4.5",
        "price_range": "$$",
        "description": "A cozy restaurant known for its delicious food",
        "score": 0.95
    }]

    query = "What's good at Test Restaurant?"
    response = generate_response(
        query=query,
        conversation_history=conversation_history,
        client=mock_openai,
        get_similar_chunks=mock_query
    )

    # Verify response
    assert response is not None
    assert response == "This is a test response"

    # Verify that context was included in the prompt
    prompt_messages = mock_openai.chat.completions.create.call_args[1]["messages"]
    system_message = next(m for m in prompt_messages if m["role"] == "system")
    
    # Check for key elements in the system message
    assert "Test Restaurant" in system_message["content"]
    assert "4.5" in system_message["content"]
    assert "$$" in system_message["content"]
    assert "cozy restaurant" in system_message["content"]
    assert "0.95" in system_message["content"]

def test_generate_response_with_history(mock_openai, mock_query, conversation_history):
    """Test response generation with conversation history"""
    # Add some history
    conversation_history.add_message("user", "Tell me about Test Restaurant")
    conversation_history.add_message("assistant", "Test Restaurant is great!")

    # New query
    query = "What's on their menu?"
    response = generate_response(
        query=query,
        conversation_history=conversation_history,
        client=mock_openai
    )

    # Verify response
    assert response is not None
    assert response == "This is a test response"

    # Verify that history was included in the prompt
    prompt_messages = mock_openai.chat.completions.create.call_args[1]["messages"]
    history_messages = [m for m in prompt_messages if m["role"] in ("user", "assistant")]
    assert len(history_messages) == 3  # 2 history messages + current query
    assert history_messages[0]["role"] == "user"
    assert history_messages[0]["content"] == "Tell me about Test Restaurant"
    assert history_messages[1]["role"] == "assistant"
    assert history_messages[1]["content"] == "Test Restaurant is great!"
    assert history_messages[2]["role"] == "user"
    assert history_messages[2]["content"] == "What's on their menu?"

def test_generate_response_error_handling(mock_openai, mock_query, conversation_history):
    """Test error handling in response generation"""
    # Make the OpenAI client raise an exception
    mock_openai.chat.completions.create.side_effect = Exception("Test error")
    
    query = "Tell me about Test Restaurant"
    response = generate_response(
        query=query,
        conversation_history=conversation_history,
        client=mock_openai
    )
    
    # Verify that None is returned on error
    assert response is None 