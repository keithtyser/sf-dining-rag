# -*- coding: utf-8 -*-

from typing import List, Dict, Any
import re
from dataclasses import dataclass

@dataclass
class TextChunk:
    """Class to represent a chunk of text with its metadata"""
    text: str
    metadata: Dict[str, Any]
    token_count: int

def count_tokens(text: str) -> int:
    """
    estimate the number of tokens in a text string
    this is a simple estimation; for production, use tiktoken or similar
    
    args:
        text (str): input text
        
    returns:
        int: estimated token count
    """
    # Simple estimation: split on whitespace and punctuation
    return len(re.findall(r'\w+', text))

def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """
    split text into chunks of approximately max_tokens
    
    args:
        text (str): text to split
        max_tokens (int): maximum tokens per chunk
        
    returns:
        list[str]: list of text chunks
    """
    if not text:
        return []
        
    # Split into sentences using regex
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        
        # If single sentence is too long, split on punctuation
        if sentence_tokens > max_tokens:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_token_count = 0
            
            # Split long sentence on punctuation
            parts = re.split(r'[,;:]', sentence)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                    
                part_tokens = count_tokens(part)
                
                if part_tokens > max_tokens:
                    # If still too long, split into fixed size chunks
                    words = part.split()
                    while words:
                        chunk = []
                        chunk_tokens = 0
                        while words and chunk_tokens < max_tokens:
                            word = words[0]
                            word_tokens = len(re.findall(r'\w+', word))
                            if chunk_tokens + word_tokens > max_tokens:
                                break
                            chunk_tokens += word_tokens
                            chunk.append(words.pop(0))
                        if chunk:
                            chunks.append(' '.join(chunk))
                else:
                    chunks.append(part)
        
        # If adding sentence exceeds max_tokens, start new chunk
        elif current_token_count + sentence_tokens > max_tokens:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_token_count = sentence_tokens
        
        # Add sentence to current chunk
        else:
            current_chunk.append(sentence)
            current_token_count += sentence_tokens
    
    # Add final chunk if exists
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return [c for c in chunks if c.strip()]

def create_restaurant_chunks(restaurant_data: Dict[str, Any], max_tokens: int = 500) -> List[TextChunk]:
    """
    create chunks from restaurant data with appropriate metadata
    
    args:
        restaurant_data (dict): hierarchical restaurant data
        max_tokens (int): maximum tokens per chunk
        
    returns:
        list[TextChunk]: list of text chunks with metadata
    """
    chunks = []
    
    for restaurant_name, restaurant_info in restaurant_data.items():
        # Create restaurant overview chunk
        overview = f"Restaurant: {restaurant_name}\n"
        if restaurant_info['rating']:
            overview += f"Rating: {restaurant_info['rating']}\n"
        if restaurant_info['price_range']:
            overview += f"Price Range: {restaurant_info['price_range']}\n"
        
        chunks.append(TextChunk(
            text=overview,
            metadata={
                'restaurant_name': restaurant_name,
                'type': 'restaurant_overview',
                'rating': restaurant_info['rating'],
                'price_range': restaurant_info['price_range']
            },
            token_count=count_tokens(overview)
        ))
        
        # Process each menu category
        for category, items in restaurant_info['menu_categories'].items():
            for item in items:
                # Create item description
                item_text = f"Restaurant: {restaurant_name}\n"
                item_text += f"Category: {category}\n"
                item_text += f"Item: {item['item_name']}\n"
                
                if item['description']:
                    item_text += f"Description: {item['description']}\n"
                
                if item['ingredients']:
                    item_text += f"Ingredients: {', '.join(item['ingredients'])}\n"
                
                if item['co2_emission']:
                    item_text += f"CO2 Emission: {item['co2_emission']}\n"
                
                # Split into chunks if too long
                item_chunks = chunk_text(item_text, max_tokens)
                
                for i, chunk in enumerate(item_chunks):
                    chunks.append(TextChunk(
                        text=chunk,
                        metadata={
                            'restaurant_name': restaurant_name,
                            'type': 'menu_item',
                            'category': category,
                            'item_name': item['item_name'],
                            'chunk_index': i,
                            'total_chunks': len(item_chunks)
                        },
                        token_count=count_tokens(chunk)
                    ))
    
    return chunks

def get_ingredient_chunks(ingredients: List[str], max_tokens: int = 500) -> List[TextChunk]:
    """
    create chunks for ingredient descriptions
    
    args:
        ingredients (list): list of ingredient names
        max_tokens (int): maximum tokens per chunk
        
    returns:
        list[TextChunk]: list of ingredient chunks
    """
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for ingredient in ingredients:
        ingredient_tokens = count_tokens(ingredient)
        
        if current_token_count + ingredient_tokens > max_tokens:
            # Create chunk from accumulated ingredients
            text = "Ingredients: " + ", ".join(current_chunk)
            chunks.append(TextChunk(
                text=text,
                metadata={'type': 'ingredient_list'},
                token_count=current_token_count
            ))
            current_chunk = []
            current_token_count = 0
        
        current_chunk.append(ingredient)
        current_token_count += ingredient_tokens
    
    # Add final chunk if exists
    if current_chunk:
        text = "Ingredients: " + ", ".join(current_chunk)
        chunks.append(TextChunk(
            text=text,
            metadata={'type': 'ingredient_list'},
            token_count=current_token_count
        ))
    
    return chunks

if __name__ == "__main__":
    # Test the chunking functionality
    from ingestion import load_csv, organize_restaurant_data, get_unique_ingredients
    
    print("\n=== Testing Text Chunking ===")
    
    # Load and organize data
    df = load_csv('../data/sample_restaurant_data.csv')
    if not df.empty:
        restaurants = organize_restaurant_data(df)
        ingredients = get_unique_ingredients(restaurants)
        
        # Create chunks
        print("\n=== Creating Restaurant Chunks ===")
        restaurant_chunks = create_restaurant_chunks(restaurants)
        print(f"Created {len(restaurant_chunks)} restaurant chunks")
        
        # Display sample chunks
        print("\n=== Sample Restaurant Chunks ===")
        for chunk in restaurant_chunks[:3]:
            print("\nChunk:")
            print(f"Text: {chunk.text[:200]}...")
            print(f"Metadata: {chunk.metadata}")
            print(f"Token Count: {chunk.token_count}")
        
        # Create ingredient chunks
        print("\n=== Creating Ingredient Chunks ===")
        ingredient_chunks = get_ingredient_chunks(ingredients)
        print(f"Created {len(ingredient_chunks)} ingredient chunks")
        
        # Display sample ingredient chunks
        print("\n=== Sample Ingredient Chunks ===")
        for chunk in ingredient_chunks[:2]:
            print("\nChunk:")
            print(f"Text: {chunk.text[:200]}...")
            print(f"Token Count: {chunk.token_count}")
    else:
        print("Error: Could not load restaurant data")
