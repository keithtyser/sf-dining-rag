﻿# -*- coding: utf-8 -*-

import pandas as pd
import requests
import os
from typing import Dict, Optional

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
        print(f"Successfully loaded {len(df)} restaurants from {file_path}")
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

def enrich_restaurant_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    enrich restaurant data with wikipedia information about cuisines
    
    args:
        df (pandas.DataFrame): restaurant data
        
    returns:
        pandas.DataFrame: enriched data with cuisine descriptions
    """
    # Get unique cuisines
    cuisines = df['cuisine'].unique()
    print(f"\nFound {len(cuisines)} unique cuisines: {', '.join(cuisines)}")
    
    # Fetch Wikipedia info for each cuisine
    cuisine_info = {}
    for cuisine in cuisines:
        print(f"\nProcessing {cuisine} cuisine...")
        wiki_data = fetch_wikipedia_article(f"{cuisine}_cuisine")
        if wiki_data:
            cuisine_info[cuisine] = wiki_data['extract']
            print(f"✓ Found Wikipedia information for {cuisine} cuisine")
            print(f"Extract preview: {wiki_data['extract'][:100]}...")
        else:
            print(f"✗ Could not find Wikipedia information for {cuisine} cuisine")
    
    # Add cuisine descriptions to the dataframe
    df['cuisine_description'] = df['cuisine'].map(cuisine_info)
    print(f"\nAdded cuisine descriptions to {sum(df['cuisine_description'].notna())} restaurants")
    
    return df

if __name__ == "__main__":
    print("\n=== Starting Restaurant Data Processing ===")
    print(f"Current working directory: {os.getcwd()}")
    
    # Load restaurant data
    print("\n=== Loading Restaurant Data ===")
    df = load_csv('../data/sample_restaurant_data.csv')
    
    if not df.empty:
        # Display basic information about the dataset
        print("\n=== Dataset Information ===")
        print(f"Number of restaurants: {len(df)}")
        print(f"Cuisines available: {', '.join(df['cuisine'].unique())}")
        print(f"Price ranges: {', '.join(df['price_range'].unique())}")
        print("\n=== Sample Restaurant Data ===")
        print(df[['name', 'cuisine', 'price_range', 'rating']].head())
        
        # Enrich data with Wikipedia information
        print("\n=== Enriching Data with Wikipedia Information ===")
        df = enrich_restaurant_data(df)
        
        # Display enriched data
        print("\n=== Sample Enriched Data ===")
        if 'cuisine_description' in df.columns:
            for _, row in df.head(2).iterrows():
                print(f"\nRestaurant: {row['name']}")
                print(f"Cuisine: {row['cuisine']}")
                print(f"Description: {row['cuisine_description'][:200]}..." if row['cuisine_description'] else "No cuisine description available")
    else:
        print("\nError: No data was loaded. Please check the error messages above.")
