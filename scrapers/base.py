from abc import ABC, abstractmethod
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import random

class BaseScraper(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL."""
        pass

    @abstractmethod
    def get_chapters(self, url: str, language: str = 'en'):
        """Return a list of chapters for the given URL and language."""
        pass

    @abstractmethod
    def download_chapter(self, chapter_url: str, dest_folder: str) -> bool:
        """Download the chapter to the destination folder. Return True if successful."""
        pass
    
    def get_page_content(self, url: str, retries: int = 3) -> BeautifulSoup:
        """Get page content with retry logic and anti-bot measures."""
        for attempt in range(retries):
            try:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def extract_chapter_number(self, text: str) -> str:
        """Extract chapter number from various text formats."""
        # Common patterns: "Chapter 123", "Ch. 123", "123", etc.
        patterns = [
            r'chapter\s*(\d+(?:\.\d+)?)',  # Chapter 123 or Chapter 123.5
            r'ch\.?\s*(\d+(?:\.\d+)?)',    # Ch. 123 or Ch 123
            r'(\d+(?:\.\d+)?)',            # Just numbers
        ]
        
        text_lower = text.lower().strip()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)
        return "0"
    
    def is_valid_image_url(self, url: str) -> bool:
        """Check if URL points to a valid image."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        return any(url.lower().endswith(ext) for ext in image_extensions)
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        if url.startswith('http'):
            return url
        return urljoin(base_url, url) 