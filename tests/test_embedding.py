import pytest
import asyncio
import numpy as np
from src.embedding import generate_embedding

def test_generate_embedding_valid_input():
    """Test embedding generation with valid input"""
    text = "Test restaurant query"
    embedding = generate_embedding(text)
    
    # Check that we get a valid embedding
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 1536  # OpenAI embedding dimension
    assert all(isinstance(x, float) for x in embedding)

def test_generate_embedding_empty_input():
    """Test embedding generation with empty input"""
    text = ""
    embedding = generate_embedding(text)
    
    # Should return None for empty input
    assert embedding is None

def test_generate_embedding_whitespace_input():
    """Test embedding generation with whitespace input"""
    text = "   \n\t   "
    embedding = generate_embedding(text)
    
    # Should return None for whitespace-only input
    assert embedding is None

def test_generate_embedding_long_input():
    """Test embedding generation with long input"""
    # Create a long text input
    text = "restaurant " * 1000
    embedding = generate_embedding(text)
    
    # Should still get a valid embedding
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 1536

def test_generate_embedding_special_chars():
    """Test embedding generation with special characters"""
    text = "Restaurant & Café! #1 (Best) [Food]"
    embedding = generate_embedding(text)
    
    # Should handle special characters
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) == 1536

@pytest.mark.asyncio
async def test_generate_embedding_concurrent():
    """Test concurrent embedding generation"""
    texts = [
        "First restaurant query",
        "Second restaurant query",
        "Third restaurant query"
    ]
    
    # Generate embeddings concurrently
    embeddings = await asyncio.gather(*[
        asyncio.to_thread(generate_embedding, text)
        for text in texts
    ])
    
    # Check all embeddings
    for embedding in embeddings:
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 1536

def test_generate_embedding_consistency():
    """Test that same input produces consistent embeddings"""
    text = "Test restaurant consistency"
    
    # Generate embeddings multiple times
    embedding1 = generate_embedding(text)
    embedding2 = generate_embedding(text)
    
    # Convert to numpy arrays for comparison
    arr1 = np.array(embedding1)
    arr2 = np.array(embedding2)
    
    # Check that embeddings are identical
    assert np.allclose(arr1, arr2) 