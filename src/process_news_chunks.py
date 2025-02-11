import os
import json
import logging
from typing import List, Dict
from tqdm import tqdm
from openai import OpenAI
from pinecone import Pinecone
import time
import argparse
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv, dotenv_values

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('news_processing.log')
    ]
)

def get_embedding(text: str, client: OpenAI, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for a piece of text using OpenAI's API."""
    text = text.replace("\n", " ")
    try:
        return client.embeddings.create(input=[text], model=model).data[0].embedding
    except Exception as e:
        logging.error(f"Error getting embedding: {e}")
        return None

def calculate_time_weight(publish_date: str, chunk_type: str = "content") -> float:
    """Calculate a weight based on how recent the article is and chunk type."""
    try:
        pub_date = datetime.fromisoformat(publish_date)
        now = datetime.utcnow()
        age_days = (now - pub_date).days
        
        # Exponential decay with half-life of 30 days
        base_weight = 2 ** (-age_days / 30)
        
        # Title chunks get a small boost as they're more important for context
        type_multiplier = 1.2 if chunk_type == "title" else 1.0
        
        weight = base_weight * type_multiplier
        return min(max(weight, 0.1), 1.0)  # Clamp between 0.1 and 1.0
    except:
        return 0.5  # Default weight if date parsing fails

def generate_chunk_id(chunk: Dict) -> str:
    """Generate a unique ID for a chunk based on its content."""
    # Create a string combining text and metadata
    content = chunk.get("text", "") + str(chunk.get("metadata", {}))
    # Generate a hash
    hash_id = hashlib.md5(content.encode()).hexdigest()
    return f"news_{hash_id}"

def validate_chunk(chunk: Dict) -> bool:
    """Validate that a chunk has all required fields and proper structure."""
    try:
        # Check required top-level fields
        required_fields = ["text", "metadata"]
        if not all(field in chunk for field in required_fields):
            logging.warning(f"Chunk missing required fields: {required_fields}")
            return False
            
        # Check text content
        if not chunk["text"] or len(chunk["text"].strip()) < 10:
            logging.warning("Chunk text too short or empty")
            return False
            
        # Check required metadata fields
        required_metadata = ["source", "title", "url", "publish_date", "chunk_type", "type"]
        if not all(field in chunk["metadata"] for field in required_metadata):
            logging.warning(f"Chunk metadata missing required fields: {required_metadata}")
            return False
            
        # Validate chunk type
        if chunk["metadata"]["chunk_type"] not in ["title", "content"]:
            logging.warning(f"Invalid chunk type: {chunk['metadata']['chunk_type']}")
            return False
            
        # Validate publish date format
        try:
            datetime.fromisoformat(chunk['metadata']['publish_date'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logging.warning("Invalid publish_date format")
            return False
            
        return True
    except Exception as e:
        logging.warning(f"Error validating chunk: {str(e)}")
        return False

def process_chunks(chunks: List[Dict], client: OpenAI, test_mode: bool = False) -> List[Dict]:
    """Process news chunks by adding embeddings and temporal weights."""
    processed_chunks = []
    
    # If in test mode, only process a small sample
    if test_mode:
        sample_size = min(10, len(chunks))
        chunks = chunks[:sample_size]
        logging.info(f"Test mode: Processing {sample_size} chunks as a sample")
    
    # First, validate all chunks
    valid_chunks = []
    for chunk in tqdm(chunks, desc="Validating chunks"):
        if validate_chunk(chunk):
            valid_chunks.append(chunk)
        else:
            logging.warning(f"Skipping invalid chunk: {chunk.get('id', 'unknown')}")
    
    logging.info(f"Found {len(valid_chunks)} valid chunks out of {len(chunks)} total chunks")
    
    for chunk in tqdm(valid_chunks, desc="Processing chunks"):
        try:
            # Clean text by removing excessive whitespace
            chunk['text'] = ' '.join(chunk['text'].split())
            
            # Generate ID if not present
            if "id" not in chunk:
                chunk["id"] = f"news_{hashlib.md5(chunk['text'].encode()).hexdigest()}"
            
            # Calculate temporal weight based on chunk type
            time_weight = calculate_time_weight(
                chunk['metadata'].get('publish_date', ''),
                chunk['metadata'].get('chunk_type', 'content')
            )
            
            # Get embedding for the chunk text
            embedding = get_embedding(chunk['text'], client)
            if embedding and len(embedding) == 1536:  # Verify embedding dimension
                # Add temporal weight and embedding
                chunk['embedding'] = embedding
                chunk['metadata']['time_weight'] = time_weight
                processed_chunks.append(chunk)
                
                # In test mode, print more detailed information
                if test_mode:
                    logging.info(f"Successfully processed chunk: {chunk['id']}")
                    logging.info(f"Text length: {len(chunk['text'])}")
                    logging.info(f"Embedding dimension: {len(embedding)}")
                    logging.info(f"Time weight: {time_weight}")
            else:
                logging.warning(f"Failed to get valid embedding for chunk: {chunk['id']}")
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            logging.error(f"Error processing chunk {chunk.get('id', 'unknown')}: {str(e)}")
            continue
    
    return processed_chunks

def upload_to_pinecone(chunks: List[Dict], index_name: str = "news-chunks", test_mode: bool = False):
    """Upload processed chunks to Pinecone with temporal metadata."""
    try:
        # Load API key from .env file
        config = dotenv_values(".env")
        api_key = config.get('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in .env file")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        index = pc.Index(name=index_name)
        
        # In test mode, verify the connection and index first
        if test_mode:
            logging.info("Test mode: Verifying Pinecone connection and index...")
            try:
                stats = index.describe_index_stats()
                logging.info(f"Successfully connected to index. Current stats: {stats}")
            except Exception as e:
                logging.error(f"Error connecting to Pinecone: {str(e)}")
                return
        
        # Prepare vectors for upload
        vectors = []
        for chunk in chunks:
            try:
                # Final validation before upload
                if not chunk.get('embedding') or len(chunk['embedding']) != 1536:
                    logging.warning(f"Skipping chunk {chunk['id']} due to invalid embedding")
                    continue
                
                if not chunk.get('text'):
                    logging.warning(f"Skipping chunk {chunk['id']} due to missing text content")
                    continue
                
                # Ensure metadata values are of valid types for Pinecone
                metadata = {
                    'text': str(chunk['text']),  # Include the actual text content
                    'source': str(chunk['metadata'].get('source', '')),
                    'title': str(chunk['metadata'].get('title', '')),
                    'url': str(chunk['metadata'].get('url', '')),
                    'author': str(chunk['metadata'].get('author', '')),
                    'publish_date': str(chunk['metadata'].get('publish_date', '')),
                    'chunk_type': str(chunk['metadata'].get('chunk_type', 'content')),
                    'type': str(chunk['metadata'].get('type', 'article')),
                    'time_weight': float(chunk['metadata'].get('time_weight', 0.5)),
                    'source_type': 'news',
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                # Handle complex types (lists, dicts) by converting to JSON strings
                if chunk['metadata'].get('keywords'):
                    metadata['keywords'] = json.dumps(chunk['metadata']['keywords'])
                if chunk['metadata'].get('categories'):
                    metadata['categories'] = json.dumps(chunk['metadata']['categories'])
                
                # Add any additional metadata fields
                for k, v in chunk['metadata'].items():
                    if k not in metadata:
                        if isinstance(v, (list, dict)):
                            metadata[k] = json.dumps(v)  # Convert complex types to JSON strings
                        else:
                            metadata[k] = str(v) if not isinstance(v, (bool, int, float)) else v
                
                vectors.append((
                    chunk["id"],
                    [float(v) for v in chunk["embedding"]],  # Ensure all values are float
                    metadata
                ))
            except Exception as e:
                logging.error(f"Error preparing chunk for upload: {str(e)}")
                continue
        
        if not vectors:
            logging.warning("No valid vectors to upload")
            return
            
        logging.info(f"Preparing to upload {len(vectors)} vectors")
        
        # Upload in batches
        batch_size = 10 if test_mode else 100
        total_batches = (len(vectors) + batch_size - 1) // batch_size
        
        with tqdm(total=len(vectors), desc="Uploading to Pinecone") as pbar:
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                try:
                    index.upsert(vectors=batch)
                    pbar.update(len(batch))
                    if test_mode:
                        logging.info(f"Successfully uploaded batch {i//batch_size + 1}/{total_batches}")
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    logging.error(f"Error uploading batch {i//batch_size + 1}: {str(e)}")
                    continue
        
        # Verify upload
        final_stats = index.describe_index_stats()
        logging.info(f"Upload complete. Final index stats: {final_stats}")
                
    except Exception as e:
        logging.error(f"Error in Pinecone upload: {str(e)}")
        raise

def cleanup_old_news(index_name: str = "restaurant-chatbot", max_age_days: int = 90):
    """Remove news articles older than the specified age."""
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index(index_name)
        
        cutoff_date = (datetime.utcnow() - timedelta(days=max_age_days)).isoformat()
        
        # Query for old news articles
        old_articles = index.query(
            filter={
                "source_type": "news",
                "publish_date": {"$lt": cutoff_date}
            },
            top_k=10000,  # Adjust based on your needs
            include_metadata=True
        )
        
        if old_articles.matches:
            # Delete old articles
            ids_to_delete = [match.id for match in old_articles.matches]
            index.delete(ids=ids_to_delete)
            
            logging.info(f"Removed {len(ids_to_delete)} old news articles")
            
    except Exception as e:
        logging.error(f"Error cleaning up old news: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Process news chunks and upload to Pinecone')
    parser.add_argument('--input', default='data/news_chunks.json', help='Input JSON file containing news chunks')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for uploads')
    parser.add_argument('--test', action='store_true', help='Run in test mode with a small sample')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup of old news articles')
    parser.add_argument('--max-age-days', type=int, default=90, help='Maximum age in days for news articles')
    parser.add_argument('--skip-upload', action='store_true', help='Skip uploading to Pinecone')
    parser.add_argument('--index-name', default='news-chunks', help='Name of the Pinecone index to use')
    args = parser.parse_args()
    
    try:
        # Check for required environment variables
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not os.getenv('PINECONE_API_KEY'):
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        client = OpenAI()
        
        if args.cleanup:
            cleanup_old_news(max_age_days=args.max_age_days, index_name=args.index_name)
            return
        
        # Load chunks
        logging.info(f"Loading chunks from {args.input}")
        with open(args.input, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        total_chunks = len(chunks)
        logging.info(f"Loaded {total_chunks} chunks")
        
        if args.test:
            logging.info("Running in test mode with a small sample")
            # Save a sample of the chunks for testing
            sample_file = args.input.replace('.json', '_sample.json')
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(chunks[:10], f, ensure_ascii=False, indent=2)
            logging.info(f"Saved sample chunks to {sample_file}")
        
        # Process chunks
        processed_chunks = process_chunks(chunks, client, test_mode=args.test)
        logging.info(f"Successfully processed {len(processed_chunks)} chunks")
        
        if args.test:
            # Save processed sample for verification
            output_file = args.input.replace('.json', '_processed_sample.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_chunks, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved processed sample to {output_file}")
        
        # Upload to Pinecone if not skipped
        if not args.skip_upload:
            upload_to_pinecone(processed_chunks, index_name=args.index_name, test_mode=args.test)
            logging.info("Upload complete")
        
        if args.test:
            logging.info("Test run completed successfully. Review the sample files and logs before running on the full dataset.")
        
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 