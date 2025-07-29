# Webcomic Downloader

A Python-based webcomic downloader with a modern GUI that supports multiple scanlation sites.

## Features

- **Multi-Site Support**: Download from various scanlation sites including:
  - MangaDex
  - Asura Scans (and multiple domains)
  - Reaper Scans
  - Flame Scans
  - Any WordPress-based manga site
- **Modern GUI**: Built with PySide6 for a clean, responsive interface
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Flexible Architecture**: Easy to add new sites and handle domain changes
- **Batch Downloading**: Download entire series with progress tracking
- **Retry Mechanism**: Automatic retry for failed downloads
- **Advanced Image Detection**: Handles lazy loading and dynamic content loading
- **API Integration**: Uses WordPress API endpoints for reliable image extraction

## Supported Sites

### Currently Supported
- **MangaDex** (`mangadex.org`) - Official API support
- **Asura Scans** - Multiple domains supported:
  - `asurascanlation.com`
  - `asurascans.com`
  - `asura.gg`
  - `asura.xyz`
  - `asurascans.net`
  - `asurascans.org`
- **Reaper Scans** - WordPress-based site
- **Flame Scans** - WordPress-based site
- **Generic WordPress Sites** - Automatically detects and handles most WordPress manga sites

### Adding New Sites

The application uses a modular scraper system. To add a new site:

1. **For WordPress-based sites**: The generic `WordPressMangaScraper` will automatically handle most sites
2. **For custom sites**: Create a new scraper class in the `scrapers/` directory
3. **Update site configuration**: Add domain information to `scrapers/site_config.py`

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/webcomic-downloader.git
   cd webcomic-downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

   Or on Windows:
   ```bash
   run_windows.bat
   ```

## Usage

1. **Launch the application** - The GUI will open with a clean, modern interface
2. **Enter a webcomic URL** - Paste the URL of any supported scanlation site
3. **Select language** - Choose your preferred language (English, Spanish, French, or All)
4. **Start download** - Click "Start Download" to begin downloading chapters
5. **Monitor progress** - Watch the progress bar and chapter status table
6. **Retry failed downloads** - Use the retry buttons for any failed chapters

## Architecture

### Scraper System
The application uses a modular scraper architecture:

- **Base Scraper** (`scrapers/base.py`): Abstract base class with common functionality
- **Site-Specific Scrapers**: Specialized scrapers for specific sites
- **Generic WordPress Scraper**: Handles most WordPress manga sites
- **Configuration System**: Easy management of site domains and selectors

### Key Components
- `main.py`: Application entry point
- `ui/main_window.py`: GUI implementation
- `scrapers/`: Scraper modules
  - `base.py`: Base scraper class
  - `mangadex.py`: MangaDex API scraper
  - `asura_scans.py`: Asura Scans scraper
  - `wordpress_manga.py`: Generic WordPress scraper
  - `site_config.py`: Site configuration management
- `utils/`: Utility functions

## Technical Features

### Advanced Image Detection
The application handles various challenges in modern web scraping:

- **Lazy Loading**: Detects and handles images loaded via JavaScript
- **Dynamic Content**: Uses WordPress API endpoints for reliable image extraction
- **Multiple Fallback Methods**: Tries different approaches if primary method fails
- **Anti-Bot Protection**: Implements delays and user agent spoofing
- **Image Filtering**: Automatically filters out ads, logos, and non-manga content

### WordPress Integration
For WordPress-based sites, the application:

- Uses WordPress REST API endpoints for reliable data extraction
- Handles various WordPress manga plugin structures
- Supports multiple domain configurations
- Automatically detects site structure changes

## Adding Support for New Sites

### Method 1: Using the Generic WordPress Scraper
Most scanlation sites use WordPress with manga plugins. The generic scraper will automatically detect and handle these sites.

### Method 2: Creating a Custom Scraper
For sites with unique structures:

1. Create a new file in `scrapers/` (e.g., `scrapers/my_site.py`)
2. Inherit from `BaseScraper`
3. Implement the required methods:
   - `can_handle(url)`: Return True if this scraper can handle the URL
   - `get_chapters(url, language)`: Extract chapter list
   - `download_chapter(chapter_url, dest_folder)`: Download chapter images

Example:
```python
from .base import BaseScraper

class MySiteScraper(BaseScraper):
    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url
    
    def get_chapters(self, url: str, language: str = 'en'):
        # Implementation here
        pass
    
    def download_chapter(self, chapter_url: str, dest_folder: str) -> bool:
        # Implementation here
        pass
```

### Method 3: Updating Site Configuration
For existing sites with new domains:

1. Edit `scrapers/site_config.py`
2. Add new domains to the appropriate site configuration
3. Or use the helper functions:
   ```python
   from scrapers.site_config import update_site_domains
   update_site_domains("asura_scans", ["newdomain.com", "anotherdomain.com"])
   ```

## Troubleshooting

### Common Issues

1. **No chapters found**: The site structure may have changed. Try updating the selectors in the site configuration.

2. **Download failures**: 
   - Check your internet connection
   - The site may be blocking automated requests
   - Try again later (sites may have temporary issues)

3. **Domain changes**: Scanlation sites often change domains. Update the site configuration with new domains.

4. **Lazy loading issues**: The application now handles most lazy loading scenarios automatically. If issues persist, the site may have implemented new anti-bot measures.

### Debugging
Use the test scripts to debug issues:
```bash
python test_scrapers.py  # Test scraper detection
python debug_asura.py    # Debug specific site issues
```

## Recent Updates

### Version 2.0 - Multi-Site Support
- Added support for multiple scanlation sites
- Implemented WordPress API integration
- Fixed lazy loading and dynamic content issues
- Enhanced image detection and filtering
- Added domain change handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for personal use only. Please respect the terms of service of the websites you download from and support the creators when possible. 