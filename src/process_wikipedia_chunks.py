import os
import json
import logging
from typing import List, Dict
from tqdm import tqdm
from openai import OpenAI
from pinecone import Pinecone
import time
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wikipedia_processing.log')
    ]
)

def get_embedding(text: str, client: OpenAI, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for a piece of text using OpenAI's API."""
    try:
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error getting embedding: {str(e)}")
        return None

def validate_chunk(chunk: Dict) -> bool:
    """Validate chunk data before processing and upload."""
    try:
        # Check for required fields
        if not all(k in chunk for k in ['id', 'text', 'metadata']):
            logging.warning(f"Chunk {chunk.get('id', 'unknown')} missing required fields")
            return False
            
        # Validate text content
        if not chunk['text'] or len(chunk['text'].strip()) < 10:
            logging.warning(f"Chunk {chunk.get('id', 'unknown')} has insufficient text content")
            return False
            
        # Validate metadata
        required_metadata = ['title', 'source', 'type']
        if not all(k in chunk['metadata'] for k in required_metadata):
            logging.warning(f"Chunk {chunk.get('id', 'unknown')} missing required metadata fields")
            return False
            
        return True
        
    except Exception as e:
        logging.warning(f"Error validating chunk: {str(e)}")
        return False

def process_chunks(chunks: List[Dict], client: OpenAI, test_mode: bool = False) -> List[Dict]:
    """Process chunks by adding embeddings."""
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
            
            # Get embedding for the chunk text
            embedding = get_embedding(chunk['text'], client)
            if embedding and len(embedding) == 1536:  # Verify embedding dimension
                chunk['embedding'] = embedding
                processed_chunks.append(chunk)
                
                # In test mode, print more detailed information
                if test_mode:
                    logging.info(f"Successfully processed chunk: {chunk['id']}")
                    logging.info(f"Text length: {len(chunk['text'])}")
                    logging.info(f"Embedding dimension: {len(embedding)}")
            else:
                logging.warning(f"Failed to get valid embedding for chunk: {chunk['id']}")
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Error processing chunk {chunk['id']}: {str(e)}")
            continue
    
    return processed_chunks

def upload_to_pinecone(chunks: List[Dict], index_name: str = "wikipedia-chunks", test_mode: bool = False):
    """Upload processed chunks to Pinecone."""
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index(index_name)
        
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
                    'type': str(chunk['metadata'].get('type', '')),
                    'source_type': 'wikipedia',
                    'summary': str(chunk['metadata'].get('summary', '')),
                    'category': str(chunk['metadata'].get('category', '')),
                    'subcategory': str(chunk['metadata'].get('subcategory', '')),
                    'url': str(chunk['metadata'].get('url', '')),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
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
        batch_size = 10 if test_mode else 100  # Smaller batch size for testing
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
        logging.error(f"Error initializing Pinecone: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Process Wikipedia chunks and upload to Pinecone')
    parser.add_argument('--input', default='data/wikipedia_chunks.json', help='Input JSON file containing Wikipedia chunks')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for uploads')
    parser.add_argument('--test', action='store_true', help='Run in test mode with a small sample')
    parser.add_argument('--skip-upload', action='store_true', help='Skip uploading to Pinecone')
    parser.add_argument('--index-name', default='wikipedia-chunks', help='Name of the Pinecone index to use')
    args = parser.parse_args()
    
    try:
        # Check for required environment variables
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not os.getenv('PINECONE_API_KEY'):
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        client = OpenAI()
        
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