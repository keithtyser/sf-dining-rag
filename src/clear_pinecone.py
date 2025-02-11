import os
import logging
import argparse
from dotenv import load_dotenv, dotenv_values
from pinecone import Pinecone
from typing import Literal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pinecone_clear.log')
    ]
)

# Define valid index names
VALID_INDEXES = {
    "restaurant-chatbot": "Restaurant data index",
    "wikipedia-chunks": "Wikipedia articles index",
    "news-chunks": "News articles index"
}

def clear_pinecone_index(index_name: str = "restaurant-chatbot"):
    """Clear all vectors from the specified Pinecone index."""
    try:
        # Validate index name
        if index_name not in VALID_INDEXES:
            raise ValueError(f"Invalid index name. Must be one of: {', '.join(VALID_INDEXES.keys())}")

        # Load API key from .env
        config = dotenv_values(".env")
        api_key = config.get('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in .env file")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # Get the index
        index = pc.Index(name=index_name)
        
        # Get all vector IDs
        stats = index.describe_index_stats()
        logging.info(f"Current stats for index '{index_name}' ({VALID_INDEXES[index_name]}):")
        logging.info(f"Vector count: {stats.total_vector_count}")
        logging.info(f"Dimension: {stats.dimension}")
        
        # Delete all vectors
        index.delete(delete_all=True)
        logging.info(f"Successfully cleared all vectors from index '{index_name}'")
        
        # Verify deletion
        stats = index.describe_index_stats()
        logging.info(f"Index stats after clearing:")
        logging.info(f"Vector count: {stats.total_vector_count}")
        
    except Exception as e:
        logging.error(f"Error clearing Pinecone index '{index_name}': {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Clear all vectors from a Pinecone index')
    parser.add_argument(
        '--index-name',
        default='restaurant-chatbot',
        choices=list(VALID_INDEXES.keys()),
        help='Name of the Pinecone index to clear'
    )
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    try:
        # Check for required environment variables
        if not os.getenv('PINECONE_API_KEY'):
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        
        # Confirm with user unless --force is used
        if not args.force:
            print(f"\nYou are about to clear the following index:")
            print(f"Index: {args.index_name}")
            print(f"Description: {VALID_INDEXES[args.index_name]}")
            print("\nWARNING: This action will permanently delete all vectors in the index.")
            response = input(f"\nAre you sure you want to proceed? Type the index name '{args.index_name}' to confirm: ")
            if response != args.index_name:
                logging.info("Operation cancelled - index name confirmation did not match")
                return
        
        # Clear the index
        logging.info(f"Clearing Pinecone index '{args.index_name}' ({VALID_INDEXES[args.index_name]})...")
        clear_pinecone_index(args.index_name)
        logging.info("Operation completed successfully")
        
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 