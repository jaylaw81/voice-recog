# Requires: pip install requests beautifulsoup4 flask flask-cors xmltodict
import json
from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import xmltodict
import re
import certifi
import ssl

# Create a custom SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)
CORS(app)

# Define custom headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

# Load configuration from config.json
def load_config():
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

config = load_config()

def get_first_image(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        first_image = soup.find('img')
        if first_image:
            return first_image['src']
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
         print(f"An error occurred: {e}")
         return None

def get_sitemap_urls(sitemap_url):
    try:
        s = requests.Session()
        response = s.get(sitemap_url, headers=HEADERS)
        response.raise_for_status()
        sitemap = xmltodict.parse(response.content)
        
        urls = []
        for entry in sitemap.get('sitemapindex', {}).get('sitemap', []):
            if 'loc' in entry:
                urls.extend(get_sitemap_urls(entry['loc']))
        
        if not urls:  # If it's a regular sitemap
            for entry in sitemap.get('urlset', {}).get('url', []):
                if 'loc' in entry:
                    urls.append(entry['loc'])
        print(f"sitemap urls: {urls}")
        return urls
    except Exception as e:
        print(f"Error processing sitemap: {e}")
        return []

def scrape_page(url):
    try:
        s = requests.Session()
        response = s.get(url, headers=HEADERS, verify=certifi.where())
        soup = BeautifulSoup(response.text, 'html.parser')
        faqs = []  # List to store the extracted FAQs
        hero_image = get_first_image(url)  # Fetch the hero image

        # Load scrape patterns from config
        scrape_patterns = config.get("scrape_patterns", [])

        # Process each pattern in the array
        for pattern_config in scrape_patterns:
            # Get the selectors for the current pattern
            selector = pattern_config.get("selector")
            question_selector = pattern_config.get("question")
            answer_selector = pattern_config.get("answer")

            if not selector or not question_selector or not answer_selector:
                continue  # Skip if any selector is missing

            # Find all items matching the selector
            items = soup.select(selector)
            for item in items:
                question = item.select_one(question_selector)
                answer = item.select_one(answer_selector)

                # Validate and store the question and answer
                if question and answer:
                    faqs.append({
                        "question": question.get_text(strip=True).strip("?"),
                        "answer": answer.get_text(),
                        "image": hero_image,
                        "source_url": url
                    })

        return faqs
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def scrape_site():

    sitemap_path = config.get("sitemap", "")

    sitemap_url = sitemap_path
    all_urls = get_sitemap_urls(sitemap_url)
    
    # Load FAQ URL pattern from config
    faq_url_pattern = config.get("faq_url_pattern", "")
    
    # Filter URLs for relevant content
    faq_urls = [
        url for url in all_urls
        if re.search(faq_url_pattern, url, re.I)
    ]
    # Scrape filtered URLs
    all_faqs = []
    for url in faq_urls:
        all_faqs.extend(scrape_page(url))
    
    # Deduplicate FAQs
    seen = set()
    return [faq for faq in all_faqs if not (faq['question'] in seen or seen.add(faq['question']))]

@app.route('/api/faqs')
def get_faqs():
    return jsonify(scrape_site())

if __name__ == '__main__':
    app.run(port=5000)