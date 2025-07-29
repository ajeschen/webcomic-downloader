from abc import ABC, abstractmethod

class BaseScraper(ABC):
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