import os
import json
import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
from tqdm import tqdm
import argparse
import sys
import feedparser
from urllib.parse import urlparse
from dotenv import load_dotenv
from textblob import TextBlob
import nltk
from tenacity import retry, stop_after_attempt, wait_exponential
import random
import re

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    logging.warning(f"Failed to download NLTK data: {e}")

# load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('news_scraping.log')
    ]
)

class NewsArticleScraper:
    def __init__(self):
        # Default headers for requests
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }

        # Site-specific headers and selectors
        self.site_configs = {
            'sfgate.com': {
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                },
                'selectors': {
                    'title': '.article-headline',
                    'content': '.article-body',
                    'date': 'time',
                    'author': '.article-author'
                }
            },
            'eater.com': {
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive'
                },
                'selectors': {
                    'title': '.c-page-title',
                    'content': '.c-entry-content',
                    'date': 'time',
                    'author': '.c-byline__author-name'
                }
            },
            'forbes.com': {
                'headers': self.default_headers,
                'selectors': {
                    'title': '.fs-article-page-title',
                    'content': '.article-body',
                    'date': '.fs-article-date',
                    'author': '.fs-author-name'
                }
            }
        }
        
        # initialize session with default headers
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        
        # configuration
        self.max_articles = int(os.getenv('MAX_ARTICLES_PER_SOURCE', 50))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        self.rate_limit_delay = int(os.getenv('RATE_LIMIT_DELAY', 1))
        self.historical_months = int(os.getenv('HISTORICAL_DATA_MONTHS', 12))
        
        # track processed URLs to avoid duplicates
        self.processed_urls = set()
        
        # configure newspaper
        self.config = Config()
        self.config.browser_user_agent = self.session.headers['User-Agent']
        self.config.request_timeout = 20
        self.config.memoize_articles = False
        
        # initialize sources
        self.sources = {
            'rss_feeds': [
                'https://www.reddit.com/r/Cooking/top.rss',
                'https://www.reddit.com/r/food/top.rss',
                'https://sf.eater.com/rss/index.xml',
                'https://www.sfgate.com/food/feed/Food-News-482.php',
                'https://www.7x7.com/feed/food',
                'https://www.timeout.com/san-francisco/restaurants/rss.xml',
                'https://hoodline.com/location/san-francisco/food/rss',
                'https://www.thrillist.com/san-francisco/food-and-drink.rss'
            ],
            'historical_sources': [
                'https://web.archive.org/web/*/https://sf.eater.com/*',
                'https://web.archive.org/web/*/https://www.sfgate.com/food/*',
                'https://web.archive.org/web/*/https://www.7x7.com/food/*'
            ]
        }
        
        # setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # NewsAPI configuration
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        if not self.newsapi_key:
            raise ValueError("NEWSAPI_KEY environment variable is not set")
        
        # Search queries for restaurant and dining news
        self.search_queries = [
            'San Francisco restaurants',
            'San francisco dining',
            'San Francisco food scene',
            'Bay Area restaurants',
            'San Francisco culinary',
            'San francisco food news',
            'San Francisco chef',
            'Bay Area dining'
        ]

        # Initialize category patterns
        self.category_patterns = {
            'opening': (r'(new|opening|opened|debuts?|launches?|coming soon)', 2.0),
            'closing': (r'(closing|closed|shuttered|shutdown)', 1.5),
            'review': (r'(review|rating|stars?|experience)', 1.2),
            'chef': (r'(chef|cook|kitchen|culinary)', 1.3),
            'menu': (r'(menu|dish|cuisine|food|specialties)', 1.4),
            'award': (r'(award|michelin|best|top|rated)', 1.6),
            'event': (r'(event|festival|pop-up|special)', 1.3),
            'business': (r'(business|sales|revenue|industry)', 1.0)
        }
        
    def generate_chunk_id(self, content: str, source: str, date: str) -> str:
        """Generate a unique ID for a chunk based on its content and metadata."""
        unique_string = f"{content}{source}{date}"
        return f"news_{hashlib.md5(unique_string.encode()).hexdigest()}"
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
            
        # Remove any "Title:" prefixes
        text = re.sub(r'^Title:\s*\n+', '', text)
        
        # Remove multiple newlines and whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise patterns
        text = re.sub(r'\[(\+\d+)? chars\]', '', text)
        text = re.sub(r'\[\+\d+ chars\]', '', text)
        
        # Remove any remaining special characters
        text = re.sub(r'[^\w\s.,!?;:()\-\'"\n]', '', text)
        
        return text.strip()
        
    def get_site_config(self, url: str) -> Dict:
        """Get site-specific configuration including headers and selectors."""
        domain = urlparse(url).netloc
        for site_domain, config in self.site_configs.items():
            if site_domain in domain:
                return config
        return {'headers': self.default_headers, 'selectors': {}}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_article_content(self, url: str) -> Optional[Dict]:
        """Extract content from an article URL with retry logic and site-specific handling."""
        if url in self.processed_urls:
            return None
            
        try:
            # Get site-specific headers
            site_config = self.get_site_config(url)
            
            # Configure newspaper with site-specific settings
            config = Config()
            config.browser_user_agent = site_config['headers']['User-Agent']
            config.request_timeout = 20
            config.number_threads = 1
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Create article with custom headers
            article = Article(url, config=config)
            
            try:
                # Use requests to get the page content with proper headers
                response = requests.get(url, headers=site_config['headers'], timeout=20)
                response.raise_for_status()
                
                # Set the html content directly
                article.html = response.text
                article.download_state = 2  # Mark as downloaded
                article.parse()
                
                try:
                    article.nlp()
                except Exception as e:
                    logging.warning(f"NLP processing failed for {url}: {str(e)}")
                    # Continue with basic parsing if NLP fails
                    if not article.is_parsed:
                        article.parse()
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logging.error(f"Access forbidden for {url}. Trying alternative method...")
                    # For SFGATE and similar sites, try using selenium or another method
                    return self.extract_article_fallback(url, site_config)
                raise
            
            # Extract basic content even if NLP fails
            content = {
                'title': article.title,
                'text': article.text,
                'url': url,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'authors': article.authors,
                'top_image': article.top_image,
            }
            
            # Add NLP-based features if available
            if hasattr(article, 'keywords') and article.keywords:
                content['keywords'] = article.keywords
            
            self.processed_urls.add(url)
            
            return {
                'url': url,
                'title': article.title or "Untitled",
                'text': article.text,
                'keywords': getattr(article, 'keywords', []),
                'authors': article.authors,
                'publish_date': article.publish_date.isoformat() if article.publish_date else datetime.now().isoformat(),
                'top_image': article.top_image,
                'source_domain': article.source_url,
                'metadata': {
                    'type': 'news_article',
                    'sentiment': self.analyze_sentiment(article.text)
                }
            }
            
        except Exception as e:
            logging.error(f"Error processing article {url}: {str(e)}")
            return None

    def extract_article_fallback(self, url: str, site_config: Dict) -> Optional[Dict]:
        """Fallback method for extracting content when normal extraction fails."""
        try:
            # Use requests with extended headers
            response = requests.get(
                url,
                headers={
                    **site_config['headers'],
                    'Cookie': '',  # Add any required cookies
                    'Referer': 'https://www.google.com/'
                },
                timeout=30
            )
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try site-specific selectors first
            selectors = site_config.get('selectors', {})
            
            # Extract title
            title = None
            if selectors.get('title'):
                title_elem = soup.select_one(selectors['title'])
                if title_elem:
                    title = title_elem.text.strip()
            if not title:
                title = soup.find('h1') or soup.find('title')
                title = title.text.strip() if title else "Untitled"
            
            # Extract content
            content = None
            if selectors.get('content'):
                content = soup.select_one(selectors['content'])
            
            # If site-specific selector failed, try common patterns
            if not content:
                content_selectors = [
                    'article',
                    '.article-content',
                    '.story-body',
                    '.content-body',
                    '#article-body',
                    '.post-content',
                    'main',
                    '[role="main"]'
                ]
                
                for selector in content_selectors:
                    content = soup.select_one(selector)
                    if content:
                        break
            
            if not content:
                logging.warning(f"Could not find article content for {url}")
                return None
            
            # Extract date
            publish_date = None
            if selectors.get('date'):
                date_elem = soup.select_one(selectors['date'])
                if date_elem and date_elem.get('datetime'):
                    publish_date = date_elem['datetime']
                elif date_elem:
                    publish_date = date_elem.text.strip()
            
            # Extract authors
            authors = []
            if selectors.get('author'):
                author_elems = soup.select(selectors['author'])
                authors = [author.text.strip() for author in author_elems if author.text.strip()]
            
            # Clean the content
            text = self.clean_text(content.get_text())
            
            # Remove common noise patterns
            text = self.remove_noise(text)
            
            return {
                'url': url,
                'title': title,
                'text': text,
                'summary': text[:500] + '...' if len(text) > 500 else text,
                'keywords': self.extract_keywords(text),
                'authors': authors,
                'publish_date': publish_date or datetime.now().isoformat(),
                'top_image': None,
                'source_domain': urlparse(url).netloc,
                'metadata': {
                    'type': 'news_article',
                    'sentiment': self.analyze_sentiment(text)
                }
            }
            
        except Exception as e:
            logging.error(f"Fallback extraction failed for {url}: {str(e)}")
            return None

    def remove_noise(self, text: str) -> str:
        """Remove common noise patterns from article text."""
        # Remove advertisement text
        ad_patterns = [
            r'Advertisement\s*',
            r'Sponsored\s*',
            r'Share this article',
            r'Share this story',
            r'Follow us on',
            r'Sign up for our newsletter',
            r'Subscribe to our newsletter',
            r'Related Articles',
            r'Read more:',
            r'More from'
        ]
        
        cleaned_text = text
        for pattern in ad_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove multiple spaces and newlines
        cleaned_text = ' '.join(cleaned_text.split())
        
        return cleaned_text.strip()

    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from the text."""
        try:
            # Use TextBlob for noun phrase extraction
            blob = TextBlob(text)
            
            # Get noun phrases and individual nouns
            keywords = set(phrase.lower() for phrase in blob.noun_phrases)
            keywords.update(word.lower() for word, tag in blob.tags if tag.startswith('NN'))
            
            # Filter keywords
            keywords = {k for k in keywords 
                       if len(k) > 2  # Skip very short words
                       and not any(char.isdigit() for char in k)  # Skip words with numbers
                       and k not in {'com', 'org', 'net'}}  # Skip common TLDs
            
            # Add restaurant-specific keywords if present
            restaurant_keywords = {'restaurant', 'cafe', 'bistro', 'eatery', 'dining'}
            keywords.update(k for k in restaurant_keywords if k.lower() in text.lower())
            
            return sorted(list(keywords))[:10]  # Limit to top 10 keywords
            
        except Exception as e:
            logging.error(f"Error extracting keywords: {str(e)}")
            return []

    def determine_category(self, text: str) -> Tuple[str, Optional[str]]:
        # calculate category scores
        scores = {category: 0 for category in self.category_patterns}
        text_lower = text.lower()
        
        for category, (pattern, weight) in self.category_patterns.items():
            if pattern.lower() in text_lower:
                scores[category] = weight

        # get top two categories
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_categories[0][0]
        secondary = sorted_categories[1][0] if sorted_categories[1][1] > 0 else None

        return primary, secondary
        
    def analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of a text using TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.3:
                return 'positive'
            elif polarity < -0.3:
                return 'negative'
            else:
                return 'neutral'
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            return 'neutral'
        
    def chunk_article(self, article: Dict) -> List[Dict]:
        """Split article into appropriate chunks while preserving context."""
        chunks = []
        max_chunk_size = 1000  # Target chunk size
        
        # Always include title and basic metadata in each chunk
        base_metadata = {
            'source': article.get('source_domain', ''),
            'title': article.get('title', '').strip(),
            'authors': article.get('authors', []),
            'publish_date': self.normalize_date(article.get('publish_date')),
            'url': article.get('url', ''),
            'sentiment': article.get('metadata', {}).get('sentiment', 'neutral'),
            'type': 'article',
            'chunk_type': 'body',
            'keywords': article.get('keywords', [])
        }
        
        # Get the main text content
        text = article.get('text', '')
        if not text:
            # If no text, try to use summary
            text = article.get('summary', '')
            if not text:
                logging.warning(f"No content found for article: {article.get('url', 'unknown')}")
                return chunks
        
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                # Create chunk with current content
                chunk_id = self.generate_chunk_id(
                    current_chunk,
                    article.get('source_domain', ''),
                    base_metadata['publish_date']
                )
                
                chunks.append({
                    'id': chunk_id,
                    'text': current_chunk,
                    'metadata': {
                        **base_metadata,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
                
                current_chunk = paragraph
                current_paragraphs = [paragraph]
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_paragraphs.append(paragraph)
        
        # Add any remaining content as a final chunk
        if current_chunk:
            chunk_id = self.generate_chunk_id(
                current_chunk,
                article.get('source_domain', ''),
                base_metadata['publish_date']
            )
            
            chunks.append({
                'id': chunk_id,
                'text': current_chunk,
                'metadata': {
                    **base_metadata,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        
        return chunks

    def normalize_date(self, date_str: Optional[str]) -> str:
        """Normalize date string to ISO format and ensure it's not in the future."""
        try:
            if not date_str:
                return datetime.utcnow().isoformat()
                
            # Parse the date string
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # If date is in the future, use current time
            if date > datetime.utcnow():
                return datetime.utcnow().isoformat()
                
            return date.isoformat()
        except Exception as e:
            logging.warning(f"Error normalizing date {date_str}: {str(e)}")
            return datetime.utcnow().isoformat()

    def process_rss_feed(self, url: str) -> List[Dict]:
        """Process an RSS feed and extract articles."""
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:10]:  # Process up to 10 entries
                try:
                    article_data = {
                        'url': entry.link,
                        'title': entry.title,
                        'text': entry.description,
                        'summary': entry.get('summary', ''),
                        'authors': [entry.get('author', 'Unknown')],
                        'publish_date': entry.get('published', datetime.now().isoformat()),
                        'source_domain': urlparse(url).netloc,
                        'metadata': {
                            'type': 'rss_entry',
                            'sentiment': self.analyze_sentiment(entry.description)
                        }
                    }
                    articles.append(article_data)
                except Exception as e:
                    logging.error(f"Error processing RSS entry: {str(e)}")
                    continue
                    
            return articles
            
        except Exception as e:
            logging.error(f"Error processing RSS feed {url}: {str(e)}")
            return []
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_historical_data(self, url: str) -> List[Dict]:
        """Process historical data from Wayback Machine with improved error handling."""
        chunks = []
        try:
            # Use CDX API to get historical snapshots
            cdx_url = f"http://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=50"
            response = self.session.get(cdx_url, timeout=30)
            response.raise_for_status()
            snapshots = response.json()
            
            if not snapshots or len(snapshots) < 2:  # First row is header
                return chunks
                
            # Skip header row and process each snapshot
            for snapshot in tqdm(snapshots[1:], desc="Processing historical snapshots"):
                try:
                    timestamp = snapshot[1]
                    archive_url = f"http://web.archive.org/web/{timestamp}/{url}"
                    
                    article = self.extract_article_content(archive_url)
                    if article and article['text'].strip():
                        chunks.extend(self.chunk_article(article))
                    
                    time.sleep(self.rate_limit_delay)  # Rate limiting
                    
                except Exception as e:
                    logging.warning(f"Failed to process snapshot {archive_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error processing historical data for {url}: {str(e)}")
            
        return chunks

    def get_newsapi_articles(self, days_back: int = 30) -> List[Dict]:
        """Fetch articles from NewsAPI with improved query relevance."""
        try:
            if not self.newsapi_key:
                raise ValueError("NEWSAPI_KEY environment variable is not set")

            articles = []
            # More specific queries with exact phrase matching and required terms
            queries = [
                'San Francisco restaurant',
                'San Francisco dining',
                'Bay Area restaurant',
                'San Francisco food scene',
                'San Francisco chef',
                'san francisco restaurant opening new launch',
                'san francisco michelin',
                'san francisco fine dining'
                'San Francisco food news'
                'san francisco food'
            ]

            # Configure newspaper
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            config.request_timeout = 10
            config.fetch_images = False
            
            # Calculate date range - use UTC for consistency
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # Format dates as strings for the API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Relevant SF food news domains
            domains = [
                'sfgate.com',
                'sf.eater.com',
                'sfchronicle.com',
                'sfweekly.com',
                'timeout.com/san-francisco',
                '7x7.com',
                'sfist.com',
                'thebolditalic.com'
            ]

            for query in tqdm(queries, desc="Fetching from NewsAPI"):
                try:
                    # Log the request parameters
                    request_params = {
                        'q': query,
                        'apiKey': '***',  # Masked for security
                        'language': 'en',
                        'sortBy': 'relevancy',
                        'pageSize': 100,
                        'searchIn': 'title,description',
                        'from': start_date_str,
                        'to': end_date_str,
                        'domains': ','.join(domains)
                    }
                    logging.info(f"Making NewsAPI request with params: {json.dumps({k:v for k,v in request_params.items() if k != 'apiKey'}, indent=2)}")

                    response = requests.get(
                        'https://newsapi.org/v2/everything',
                        params={
                            'q': query,
                            'apiKey': self.newsapi_key,
                            'language': 'en',
                            'sortBy': 'relevancy',
                            'pageSize': 100,
                            'searchIn': 'title,description',
                            'from': start_date_str,
                            'to': end_date_str,
                            'domains': ','.join(domains)
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Log the raw API response
                    logging.info(f"NewsAPI Response for query '{query}':")
                    logging.info(f"Status: {data.get('status')}")
                    logging.info(f"Total Results: {data.get('totalResults')}")
                    
                    if data.get('status') == 'ok':
                        found_articles = data.get('articles', [])
                        logging.info(f"Found {len(found_articles)} articles for query: {query}")
                        
                        # Pre-process articles before adding
                        for article in found_articles:
                            # Log article processing
                            logging.info(f"\nProcessing article: {article.get('title', 'No Title')}")
                            logging.info(f"URL: {article.get('url', 'No URL')}")
                            
                            # Skip articles without required fields
                            if not all(article.get(field) for field in ['title', 'url', 'publishedAt']):
                                logging.warning("Skipping article due to missing required fields")
                                continue
                                
                            # Convert publishedAt to UTC datetime object
                            try:
                                pub_date = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                                pub_date = pub_date.replace(tzinfo=None)  # Make naive for comparison
                                
                                if pub_date > end_date:
                                    logging.warning(f"Skipping article with future date: {pub_date}")
                                    continue
                                    
                                article['publishedAt'] = pub_date.isoformat()
                                logging.info(f"Validated publish date: {article['publishedAt']}")
                                
                                # Try to get full content if API content is truncated
                                api_content = article.get('content', '')
                                full_content = None
                                
                                if '[+' in api_content and article['url']:  # Content is truncated
                                    try:
                                        logging.info(f"Attempting to fetch full content from: {article['url']}")
                                        news_article = Article(article['url'], config=config)
                                        news_article.download()
                                        news_article.parse()
                                        if news_article.text:
                                            full_content = news_article.text
                                            logging.info(f"Successfully extracted full content: {len(full_content)} chars")
                                    except Exception as e:
                                        logging.warning(f"Failed to fetch full content: {str(e)}")
                                
                                # Create initial chunk from the article
                                chunk = {
                                    "title": article['title'],
                                    "url": article['url'],
                                    "source": article['source']['name'],
                                    "publish_date": article['publishedAt'],
                                    "author": article.get('author', ''),
                                    "description": article.get('description', ''),
                                    "content": full_content or api_content,  # Use full content if available
                                    "image_url": article.get('urlToImage', '')
                                }
                                articles.append(chunk)
                                logging.info("Article successfully processed and added")
                                
                            except (ValueError, TypeError) as e:
                                logging.error(f"Date validation error: {str(e)}")
                                continue
                    else:
                        logging.error(f"Error in NewsAPI response: {data.get('message', 'Unknown error')}")
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logging.error(f"Error fetching articles for query '{query}': {str(e)}")
                    continue

            # Remove duplicates based on URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                url = article.get('url')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)

            logging.info(f"Found {len(unique_articles)} unique articles after deduplication")
            return unique_articles

        except Exception as e:
            logging.error(f"Error in get_newsapi_articles: {str(e)}")
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_full_content(self, url: str, config: Config) -> Optional[str]:
        """Extract full article content from URL with retry logic."""
        try:
            article = Article(url, config=config)
            article.download()
            article.parse()
            return article.text if article.text else None
        except Exception as e:
            logging.error(f"Failed to extract full content from {url}: {str(e)}")
            return None

    def process_newsapi_article(self, article: Dict) -> List[Dict]:
        """Process an article from NewsAPI and extract relevant information into chunks."""
        try:
            # Extract basic metadata
            source = article.get('source', 'Unknown Source')
            title = article.get('title', '').strip()
            url = article.get('url', '')
            author = article.get('author', '')
            description = article.get('description', '').strip()
            content = article.get('content', '').strip()
            publish_date = article.get('publish_date')
            image_url = article.get('image_url', '')

            if not url or url in self.processed_urls:
                logging.warning(f"Skipping article - {'No URL' if not url else 'Already processed'}")
                return []

            self.processed_urls.add(url)

            # Create chunks from the article content
            chunks = []
            
            # Create a title chunk with metadata
            title_chunk = {
                "id": self.generate_chunk_id(title, source, publish_date),
                "text": f"{title}\n\n{description}",
                "metadata": {
                    "source": source,
                    "title": title,
                    "url": url,
                    "author": author,
                    "publish_date": publish_date,
                    "image_url": image_url,
                    "chunk_type": "title",
                    "type": "article"
                }
            }
            chunks.append(title_chunk)

            # Process the main content
            if content:
                # Clean the content - remove truncation markers
                content = re.sub(r'\[\+\d+ chars\]$', '', content).strip()
                
                # Split content into paragraphs
                paragraphs = content.split('\n\n')
                current_chunk = ""
                chunk_number = 1
                
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue

                    # If adding this paragraph would exceed chunk size, create a new chunk
                    if len(current_chunk) + len(paragraph) > 1000:
                        if current_chunk:
                            chunk_id = self.generate_chunk_id(
                                current_chunk, 
                                source, 
                                f"{publish_date}_{chunk_number}"
                            )
                            
                            content_chunk = {
                                "id": chunk_id,
                                "text": current_chunk,
                                "metadata": {
                                    "source": source,
                                    "title": title,
                                    "url": url,
                                    "author": author,
                                    "publish_date": publish_date,
                                    "chunk_type": "content",
                                    "chunk_number": chunk_number,
                                    "type": "article"
                                }
                            }
                            chunks.append(content_chunk)
                            chunk_number += 1
                            current_chunk = paragraph
                    else:
                        current_chunk += "\n\n" + paragraph if current_chunk else paragraph

                # Add any remaining content as the final chunk
                if current_chunk:
                    chunk_id = self.generate_chunk_id(
                        current_chunk,
                        source,
                        f"{publish_date}_{chunk_number}"
                    )
                    
                    content_chunk = {
                        "id": chunk_id,
                        "text": current_chunk,
                        "metadata": {
                            "source": source,
                            "title": title,
                            "url": url,
                            "author": author,
                            "publish_date": publish_date,
                            "chunk_type": "content",
                            "chunk_number": chunk_number,
                            "type": "article"
                        }
                    }
                    chunks.append(content_chunk)

            logging.info(f"Created {len(chunks)} chunks for article: {title}")
            return chunks

        except Exception as e:
            logging.error(f"Error processing article into chunks: {str(e)}")
            return []

    def scrape_articles(self, test_mode: bool = False) -> None:
        """Main method to scrape and process articles."""
        try:
            # Get articles from NewsAPI
            days_back = 7 if test_mode else 30
            articles = self.get_newsapi_articles(days_back=days_back)
            logging.info(f"Found {len(articles)} unique articles")
            
            # Process articles and create chunks
            all_chunks = []
            for article in tqdm(articles, desc="Processing articles"):
                try:
                    chunks = self.process_newsapi_article(article)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logging.error(f"Error processing article: {str(e)}")
                    continue
            
            # Save chunks
            output_file = 'data/news_chunks_sample.json' if test_mode else 'data/news_chunks.json'
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Saved {len(all_chunks)} chunks to {output_file}")
            
        except Exception as e:
            logging.error(f"Error in scrape_articles: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Scrape news articles about San Francisco restaurants')
    parser.add_argument('--test', action='store_true', help='Run in test mode with limited articles')
    args = parser.parse_args()
    
    try:
        scraper = NewsArticleScraper()
        scraper.scrape_articles(test_mode=args.test)
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 