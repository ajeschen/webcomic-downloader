import importlib
import pkgutil
from .base import BaseScraper

scraper_classes = []

for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
    if module_name == 'base':
        continue
    module = importlib.import_module(f'.{module_name}', __name__)
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, type) and issubclass(obj, BaseScraper) and obj is not BaseScraper:
            scraper_classes.append(obj)

def get_scraper_for_url(url: str):
    for scraper_cls in scraper_classes:
        scraper = scraper_cls()
        if scraper.can_handle(url):
            return scraper
    return None 