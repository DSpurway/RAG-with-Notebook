"""
Web Scraper for IBM Documentation Pages
Extracts content from IBM Docs pages for ingestion into vector database
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class IBMDocsScraperError(Exception):
    """Custom exception for scraping errors"""
    pass


class IBMDocsScraper:
    """Scraper for IBM Documentation pages"""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the scraper
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url: str) -> str:
        """
        Fetch HTML content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            IBMDocsScraperError: If fetch fails
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise IBMDocsScraperError(f"Failed to fetch URL {url}: {str(e)}")
    
    def extract_main_content(self, html: str, url: str) -> Dict[str, any]:
        """
        Extract main content from IBM Docs page
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Dictionary with extracted content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract main content
        content = self._extract_content(soup)
        
        # Extract metadata
        metadata = self._extract_metadata(soup, url)
        
        return {
            'title': title,
            'content': content,
            'metadata': metadata,
            'url': url
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        # Try multiple selectors for IBM Docs pages
        title_selectors = [
            'h1.bx--type-productive-heading-05',
            'h1.title',
            'h1',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return "Untitled"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from IBM Docs page
        
        IBM Docs pages typically use specific content containers
        """
        content_parts = []
        
        # Try to find main content area
        # IBM Docs often uses these containers
        content_selectors = [
            'div.bx--content',
            'main',
            'article',
            'div.content',
            'div#content',
            'div.main-content'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                logger.info(f"Found content using selector: {selector}")
                break
        
        if not main_content:
            # Fallback: use body
            main_content = soup.body
            logger.warning("Using body as fallback for content extraction")
        
        if main_content:
            # Remove unwanted elements
            for unwanted in main_content.select('script, style, nav, header, footer, .navigation, .breadcrumb'):
                unwanted.decompose()
            
            # Extract text from paragraphs, headings, lists, and tables
            for elem in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']):
                text = elem.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short text
                    content_parts.append(text)
        
        content = '\n\n'.join(content_parts)
        
        if not content:
            raise IBMDocsScraperError("No content extracted from page")
        
        logger.info(f"Extracted {len(content)} characters of content")
        return content
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extract metadata from page"""
        metadata = {
            'source': url,
            'source_type': 'web_page'
        }
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['description'] = meta_desc['content']
        
        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            metadata['keywords'] = meta_keywords['content']
        
        # Extract publication date if available
        date_elem = soup.find('meta', attrs={'name': 'DC.date'})
        if date_elem and date_elem.get('content'):
            metadata['publication_date'] = date_elem['content']
        
        # Parse URL for additional metadata
        parsed_url = urlparse(url)
        metadata['domain'] = parsed_url.netloc
        
        return metadata
    
    def scrape_url(self, url: str) -> Dict[str, any]:
        """
        Scrape a single URL and return structured content
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with title, content, metadata, and url
        """
        html = self.fetch_page(url)
        return self.extract_main_content(html, url)
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, any]]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of dictionaries with scraped content
        """
        results = []
        for url in urls:
            try:
                result = self.scrape_url(url)
                results.append(result)
            except IBMDocsScraperError as e:
                logger.error(f"Failed to scrape {url}: {e}")
                # Continue with other URLs
        
        return results


def create_langchain_documents(scraped_data: Dict[str, any]) -> List:
    """
    Convert scraped data to LangChain Document format
    
    Args:
        scraped_data: Dictionary from scrape_url()
        
    Returns:
        List of LangChain Document objects
    """
    from langchain.schema import Document
    
    # Create a single document with the full content
    # The text splitter will handle chunking later
    doc = Document(
        page_content=f"# {scraped_data['title']}\n\n{scraped_data['content']}",
        metadata=scraped_data['metadata']
    )
    
    return [doc]

# Made with Bob
