# Requires: pip install requests beautifulsoup4 xmltodict
import json
import requests
from bs4 import BeautifulSoup
import xmltodict
import re
import certifi
import ssl

# Define headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

# Create a custom SSL context for secure HTTPS requests
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Load configuration from config.json
def load_config():
    try:
        with open("config_terms.json", "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

# Parse the sitemap and retrieve all URLs
def get_sitemap_urls(sitemap_url):
    try:
        response = requests.get(sitemap_url, headers=HEADERS)
        response.raise_for_status()
        sitemap = xmltodict.parse(response.content)
        urls = []
        
        # Handle sitemap indexes if present
        for entry in sitemap.get('sitemapindex', {}).get('sitemap', []):
            if 'loc' in entry:
                urls.extend(get_sitemap_urls(entry['loc']))
        
        # Handle regular sitemap
        for entry in sitemap.get('urlset', {}).get('url', []):
            if 'loc' in entry:
                urls.append(entry['loc'])
        
        return urls
    except Exception as e:
        print(f"Error processing sitemap: {e}")
        return []

# Scrape a single page based on the "selector" in the config
def scrape_page(url, selector):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []

        # Find all elements matching the specified selector
        elements = soup.select(selector)

        # Extract and store text content from each matching element
        for element in elements:
            results.append({
                "content": element.get_text(strip=True),
                "source_url": url
            })

        return results
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# Function to scrape the entire site based on the selector
def scrape_site():
    config = load_config()

    sitemap_url = config.get("sitemap", "")
    selector = config.get("scrape_patterns", [])[0].get("selector", "")  # Use the first selector

    if not selector:
        print("Error: No selector found in the configuration.")
        return []

    # Get all URLs from the sitemap
    all_urls = get_sitemap_urls(sitemap_url)

    # Scrape each URL and gather results
    all_results = []
    for url in all_urls:
        all_results.extend(scrape_page(url, selector))

    return all_results

# Entry point for the script
if __name__ == "__main__":
    print("Scraping site based on the selector in config.json...")
    results = scrape_site()

    # Output the results as JSON
    print(json.dumps(results, indent=2))