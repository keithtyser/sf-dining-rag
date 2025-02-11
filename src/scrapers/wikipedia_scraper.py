import os
import json
import logging
import time
from typing import List, Dict, Optional
import wikipediaapi
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import hashlib
from datetime import datetime
import argparse  # Add argparse for command line arguments

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wikipedia_scraping.log')
    ]
)

class WikipediaScraper:
    def __init__(self, user_agent: str = "RestaurantChatbot/1.0"):
        self.wiki = wikipediaapi.Wikipedia(
            user_agent,
            'en',  # Language
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        
        # Base categories for food-related content
        self.base_categories = [
            "Category:Cuisines",
            "Category:Food_ingredients",
            "Category:Restaurants",
            "Category:Food_history"
        ]
        
        # Track processed pages to avoid duplicates
        self.processed_pages = set()
        
    def generate_chunk_id(self, content: str) -> str:
        """Generate a unique ID for a chunk based on its content."""
        return f"wiki_{hashlib.md5(content.encode()).hexdigest()}"
        
    def get_category_members(self, category_name: str, max_depth: int = 2) -> List[str]:
        """Recursively get all pages in a category up to max_depth."""
        logging.info(f"Getting members of category: {category_name}")
        pages = []
        visited_categories = set()
        
        def _get_members(cat_name: str, depth: int):
            if depth > max_depth or cat_name in visited_categories:
                return
                
            visited_categories.add(cat_name)
            category = self.wiki.page(cat_name)
            
            if not category.exists():
                logging.warning(f"Category does not exist: {cat_name}")
                return
                
            # Get all pages in this category
            for member in category.categorymembers.values():
                if "Category:" in member.title:
                    _get_members(member.title, depth + 1)
                else:
                    pages.append(member.title)
                    
        _get_members(category_name, 0)
        return list(set(pages))  # Remove duplicates
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove multiple newlines
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        # Remove references [1], [2], etc.
        text = ' '.join(word for word in text.split() if not (word.startswith('[') and word.endswith(']')))
        return text
        
    def extract_section_hierarchy(self, page) -> List[Dict]:
        """Extract the section hierarchy of a Wikipedia page."""
        sections = []
        
        def _process_section(section, depth=0):
            sections.append({
                'title': section.title,
                'level': depth,
                'text': self.clean_text(section.text)
            })
            for subsection in section.sections:
                _process_section(subsection, depth + 1)
                
        for section in page.sections:
            _process_section(section)
            
        return sections
        
    def chunk_content(self, content: Dict) -> List[Dict]:
        """Create a single chunk per article with summary."""
        return [{
            "id": self.generate_chunk_id(content['title']),
            "text": content['text'],
            "metadata": {
                "type": "wikipedia",
                "source": "wikipedia",
                "title": content['title'],
                "url": content['url'],
                "summary": content['summary'],  # Include the summary here
                "timestamp": datetime.utcnow().isoformat(),
                "category": content.get('category', 'general'),
                "subcategory": self.determine_subcategory(content['title']),
                "related_titles": content.get('related_titles', [])
            }
        }]
        
    def determine_subcategory(self, section_title: str) -> str:
        """Determine the subcategory based on section title."""
        title_lower = section_title.lower()
        
        if any(word in title_lower for word in ['history', 'origin', 'background']):
            return 'history'
        elif any(word in title_lower for word in ['preparation', 'cooking', 'recipe']):
            return 'preparation'
        elif any(word in title_lower for word in ['ingredient', 'component']):
            return 'ingredients'
        elif any(word in title_lower for word in ['variation', 'type', 'style']):
            return 'variations'
        elif any(word in title_lower for word in ['culture', 'tradition', 'custom']):
            return 'cultural'
        else:
            return 'general'
            
    def scrape_page(self, title: str) -> Optional[Dict]:
        """Scrape and process a single Wikipedia page."""
        if title in self.processed_pages:
            return None
            
        page = self.wiki.page(title)
        if not page.exists():
            logging.warning(f"Page does not exist: {title}")
            return None
            
        self.processed_pages.add(title)
        
        # Get related pages through links
        related_titles = [link for link in list(page.links.keys())[:10]]  # Limit to top 10 related pages
        
        # Get the full text of the article
        full_text = self.clean_text(page.text)
        
        content = {
            'title': page.title,
            'url': page.fullurl,
            'summary': self.clean_text(page.summary),  # Get the summary
            'text': full_text,  # Store full text instead of sections
            'related_titles': related_titles,
            'category': self.determine_category(page.title, page.text)
        }
        
        return content
        
    def determine_category(self, title: str, text: str) -> str:
        """Determine the main category of the article."""
        title_lower = title.lower()
        text_lower = text.lower()
        
        if any(word in title_lower for word in ['cuisine', 'food', 'dish', 'meal']):
            return 'cuisine'
        elif any(word in title_lower for word in ['ingredient', 'spice', 'herb']):
            return 'ingredient'
        elif any(word in title_lower for word in ['cooking', 'technique', 'method']):
            return 'technique'
        elif any(word in title_lower for word in ['restaurant', 'eatery', 'dining']):
            return 'restaurant'
        else:
            return 'general'
            
    def scrape_all_categories(self, output_file: str = 'data/wikipedia_chunks.json', test_mode: bool = False):
        """Scrape all base categories and save chunks to file."""
        all_chunks = []
        all_pages = set()
        
        # Get all pages from all categories
        for category in self.base_categories:
            pages = self.get_category_members(category, max_depth=1 if test_mode else 2)
            all_pages.update(pages)
            
            # In test mode, limit pages per category
            if test_mode and len(all_pages) > 5:
                all_pages = set(list(all_pages)[:5])
                break
        
        logging.info(f"Found {len(all_pages)} unique pages to process")
        
        # Process each page
        for page_title in tqdm(all_pages, desc="Processing pages"):
            try:
                content = self.scrape_page(page_title)
                if content:
                    chunks = self.chunk_content(content)
                    all_chunks.extend(chunks)
                    
                    # In test mode, provide more detailed logging
                    if test_mode:
                        logging.info(f"Processed page: {page_title}")
                        logging.info(f"Generated {len(chunks)} chunks")
                        logging.info(f"First chunk preview: {chunks[0]['text'][:200]}...")
                    
                    # Save progress periodically
                    if len(all_chunks) % 1000 == 0:
                        self.save_chunks(all_chunks, output_file)
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logging.error(f"Error processing page {page_title}: {str(e)}")
                continue
        
        # Save final results
        self.save_chunks(all_chunks, output_file)
        
        # In test mode, also save a sample file
        if test_mode:
            sample_file = output_file.replace('.json', '_sample.json')
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(all_chunks[:5], f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(all_chunks)} sample chunks to {sample_file}")
        else:
            logging.info(f"Scraped {len(all_chunks)} chunks from {len(all_pages)} pages")
            
    def save_chunks(self, chunks: List[Dict], output_file: str):
        """Save chunks to a JSON file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
def main():
    parser = argparse.ArgumentParser(description='Scrape Wikipedia for food and restaurant related content')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited pages and detailed logging')
    parser.add_argument('--output', default='data/wikipedia_chunks.json', help='Output file path')
    args = parser.parse_args()
    
    try:
        scraper = WikipediaScraper()
        if args.test:
            logging.info("Running in test mode - processing limited pages with detailed logging")
        scraper.scrape_all_categories(output_file=args.output, test_mode=args.test)
        
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 