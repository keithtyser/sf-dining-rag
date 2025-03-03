"""
Chat module for generating responses using OpenAI's API with conversation context.
"""

import os
import uuid
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dotenv import load_dotenv
from openai import OpenAI
from src.embedding import get_embedding
from src.conversation import ConversationManager, Message, Conversation
import time

# Load environment variables
load_dotenv()

# Initialize conversation manager
conversation_manager = ConversationManager()

async def generate_response(
    query: str,
    conversation_id: str,
    client: OpenAI,
    get_similar_chunks: Callable[[str, int], Awaitable[List[Dict[str, Any]]]],
    max_tokens: int = 500,
    temperature: float = 0.7,
    context_window_size: int = 5
) -> Optional[str]:
    """
    Generate a response using OpenAI's API with context from vector search and conversation history
    
    Args:
        query: User's query
        conversation_id: ID of the conversation
        client: OpenAI client
        get_similar_chunks: Async function to get similar chunks from vector search
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0-1)
        context_window_size: Number of recent messages to include
        
    Returns:
        Optional[str]: Generated response or None if generation fails
    """
    try:
        # Get conversation or create new one
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            conversation = Conversation(
                id=conversation_id,
                storage_dir=conversation_manager.storage_dir
            )
            conversation_manager.conversations[conversation_id] = conversation
        
        # Get relevant context from vector search
        context_chunks = await get_similar_chunks(query, top_k=3)
        context_text = "\n".join([
            f"Context {i+1}:\n{chunk['metadata']['text']}\n"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Add user message to conversation first
        conversation.add_message(
            role="user",
            content=query,
            metadata={
                "timestamp": time.time(),
                "context_chunks": len(context_chunks),
                "type": "user_query"
            }
        )
        
        # Get conversation context window
        conversation_context = conversation.get_context_window(context_window_size)
        
        # Construct prompt with context
        system_prompt = (
            "You are a helpful assistant for a restaurant information system. "
            "Use the provided context to answer questions about restaurants, "
            "their menus, and related information. If you're not sure about "
            "something, say so rather than making assumptions. "
            "Maintain a natural conversation flow while staying focused on "
            "restaurant-related information."
        )
        
        # Prepare messages for API call
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context if available
        if context_text:
            messages.append({
                "role": "system",
                "content": f"Here is some relevant information:\n\n{context_text}"
            })
        
        # Add conversation history
        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_context
        ])
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        # Add assistant response to conversation
        conversation.add_message(
            role="assistant",
            content=response_text,
            metadata={
                "timestamp": time.time(),
                "model": "gpt-3.5-turbo",
                "tokens": response.usage.total_tokens,
                "type": "assistant_response"
            }
        )
        
        return response_text
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the chat functionality
    print("\n=== Testing Chat Response Generation ===")
    
    # Create OpenAI client
    client = OpenAI()
    
    # Test queries
    test_queries = [
        "What are some highly rated restaurants?",
        "Tell me more about their menu items",
        "Are there any vegetarian options?",
        "What's the price range like?"
    ]
    
    conversation_id = "test_conversation"
    
    for query in test_queries:
        print(f"\nUser: {query}")
        response = generate_response(
            query=query,
            conversation_id=conversation_id,
            client=client,
            get_similar_chunks=lambda q, top_k: []  # Mock function for testing
        )
        if response:
            print(f"\nAssistant: {response}")
        else:
            print("\nError: Could not generate response")
        print("\n" + "="*50) 