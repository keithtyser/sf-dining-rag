import os
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from src.query import get_similar_chunks, format_results
from src.embedding import generate_embedding

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ConversationHistory:
    def __init__(self, max_history: int = 5):
        self.messages: List[Dict[str, str]] = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})
        # Keep only the last max_history messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get the conversation history"""
        return self.messages.copy()
    
    def clear(self):
        """Clear the conversation history"""
        self.messages = []

def create_prompt_with_context(query: str, context: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Create a chat prompt with context from vector search results"""
    system_message = (
        "You are a knowledgeable restaurant assistant who helps users find information about restaurants "
        "and their menus. \n"
        "Your responses should be:\n"
        "1. Accurate and based only on the provided context\n"
        "2. Natural and conversational\n"
        "3. Concise but informative\n"
        "4. Focused on answering the user's specific question\n\n"
    )

    if context:
        system_message += "Here is the relevant context for the current query:\n"
        for i, result in enumerate(context, 1):
            system_message += (
                f"{i}. Restaurant: {result.get('restaurant', 'N/A')}\n"
                f"   Rating: {result.get('rating', 'N/A')}\n"
                f"   Price Range: {result.get('price_range', 'N/A')}\n"
                f"   Description: {result.get('description', 'N/A')}\n"
                f"   Relevance Score: {result.get('score', 0):.2f}\n\n"
            )
    
    system_message += (
        "If you don't have enough information in the context to fully answer a question, "
        "acknowledge what you don't know.\n"
        "If the context doesn't contain any relevant information, politely say so."
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": query}
    ]

def generate_response(
    query: str,
    conversation_history: ConversationHistory,
    client: Optional[OpenAI] = None,
    get_similar_chunks: Optional[Callable] = None
) -> Optional[str]:
    """Generate a response to the user's query using the OpenAI API"""
    try:
        # Use the provided client or create a new one
        openai_client = client or OpenAI()
        
        # Get similar chunks if the function is provided
        context = []
        if get_similar_chunks:
            context = get_similar_chunks(query)
        
        # Create the base messages list with just the system message
        messages = [create_prompt_with_context(query, context)[0]]  # Get only the system message
        
        # Add conversation history
        if conversation_history.messages:
            messages.extend(conversation_history.messages)
            
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        # Extract and return the response content
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content
        
        return None
        
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