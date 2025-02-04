import os
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import pinecone
from tqdm import tqdm
from src.embedding import EmbeddedChunk, load_embeddings
import time
from dataclasses import dataclass
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv(override=True)  # Force reload of environment variables

# Constants
INDEX_NAME = "restaurant-chatbot"
DIMENSION = 1536  # OpenAI ada-002 embedding dimension

def convert_to_native_types(obj: Any) -> Any:
    """
    Convert numpy types to Python native types
    
    Args:
        obj: Any object that might contain numpy types
        
    Returns:
        The same object with numpy types converted to Python native types
    """
    if isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

@dataclass
class SearchResult:
    """Class to represent a search result"""
    id: str
    score: float
    metadata: Dict[str, Any]

def init_pinecone() -> Optional[pinecone.Index]:
    """
    Initialize Pinecone client and return index
    
    Returns:
        Optional[pinecone.Index]: Pinecone index or None if initialization fails
    """
    try:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            print("Error: Pinecone API key not found")
            return None
            
        pc = Pinecone(api_key=api_key)
        
        # Check if index exists
        indexes = pc.list_indexes()
        if not any(idx.name == INDEX_NAME for idx in indexes):
            # Create index if it doesn't exist
            pc.create_index(
                name=INDEX_NAME,
                dimension=DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-west-2")
            )
            
        # Get index and verify dimension
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        if stats["dimension"] != DIMENSION:
            print(f"Error: Index dimension mismatch. Expected {DIMENSION}, got {stats['dimension']}")
            return None
            
        return index
        
    except Exception as e:
        print(f"Error initializing Pinecone: {str(e)}")
        return None

def upsert_embeddings(index: pinecone.Index, chunks: List[EmbeddedChunk], batch_size: int = 100) -> bool:
    """
    Upsert embeddings to Pinecone index in batches
    
    Args:
        index: Pinecone index
        chunks: List of EmbeddedChunk objects
        batch_size: Number of vectors to upsert in each batch
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        for i in tqdm(range(0, len(chunks), batch_size), total=total_batches, desc="Upserting vectors"):
            batch = chunks[i:i + batch_size]
            
            # Convert embeddings to native Python types
            vectors = []
            for chunk in batch:
                vector = convert_to_native_types(chunk.embedding)
                metadata = {
                    "text": chunk.text,
                    "type": chunk.metadata.get("type", "unknown"),
                    "restaurant_id": chunk.metadata.get("restaurant_id", "unknown"),
                    "restaurant_name": chunk.metadata.get("restaurant_name", "unknown"),
                    "category": chunk.metadata.get("category", "unknown"),
                    "timestamp": time.time()
                }
                vectors.append((str(chunk.id), vector, metadata))
            
            # Upsert batch
            index.upsert(vectors=vectors)
            
        return True
        
    except Exception as e:
        print(f"Error upserting vectors: {str(e)}")
        return False

def query_similar(
    index: pinecone.Index,
    query_embedding: List[float],
    top_k: int = 5,
    score_threshold: float = 0.7,
    filter: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    Query similar vectors from Pinecone
    
    Args:
        index: Pinecone index
        query_embedding: Query vector
        top_k: Number of results to return
        score_threshold: Minimum similarity score threshold
        filter: Optional metadata filters
        
    Returns:
        List of similar vectors with their metadata and scores
    """
    try:
        # Query the index
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        # Filter and format results
        filtered_results = []
        for match in results.matches:
            if match.score >= score_threshold:
                filtered_results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
        
        return filtered_results
        
    except Exception as e:
        print(f"Error querying similar vectors: {str(e)}")
        return []

def delete_old_vectors(index: pinecone.Index, days_old: int = 30) -> bool:
    """
    Delete vectors older than specified days
    
    Args:
        index: Pinecone index
        days_old: Age threshold in days
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Calculate timestamp threshold
        threshold = time.time() - (days_old * 24 * 60 * 60)
        
        # Delete old vectors
        index.delete(
            filter={
                "timestamp": {"$lt": threshold}
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Error deleting old vectors: {str(e)}")
        return False

if __name__ == "__main__":
    # Test Pinecone connection and basic operations
    print("\n=== Testing Pinecone Integration ===")
    
    # Initialize Pinecone
    print("\n=== Initializing Pinecone ===")
    index = init_pinecone()
    if not index:
        print("Failed to initialize Pinecone")
        exit(1)
    
    print(f"\nSuccessfully connected to Pinecone index: {INDEX_NAME}")
    print(f"Index stats: {index.describe_index_stats()}")
    
    # Test upserting embeddings
    print("\n=== Testing Embedding Upsert ===")
    try:
        # Load test embeddings
        test_embeddings = load_embeddings('../data/test_embeddings.npz')
        if test_embeddings:
            print(f"\nLoaded {len(test_embeddings)} test embeddings")
            
            # Upsert embeddings
            success = upsert_embeddings(index, test_embeddings)
            if success:
                print("\nSuccessfully upserted test embeddings to Pinecone")
                
                # Verify the upsert by querying the first vector
                print("\n=== Verifying Upsert with Query ===")
                first_embedding = convert_to_native_types(test_embeddings[0].embedding)
                results = query_similar(index, first_embedding, top_k=1)
                
                if results:
                    print("\nSuccessfully retrieved a matching vector:")
                    print(f"Score: {results[0]['score']}")
                    print(f"Metadata: {results[0]['metadata']}")
                else:
                    print("\nWarning: Could not retrieve the upserted vector")
            else:
                print("\nFailed to upsert some or all test embeddings")
                
            # Get updated stats
            print("\n=== Updated Index Stats ===")
            print(index.describe_index_stats())
        else:
            print("\nNo test embeddings found. Please run embedding.py first to generate test embeddings.")
    except Exception as e:
        print(f"Error testing embedding upsert: {str(e)}") 