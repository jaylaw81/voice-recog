import json
from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import xmltodict
import re
import certifi
import ssl
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Create a custom SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)
CORS(app)

# Initialize BERT model for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

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
        with open("config_nlp.json", "r") as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

config = load_config()

def is_faq_related_bert(url, page_content=None, threshold=0.7):
    """
    Use BERT to determine if a URL or page content is FAQ-related
    """
    try:
        faq_keywords = [
            "frequently asked questions",
            "common questions",
            "help center",
            "support questions",
            "customer questions",
            "FAQ",
            "questions and answers",
            "Q&A",
            "help and support"
        ]
        
        url_parts = url.replace('/', ' ').replace('-', ' ').replace('_', ' ')
        text_to_analyze = page_content if page_content else url_parts
        
        text_embedding = model.encode([text_to_analyze])
        keyword_embeddings = model.encode(faq_keywords)
        
        similarities = cosine_similarity(text_embedding, keyword_embeddings)[0]
        max_similarity = np.max(similarities)
        
        print(f"URL: {url}, Max similarity: {max_similarity:.3f}")
        
        return max_similarity >= threshold
        
    except Exception as e:
        print(f"Error in BERT analysis for {url}: {e}")
        return False

def classify_faq_content_bert(text, threshold=0.5):
    """
    Use BERT with more flexible partial matching patterns
    """
    try:
        # More flexible patterns that can match partially
        faq_patterns = [
            "common questions",
            "questions about",
            "what to know",
            "frequently asked",
            "FAQ",
            "Q&A",
            "help center",
            "support",
            "can",
            "are",
            "how to",
            "what is",
            "why does",
            "where can",
            "when should",
            "who is",
            "which is",
            "how does",
            "how can",
            "how do",
            "how will",
            "do I",
            "does it",
            "is it",            
        ]
        
        # Substring matching first
        text_lower = text.lower()
        for pattern in faq_patterns:
            if pattern.lower() in text_lower:
                print(f"Partial substring match found: '{pattern}'")
                return True
        
        # BERT semantic matching with lower threshold since we have more patterns
        cleaned_text = ' '.join(text.split()[:200])
        
        text_embedding = model.encode([cleaned_text])
        pattern_embeddings = model.encode(faq_patterns)
        
        similarities = cosine_similarity(text_embedding, pattern_embeddings)[0]
        max_similarity = np.max(similarities)
        
        print(f"Content classification similarity: {max_similarity:.3f}")
        
        return max_similarity >= threshold
        
    except Exception as e:
        print(f"Error in content classification: {e}")
        return False

def get_page_content_preview(url, max_chars=500):
    """
    Get a preview of page content for BERT analysis
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        print(f"Error getting page content for {url}: {e}")
        return ""

def get_first_image(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
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
        
        if not urls:
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
        faqs = []
        hero_image = get_first_image(url)

        # First, check if the page content is FAQ-related using BERT
        page_text = soup.get_text()
        if not classify_faq_content_bert(page_text):
            print(f"Page content not classified as FAQ-related: {url}")
            return []

        scrape_patterns = config.get("scrape_patterns", [])

        for pattern_config in scrape_patterns:
            selector = pattern_config.get("selector")
            question_selector = pattern_config.get("question")
            answer_selector = pattern_config.get("answer")

            if not selector or not question_selector or not answer_selector:
                continue

            items = soup.select(selector)
            for item in items:
                question = item.select_one(question_selector)
                answer = item.select_one(answer_selector)

                if question and answer:
                    # Use BERT to validate each individual FAQ item
                    combined_text = f"{question.get_text()} {answer.get_text()}"
                    
                    # Only include if it passes BERT FAQ classification
                    if len(combined_text.strip()) > 20 and classify_faq_content_bert(combined_text, threshold=0.5):
                        faqs.append({
                            "question": question.get_text(strip=True).strip("?"),
                            "answer": answer.get_text(),
                            "image": hero_image,
                            "source_url": url
                        })
                    else:
                        print(f"FAQ item filtered out by BERT: {question.get_text()[:50]}...")

        return faqs
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def scrape_site():
    sitemap_path = config.get("sitemap", "")
    sitemap_url = sitemap_path
    all_urls = get_sitemap_urls(sitemap_url)
    
    # Use BERT for URL filtering
    faq_urls = []
    
    for url in all_urls:
        # Deeper analysis with page content
        page_content = get_page_content_preview(url)
        if page_content:
            faq_urls.append(url)
    
    print(f"Found {len(faq_urls)} FAQ-related URLs using BERT")
    
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