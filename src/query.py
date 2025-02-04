import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import numpy as np
from pinecone import Index
from src.embedding import get_embedding
from src.vector_db import init_pinecone, query_similar, convert_to_native_types

# Load environment variables
load_dotenv(override=True)

def embed_query(query: str) -> Optional[List[float]]:
    """
    Generate an embedding for a user query
    
    Args:
        query (str): The user's query text
        
    Returns:
        Optional[List[float]]: Embedding vector if successful, None otherwise
    """
    try:
        # Clean and validate query
        if not query or not query.strip():
            print("Error: Query cannot be empty")
            return None
            
        # Generate embedding
        embedding = get_embedding(query.strip())
        if embedding:
            # Convert to native Python types for Pinecone
            return convert_to_native_types(embedding)
        return None
        
    except Exception as e:
        print(f"Error embedding query: {str(e)}")
        return None

async def get_similar_chunks(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.7,
    filter_dict: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Get chunks similar to the query using vector search
    
    Args:
        query: Search query
        top_k: Number of results to return
        score_threshold: Minimum similarity score
        filter_dict: Optional metadata filters
        
    Returns:
        List of similar chunks with metadata and scores
    """
    try:
        # Initialize Pinecone
        index = init_pinecone()
        if not index:
            print("Error: Failed to initialize vector database")
            return []
            
        # Get query embedding
        query_embedding = await get_embedding(query)
        if not query_embedding:
            print("Error: Failed to generate query embedding")
            return []
            
        # Query similar vectors
        results = query_similar(
            index=index,
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            filter=filter_dict
        )
        
        return results
        
    except Exception as e:
        print(f"Error getting similar chunks: {str(e)}")
        return []

def format_results(results: List[Dict[str, Any]]) -> str:
    """
    Format the search results into a readable string
    
    Args:
        results (List[Dict[str, Any]]): List of search results
        
    Returns:
        str: Formatted string of results
    """
    if not results:
        return "No relevant information found."
        
    formatted = []
    for i, result in enumerate(results, 1):
        score = result.get('score', 0)
        metadata = result.get('metadata', {})
        
        # Format based on chunk type
        chunk_type = metadata.get('type', '')
        if chunk_type == 'restaurant_overview':
            formatted.append(
                f"{i}. Restaurant: {metadata.get('restaurant_name', 'Unknown')}\n"
                f"   Rating: {metadata.get('rating', 'N/A')}\n"
                f"   Price Range: {metadata.get('price_range', 'N/A')}\n"
                f"   Relevance Score: {score:.2f}"
            )
        elif chunk_type == 'menu_item':
            formatted.append(
                f"{i}. Menu Item: {metadata.get('item_name', 'Unknown')}\n"
                f"   Restaurant: {metadata.get('restaurant_name', 'Unknown')}\n"
                f"   Category: {metadata.get('category', 'N/A')}\n"
                f"   Relevance Score: {score:.2f}"
            )
        else:
            # Generic format for other types
            formatted.append(
                f"{i}. Result:\n"
                f"   {metadata}\n"
                f"   Relevance Score: {score:.2f}"
            )
    
    return "\n\n".join(formatted)

if __name__ == "__main__":
    # Test the query functionality
    print("\n=== Testing Query Processing ===")
    
    # Test queries
    test_queries = [
        "What are some highly rated restaurants?",
        "Tell me about Italian restaurants",
        "What vegetarian options are available?",
        "Show me restaurants with good ratings"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = get_similar_chunks(query, top_k=3)
        print("\nResults:")
        print(format_results(results))
        print("\n" + "="*50) 