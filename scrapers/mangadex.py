import os
import re
import requests
from .base import BaseScraper

def sanitize_filename(name):
    # Remove invalid Windows filename characters and trailing dots/spaces
    return re.sub(r'[<>:"/\\|?*]', '', name).rstrip('. ')

class MangaDexScraper(BaseScraper):
    """Scraper for MangaDex titles and chapters."""

    API_URL = "https://api.mangadex.org"
    CDN_URL = "https://uploads.mangadex.org"

    def can_handle(self, url: str) -> bool:
        return "mangadex.org" in url

    def get_chapters(self, url: str, language: str = 'en'):
        # Extract manga ID from URL
        try:
            manga_id = url.split("/title/")[1].split("/")[0]
        except Exception:
            raise ValueError("Invalid MangaDex URL")
        # Fetch chapters
        chapters = []
        offset = 0
        all_chapters = []
        while True:
            params = {
                "manga": manga_id,
                "translatedLanguage[]": [language] if language != 'all' else None,
                "order[chapter]": "asc",
                "limit": 100,
                "offset": offset
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            resp = requests.get(f"{self.API_URL}/chapter", params=params)
            resp.raise_for_status()
            data = resp.json()
            for ch in data["data"]:
                all_chapters.append({
                    "id": ch["id"],
                    "chapter": ch["attributes"].get("chapter", "?"),
                    "title": ch["attributes"].get("title", ""),
                    "lang": ch["attributes"].get("translatedLanguage", "")
                })
            if len(data["data"]) < 100:
                break
            offset += 100
        # Deduplicate: only one translation per chapter number
        seen = set()
        for ch in all_chapters:
            ch_num = ch["chapter"]
            if ch_num in seen:
                continue
            seen.add(ch_num)
            chapters.append(ch)
        return chapters

    def download_chapter(self, chapter_id: str, dest_folder: str) -> bool:
        # Get server info
        resp = requests.get(f"{self.API_URL}/at-home/server/{chapter_id}")
        if resp.status_code != 200:
            return False
        data = resp.json()
        base_url = data["baseUrl"]
        chapter = data["chapter"]
        hash_ = chapter["hash"]
        pages = chapter["data"]
        # Sanitize dest_folder
        safe_folder = os.path.sep.join(sanitize_filename(part) for part in dest_folder.split(os.path.sep))
        os.makedirs(safe_folder, exist_ok=True)
        for i, page in enumerate(pages):
            img_url = f"{base_url}/data/{hash_}/{page}"
            img_path = os.path.join(safe_folder, f"{i+1:03d}_{page}")
            if os.path.exists(img_path):
                continue  # Skip duplicates
            img_resp = requests.get(img_url, stream=True)
            if img_resp.status_code == 200:
                with open(img_path, "wb") as f:
                    for chunk in img_resp.iter_content(1024):
                        f.write(chunk)
            else:
                return False
        return True 