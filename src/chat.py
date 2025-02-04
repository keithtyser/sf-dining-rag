import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI
from src.embedding import get_embedding
import time

# Load environment variables
load_dotenv(override=True)

@dataclass
class Message:
    """Class to represent a chat message"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class ConversationHistory:
    """Class to manage conversation history"""
    messages: List[Message] = field(default_factory=list)
    max_messages: int = 10
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the history"""
        self.messages.append(Message(role=role, content=content))
        # Trim history if it exceeds max length
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages in format for OpenAI API"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

def generate_response(
    query: str,
    conversation_history: ConversationHistory,
    client: OpenAI,
    get_similar_chunks: Callable,
    max_tokens: int = 500,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Generate a response using OpenAI's API with context from vector search
    
    Args:
        query: User's query
        conversation_history: Conversation history
        client: OpenAI client
        get_similar_chunks: Function to get similar chunks from vector search
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0-1)
        
    Returns:
        Optional[str]: Generated response or None if generation fails
    """
    try:
        # Get relevant context from vector search
        context_chunks = get_similar_chunks(query, top_k=3)
        context_text = "\n".join([
            f"Context {i+1}:\n{chunk['metadata']['text']}\n"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Construct prompt with context
        system_prompt = (
            "You are a helpful assistant for a restaurant information system. "
            "Use the provided context to answer questions about restaurants, "
            "their menus, and related information. If you're not sure about "
            "something, say so rather than making assumptions."
        )
        
        user_prompt = f"Question: {query}\n\nRelevant Context:\n{context_text}"
        
        # Get conversation history
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history.get_messages())
        messages.append({"role": "user", "content": user_prompt})
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            n=1,
            stop=None
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the chat functionality
    print("\n=== Testing Chat Response Generation ===")
    
    # Create conversation history
    history = ConversationHistory()
    
    # Test queries
    test_queries = [
        "What are some highly rated restaurants?",
        "Tell me more about their menu items",
        "Are there any vegetarian options?",
        "What's the price range like?"
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        response = generate_response(query, conversation_history=history)
        if response:
            print(f"\nAssistant: {response}")
        else:
            print("\nError: Could not generate response")
        print("\n" + "="*50) 