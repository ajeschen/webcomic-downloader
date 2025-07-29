import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .base import BaseScraper

class WordPressMangaScraper(BaseScraper):
    """Generic scraper for WordPress-based manga sites using common patterns."""
    
    def can_handle(self, url: str) -> bool:
        """Check if this is a WordPress-based manga site."""
        try:
            soup = self.get_page_content(url)
            if not soup:
                return False
            
            # Check for common WordPress indicators
            wp_indicators = [
                'wp-content',
                'wp-includes', 
                'wordpress',
                'wp-manga',
                'madara'
            ]
            
            # Check for manga-specific indicators
            manga_indicators = [
                'chapter',
                'manga',
                'manhwa',
                'manhua'
            ]
            
            page_text = soup.get_text().lower()
            html_content = str(soup).lower()
            
            has_wp = any(indicator in html_content for indicator in wp_indicators)
            has_manga = any(indicator in page_text for indicator in manga_indicators)
            
            return has_wp and has_manga
            
        except Exception:
            return False
    
    def get_chapters(self, url: str, language: str = 'en'):
        """Extract chapters from WordPress manga site."""
        try:
            soup = self.get_page_content(url)
            if not soup:
                return []
            
            chapters = []
            
            # Realistic selectors used by common WordPress manga themes
            chapter_selectors = [
                'a[href*="chapter"]',
                '.wp-manga-chapter a',
                '.chapter-item a',
                '.chapters a',
                '.manga-chapters a',
                '.chapter-list a',
                '.wp-manga-chapter-list a',
                '.manga-chapter-list a',
                '.chapter-list-item a',
                '.wp-manga-chapter-list-item a',
                '.chapter-name a',
                '.chapter-title a',
                '.chapter-link',
                '.wp-manga-chapter-name a',
                '.manga-chapter a',
                '.chapter a',
                '.wp-manga-chapter-list .chapter a',
                '.manga-chapter-list .chapter a'
            ]
            
            # Try each selector until we find chapters
            for selector in chapter_selectors:
                chapter_links = soup.select(selector)
                if chapter_links:
                    for link in chapter_links:
                        href = link.get('href', '')
                        if href and ('chapter' in href.lower() or 'ch' in href.lower()):
                            chapter_text = link.get_text().strip()
                            chapter_num = self.extract_chapter_number(chapter_text)
                            
                            chapters.append({
                                'id': href,
                                'chapter': chapter_num,
                                'title': chapter_text,
                                'lang': language
                            })
                    break
            
            # If no chapters found with selectors, try a more generic approach
            if not chapters:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Look for chapter patterns in both href and text
                    if (('chapter' in href.lower() or 'ch' in href.lower()) and 
                        ('chapter' in text.lower() or re.search(r'ch\.?\s*\d+', text.lower()))):
                        
                        chapter_num = self.extract_chapter_number(text)
                        chapters.append({
                            'id': href,
                            'chapter': chapter_num,
                            'title': text,
                            'lang': language
                        })
            
            # Sort chapters by number
            chapters.sort(key=lambda x: float(x['chapter']) if x['chapter'].replace('.', '').isdigit() else 0)
            
            return chapters
            
        except Exception as e:
            print(f"Error getting chapters: {e}")
            return []
    
    def download_chapter(self, chapter_url: str, dest_folder: str) -> bool:
        """Download chapter images from WordPress manga site."""
        try:
            soup = self.get_page_content(chapter_url)
            if not soup:
                return False
            
            # Create destination folder
            os.makedirs(dest_folder, exist_ok=True)
            
            # Find image containers
            image_selectors = [
                '.reading-content img',
                '.chapter-content img',
                '.manga-chapter-content img',
                '.wp-manga-chapter-content img',
                '.chapter-images img',
                '.manga-images img',
                '.reading-content .page-break img',
                '.chapter-content .page-break img',
                '.manga-chapter-content img',
                '.wp-manga-chapter-content .page-break img',
                '.manga-chapter-content .page-break img'
            ]
            
            images = []
            for selector in image_selectors:
                images = soup.select(selector)
                if images:
                    break
            
            # If no images found with selectors, try a more generic approach
            if not images:
                # Look for any images that might be chapter content
                all_images = soup.find_all('img')
                for img in all_images:
                    src = img.get('src') or img.get('data-src')
                    if src and self.is_valid_image_url(src):
                        # Check if it's likely a chapter image (not an ad or icon)
                        parent_classes = ' '.join(img.parent.get('class', [])) if img.parent else ''
                        if not any(ad_indicator in parent_classes.lower() for ad_indicator in ['ad', 'advertisement', 'banner', 'sidebar']):
                            images.append(img)
            
            if not images:
                return False
            
            # Download each image
            for i, img in enumerate(images):
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                img_url = self.normalize_url(img_url, chapter_url)
                
                if not self.is_valid_image_url(img_url):
                    continue
                
                # Generate filename
                ext = os.path.splitext(img_url)[1] or '.jpg'
                filename = f"{i+1:03d}{ext}"
                filepath = os.path.join(dest_folder, filename)
                
                # Download image
                try:
                    response = self.session.get(img_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)
                            
                except Exception as e:
                    print(f"Error downloading image {img_url}: {e}")
                    continue
            
            return len(images) > 0
            
        except Exception as e:
            print(f"Error downloading chapter: {e}")
            return False 