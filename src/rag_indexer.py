import os
import json
import pandas as pd
from typing import Dict, List
from openai import OpenAI
from tqdm import tqdm
import tiktoken
import logging
import argparse
from collections import defaultdict
from dotenv import dotenv_values
import time
from pinecone import Pinecone
from datetime import datetime
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('restaurant_indexing.log')
    ]
)

# initialize openai client
client = OpenAI()

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def get_embedding(text: str, model="text-embedding-3-small") -> List[float]:
    """Get embedding for a piece of text using OpenAI's API."""
    text = text.replace("\n", " ")
    try:
        return client.embeddings.create(input=[text], model=model).data[0].embedding
    except Exception as e:
        logging.error(f"Error getting embedding: {e}")
        return None

def categorize_menu_item(category: str) -> str:
    """Categorize menu items into broader groups."""
    category = category.lower()
    if any(drink in category for drink in ['wine', 'beer', 'cocktail', 'spirit', 'beverage', 'drink', 'champagne', 'no proof']):
        return 'drinks'
    elif any(dessert in category for dessert in ['dessert', 'sweet', 'pastry']):
        return 'desserts'
    elif any(starter in category for starter in ['appetizer', 'starter', 'snack', 'small plate']):
        return 'starters'
    elif any(main in category for main in ['main', 'entree', 'pizza', 'pasta']):
        return 'mains'
    else:
        return 'other'

def generate_restaurant_keywords(row: pd.Series, menu_items: pd.DataFrame) -> List[str]:
    """Generate relevant keywords for a restaurant based on its data."""
    keywords = set()
    
    # Add categories as keywords
    if pd.notna(row['categories']):
        keywords.update(cat.lower().strip() for cat in row['categories'].split('|'))
    
    # Add price-based keywords
    if pd.notna(row['price']):
        if row['price'] == '$':
            keywords.update(['cheap', 'affordable', 'budget-friendly'])
        elif row['price'] == '$$':
            keywords.update(['moderate', 'mid-range'])
        elif row['price'] in ['$$$', '$$$$']:
            keywords.update(['expensive', 'upscale', 'fine dining'])
    
    # Add rating-based keywords
    if pd.notna(row['rating']):
        rating = float(row['rating'])
        if rating >= 4.5:
            keywords.update(['top-rated', 'highly rated', 'best'])
        elif rating >= 4.0:
            keywords.add('well-rated')
    
    # Add meal type keywords based on menu items
    menu_categories = menu_items['menu_category'].dropna().str.lower()
    if 'breakfast' in menu_categories.values or 'brunch' in menu_categories.values:
        keywords.update(['breakfast', 'brunch'])
    if 'lunch' in menu_categories.values:
        keywords.add('lunch')
    if 'dinner' in menu_categories.values:
        keywords.add('dinner')
    
    # Add cuisine type keywords
    cuisine_keywords = {
        'steakhouse': ['steak', 'steakhouse', 'prime rib'],
        'sushi': ['sushi', 'japanese', 'sashimi'],
        'italian': ['pasta', 'pizza', 'italian'],
        'mexican': ['tacos', 'burritos', 'mexican'],
        'chinese': ['dim sum', 'chinese', 'asian'],
        'indian': ['curry', 'indian', 'tandoori'],
        'vegetarian': ['vegetarian', 'vegan', 'plant-based'],
        'seafood': ['seafood', 'fish', 'oysters']
    }
    
    # Check menu items and categories for cuisine keywords
    menu_text = ' '.join(menu_items['menu_item'].dropna().astype(str).str.lower())
    for cuisine_type, keywords_list in cuisine_keywords.items():
        if any(keyword in menu_text.lower() for keyword in keywords_list):
            keywords.add(cuisine_type)
    
    return sorted(list(keywords))

def sanitize_id(text: str) -> str:
    """Sanitize text to create a valid Pinecone ID (ASCII only)."""
    # Replace special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    # Replace multiple underscores with a single one
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized

def process_restaurant_data(df: pd.DataFrame, test_mode: bool = False) -> List[Dict]:
    """Process restaurant data into chunks with comprehensive metadata."""
    chunks = []
    MAX_TOKENS = 4096  # Set to half of model's limit to be safe
    
    # Group data by restaurant
    restaurant_groups = df.groupby('restaurant_name')
    restaurant_names = list(restaurant_groups.groups.keys())
    
    # In test mode, only process a few restaurants
    if test_mode:
        sample_size = min(1, len(restaurant_names))
        restaurant_names = restaurant_names[:sample_size]
        logging.info(f"Test mode: Processing {sample_size} restaurants as a sample")
    
    # Process each restaurant
    for restaurant_name in tqdm(restaurant_names, desc="Processing restaurants"):
        try:
            restaurant_df = restaurant_groups.get_group(restaurant_name)
            
            # Generate keywords for the restaurant
            sample_row = restaurant_df.iloc[0]
            keywords = generate_restaurant_keywords(sample_row, restaurant_df)
            
            # Group menu items by category
            menu_by_category = defaultdict(list)
            for _, row in restaurant_df.iterrows():
                category = categorize_menu_item(row['menu_category'])
                menu_by_category[category].append(row)
            
            # Create restaurant overview chunk
            overview_text = f"""
Restaurant: {restaurant_name}
Location: {sample_row['address1']}, {sample_row['city']}, {sample_row['state']} {sample_row['zip_code']}
Categories: {sample_row['categories']}
Rating: {sample_row['rating']} stars ({sample_row['review_count']} reviews)
Price Range: {sample_row['price']}
Menu Categories: {', '.join(sorted(set(restaurant_df['menu_category'].dropna())))}
Keywords: {', '.join(keywords)}
"""
            
            # Check overview chunk size
            overview_tokens = count_tokens(overview_text)
            if overview_tokens <= MAX_TOKENS:
                overview_embedding = get_embedding(overview_text)
                if overview_embedding:
                    overview_chunk = {
                        "id": f"restaurant_{sanitize_id(restaurant_name)}_overview",
                        "text": overview_text,
                        "tokens": overview_tokens,
                        "embedding": overview_embedding,
                        "metadata": {
                            "type": "restaurant_overview",
                            "source": "menu",
                            "text": overview_text,
                            "restaurant_name": restaurant_name,
                            "address1": sample_row['address1'],
                            "city": sample_row['city'],
                            "state": sample_row['state'],
                            "zip_code": sample_row['zip_code'],
                            "country": sample_row['country'],
                            "rating": float(sample_row['rating']),
                            "review_count": int(sample_row['review_count']),
                            "price": sample_row['price'],
                            "categories": sample_row['categories'].split('|') if pd.notna(sample_row['categories']) else [],
                            "keywords": keywords,
                            "city": sample_row['city'],
                            "address1": sample_row['address1'],
                        }
                    }
                    chunks.append(overview_chunk)
            else:
                logging.warning(f"Overview chunk for {restaurant_name} exceeds token limit ({overview_tokens} tokens)")
            
            # Create category-specific chunks
            for category, items in menu_by_category.items():
                # Split items into smaller groups if needed
                items_per_chunk = 20  # Adjust this number based on average item size
                for chunk_index in range(0, len(items), items_per_chunk):
                    chunk_items = items[chunk_index:chunk_index + items_per_chunk]
                    
                    # Create category text
                    category_items = []
                    for item in chunk_items:
                        item_text = f"- {item['menu_item']}"
                        if pd.notna(item['menu_description']):
                            item_text += f": {item['menu_description']}"
                        if pd.notna(item['ingredient_name']):
                            item_text += f" (Ingredients: {item['ingredient_name']})"
                        category_items.append(item_text)
                    
                    category_text = f"""
Restaurant: {restaurant_name}
Category: {category.title()}
Items:
{chr(10).join(category_items)}
"""
                    
                    # Check category chunk size
                    category_tokens = count_tokens(category_text)
                    if category_tokens <= MAX_TOKENS:
                        category_embedding = get_embedding(category_text)
                        if category_embedding:
                            chunk_suffix = f"_part{chunk_index//items_per_chunk + 1}" if len(items) > items_per_chunk else ""
                            category_chunk = {
                                "id": f"restaurant_{sanitize_id(restaurant_name)}_{sanitize_id(category)}{chunk_suffix}",
                                "text": category_text,
                                "tokens": category_tokens,
                                "embedding": category_embedding,
                                "metadata": {
                                    "type": "menu_category",
                                    "source": "menu",
                                    "text": category_text,
                                    "restaurant_name": restaurant_name,
                                    "category": category,
                                    "item_count": len(chunk_items),
                                    "total_items": len(items),
                                    "chunk_part": chunk_index//items_per_chunk + 1 if len(items) > items_per_chunk else 1,
                                    "total_parts": (len(items) + items_per_chunk - 1) // items_per_chunk,
                                    "rating": float(sample_row['rating']),
                                    "price": sample_row['price'],
                                    "categories": sample_row['categories'].split('|') if pd.notna(sample_row['categories']) else [],
                                    "city": sample_row['city'],
                                    "address1": sample_row['address1'],
                                }
                            }
                            chunks.append(category_chunk)
                    else:
                        logging.warning(f"Category chunk for {restaurant_name} {category} exceeds token limit ({category_tokens} tokens)")
                    
                # Create individual item chunks
                for item in items:
                    item_text = f"""
Restaurant: {restaurant_name}
Menu Category: {item['menu_category']}
Item: {item['menu_item']}
Description: {item['menu_description'] if pd.notna(item['menu_description']) else 'No description available'}
Ingredients: {item['ingredient_name'] if pd.notna(item['ingredient_name']) else 'No ingredients listed'}
Price Range: {item['price']}
"""
                    
                    # Check item chunk size
                    item_tokens = count_tokens(item_text)
                    if item_tokens <= MAX_TOKENS:
                        item_embedding = get_embedding(item_text)
                        if item_embedding:
                            item_chunk = {
                                "id": f"menu_item_{sanitize_id(restaurant_name)}_{sanitize_id(str(item['menu_item']))}",
                                "text": item_text,
                                "tokens": item_tokens,
                                "embedding": item_embedding,
                "metadata": {
                    "type": "menu_item",
                    "source": "menu",
                                    "text": item_text,
                                    "restaurant_name": restaurant_name,
                                    "menu_category": item['menu_category'],
                                    "broad_category": category,
                                    "menu_item": item['menu_item'],
                                    "ingredients": [ing.strip() for ing in str(item['ingredient_name']).split(',')] if pd.notna(item['ingredient_name']) else [],
                                    "price": item['price'],
                                    "rating": float(item['rating']),
                                    "item_id": item['item_id'],
                                    "city": sample_row['city'],
                                    "address1": sample_row['address1'],
                                }
                            }
                            chunks.append(item_chunk)
                    else:
                        logging.warning(f"Item chunk for {restaurant_name} {item['menu_item']} exceeds token limit ({item_tokens} tokens)")
            
            # Log detailed information about the chunks for this restaurant
            logging.info(f"\nProcessed restaurant: {restaurant_name}")
            chunk_counts = defaultdict(int)
            for chunk in chunks:
                chunk_counts[chunk['metadata']['type']] += 1
            logging.info(f"Created {len(chunks)} chunks:")
            for chunk_type, count in chunk_counts.items():
                logging.info(f"- {count} {chunk_type} chunks")
            
            # Show sample of each type
            for chunk_type in ['restaurant_overview', 'menu_category', 'menu_item']:
                sample = next((c for c in chunks if c['metadata']['type'] == chunk_type), None)
                if sample:
                    logging.info(f"\nSample {chunk_type} chunk:")
                    sample_copy = sample.copy()
                    sample_copy['embedding'] = f"[{len(sample_copy['embedding'])} dimensions]"
                    logging.info(json.dumps(sample_copy, indent=2))
            
        except Exception as e:
            logging.error(f"Error processing restaurant {restaurant_name}: {str(e)}")
            continue
    
    return chunks

def save_chunks(chunks: List[Dict], output_file: str, test_mode: bool = False):
    """Save chunks with embeddings to a JSON file."""
    # In test mode, save to a sample file
    if test_mode:
        output_file = output_file.replace('.json', '_sample.json')
    
    logging.info(f"\nSaving {len(chunks)} chunks to {output_file}...")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Group chunks by type for the summary
    chunks_by_type = defaultdict(int)
    for chunk in chunks:
        chunks_by_type[chunk['metadata']['type']] += 1
    
    # Save the chunks
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    logging.info("Chunks summary:")
    for chunk_type, count in chunks_by_type.items():
        logging.info(f"- {chunk_type}: {count} chunks")
    logging.info(f"Successfully saved all chunks to {output_file}")

def clear_pinecone_index(index_name: str = "restaurant-chatbot"):
    """Clear all vectors from the Pinecone index."""
    try:
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
        logging.info(f"Current index stats before clearing: {stats}")
        
        # Delete all vectors
        index.delete(delete_all=True)
        logging.info("Successfully cleared all vectors from the index")
        
        # Verify deletion
        stats = index.describe_index_stats()
        logging.info(f"Index stats after clearing: {stats}")
        
    except Exception as e:
        logging.error(f"Error clearing Pinecone index: {str(e)}")
        raise

def validate_chunk(chunk: Dict) -> bool:
    """Validate chunk data before upload to Pinecone."""
    try:
        # Check for required fields
        if not all(k in chunk for k in ['id', 'text', 'embedding', 'metadata']):
            logging.warning(f"Chunk {chunk.get('id', 'unknown')} missing required fields")
            return False
            
        # Validate text content
        if not chunk['text'] or len(chunk['text'].strip()) < 10:
            logging.warning(f"Chunk {chunk['id']} has insufficient text content")
            return False
            
        # Validate embedding
        if not chunk['embedding'] or len(chunk['embedding']) != 1536:
            logging.warning(f"Chunk {chunk['id']} has invalid embedding")
            return False
            
        # Validate metadata
        required_metadata = ['type', 'source', 'restaurant_name']
        if not all(k in chunk['metadata'] for k in required_metadata):
            logging.warning(f"Chunk {chunk['id']} missing required metadata fields")
            return False
            
        return True
        
    except Exception as e:
        logging.warning(f"Error validating chunk: {str(e)}")
        return False

def upload_to_pinecone(chunks: List[Dict], index_name: str = "restaurant-chatbot", test_mode: bool = False, batch_size: int = 100):
    """Upload processed chunks to Pinecone with validation."""
    try:
        # Load API key from .env file
        config = dotenv_values(".env")
        api_key = config.get('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in .env file")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        index = pc.Index(name=index_name)
        
        # Track chunks by type
        chunks_by_type = defaultdict(int)
        vectors_by_type = defaultdict(int)
        
        # Validate and prepare vectors
        vectors = []
        for chunk in tqdm(chunks, desc="Preparing vectors"):
            try:
                chunks_by_type[chunk['metadata'].get('type', 'unknown')] += 1
                
                # Final validation before upload
                if not chunk.get('embedding') or len(chunk['embedding']) != 1536:
                    logging.warning(f"Skipping chunk {chunk['id']} due to invalid embedding")
                    continue
                
                if not chunk.get('text'):
                    logging.warning(f"Skipping chunk {chunk['id']} due to missing text content")
                    continue
                
                # Ensure metadata values are of valid types for Pinecone
                metadata = {
                    'text': str(chunk['text']),  # Include the actual text content first
                    'type': str(chunk['metadata'].get('type', '')),
                    'source': str(chunk['metadata'].get('source', '')),
                    'restaurant_name': str(chunk['metadata'].get('restaurant_name', '')),
                    'title': str(chunk['metadata'].get('title', '')),
                    'menu_category': str(chunk['metadata'].get('menu_category', '')),
                    'menu_item': str(chunk['metadata'].get('menu_item', '')),
                    'menu_description': str(chunk['metadata'].get('menu_description', '')),
                    'broad_category': str(chunk['metadata'].get('broad_category', '')),
                    'address1': str(chunk['metadata'].get('address1', '')),
                    'city': str(chunk['metadata'].get('city', '')),
                    'state': str(chunk['metadata'].get('state', '')),
                    'zip_code': str(chunk['metadata'].get('zip_code', '')),
                    'country': str(chunk['metadata'].get('country', '')),
                    'price': str(chunk['metadata'].get('price', '')),
                    'rating': float(chunk['metadata'].get('rating', 0)),
                    'review_count': int(chunk['metadata'].get('review_count', 0)),
                    'item_id': str(chunk['metadata'].get('item_id', '')),
                    'description': str(chunk['metadata'].get('description', '')),
                    'summary': str(chunk['metadata'].get('summary', '')),
                    'publish_date': str(chunk['metadata'].get('publish_date', '')),
                    'source_type': str(chunk['metadata'].get('source_type', 'restaurant')),
                    'last_updated': datetime.utcnow().isoformat()
                }

                # Handle complex types (lists, dicts) by converting to strings
                if chunk['metadata'].get('categories'):
                    metadata['categories'] = json.dumps(chunk['metadata']['categories'])
                if chunk['metadata'].get('ingredients'):
                    metadata['ingredients'] = json.dumps(chunk['metadata']['ingredients'])
                if chunk['metadata'].get('keywords'):
                    metadata['keywords'] = json.dumps(chunk['metadata']['keywords'])

                # Add any additional metadata fields we might have missed
                for k, v in chunk['metadata'].items():
                    if k not in metadata:
                        if isinstance(v, (list, dict)):
                            metadata[k] = json.dumps(v)
                        else:
                            metadata[k] = str(v) if not isinstance(v, (bool, int, float)) else v
                
                vectors.append((
                    chunk["id"],
                    [float(v) for v in chunk["embedding"]],  # Ensure all values are float
                    metadata
                ))
                vectors_by_type[chunk['metadata'].get('type', 'unknown')] += 1
                
            except Exception as e:
                logging.error(f"Error preparing chunk for upload: {str(e)}")
                continue
        
        if not vectors:
            logging.warning("No valid vectors to upload")
            return
        
        # Log chunk type statistics
        logging.info("\nChunk type statistics:")
        logging.info("Input chunks by type:")
        for chunk_type, count in chunks_by_type.items():
            logging.info(f"- {chunk_type}: {count} chunks")
        logging.info("\nValid vectors by type:")
        for chunk_type, count in vectors_by_type.items():
            logging.info(f"- {chunk_type}: {count} vectors")
            
        logging.info(f"\nPreparing to upload {len(vectors)} vectors")
        
        # Upload in batches
        batch_size = min(batch_size, 100)  # Ensure batch size doesn't exceed Pinecone limits
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
        logging.info(f"Final index stats: {final_stats}")
        
    except Exception as e:
        logging.error(f"Error in Pinecone upload: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Process restaurant data and upload to Pinecone')
    parser.add_argument('--input', default='data/sample_restaurant_data.csv', help='Input CSV file')
    parser.add_argument('--output', default='data/indexed_chunks.json', help='Output JSON file')
    parser.add_argument('--test', action='store_true', help='Run in test mode with a small sample')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for Pinecone uploads')
    parser.add_argument('--clear-index', action='store_true', help='Clear the Pinecone index before uploading')
    parser.add_argument('--skip-pinecone', action='store_true', help='Skip uploading to Pinecone')
    args = parser.parse_args()
    
    try:
        # Check for required environment variables
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not os.getenv('PINECONE_API_KEY'):
            raise ValueError("PINECONE_API_KEY environment variable is not set")
        
        # Initialize OpenAI client
        client = OpenAI()
        
        # Clear Pinecone index if requested
        if args.clear_index and not args.skip_pinecone:
            logging.info("Clearing Pinecone index...")
            clear_pinecone_index()
        
        # Load and process restaurant data
        logging.info(f"Loading restaurant data from {args.input}")
        df = pd.read_csv(args.input)
        logging.info(f"Loaded {len(df)} rows of restaurant data")
    
    # Process restaurant data
        chunks = process_restaurant_data(df, test_mode=args.test)
        logging.info(f"Processed {len(chunks)} chunks")
    
    # Save chunks locally
        save_chunks(chunks, args.output, test_mode=args.test)
        
        # Upload to Pinecone if not skipped
        if not args.skip_pinecone:
            logging.info("Uploading chunks to Pinecone...")
            upload_to_pinecone(chunks, test_mode=args.test, batch_size=args.batch_size)
            logging.info("Pinecone upload complete")
        
        if args.test:
            logging.info("\nTest run completed. Review the sample files and logs before running on the full dataset.")
            
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 