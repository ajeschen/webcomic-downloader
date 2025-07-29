"""
Configuration for different scanlation sites and their domains.
This makes it easy to add new sites and handle domain changes.
"""

# Configuration for different scanlation sites
SITE_CONFIGS = {
    "asura_scans": {
        "name": "Asura Scans",
        "domains": [
            "asurascanlation.com",
            "asurascans.com",
            "asura.gg",
            "asura.xyz",
            "asurascans.net",
            "asurascans.org"
        ],
        "scraper_class": "AsuraScansScraper",
        "chapter_selectors": [
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
            '.wp-manga-chapter a',
            '.manga-chapter a',
            '.chapter a',
            '.wp-manga-chapter-list .chapter a',
            '.manga-chapter-list .chapter a'
        ],
        "image_selectors": [
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
            '.manga-chapter-content .page-break img'
        ]
    },
    
    "reaper_scans": {
        "name": "Reaper Scans",
        "domains": [
            "reaperscans.com",
            "reaperscans.net",
            "reaperscans.org"
        ],
        "scraper_class": "WordPressMangaScraper",
        "chapter_selectors": [
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
            '.wp-manga-chapter-name a'
        ],
        "image_selectors": [
            '.reading-content img',
            '.chapter-content img',
            '.manga-chapter-content img',
            '.wp-manga-chapter-content img',
            '.reading-content .page-break img',
            '.chapter-content .page-break img'
        ]
    },
    
    "flame_scans": {
        "name": "Flame Scans",
        "domains": [
            "flamescans.org",
            "flamescans.com",
            "flamescans.net"
        ],
        "scraper_class": "WordPressMangaScraper",
        "chapter_selectors": [
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
            '.wp-manga-chapter-name a'
        ],
        "image_selectors": [
            '.reading-content img',
            '.chapter-content img',
            '.manga-chapter-content img',
            '.wp-manga-chapter-content img',
            '.reading-content .page-break img',
            '.chapter-content .page-break img'
        ]
    }
}

def get_site_config_for_url(url: str):
    """Get the site configuration for a given URL."""
    from urllib.parse import urlparse
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    for site_id, config in SITE_CONFIGS.items():
        for known_domain in config["domains"]:
            if known_domain in domain:
                return site_id, config
    
    return None, None

def add_site_config(site_id: str, name: str, domains: list, scraper_class: str = "WordPressMangaScraper"):
    """Add a new site configuration."""
    SITE_CONFIGS[site_id] = {
        "name": name,
        "domains": domains,
        "scraper_class": scraper_class,
        "chapter_selectors": [
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
            '.wp-manga-chapter-name a'
        ],
        "image_selectors": [
            '.reading-content img',
            '.chapter-content img',
            '.manga-chapter-content img',
            '.wp-manga-chapter-content img',
            '.reading-content .page-break img',
            '.chapter-content .page-break img'
        ]
    }

def update_site_domains(site_id: str, new_domains: list):
    """Update domains for an existing site."""
    if site_id in SITE_CONFIGS:
        SITE_CONFIGS[site_id]["domains"] = new_domains 