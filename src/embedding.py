import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables. Please set OPENAI_API_KEY.")

client = OpenAI(api_key=api_key)

@dataclass
class EmbeddedChunk:
    """Class to hold text chunk and its embedding"""
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]

def generate_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for a single text using OpenAI's API"""
    # Handle empty or whitespace-only input
    if not text or not text.strip():
        return None
        
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        raise

def batch_generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a batch of texts using OpenAI's API"""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        raise

def embed_chunks(
    chunks: List[Dict[str, Any]], 
    batch_size: int = 100,
    max_retries: int = 3
) -> List[EmbeddedChunk]:
    """
    Generate embeddings for a list of text chunks
    
    Args:
        chunks (List[Dict[str, Any]]): List of chunks with text and metadata
        batch_size (int): Number of chunks to process at once
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        List[EmbeddedChunk]: List of chunks with embeddings
    """
    embedded_chunks = []
    
    for i in tqdm(range(0, len(chunks), batch_size)):
        batch = chunks[i:i + batch_size]
        
        for chunk in batch:
            embedding = generate_embedding(chunk["text"])
            if embedding:
                embedded_chunks.append(EmbeddedChunk(
                    text=chunk["text"],
                    embedding=embedding,
                    metadata=chunk["metadata"]
                ))
    
    return embedded_chunks

def save_embeddings(embedded_chunks: List[EmbeddedChunk], output_file: str) -> None:
    """
    Save embeddings and their metadata to a numpy file
    
    Args:
        embedded_chunks (List[EmbeddedChunk]): List of embedded chunks
        output_file (str): Path to save the embeddings
    """
    # Convert to numpy arrays
    embeddings = np.array([chunk.embedding for chunk in embedded_chunks])
    texts = np.array([chunk.text for chunk in embedded_chunks])
    metadata = np.array([chunk.metadata for chunk in embedded_chunks])
    
    # Save to file
    np.savez(
        output_file,
        embeddings=embeddings,
        texts=texts,
        metadata=metadata
    )
    print(f"Saved {len(embedded_chunks)} embeddings to {output_file}")

def load_embeddings(file_path: str) -> List[EmbeddedChunk]:
    """
    Load pre-computed embeddings from a numpy file
    
    Args:
        file_path (str): Path to the .npz file containing embeddings
        
    Returns:
        List[EmbeddedChunk]: List of chunks with embeddings
    """
    try:
        data = np.load(file_path, allow_pickle=True)
        chunks = []
        
        for text, embedding, metadata in zip(data['texts'], data['embeddings'], data['metadata']):
            chunks.append(EmbeddedChunk(
                text=text,
                embedding=embedding.tolist(),
                metadata=metadata.item()
            ))
            
        return chunks
    except Exception as e:
        print(f"Error loading embeddings: {str(e)}")
        return []

if __name__ == "__main__":
    # Test the embedding functionality
    from chunking import TextChunk, create_restaurant_chunks
    from ingestion import load_csv, organize_restaurant_data
    
    print("\n=== Testing Embedding Generation ===")
    
    # Check if OpenAI API key is configured
    if not client.api_key:
        print("Error: OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        exit(1)
    
    # Load and organize data
    print("\n=== Loading Restaurant Data ===")
    df = load_csv('../data/sample_restaurant_data.csv')
    
    if not df.empty:
        # Create chunks from first restaurant only for testing
        print("\n=== Creating Test Chunks ===")
        restaurants = organize_restaurant_data(df)
        first_restaurant = dict(list(restaurants.items())[0:1])
        chunks = create_restaurant_chunks(first_restaurant)
        print(f"Created {len(chunks)} chunks for testing")
        
        # Generate embeddings
        print("\n=== Generating Embeddings ===")
        embedded_chunks = embed_chunks(chunks[:5])  # Test with first 5 chunks only
        print(f"Generated {len(embedded_chunks)} embeddings")
        
        # Display sample results
        print("\n=== Sample Embedded Chunks ===")
        for chunk in embedded_chunks[:2]:
            print("\nChunk:")
            print(f"Text: {chunk.text[:100]}...")
            print(f"Embedding shape: {len(chunk.embedding)}")
            print(f"Metadata: {chunk.metadata}")
        
        # Test saving and loading
        print("\n=== Testing Save/Load ===")
        save_embeddings(embedded_chunks, '../data/test_embeddings.npz')
        loaded_chunks = load_embeddings('../data/test_embeddings.npz')
        print(f"Successfully loaded {len(loaded_chunks)} embedded chunks")
        
    else:
        print("Error: Could not load restaurant data") 