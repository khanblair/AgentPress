"""
app/tools/research_skills/web_scraper.py

Agent Reach tool for generic HTTP scraping.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict


def scrape_urls(urls: List[str]) -> Dict[str, str]:
    """
    Scrapes a list of URLs and returns a combined text dump.
    """
    results = {}
    combined_text = ""
    
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator=' ')
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            results[url] = clean_text[:5000] # Cap per URL
            combined_text += f"\n--- SOURCE: {url} ---\n{clean_text[:5000]}\n"
        except Exception as e:
            results[url] = f"Error: {str(e)}"
            
    return {"text": combined_text, "results": results}
