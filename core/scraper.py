"""
Web scraping engine — fetches pages and extracts raw content.
Supports static HTML, JavaScript-rendered pages, and API endpoints.
"""

import json
import re
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class ScrapeResult:
    """Container for scraped page data."""
    
    def __init__(self, url: str, html: str = "", text: str = "", 
                 title: str = "", status_code: int = 200, error: str = ""):
        self.url = url
        self.html = html
        self.text = text
        self.title = title
        self.status_code = status_code
        self.error = error
        self.metadata = {}
    
    @property
    def success(self) -> bool:
        return self.status_code < 400 and not self.error
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "text_preview": self.text[:500],
            "text_length": len(self.text),
            "status_code": self.status_code,
            "success": self.success,
            "error": self.error,
        }


def scrape(url: str, timeout: int = 30, user_agent: str = None,
           headers: dict = None, proxy: str = None) -> ScrapeResult:
    """
    Fetch a URL and extract clean text content.
    
    Args:
        url: The URL to scrape
        timeout: Request timeout in seconds
        user_agent: Custom User-Agent header
        headers: Additional HTTP headers
        proxy: Proxy URL (e.g., http://proxy:8080)
    
    Returns:
        ScrapeResult with extracted data
    """
    default_ua = "ExtractX/1.0 (AI Web Scraper; +https://extractx.dev)"
    
    req_headers = {
        "User-Agent": user_agent or default_ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
    }
    
    if headers:
        req_headers.update(headers)
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        # First try direct GET
        resp = requests.get(
            url,
            headers=req_headers,
            timeout=timeout,
            proxies=proxies,
            allow_redirects=True,
        )
        resp.raise_for_status()
        
        html = resp.text
        soup = BeautifulSoup(html, "lxml")
        
        # Remove script/style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        # Extract clean text
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        # Get title
        title = soup.title.string.strip() if soup.title else ""
        
        # Extract metadata
        meta = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property") or tag.get("itemprop")
            content = tag.get("content")
            if name and content:
                meta[name] = content
        
        # Extract JSON-LD
        jsonld = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                jsonld.append(json.loads(script.string))
            except (json.JSONDecodeError, TypeError):
                pass
        
        result = ScrapeResult(
            url=resp.url,  # Final URL after redirects
            html=html,
            text=text,
            title=title,
            status_code=resp.status_code,
        )
        result.metadata = {"meta": meta, "jsonld": jsonld}
        return result
        
    except requests.RequestException as e:
        return ScrapeResult(url=url, status_code=0, error=str(e))


def fetch_json(url: str, timeout: int = 30, **kwargs) -> dict:
    """Fetch a JSON API endpoint."""
    try:
        resp = requests.get(url, timeout=timeout, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
