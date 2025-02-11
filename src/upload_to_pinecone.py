import os
import json
import argparse
from pinecone import Pinecone
from tqdm import tqdm
import time
import sys
import ijson  # For streaming JSON processing
import hashlib
import re
from typing import List, Union, Dict, Tuple
import numpy as np
from decimal import Decimal
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pinecone_upload.log')
    ]
)

def sanitize_id(id_str: str) -> str:
    """Sanitize ID to ensure it only contains ASCII characters."""
    # Replace non-alphanumeric characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9]', '_', id_str)
    # Ensure the ID starts with a letter (Pinecone requirement)
    if not sanitized[0].isalpha():
        sanitized = 'id_' + sanitized
    return sanitized

def convert_to_float_list(embedding: Union[List, Dict]) -> List[float]:
    """Convert embedding values to float type."""
    if isinstance(embedding, dict):
        # Handle case where embedding might be a dictionary
        return [float(v) for v in embedding.values()]
    return [float(v) for v in embedding]

def sanitize_metadata(metadata: Dict) -> Dict:
    """Sanitize metadata values to ensure they are of valid types for Pinecone."""
    sanitized = {}
    for key, value in metadata.items():
        # Skip null/None values entirely
        if value is None:
            continue
            
        if isinstance(value, (int, float, str, bool)):
            # Handle NaN values by skipping them
            if isinstance(value, float) and np.isnan(value):
                continue
                
            # Convert numpy types to Python native types
            if isinstance(value, (np.int64, np.int32)):
                sanitized[key] = int(value)
            elif isinstance(value, (np.float64, np.float32, Decimal)):
                # Keep tokens as integer, convert other numeric fields to float
                if key == 'tokens':
                    sanitized[key] = int(value)
                else:
                    sanitized[key] = float(value)
            else:
                sanitized[key] = value
        elif isinstance(value, list):
            # Filter out None values from lists and convert remaining items
            valid_items = [item for item in value if item is not None]
            if valid_items:  # Only include non-empty lists
                sanitized[key] = [str(item) if not isinstance(item, (int, float, str, bool)) else item 
                                for item in valid_items]
        else:
            # Convert other types to string, but only if they have a value
            str_value = str(value)
            if str_value.strip():  # Only include non-empty strings
                sanitized[key] = str_value
    
    return sanitized

def generate_chunk_id(chunk: dict) -> str:
    """Generate a unique ID for a chunk based on its content."""
    # Create a string combining text and metadata
    content = chunk.get("text", "") + str(chunk.get("metadata", {}))
    # Generate a hash
    hash_id = hashlib.md5(content.encode()).hexdigest()
    return f"chunk_{hash_id}"  # Ensure ID starts with a letter

def verify_index_count(index) -> int:
    """Verify the number of vectors in the index."""
    try:
        stats = index.describe_index_stats()
        return stats.total_vector_count
    except Exception as e:
        logging.error(f"Error getting index stats: {str(e)}")
        return 0

def clear_index(index) -> None:
    """Clear all vectors from the Pinecone index."""
    try:
        current_count = verify_index_count(index)
        logging.info(f"Current vector count before clearing: {current_count}")
        
        # Delete all vectors in the index
        logging.info("Clearing existing vectors from the index...")
        index.delete(delete_all=True)
        
        # Verify deletion
        time.sleep(2)  # Wait for deletion to complete
        new_count = verify_index_count(index)
        logging.info(f"Vector count after clearing: {new_count}")
        
        if new_count > 0:
            logging.warning(f"Index still contains {new_count} vectors after clearing")
    except Exception as e:
        logging.error(f"Error clearing index: {str(e)}")
        raise

def upload_batch(index, batch: list) -> Tuple[int, int, List[str]]:
    """Upload a single batch of vectors to Pinecone."""
    successful = 0
    failed = 0
    failed_ids = []
    
    try:
        vectors = []
        for chunk in batch:
            try:
                # Add ID if not present or sanitize existing ID
                if "id" not in chunk:
                    chunk_id = generate_chunk_id(chunk)
                else:
                    chunk_id = sanitize_id(chunk["id"])
                
                # Convert embedding to float list
                embedding = convert_to_float_list(chunk["embedding"])
                
                # Sanitize metadata
                metadata = sanitize_metadata(chunk["metadata"])
                
                vectors.append((
                    chunk_id,
                    embedding,
                    metadata
                ))
            except Exception as e:
                logging.error(f"Error processing chunk: {str(e)}")
                failed += 1
                failed_ids.append(chunk_id if 'chunk_id' in locals() else 'unknown')
                continue
        
        if vectors:
            index.upsert(vectors=vectors)
            successful = len(vectors)
        
        return successful, failed, failed_ids
    except Exception as e:
        logging.error(f"Error uploading batch: {str(e)}")
        return 0, len(batch), [f"batch_{time.time()}"]

def process_and_upload(pc: Pinecone, file_path: str, index_name: str = "restaurant-chatbot", batch_size: int = 100, should_clear: bool = False):
    """Process JSON file in chunks and upload to Pinecone."""
    try:
        file_size = os.path.getsize(file_path)
        logging.info(f"Processing {file_size / (1024*1024):.2f} MB from {file_path}")
        
        # Get existing index
        index = pc.Index(index_name)
        
        # Get initial count
        initial_count = verify_index_count(index)
        logging.info(f"Initial vector count: {initial_count}")
        
        # Clear the index if requested
        if should_clear:
            clear_index(index)
        
        # Process file in chunks
        successful_uploads = 0
        failed_uploads = 0
        failed_chunk_ids = []
        current_batch = []
        total_chunks = 0
        
        # First, count total chunks
        logging.info("Counting total chunks...")
        with open(file_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            total_chunks = len(chunks)
        
        logging.info(f"Found {total_chunks} chunks to process")
        
        # Process chunks with progress bar
        with tqdm(total=total_chunks, desc="Uploading chunks") as pbar:
            for chunk in chunks:
                # Validate chunk has required fields
                if not all(k in chunk for k in ["text", "embedding", "metadata"]):
                    logging.warning(f"Skipping invalid chunk: missing required fields")
                    failed_uploads += 1
                    continue
                
                current_batch.append(chunk)
                
                if len(current_batch) >= batch_size:
                    success, failed, failed_ids = upload_batch(index, current_batch)
                    successful_uploads += success
                    failed_uploads += failed
                    failed_chunk_ids.extend(failed_ids)
                    current_batch = []
                    pbar.update(batch_size)
                    
                    # Log progress
                    logging.info(f"Progress: {successful_uploads}/{total_chunks} chunks uploaded successfully")
                    if failed_uploads > 0:
                        logging.warning(f"Failed uploads so far: {failed_uploads}")
                    
                    time.sleep(0.5)  # Rate limiting
            
            # Upload any remaining chunks
            if current_batch:
                success, failed, failed_ids = upload_batch(index, current_batch)
                successful_uploads += success
                failed_uploads += failed
                failed_chunk_ids.extend(failed_ids)
                pbar.update(len(current_batch))
        
        # Verify final count
        final_count = verify_index_count(index)
        logging.info("\nUpload Summary:")
        logging.info(f"- Total chunks processed: {total_chunks}")
        logging.info(f"- Successfully uploaded: {successful_uploads} chunks")
        logging.info(f"- Failed to upload: {failed_uploads} chunks")
        logging.info(f"- Initial vector count: {initial_count}")
        logging.info(f"- Final vector count: {final_count}")
        logging.info(f"- Net change: {final_count - initial_count} vectors")
        
        if failed_chunk_ids:
            logging.warning("Failed chunk IDs:")
            for chunk_id in failed_chunk_ids[:10]:  # Show first 10 failed IDs
                logging.warning(f"- {chunk_id}")
            if len(failed_chunk_ids) > 10:
                logging.warning(f"... and {len(failed_chunk_ids) - 10} more")
        
        if final_count != total_chunks and not should_clear:
            logging.warning(f"WARNING: Final count ({final_count}) does not match total chunks ({total_chunks})")
            
    except Exception as e:
        logging.error(f"Error during processing: {str(e)}")
        sys.exit(1)

def main():
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Upload chunks to Pinecone index')
        parser.add_argument('--clear', action='store_true', help='Clear the index before uploading')
        parser.add_argument('--batch-size', type=int, default=100, help='Batch size for uploads')
        args = parser.parse_args()
        
        # Initialize Pinecone
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            logging.error("PINECONE_API_KEY environment variable not set")
            sys.exit(1)
            
        pc = Pinecone(api_key=api_key)
        
        # Process and upload chunks
        process_and_upload(
            pc, 
            "data/indexed_chunks.json", 
            should_clear=args.clear,
            batch_size=args.batch_size
        )
        
    except KeyboardInterrupt:
        logging.warning("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 