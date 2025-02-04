import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from query import get_similar_chunks, format_results

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

def create_prompt_with_context(
    query: str,
    context_results: List[Dict[str, Any]],
    conversation_history: Optional[ConversationHistory] = None
) -> List[Dict[str, str]]:
    """
    Create a prompt for the OpenAI API using the query, context, and conversation history
    
    Args:
        query (str): The user's query
        context_results (List[Dict[str, Any]]): Retrieved context from vector search
        conversation_history (Optional[ConversationHistory]): Previous conversation history
        
    Returns:
        List[Dict[str, str]]: Messages for the OpenAI chat completion API
    """
    # Start with system message defining the assistant's role
    messages = [{
        "role": "system",
        "content": """You are a knowledgeable restaurant assistant who helps users find information about restaurants and their menus. 
Your responses should be:
1. Accurate and based only on the provided context
2. Natural and conversational
3. Concise but informative
4. Focused on answering the user's specific question

If you don't have enough information in the context to fully answer a question, acknowledge what you don't know.
If the context doesn't contain any relevant information, politely say so."""
    }]
    
    # Add conversation history if available
    if conversation_history:
        messages.extend(conversation_history.get_messages())
    
    # Format context into a string
    context_str = format_results(context_results)
    
    # Add context and query as user message
    messages.append({
        "role": "user",
        "content": f"""Context information:
{context_str}

User question: {query}"""
    })
    
    return messages

def generate_response(
    query: str,
    conversation_history: Optional[ConversationHistory] = None,
    model: str = "gpt-4-turbo-preview",
    temperature: float = 0.7,
    max_tokens: int = 500
) -> Optional[str]:
    """
    Generate a response to the user's query using the OpenAI API
    
    Args:
        query (str): The user's query
        conversation_history (Optional[ConversationHistory]): Previous conversation history
        model (str): OpenAI model to use
        temperature (float): Response creativity (0.0 to 1.0)
        max_tokens (int): Maximum response length
        
    Returns:
        Optional[str]: Generated response if successful, None otherwise
    """
    try:
        # Get relevant context from vector search
        context_results = get_similar_chunks(query, top_k=3)
        
        # Create prompt with context
        messages = create_prompt_with_context(
            query,
            context_results,
            conversation_history
        )
        
        # Generate response using OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract response text
        if response.choices and response.choices[0].message:
            response_text = response.choices[0].message.content
            
            # Update conversation history if provided
            if conversation_history:
                conversation_history.add_message("user", query)
                conversation_history.add_message("assistant", response_text)
            
            return response_text
            
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