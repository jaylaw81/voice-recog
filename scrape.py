# Requires: pip install requests beautifulsoup4 flask flask-cors xmltodict
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

def get_first_image(url):
    try:
        response = requests.get(url)
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
        response = s.get(sitemap_url)
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
        response = s.get(url, verify=certifi.where())
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for FAQ content patterns
        faqs = []
        
        # Pattern 1: FAQ pages with question/answer sections
        faq_items = soup.select('details[data-component="accordion"]')
        card_items = soup.select('.exposedgridcard')
        hero_image = get_first_image(url)
        for item in faq_items:
            question = item.select_one('.accordion__subheading h3')
            answer = item.select_one('.accordion__body p')
            print(f"URL {url} Question: {question}")
            
            if question and answer:
                faqs.append({
                    'question': question.get_text(strip=True).strip("?"),
                    'answer': answer.get_text(),
                    'image': hero_image,
                    'source_url': url
                })

        
        for item in card_items:
            question = item.select_one('h3.card-content__heading')
            answer = item.select_one('.rte p')
            
            if question and answer:
                faqs.append({
                    'question': question.get_text(strip=True).strip("?"),
                    'answer': answer.get_text(),
                    'image': hero_image,
                    'source_url': url
                })

        return faqs
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def scrape_site():
    sitemap_url = 'http://localhost:3000/sitemap.xml'
    all_urls = get_sitemap_urls(sitemap_url)
    
    # Filter URLs for relevant content
    faq_urls = [
        url for url in all_urls
        if re.search(r'(army-life|basic-training|how-to|requirements|basic-training|benefits|find-your-path|specialty-careers|job-training)', url, re.I)
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