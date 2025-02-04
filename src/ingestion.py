# -*- coding: utf-8 -*-

import pandas as pd
import requests
import os
from typing import Dict, Optional, List

def load_csv(file_path: str) -> pd.DataFrame:
    """
    load restaurant data from a csv file
    
    args:
        file_path (str): path to the csv file
        
    returns:
        pandas.DataFrame: loaded data
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File does not exist at path: {file_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Absolute path attempted: {os.path.abspath(file_path)}")
            return pd.DataFrame()
            
        # Try to read the file
        print(f"Attempting to read file: {file_path}")
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {len(df)} records from {file_path}")
        return df
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Absolute path attempted: {os.path.abspath(file_path)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        print(f"Error type: {type(e)}")
        return pd.DataFrame()

def clean_value(value) -> str:
    """
    clean and convert a value to string, handling nan values
    
    args:
        value: any value that needs to be cleaned
        
    returns:
        str: cleaned string value
    """
    if pd.isna(value):
        return ""
    return str(value).strip()

def organize_restaurant_data(df: pd.DataFrame) -> Dict:
    """
    organize the flat csv data into a hierarchical structure
    
    args:
        df (pandas.DataFrame): raw restaurant data
        
    returns:
        dict: organized restaurant data with menus and ingredients
    """
    restaurants = {}
    
    # Group by restaurant first
    for restaurant_name in df['restaurant_name'].unique():
        restaurant_df = df[df['restaurant_name'] == restaurant_name]
        
        # Get restaurant info from first row
        first_row = restaurant_df.iloc[0]
        restaurants[restaurant_name] = {
            'rating': first_row.get('rating', None),
            'price_range': clean_value(first_row.get('price_range', None)),
            'menu_categories': {}
        }
        
        # Group by menu category
        for category in restaurant_df['menu_category'].unique():
            category_df = restaurant_df[restaurant_df['menu_category'] == category]
            
            menu_items = []
            for _, item in category_df.groupby('item_id').first().iterrows():
                # Get ingredients for this item
                ingredients = category_df[
                    category_df['item_id'] == item.name
                ]['ingredient_name'].dropna().unique().tolist()
                
                menu_items.append({
                    'item_name': clean_value(item['menu_item']),
                    'description': clean_value(item['menu_description']),
                    'ingredients': [clean_value(i) for i in ingredients if pd.notna(i)],
                    'co2_emission': item.get('co2_emission', None)
                })
            
            restaurants[restaurant_name]['menu_categories'][clean_value(category)] = menu_items
    
    return restaurants

def fetch_wikipedia_article(title: str) -> Optional[Dict]:
    """
    fetch article summary from wikipedia api
    
    args:
        title (str): title of the wikipedia article
        
    returns:
        dict: article data containing 'title', 'extract', and 'url' if successful
        none: if the article cannot be found or there's an error
    """
    try:
        print(f"Fetching Wikipedia article for: {title}")
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', ''),
                'extract': data.get('extract', ''),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
            }
        else:
            print(f"Error: Could not fetch article. Status code: {response.status_code}")
            print(f"Response text: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"Error fetching Wikipedia article: {str(e)}")
        print(f"Error type: {type(e)}")
        return None

def get_unique_ingredients(restaurants: Dict) -> List[str]:
    """
    extract all unique ingredients from the restaurant data
    
    args:
        restaurants (dict): organized restaurant data
        
    returns:
        list: unique ingredients across all restaurants
    """
    ingredients = set()
    for restaurant in restaurants.values():
        for category in restaurant['menu_categories'].values():
            for item in category:
                ingredients.update(i for i in item['ingredients'] if i)  # Only add non-empty ingredients
    return sorted(list(ingredients))

if __name__ == "__main__":
    print("\n=== Starting Restaurant Data Processing ===")
    print(f"Current working directory: {os.getcwd()}")
    
    # Load restaurant data
    print("\n=== Loading Restaurant Data ===")
    df = load_csv('../data/sample_restaurant_data.csv')
    
    if not df.empty:
        # Display basic information about the dataset
        print("\n=== Dataset Information ===")
        print(f"Number of records: {len(df)}")
        print(f"Number of unique restaurants: {df['restaurant_name'].nunique()}")
        print(f"Number of menu categories: {df['menu_category'].nunique()}")
        print(f"Number of unique menu items: {df['item_id'].nunique()}")
        
        # Organize data hierarchically
        print("\n=== Organizing Data ===")
        restaurants = organize_restaurant_data(df)
        
        # Display sample of organized data
        print("\n=== Sample Organized Data ===")
        sample_restaurant = next(iter(restaurants))
        print(f"\nSample Restaurant: {sample_restaurant}")
        print(f"Rating: {restaurants[sample_restaurant]['rating']}")
        print(f"Price Range: {restaurants[sample_restaurant]['price_range']}")
        print("\nMenu Categories:")
        for category, items in list(restaurants[sample_restaurant]['menu_categories'].items())[:2]:
            print(f"\n  {category}:")
            for item in items[:2]:  # Show first 2 items in each category
                print(f"    - {item['item_name']}")
                if item['description']:
                    print(f"      Description: {item['description'][:100]}...")
                if item['ingredients']:
                    print(f"      Ingredients: {', '.join(item['ingredients'])}")
                if item['co2_emission']:
                    print(f"      CO2 Emission: {item['co2_emission']}")
        
        # Get unique ingredients
        print("\n=== Ingredient Analysis ===")
        ingredients = get_unique_ingredients(restaurants)
        print(f"Total unique ingredients: {len(ingredients)}")
        print("Sample ingredients:", ', '.join(ingredients[:10]))
        
    else:
        print("\nError: No data was loaded. Please check the error messages above.")
