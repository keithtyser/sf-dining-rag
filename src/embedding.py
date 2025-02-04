import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dataclasses import dataclass
import numpy as np
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Constants
EMBEDDING_MODEL = "text-embedding-ada-002"
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Initialize OpenAI client with API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables. Please set OPENAI_API_KEY.")

client = OpenAI(api_key=api_key)

@dataclass
class EmbeddedChunk:
    """Class to hold text chunk and its embedding"""
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]

def get_openai_client() -> Optional[OpenAI]:
    """
    Get an initialized OpenAI client
    
    Returns:
        Optional[OpenAI]: Initialized OpenAI client or None if initialization fails
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key not found")
            return None
            
        return OpenAI(api_key=api_key)
        
    except Exception as e:
        print(f"Error initializing OpenAI client: {str(e)}")
        return None

async def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding for a single text using OpenAI's API
    
    Args:
        text: Text to embed
        
    Returns:
        Optional[List[float]]: Embedding vector or None if generation fails
    """
    client = get_openai_client()
    if not client:
        return None
        
    try:
        for attempt in range(MAX_RETRIES):
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"Failed to generate embedding after {MAX_RETRIES} attempts: {str(e)}")
                    return None
                time.sleep(RETRY_DELAY)
                
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None

async def batch_generate_embeddings(texts: List[str], batch_size: int = 100) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts in batches
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts to process in each batch
        
    Returns:
        List[Optional[List[float]]]: List of embedding vectors (None for failed generations)
    """
    client = get_openai_client()
    if not client:
        return [None] * len(texts)
        
    embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    for i in tqdm(range(0, len(texts), batch_size), total=total_batches, desc="Generating embeddings"):
        batch = texts[i:i + batch_size]
        
        try:
            for attempt in range(MAX_RETRIES):
                try:
                    response = client.embeddings.create(
                        model=EMBEDDING_MODEL,
                        input=batch
                    )
                    batch_embeddings = [data.embedding for data in response.data]
                    embeddings.extend(batch_embeddings)
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:
                        print(f"Failed to generate batch embeddings after {MAX_RETRIES} attempts: {str(e)}")
                        embeddings.extend([None] * len(batch))
                    else:
                        time.sleep(RETRY_DELAY)
                        
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            embeddings.extend([None] * len(batch))
            
    return embeddings

async def create_restaurant_embedding(restaurant: Dict[str, Any]) -> Optional[EmbeddedChunk]:
    """
    Create an embedding for a restaurant
    
    Args:
        restaurant: Restaurant data dictionary
        
    Returns:
        Optional[EmbeddedChunk]: Embedded restaurant data or None if embedding fails
    """
    try:
        # Create descriptive text for the restaurant
        text = f"{restaurant['name']} is a {restaurant.get('cuisine_type', 'restaurant')}. "
        text += f"It has a rating of {restaurant.get('rating', 'N/A')} and a price range of {restaurant.get('price_range', 'N/A')}. "
        text += f"{restaurant.get('description', '')} "
        if restaurant.get('popular_dishes'):
            text += f"Popular dishes include: {', '.join(restaurant['popular_dishes'])}. "
        text += f"Located at: {restaurant.get('location', 'N/A')}"
        
        # Generate embedding
        embedding = await get_embedding(text)
        if not embedding:
            return None
            
        return EmbeddedChunk(
            id=restaurant['id'],
            text=text,
            embedding=np.array(embedding),
            metadata={
                "type": "restaurant_overview",
                "restaurant_id": restaurant['id'],
                "restaurant_name": restaurant['name'],
                "rating": restaurant.get('rating'),
                "price_range": restaurant.get('price_range'),
                "cuisine_type": restaurant.get('cuisine_type'),
                "description": restaurant.get('description'),
                "location": restaurant.get('location'),
                "popular_dishes": restaurant.get('popular_dishes', [])
            }
        )
        
    except Exception as e:
        print(f"Error creating restaurant embedding: {str(e)}")
        return None

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