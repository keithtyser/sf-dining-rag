import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm
import time

def load_api_key(file_path: str = '../api_key.txt') -> Optional[str]:
    """
    Load OpenAI API key from a text file
    
    Args:
        file_path (str): Path to the API key file
        
    Returns:
        Optional[str]: API key if found, None otherwise
    """
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading API key: {str(e)}")
        return None

# Initialize OpenAI client
api_key = load_api_key()
if not api_key:
    raise ValueError("OpenAI API key not found. Please create api_key.txt file with your API key.")
    
client = OpenAI(api_key=api_key)

@dataclass
class EmbeddedChunk:
    """Class to represent a chunk of text with its embedding and metadata"""
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]

def get_embedding(
    text: str,
    model: str = "text-embedding-ada-002",
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Optional[List[float]]:
    """
    Generate an embedding for a piece of text using OpenAI's API
    
    Args:
        text (str): Text to embed
        model (str): OpenAI model to use for embedding
        max_retries (int): Maximum number of retry attempts
        retry_delay (float): Delay between retries in seconds
        
    Returns:
        List[float]: Embedding vector if successful, None otherwise
    """
    if not text.strip():
        return None
        
    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=[text.strip()],
                model=model
            )
            return response.data[0].embedding
            
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                print(f"Failed to generate embedding after {max_retries} attempts.")
                print(f"Error: {str(e)}")
                return None
            print(f"Attempt {attempt + 1} failed. Retrying...")
            time.sleep(retry_delay)

def embed_chunks(
    chunks: List['TextChunk'],
    batch_size: int = 100,
    max_retries: int = 3
) -> List[EmbeddedChunk]:
    """
    Generate embeddings for a list of text chunks
    
    Args:
        chunks (List[TextChunk]): List of text chunks to embed
        batch_size (int): Number of chunks to process in each batch
        max_retries (int): Maximum number of retry attempts per chunk
        
    Returns:
        List[EmbeddedChunk]: List of chunks with their embeddings
    """
    embedded_chunks = []
    
    # Process chunks in batches with progress bar
    for i in tqdm(range(0, len(chunks), batch_size), desc="Generating embeddings"):
        batch = chunks[i:i + batch_size]
        
        for chunk in batch:
            embedding = get_embedding(chunk.text, max_retries=max_retries)
            if embedding:
                embedded_chunks.append(EmbeddedChunk(
                    text=chunk.text,
                    embedding=embedding,
                    metadata=chunk.metadata
                ))
            else:
                print(f"Warning: Failed to generate embedding for chunk: {chunk.text[:100]}...")
    
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

def load_embeddings(input_file: str) -> List[EmbeddedChunk]:
    """
    Load embeddings and their metadata from a numpy file
    
    Args:
        input_file (str): Path to the embeddings file
        
    Returns:
        List[EmbeddedChunk]: List of embedded chunks
    """
    # Load from file
    data = np.load(input_file, allow_pickle=True)
    
    # Convert back to EmbeddedChunk objects
    embedded_chunks = [
        EmbeddedChunk(text=text, embedding=embedding, metadata=metadata)
        for text, embedding, metadata in zip(
            data['texts'],
            data['embeddings'],
            data['metadata']
        )
    ]
    
    print(f"Loaded {len(embedded_chunks)} embeddings from {input_file}")
    return embedded_chunks

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