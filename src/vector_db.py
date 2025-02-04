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

def init_pinecone() -> Optional[Any]:
    """
    Initialize Pinecone with environment variables and connect to existing index
    
    Returns:
        Optional[Any]: Initialized Pinecone index if successful, None otherwise
    """
    try:
        # Initialize Pinecone
        api_key = os.getenv('PINECONE_API_KEY')
        environment = os.getenv('PINECONE_ENVIRONMENT')
        
        # Debug information
        print("\nEnvironment variables:")
        print(f"API Key found: {'Yes' if api_key else 'No'}")
        print(f"Environment found: {'Yes' if environment else 'No'}")
        if environment:
            print(f"Environment value: {environment}")
            
        if not api_key or not environment:
            print("Error: Pinecone API key or environment not found in .env file")
            return None
            
        print(f"\nInitializing Pinecone with environment: {environment}")
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=api_key)
        
        # List available indexes
        indexes = pc.list_indexes()
        print("\nAvailable indexes:", [index.name for index in indexes])
        
        # Get the existing index
        if not any(index.name == INDEX_NAME for index in indexes):
            print(f"\nError: Index '{INDEX_NAME}' not found. Please create it in the Pinecone console first.")
            return None
            
        # Connect to existing index
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        print(f"\nConnected to index '{INDEX_NAME}'")
        print(f"Index stats: {stats}")
            
        return index
        
    except Exception as e:
        print(f"\nError initializing Pinecone: {str(e)}")
        print("\nDebug information:")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Environment file path: {os.path.abspath('../.env')}")
        print(f"Environment file exists: {os.path.exists('../.env')}")
        return None

def upsert_embeddings(
    index: Any,
    embedded_chunks: List[EmbeddedChunk],
    batch_size: int = 100,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> bool:
    """
    Upsert embeddings into Pinecone index
    
    Args:
        index: Initialized Pinecone index
        embedded_chunks (List[EmbeddedChunk]): List of chunks with embeddings to upsert
        batch_size (int): Number of vectors to upsert in each batch
        max_retries (int): Maximum number of retry attempts per batch
        retry_delay (float): Delay between retries in seconds
        
    Returns:
        bool: True if all upserts were successful, False otherwise
    """
    try:
        # Prepare vectors with IDs and metadata
        vectors = []
        for i, chunk in enumerate(embedded_chunks):
            # Convert numpy types to Python native types
            metadata = convert_to_native_types(chunk.metadata)
            embedding = convert_to_native_types(chunk.embedding)
            
            vectors.append({
                'id': f"chunk_{i}",
                'values': embedding,
                'metadata': metadata
            })
        
        print(f"Preparing to upsert {len(vectors)} vectors in batches of {batch_size}")
        
        # Upsert in batches with progress bar
        success = True
        for i in tqdm(range(0, len(vectors), batch_size), desc="Upserting to Pinecone"):
            batch = vectors[i:i + batch_size]
            
            # Retry logic for each batch
            for attempt in range(max_retries):
                try:
                    index.upsert(vectors=batch)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Failed to upsert batch after {max_retries} attempts.")
                        print(f"Error: {str(e)}")
                        success = False
                    else:
                        print(f"Attempt {attempt + 1} failed. Retrying...")
                        time.sleep(retry_delay)
        
        return success
        
    except Exception as e:
        print(f"Error upserting embeddings: {str(e)}")
        return False

def query_similar(
    index: Any,
    query_embedding: List[float],
    top_k: int = 5,
    include_metadata: bool = True,
    score_threshold: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Query Pinecone index for similar vectors
    
    Args:
        index: Initialized Pinecone index
        query_embedding (List[float]): Query vector to find similar embeddings
        top_k (int): Number of similar results to return
        include_metadata (bool): Whether to include metadata in results
        score_threshold (float): Minimum similarity score for results
        
    Returns:
        List[Dict[str, Any]]: List of similar items with scores and metadata
    """
    try:
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=include_metadata
        )
        
        # Filter results by score threshold
        matches = results.get('matches', [])
        if score_threshold > 0:
            matches = [m for m in matches if m.get('score', 0) >= score_threshold]
            
        return matches
        
    except Exception as e:
        print(f"Error querying Pinecone: {str(e)}")
        return []

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