import pytest
import numpy as np
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.vector_db import init_pinecone, upsert_embeddings, query_similar, delete_old_vectors, SearchResult
from src.embedding import EmbeddedChunk, get_embedding, create_restaurant_embedding

# Test data
TEST_RESTAURANT = {
    "id": "test123",
    "name": "Test Italian Restaurant",
    "cuisine_type": "Italian",
    "rating": 4.5,
    "price_range": "$$",
    "description": "A cozy Italian restaurant serving authentic pasta.",
    "popular_dishes": ["Spaghetti Carbonara", "Margherita Pizza"],
    "location": "123 Test St"
}

class MockPineconeIndex:
    """Mock Pinecone index for testing"""
    def __init__(self):
        self.vectors = {}
        self.dimension = 1536
        self.name = "restaurant-chatbot"
        self.describe_index_stats = Mock(return_value={
            "dimension": self.dimension,
            "total_vector_count": 0,
            "namespaces": {}
        })
        
    def upsert(self, vectors: List[Dict[str, Any]]):
        for vector in vectors:
            self.vectors[vector["id"]] = {
                "values": vector["values"],
                "metadata": vector.get("metadata", {})
            }
            
    def query(self, vector: List[float], top_k: int = 10, include_metadata: bool = True, filter: Dict = None):
        # Simple mock implementation - return all vectors with mock scores
        matches = []
        for vid, v in self.vectors.items():
            # Apply filter if provided
            if filter and not self._matches_filter(v["metadata"], filter):
                continue
                
            matches.append({
                "id": vid,
                "score": 0.99,  # Mock similarity score
                "metadata": v["metadata"] if include_metadata else None
            })
        return {"matches": matches[:top_k]}
        
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
        
    def delete(self, ids: List[str] = None, filter: Dict = None):
        """Mock delete operation"""
        if ids:
            for id in ids:
                self.vectors.pop(id, None)
        elif filter:
            to_delete = []
            for vid, v in self.vectors.items():
                if self._matches_filter(v["metadata"], filter):
                    to_delete.append(vid)
            for vid in to_delete:
                self.vectors.pop(vid)

@pytest.fixture
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
        with patch.dict('os.environ', {'PINECONE_API_KEY': 'test-key'}):
            yield mock_pc

@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    with patch("src.embedding.OpenAI") as mock_client:
        # Create mock response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        
        # Set up client mock
        mock_instance = Mock()
        mock_instance.embeddings.create.return_value = mock_response
        mock_client.return_value = mock_instance
        
        # Set environment variables
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            yield mock_client

@pytest.fixture
async def test_embedding(mock_openai):
    """Create a test restaurant embedding"""
    # Mock get_embedding function
    with patch('src.embedding.get_embedding', new=AsyncMock(return_value=[0.1] * 1536)):
        return await create_restaurant_embedding(TEST_RESTAURANT)

@pytest.mark.asyncio
async def test_create_restaurant_embedding(mock_openai):
    """Test creating an embedding for a restaurant"""
    # Mock get_embedding function
    with patch('src.embedding.get_embedding', new=AsyncMock(return_value=[0.1] * 1536)):
        embedding = await create_restaurant_embedding(TEST_RESTAURANT)
        
        assert embedding is not None
        assert isinstance(embedding, EmbeddedChunk)
        assert embedding.text.startswith("Test Italian Restaurant is a Italian")
        assert len(embedding.embedding) == 1536
        assert embedding.metadata["restaurant_id"] == "test123"
        assert embedding.metadata["restaurant_name"] == "Test Italian Restaurant"
        assert embedding.metadata["type"] == "restaurant_overview"

def test_init_pinecone(mock_pinecone):
    """Test Pinecone initialization"""
    index = init_pinecone()
    assert index is not None
    assert index.describe_index_stats.call_count == 1
    stats = index.describe_index_stats()
    assert stats is not None
    assert "dimension" in stats
    assert stats["dimension"] == 1536  # OpenAI embedding dimension

def test_upsert_embeddings(mock_pinecone, test_embedding):
    """Test upserting embeddings to Pinecone"""
    index = mock_pinecone
    success = upsert_embeddings(index, [test_embedding])
    
    assert success is True
    index.upsert.assert_called_once()
    
    # Verify the upserted data format
    vectors = index.upsert.call_args[1]["vectors"]
    assert len(vectors) == 1
    vector_id, vector_data, metadata = vectors[0]
    assert isinstance(vector_data, list)
    assert len(vector_data) == 1536
    assert metadata["restaurant_name"] == "Test Italian Restaurant"

def test_query_similar(mock_pinecone):
    """Test querying similar vectors"""
    index = mock_pinecone
    
    # Mock query response
    mock_match = Mock(
        id="test123",
        score=0.85,
        metadata={
            "restaurant_name": "Test Italian Restaurant",
            "rating": 4.5,
            "price_range": "$$"
        }
    )
    index.query.return_value.matches = [mock_match]
    
    # Test query
    results = query_similar(
        index=index,
        query_embedding=[0.1] * 1536,
        top_k=5,
        score_threshold=0.7
    )
    
    assert len(results) == 1
    assert results[0]["id"] == "test123"
    assert results[0]["score"] == 0.85
    assert results[0]["metadata"]["restaurant_name"] == "Test Italian Restaurant"

def test_query_similar_with_filters(mock_pinecone):
    """Test querying similar vectors with filters"""
    index = mock_pinecone
    
    # Test query with filters
    filter_dict = {
        "price_range": "$$",
        "rating": {"$gte": 4.0}
    }
    
    query_similar(
        index=index,
        query_embedding=[0.1] * 1536,
        filter=filter_dict
    )
    
    # Verify filter was passed correctly
    index.query.assert_called_once()
    assert index.query.call_args[1]["filter"] == filter_dict

def test_query_similar_score_threshold(mock_pinecone):
    """Test score threshold filtering"""
    index = mock_pinecone
    
    # Mock matches with different scores
    mock_matches = [
        Mock(id="1", score=0.9, metadata={"name": "High Score"}),
        Mock(id="2", score=0.6, metadata={"name": "Low Score"})
    ]
    index.query.return_value.matches = mock_matches
    
    # Query with threshold
    results = query_similar(
        index=index,
        query_embedding=[0.1] * 1536,
        score_threshold=0.8
    )
    
    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["score"] == 0.9

def test_delete_old_vectors(mock_pinecone):
    """Test deleting old vectors"""
    index = mock_pinecone
    success = delete_old_vectors(index, days_old=30)
    
    assert success is True
    index.delete.assert_called_once()
    
    # Verify delete filter
    delete_filter = index.delete.call_args[1]["filter"]
    assert "timestamp" in delete_filter
    assert "$lt" in delete_filter["timestamp"]

@pytest.mark.asyncio
async def test_end_to_end_vector_search(mock_pinecone, mock_openai):
    """Test the complete vector search flow"""
    # Mock get_embedding function
    with patch('src.embedding.get_embedding', new=AsyncMock(return_value=[0.1] * 1536)):
        # Create test embedding
        embedding = await create_restaurant_embedding(TEST_RESTAURANT)
        assert embedding is not None
        
        # Upsert to index
        index = mock_pinecone
        success = upsert_embeddings(index, [embedding])
        assert success is True
        
        # Generate query embedding
        query = "Italian restaurants with good pasta"
        query_embedding = await get_embedding(query)
        assert query_embedding is not None
        
        # Mock query response
        mock_match = Mock(
            id="test123",
            score=0.85,
            metadata={
                "restaurant_name": "Test Italian Restaurant",
                "rating": 4.5,
                "price_range": "$$"
            }
        )
        index.query.return_value.matches = [mock_match]
        
        # Search with filters
        results = query_similar(
            index=index,
            query_embedding=query_embedding,
            filter={"cuisine_type": "Italian", "rating": {"$gte": 4.0}},
            top_k=5
        )
        
        assert len(results) > 0
        for result in results:
            assert isinstance(result, dict)
            assert "id" in result
            assert "score" in result
            assert "metadata" in result 