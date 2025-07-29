import os
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .base import BaseScraper

class AsuraScansScraper(BaseScraper):
    """Scraper specifically for Asura Scans website."""
    
    # List of known Asura Scans domains (current and historical)
    KNOWN_DOMAINS = [
        "asurascanlation.com",
        "asurascans.com", 
        "asura.gg",  # Common new domain pattern
        "asura.xyz",  # Another common pattern
        "asurascans.net",
        "asurascans.org"
    ]
    
    def can_handle(self, url: str) -> bool:
        """Check if this is an Asura Scans URL."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check against known domains
        for known_domain in self.KNOWN_DOMAINS:
            if known_domain in domain:
                return True
        
        # Also check if the URL contains "asura" and typical manga path patterns
        if "asura" in domain and any(path in url.lower() for path in ["/manga/", "/manhwa/", "/manhua/"]):
            return True
            
        return False
    
    def get_chapters(self, url: str, language: str = 'en'):
        """Extract chapters from Asura Scans."""
        try:
            soup = self.get_page_content(url)
            if not soup:
                return []
            
            chapters = []
            
            # Asura Scans specific selectors (updated for current site structure)
            chapter_selectors = [
                '.wp-manga-chapter-list a',
                '.chapter-item a',
                '.chapters a',
                '.manga-chapters a',
                '.chapter-list a',
                '.wp-manga-chapter-list-item a',
                '.manga-chapter-list a',
                '.chapter-list-item a',
                '.chapter-name a',
                '.chapter-title a',
                '.chapter-link',
                '.wp-manga-chapter-name a',
                # Additional selectors for newer site versions
                '.wp-manga-chapter a',
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
                            
                            # Ensure the URL is absolute
                            if not href.startswith('http'):
                                href = urljoin(url, href)
                            
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
                        
                        # Ensure the URL is absolute
                        if not href.startswith('http'):
                            href = urljoin(url, href)
                        
                        chapters.append({
                            'id': href,
                            'chapter': chapter_num,
                            'title': text,
                            'lang': language
                        })
            
            # Sort chapters by number (newest first for Asura Scans)
            chapters.sort(key=lambda x: float(x['chapter']) if x['chapter'].replace('.', '').isdigit() else 0, reverse=True)
            
            return chapters
            
        except Exception as e:
            print(f"Error getting chapters from Asura Scans: {e}")
            return []
    
    def download_chapter(self, chapter_url: str, dest_folder: str) -> bool:
        """Download chapter images from Asura Scans."""
        try:
            # Create destination folder
            os.makedirs(dest_folder, exist_ok=True)
            
            # Extract series name and chapter number from URL
            series_match = re.search(r'/([^/]+)-chapter-(\d+)', chapter_url)
            if not series_match:
                print(f"Could not extract series and chapter info from {chapter_url}")
                return False
            
            series_name = series_match.group(1)
            chapter_num = series_match.group(2)
            
            # Try to get images from WordPress API first
            base_url = f"{urlparse(chapter_url).scheme}://{urlparse(chapter_url).netloc}"
            api_url = f"{base_url}/wp-json/wp/v2/posts?slug={series_name}-chapter-{chapter_num}"
            
            print(f"Trying API endpoint: {api_url}")
            
            try:
                response = self.session.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        post = data[0]
                        if 'content' in post and 'rendered' in post['content']:
                            content_html = post['content']['rendered']
                            
                            # Parse content for images
                            content_soup = BeautifulSoup(content_html, 'html.parser')
                            images = content_soup.find_all('img')
                            
                            if images:
                                print(f"Found {len(images)} images via API")
                                return self._download_images(images, dest_folder, chapter_url)
            
            except Exception as e:
                print(f"API request failed: {e}")
            
            # Fallback: Try to get images from the chapter page
            print("Falling back to chapter page scraping...")
            soup = self.get_page_content(chapter_url)
            if not soup:
                return False
            
            # Try to find images using multiple methods
            images = []
            
            # Method 1: Look for images in common manga reading containers
            image_selectors = [
                '.reading-content img',
                '.chapter-content img',
                '.manga-chapter-content img',
                '.wp-manga-chapter-content img',
                '.reading-content .page-break img',
                '.chapter-content .page-break img',
                '.manga-chapter-content img',
                '.chapter-images img',
                '.manga-images img',
                '.wp-manga-chapter-content .page-break img',
                '.manga-chapter-content .page-break img',
                '.readerarea img',
                '.wp-manga-chapter-content .readerarea img',
                '.manga-chapter-content .readerarea img',
                '.reading-content .readerarea img',
                '.chapter-content .readerarea img'
            ]
            
            for selector in image_selectors:
                images = soup.select(selector)
                if images:
                    break
            
            # Method 2: Look for JavaScript variables that might contain image URLs
            if not images:
                scripts = soup.find_all('script')
                for script in scripts:
                    script_content = script.get_text()
                    
                    # Look for common patterns in JavaScript that contain image URLs
                    patterns = [
                        r'var\s+images\s*=\s*\[(.*?)\]',
                        r'images\s*:\s*\[(.*?)\]',
                        r'imageList\s*=\s*\[(.*?)\]',
                        r'chapterImages\s*=\s*\[(.*?)\]',
                        r'"images"\s*:\s*\[(.*?)\]',
                        r"'images'\s*:\s*\[(.*?)\]"
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script_content, re.DOTALL)
                        for match in matches:
                            # Try to extract URLs from the match
                            urls = re.findall(r'["\']([^"\']*\.(?:jpg|jpeg|png|webp))["\']', match)
                            for url in urls:
                                if url and self.is_valid_image_url(url):
                                    # Create a fake img element
                                    from bs4 import Tag
                                    img = Tag(name='img')
                                    img['src'] = url
                                    images.append(img)
            
            # Method 3: Look for any images that might be chapter content
            if not images:
                all_images = soup.find_all('img')
                for img in all_images:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                    if src and self.is_valid_image_url(src):
                        # Check if it's likely a chapter image (not an ad or icon)
                        parent_classes = ' '.join(img.parent.get('class', [])) if img.parent else ''
                        alt_text = img.get('alt', '').lower()
                        
                        # Skip images that are clearly not manga pages
                        skip_indicators = ['ad', 'advertisement', 'banner', 'sidebar', 'logo', 'icon']
                        if not any(indicator in parent_classes.lower() for indicator in skip_indicators):
                            # Skip small images and logos
                            width = img.get('width', '0')
                            height = img.get('height', '0')
                            
                            if width and height:
                                try:
                                    w, h = int(width), int(height)
                                    if w > 300 and h > 300:  # Reasonable size for manga pages
                                        images.append(img)
                                except:
                                    images.append(img)
                            else:
                                # If no size info, check the URL for manga-like patterns
                                if any(pattern in src.lower() for pattern in ['chapter', 'page', 'manga']):
                                    images.append(img)
            
            if not images:
                print(f"No chapter images found on {chapter_url}")
                print("This might be due to:")
                print("1. Dynamic content loading via JavaScript")
                print("2. Anti-bot protection")
                print("3. Site structure changes")
                return False
            
            return self._download_images(images, dest_folder, chapter_url)
            
        except Exception as e:
            print(f"Error downloading chapter from Asura Scans: {e}")
            return False
    
    def _download_images(self, images, dest_folder, chapter_url):
        """Helper method to download images."""
        downloaded_count = 0
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
                
                downloaded_count += 1
                print(f"Downloaded: {filename}")
                        
            except Exception as e:
                print(f"Error downloading image {img_url}: {e}")
                continue
        
        print(f"Successfully downloaded {downloaded_count} images")
        return downloaded_count > 0 