import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch
from src.embedding import EmbeddedChunk
from src.vector_db import init_pinecone, upsert_embeddings, query_similar, convert_to_native_types

class MockPineconeIndex:
    def __init__(self):
        self.vectors = {}
        self.dimension = 1536
        self.name = "restaurant-chatbot"
        
    def describe_index_stats(self):
        return {
            "dimension": self.dimension,
            "total_vector_count": len(self.vectors),
            "namespaces": {}
        }
        
    def upsert(self, vectors: List[Dict[str, Any]]):
        for vector in vectors:
            self.vectors[vector["id"]] = {
                "values": vector["values"],
                "metadata": vector.get("metadata", {})
            }
            
    def query(self, vector: List[float], top_k: int = 10, include_metadata: bool = True):
        # Simple mock implementation - return all vectors with mock scores
        matches = []
        for vid, v in self.vectors.items():
            matches.append({
                "id": vid,
                "score": 0.99,  # Mock similarity score
                "metadata": v["metadata"] if include_metadata else None
            })
        return {"matches": matches[:top_k]}

@pytest.fixture(autouse=True)
def mock_pinecone():
    """Create a mock Pinecone client"""
    mock_index = MockPineconeIndex()
    mock_pc = MagicMock()
    mock_pc.Index.return_value = mock_index
    
    # Create a mock index object with the correct name
    mock_index_obj = MagicMock()
    mock_index_obj.name = "restaurant-chatbot"
    mock_pc.list_indexes.return_value = [mock_index_obj]
    
    with patch("src.vector_db.Pinecone", return_value=mock_pc):
        yield mock_pc

@pytest.fixture
def test_chunks(mock_embedding) -> List[EmbeddedChunk]:
    """Create test chunks with embeddings"""
    return [
        EmbeddedChunk(
            text="Test Restaurant 1 is a great place to eat",
            embedding=mock_embedding,
            metadata={
                "type": "restaurant_overview",
                "restaurant_name": "Test Restaurant 1",
                "rating": 4.5,
                "price_range": "$$"
            }
        ),
        EmbeddedChunk(
            text="Test Restaurant 2 serves amazing food",
            embedding=mock_embedding,
            metadata={
                "type": "restaurant_overview",
                "restaurant_name": "Test Restaurant 2",
                "rating": 4.0,
                "price_range": "$$$"
            }
        )
    ]

def test_init_pinecone(mock_pinecone):
    """Test Pinecone initialization"""
    index = init_pinecone()
    assert index is not None
    stats = index.describe_index_stats()
    assert stats is not None
    assert "dimension" in stats
    assert stats["dimension"] == 1536  # OpenAI embedding dimension

def test_convert_to_native_types():
    """Test conversion of numpy types to Python native types"""
    # Test with numpy scalar
    np_float = np.float64(3.14)
    assert isinstance(convert_to_native_types(np_float), float)
    
    # Test with numpy array
    np_array = np.array([1.0, 2.0, 3.0])
    result = convert_to_native_types(np_array)
    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    
    # Test with dictionary containing numpy types
    test_dict = {
        "float": np.float64(1.23),
        "array": np.array([4.0, 5.0, 6.0]),
        "nested": {
            "value": np.int64(42)
        }
    }
    result = convert_to_native_types(test_dict)
    assert isinstance(result["float"], float)
    assert isinstance(result["array"], list)
    assert isinstance(result["nested"]["value"], int)

def test_upsert_embeddings(mock_pinecone, test_chunks):
    """Test upserting embeddings to Pinecone"""
    index = init_pinecone()
    assert index is not None
    
    # Get initial stats
    initial_stats = index.describe_index_stats()
    initial_count = initial_stats.get("total_vector_count", 0)
    
    # Upsert test chunks
    success = upsert_embeddings(index, test_chunks)
    assert success is True
    
    # Verify the upsert
    final_stats = index.describe_index_stats()
    final_count = final_stats.get("total_vector_count", 0)
    assert final_count == initial_count + len(test_chunks)

def test_query_similar(mock_pinecone, test_chunks):
    """Test querying similar vectors"""
    index = init_pinecone()
    assert index is not None
    
    # First upsert test data
    success = upsert_embeddings(index, test_chunks)
    assert success is True
    
    # Query using the first chunk's embedding
    query_embedding = convert_to_native_types(test_chunks[0].embedding)
    results = query_similar(index, query_embedding, top_k=2)
    
    # Verify results
    assert len(results) > 0
    assert "score" in results[0]
    assert "metadata" in results[0]
    assert results[0]["score"] > 0.5  # Should have high similarity
    assert results[0]["metadata"]["type"] == "restaurant_overview"

def test_query_similar_with_threshold(mock_pinecone, test_chunks):
    """Test querying similar vectors with score threshold"""
    index = init_pinecone()
    assert index is not None
    
    # First upsert test data
    success = upsert_embeddings(index, test_chunks)
    assert success is True
    
    # Query with a high threshold
    query_embedding = convert_to_native_types(test_chunks[0].embedding)
    results = query_similar(index, query_embedding, top_k=2, score_threshold=0.95)
    
    # Verify results
    assert all(result["score"] >= 0.95 for result in results)

def test_query_similar_empty_index(mock_pinecone):
    """Test querying when index is empty"""
    index = init_pinecone()
    assert index is not None
    
    # Create a random query vector
    query_embedding = list(np.random.rand(1536))
    results = query_similar(index, query_embedding)
    
    # Should return empty list
    assert len(results) == 0 