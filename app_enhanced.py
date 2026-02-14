"""
Enhanced Flask API with Web Scraping
Works with ANY Amazon/Flipkart product link
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import traceback
import random
from urllib.parse import quote, quote_plus, urlparse, unquote

app = Flask(__name__)
CORS(app)

# ==========================================
# GLOBAL VARIABLES
# ==========================================
MODELS_CACHE = {}
CATEGORY_MODELS_CACHE = {}
DF_CLEAN = None
FIRST_DATE = None

# ==========================================
# WEB SCRAPING - Get Current Price from URL
# ==========================================
class PriceScraper:
    """Scrape current price from Amazon/Flipkart/Myntra."""
    
    @staticmethod
    def get_headers():
        """Random user agent to avoid blocking."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
        }

    @staticmethod
    def extract_title(soup, selectors, fallback_suffixes=None):
        """Extract product title from selectors and metadata."""
        fallback_suffixes = fallback_suffixes or []

        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = " ".join(title_elem.get_text().strip().split())
                if title:
                    for suffix in fallback_suffixes:
                        if title.lower().endswith(suffix.lower()):
                            title = title[: -len(suffix)].strip()
                    return title

        meta_selectors = [
            'meta[property="og:title"]',
            'meta[name="title"]',
            'meta[name="twitter:title"]'
        ]
        for selector in meta_selectors:
            meta_elem = soup.select_one(selector)
            if meta_elem and meta_elem.get('content'):
                title = " ".join(meta_elem.get('content').strip().split())
                if title:
                    for suffix in fallback_suffixes:
                        if title.lower().endswith(suffix.lower()):
                            title = title[: -len(suffix)].strip()
                    return title

        title_elem = soup.select_one('title')
        if title_elem:
            title = " ".join(title_elem.get_text().strip().split())
            if title:
                for suffix in fallback_suffixes:
                    if title.lower().endswith(suffix.lower()):
                        title = title[: -len(suffix)].strip()
                return title

        return None

    @staticmethod
    def parse_price(price_text):
        """Parse a human-readable price string into float."""
        if not price_text:
            return None

        normalized = (
            str(price_text)
            .replace('₹', '')
            .replace('Rs.', '')
            .replace('Rs', '')
            .strip()
        )
        match = re.search(r'(\d[\d,]*\.?\d*)', normalized)
        if not match:
            return None

        numeric_str = match.group(1).replace(',', '')
        try:
            value = float(numeric_str)
            return value if value > 0 else None
        except ValueError:
            return None

    @staticmethod
    def extract_price_from_ld_json(html):
        """Extract price from JSON-LD blocks when CSS selectors fail."""
        patterns = [
            r'"price"\s*:\s*"?(?P<price>\d[\d,]*\.?\d*)"?',
            r'"currentPrice"\s*:\s*"?(?P<price>\d[\d,]*\.?\d*)"?'
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                parsed = PriceScraper.parse_price(match.group('price'))
                if parsed:
                    return parsed
        return None

    @staticmethod
    def normalize_image_url(url):
        """Normalize image URLs to absolute URL where possible."""
        if not url:
            return None
        clean = url.strip()
        if clean.startswith('//'):
            return f"https:{clean}"
        return clean

    @staticmethod
    def extract_image_url(soup, selectors):
        """Extract product image URL from image/meta selectors."""
        for selector in selectors:
            elem = soup.select_one(selector)
            if not elem:
                continue
            src = (
                elem.get('src')
                or elem.get('data-src')
                or elem.get('data-original')
                or elem.get('content')
            )
            normalized = PriceScraper.normalize_image_url(src)
            if normalized:
                return normalized

        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get('content'):
            return PriceScraper.normalize_image_url(og_image.get('content'))

        twitter_image = soup.select_one('meta[name="twitter:image"]')
        if twitter_image and twitter_image.get('content'):
            return PriceScraper.normalize_image_url(twitter_image.get('content'))

        return None
    
    @staticmethod
    def scrape_amazon(url):
        """Scrape price and title from Amazon."""
        try:
            response = requests.get(url, headers=PriceScraper.get_headers(), timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            title = PriceScraper.extract_title(soup, [
                '#productTitle',
                'span#title',
                'h1.a-size-large'
            ], fallback_suffixes=[': Amazon.in', '| Amazon.in'])
            image_url = PriceScraper.extract_image_url(soup, [
                '#landingImage',
                '#imgTagWrapperId img',
                'img[data-old-hires]',
                'img.a-dynamic-image'
            ])
            # Try multiple selectors for price
            price_selectors = [
                'span.a-price.aok-align-center span.a-offscreen',
                'span.a-price-whole',
                'span.a-price span.a-offscreen',
                'span#priceblock_ourprice',
                'span#priceblock_dealprice',
                'span.a-color-price'
            ]
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    parsed_price = PriceScraper.parse_price(price_text)
                    if parsed_price:
                        return {'price': parsed_price, 'title': title, 'image_url': image_url}

            meta_price = soup.select_one('meta[property="product:price:amount"]')
            if meta_price and meta_price.get('content'):
                parsed_price = PriceScraper.parse_price(meta_price.get('content'))
                if parsed_price:
                    return {'price': parsed_price, 'title': title, 'image_url': image_url}

            ld_price = PriceScraper.extract_price_from_ld_json(response.text)
            if ld_price:
                return {'price': ld_price, 'title': title, 'image_url': image_url}

            return {'price': None, 'title': title, 'image_url': image_url}
        except Exception as e:
            print(f"Error scraping Amazon: {e}")
            return {'price': None, 'title': None, 'image_url': None}

    @staticmethod
    def scrape_flipkart(url):
        """Scrape price and title from Flipkart."""
        try:
            response = requests.get(url, headers=PriceScraper.get_headers(), timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            title = PriceScraper.extract_title(soup, [
                'span.VU-ZEz',
                'span.B_NuCI',
                'h1.yhB1nd span',
                'h1'
            ], fallback_suffixes=['| Flipkart.com', '| Flipkart'])
            image_url = PriceScraper.extract_image_url(soup, [
                'img._396cs4',
                'img._2r_T1I',
                'img.DByuf4',
                'img.CXW8mj',
                'div._3kidJX img'
            ])
            # Try multiple selectors for price
            price_selectors = [
                'div.Nx9bqj.CxhGGd',
                'div.Nx9bqj',
                'div._30jeq3',
                'div._1vC4OE',
                'div._3I9_wc',
                'div.CEmiEU'
            ]
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    parsed_price = PriceScraper.parse_price(price_text)
                    if parsed_price:
                        return {'price': parsed_price, 'title': title, 'image_url': image_url}

            meta_price = soup.select_one('meta[property="product:price:amount"]')
            if meta_price and meta_price.get('content'):
                parsed_price = PriceScraper.parse_price(meta_price.get('content'))
                if parsed_price:
                    return {'price': parsed_price, 'title': title, 'image_url': image_url}

            ld_price = PriceScraper.extract_price_from_ld_json(response.text)
            if ld_price:
                return {'price': ld_price, 'title': title, 'image_url': image_url}

            return {'price': None, 'title': title, 'image_url': image_url}
        except Exception as e:
            print(f"Error scraping Flipkart: {e}")
            return {'price': None, 'title': None, 'image_url': None}

    @staticmethod
    def scrape_myntra(url):
        """Scrape price and title from Myntra."""
        try:
            response = requests.get(url, headers=PriceScraper.get_headers(), timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            title = PriceScraper.extract_title(soup, [
                'h1.pdp-name',
                'h1.pdp-title',
                'h1',
                'span.pdp-name'
            ], fallback_suffixes=['| Myntra', '| Myntra.com'])
            image_url = PriceScraper.extract_image_url(soup, [
                'img.img-responsive',
                'picture img',
                'img.pdp-image'
            ])

            price_selectors = [
                'span.pdp-price strong',
                'span.pdp-price',
                'div.pdp-price-info span',
                'span[data-testid="price"]'
            ]
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    parsed_price = PriceScraper.parse_price(price_text)
                    if parsed_price:
                        return {'price': parsed_price, 'title': title, 'image_url': image_url}

            meta_price = soup.select_one('meta[property="product:price:amount"]')
            if meta_price and meta_price.get('content'):
                parsed_price = PriceScraper.parse_price(meta_price.get('content'))
                if parsed_price:
                    return {'price': parsed_price, 'title': title, 'image_url': image_url}

            ld_price = PriceScraper.extract_price_from_ld_json(response.text)
            if ld_price:
                return {'price': ld_price, 'title': title, 'image_url': image_url}

            return {'price': None, 'title': title, 'image_url': image_url}
        except Exception as e:
            print(f"Error scraping Myntra: {e}")
            return {'price': None, 'title': None, 'image_url': None}

    @staticmethod
    def scrape_details(url, source):
        """Main scraping function for product details."""
        print(f"Attempting to scrape product details from {source}...")
        if source == 'amazon':
            details = PriceScraper.scrape_amazon(url)
        elif source == 'flipkart':
            details = PriceScraper.scrape_flipkart(url)
        elif source == 'myntra':
            details = PriceScraper.scrape_myntra(url)
        else:
            details = {'price': None, 'title': None, 'image_url': None}
        price = details.get('price')
        title = details.get('title')
        image_url = details.get('image_url')
        if price:
            print(f"Scraped price: {price}")
        else:
            print("Could not scrape price, will use estimated price")
        if title:
            print(f"Scraped title: {title}")
        else:
            print("Could not scrape title, will use parsed product name")
        if image_url:
            print(f"Scraped image URL: {image_url}")
        else:
            print("Could not scrape image, will use fallback")
        return details

    @staticmethod
    def scrape_search_price(product_name, source):
        """Best-effort: scrape first visible price from search results page."""
        try:
            query = quote_plus(product_name)
            if source == 'amazon':
                search_url = f"https://www.amazon.in/s?k={query}"
                selectors = [
                    'span.a-price span.a-offscreen',
                    '.s-result-item span.a-price-whole'
                ]
            elif source == 'flipkart':
                search_url = f"https://www.flipkart.com/search?q={query}"
                selectors = [
                    'div.Nx9bqj',
                    'div._30jeq3',
                    'div._1vC4OE'
                ]
            else:
                return None

            response = requests.get(search_url, headers=PriceScraper.get_headers(), timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    parsed = PriceScraper.parse_price(elem.get_text().strip())
                    if parsed:
                        return parsed
            return None
        except Exception:
            return None

    @staticmethod
    def get_marketplace_prices(product_name):
        """Fetch Amazon and Flipkart current prices by product-name search."""
        return {
            'amazon': PriceScraper.scrape_search_price(product_name, 'amazon'),
            'flipkart': PriceScraper.scrape_search_price(product_name, 'flipkart')
        }

    @staticmethod
    def infer_product_name_from_url(url, source):
        """Infer product name from URL slug when scraper title is unavailable."""
        try:
            parsed = urlparse(url)
            segments = [s for s in parsed.path.split('/') if s]

            def prettify(segment):
                clean = unquote(segment or '')
                clean = re.sub(r'[^a-zA-Z0-9\-\+ ]', ' ', clean)
                clean = clean.replace('-', ' ').replace('+', ' ')
                clean = re.sub(r'\s+', ' ', clean).strip()
                if not clean:
                    return None
                return " ".join(word.capitalize() for word in clean.split())

            if source == 'amazon':
                if 'dp' in segments:
                    dp_index = segments.index('dp')
                    if dp_index > 0:
                        return prettify(segments[dp_index - 1])
                if 'gp' in segments and 'product' in segments:
                    gp_index = segments.index('gp')
                    if gp_index > 0:
                        return prettify(segments[gp_index - 1])

            if source == 'flipkart':
                if 'p' in segments:
                    p_index = segments.index('p')
                    if p_index > 0:
                        return prettify(segments[p_index - 1])

            if source == 'myntra':
                for segment in segments:
                    if segment.lower() != 'buy' and not segment.isdigit():
                        return prettify(segment)

            for segment in segments:
                if segment.lower() not in {'dp', 'gp', 'product', 'p', 'buy', 'd'} and not segment.isdigit():
                    name = prettify(segment)
                    if name:
                        return name
        except Exception:
            return None

        return None

# ==========================================
# SMART PRODUCT MATCHING
# ==========================================
class SmartMatcher:
    """Match ANY product to similar products in dataset."""
    
    @staticmethod
    def normalize_text(text):
        """Normalize product text for better matching."""
        if not text:
            return ""

        cleaned = str(text).lower()
        # Remove common storefront suffixes/noise from scraped titles
        noise_phrases = [
            'online at best price',
            'buy online',
            'price in india',
            'flipkart.com',
            'amazon.in',
            'amazon.com'
        ]
        for phrase in noise_phrases:
            cleaned = cleaned.replace(phrase, ' ')

        cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    @staticmethod
    def extract_keywords(product_name):
        """Extract important keywords from product name."""
        # Remove common and noisy words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'with', 'without', 'by', 'from', 'best', 'price', 'online',
            'storage', 'ram', 'gb', 'tb', 'inch', 'cm', 'mm', 'new',
            'amazon', 'flipkart', 'myntra', 'product', 'india', 'buy'
        }
        words = SmartMatcher.normalize_text(product_name).split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords

    @staticmethod
    def is_generic_product_name(product_name):
        """Detect placeholder names that should not drive model matching."""
        normalized = SmartMatcher.normalize_text(product_name)
        return normalized in {
            'amazon product',
            'flipkart product',
            'myntra product',
            'product'
        }
    
    @staticmethod
    def find_similar_products(product_name, df, top_n=10, min_score=2.0):
        """Find similar products using weighted keyword overlap."""
        keywords = set(SmartMatcher.extract_keywords(product_name))
        
        if not keywords:
            return []
        
        query_norm = SmartMatcher.normalize_text(product_name)
        products = df['product_name'].unique()
        scores = []
        
        for product in products:
            product_norm = SmartMatcher.normalize_text(product)
            product_tokens = set(SmartMatcher.extract_keywords(product_norm))
            if not product_tokens:
                continue

            overlap = keywords.intersection(product_tokens)
            if not overlap:
                continue

            union = keywords.union(product_tokens)
            jaccard = len(overlap) / len(union) if union else 0

            # Brand/model bonus for substring containment
            direct_bonus = 1.0 if any(tok in product_norm for tok in list(keywords)[:2]) else 0.0
            phrase_bonus = 1.0 if product_norm in query_norm or query_norm in product_norm else 0.0

            score = (len(overlap) * 1.5) + (jaccard * 5.0) + direct_bonus + phrase_bonus
            if score >= min_score:
                scores.append((product, score))
        
        # Sort by score
        similar = sorted(scores, key=lambda x: x[1], reverse=True)
        return [p[0] for p in similar[:top_n]]
    
    @staticmethod
    def get_category_from_name(product_name):
        """Determine category from product name."""
        product_lower = product_name.lower()
        
        categories = {
            'electronics': ['phone', 'laptop', 'tablet', 'watch', 'earphone', 'headphone', 
                          'camera', 'tv', 'monitor', 'keyboard', 'mouse', 'speaker'],
            'fashion': ['shirt', 'jeans', 'shoe', 'dress', 'jacket', 'trouser', 'bag',
                       'sunglasses', 'watch', 'belt', 'hat'],
            'home': ['furniture', 'bed', 'sofa', 'chair', 'table', 'lamp', 'curtain',
                    'vacuum', 'mixer', 'blender', 'kettle'],
            'books': ['book', 'novel', 'diary', 'notebook', 'pen', 'pencil'],
            'sports': ['gym', 'fitness', 'yoga', 'dumbbell', 'treadmill', 'cycle']
        }
        
        for category, keywords in categories.items():
            if any(kw in product_lower for kw in keywords):
                return category
        
        return 'general'

# ==========================================
# DATA PREPROCESSING (from previous code)
# ==========================================
def load_and_preprocess_data(filepath):
    """Load and clean the dataset."""
    try:
        df = pd.read_csv(filepath)
        df = df[['Description', 'InvoiceDate', 'UnitPrice']].copy()
        df.columns = ['product_name', 'date', 'price']
        df = df.dropna()
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['price'] > 0]
        df = df.sort_values('date')
        
        first_date = df['date'].min()
        df['days_since_start'] = (df['date'] - first_date).dt.days
        
        return df, first_date
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def aggregate_by_product_and_date(df):
    """Aggregate data by product and date."""
    df_agg = df.groupby(['product_name', 'date', 'days_since_start']).agg({
        'price': 'mean'
    }).reset_index()
    return df_agg

def train_price_model(df, product_name):
    """Train Linear Regression model for a product."""
    product_data = df[df['product_name'] == product_name].copy()
    
    if len(product_data) < 5:
        raise ValueError(f"Not enough data for {product_name}")
    
    X = product_data[['days_since_start']].values
    y = product_data['price'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    return {
        'model': model,
        'data': product_data,
        'r2': model.score(X, y),
        'slope': model.coef_[0]
    }

def predict_future_prices(model, current_day, future_days=[7, 15, 30, 60, 90, 120, 150, 180, 210]):
    """Predict prices for future dates."""
    predictions = {}
    for days_ahead in future_days:
        future_day = current_day + days_ahead
        predicted_price = model.predict([[future_day]])[0]
        predictions[f'{days_ahead}_days'] = float(max(0, predicted_price))  # Ensure positive
    return predictions

def make_buying_decision(current_price, predictions, threshold=0.05):
    """Decide BUY NOW or WAIT."""
    should_wait = False
    best_time = None
    max_savings = 0
    
    for period, predicted_price in predictions.items():
        days_ahead = int(period.split('_')[0])
        price_diff = current_price - predicted_price
        
        if price_diff > max_savings:
            max_savings = price_diff
            best_time = days_ahead
        
        if (price_diff / current_price) > threshold:
            should_wait = True
    
    return {
        'action': 'WAIT' if should_wait and max_savings > 0 else 'BUY_NOW',
        'savings': float(max(0, max_savings)),
        'best_time_days': best_time if should_wait else None
    }

# ==========================================
# ENHANCED API ENDPOINTS
# ==========================================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'models_loaded': len(MODELS_CACHE),
        'data_loaded': DF_CLEAN is not None,
        'scraping_enabled': True
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_product():
    """
    Enhanced endpoint - works with ANY product link.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        product_name = data.get('productName')
        source = data.get('source', 'unknown')
        url = data.get('url', '')
        
        if not product_name:
            return jsonify({'error': 'Product name is required'}), 400
        
        # Check if data is loaded
        if DF_CLEAN is None:
            return jsonify({'error': 'Dataset not loaded. Please initialize the system.'}), 500
        
        print(f"\n{'='*60}")
        print(f"Analyzing: {product_name}")
        print(f"Source: {source}")
        print(f"{'='*60}")
        
        # STEP 1: Try to scrape current price from URL
        scraped_price = None
        scraped_title = None
        scraped_image_url = None
        marketplace_prices = {'amazon': None, 'flipkart': None}
        if url and source in ['amazon', 'flipkart', 'myntra']:
            details = PriceScraper.scrape_details(url, source)
            scraped_price = details.get('price')
            scraped_title = details.get('title')
            scraped_image_url = details.get('image_url')
            if source in ['amazon', 'flipkart'] and scraped_price:
                marketplace_prices[source] = scraped_price

        # Prefer scraped title for frontend display
        if scraped_title:
            product_name = scraped_title
        elif url and source in ['amazon', 'flipkart', 'myntra'] and SmartMatcher.is_generic_product_name(product_name):
            inferred_name = PriceScraper.infer_product_name_from_url(url, source)
            if inferred_name:
                print(f"Inferred product name from URL: {inferred_name}")
                product_name = inferred_name

        # If input is a product name, fetch both marketplace prices
        if source == 'query':
            searched_prices = PriceScraper.get_marketplace_prices(product_name)
            marketplace_prices['amazon'] = searched_prices.get('amazon')
            marketplace_prices['flipkart'] = searched_prices.get('flipkart')
        elif source in ['amazon', 'flipkart']:
            other_source = 'flipkart' if source == 'amazon' else 'amazon'
            if marketplace_prices.get(other_source) is None:
                marketplace_prices[other_source] = PriceScraper.scrape_search_price(product_name, other_source)

        observed_market_prices = [
            p for p in marketplace_prices.values()
            if isinstance(p, (int, float)) and p > 0
        ]
        target_price_for_fallback = (
            float(scraped_price)
            if isinstance(scraped_price, (int, float)) and scraped_price > 0
            else (float(np.mean(observed_market_prices)) if observed_market_prices else None)
        )
        
        # STEP 2: Find similar products in dataset
        similar_products = SmartMatcher.find_similar_products(product_name, DF_CLEAN, top_n=5)
        
        if similar_products:
            print(f"Found {len(similar_products)} similar products")
            # Use the best match
            matched_product = similar_products[0]
            model_info = get_or_train_model(matched_product)
            model_source = 'similar_product'
        else:
            # STEP 3: Fallback to nearest-price product, then category-based prediction
            nearest_product = get_nearest_product_by_price(target_price_for_fallback)
            if nearest_product:
                print(f"No text match. Using nearest-price product model: {nearest_product}")
                matched_product = nearest_product
                model_info = get_or_train_model(matched_product)
                model_source = 'price_nearest_product'
            else:
                print("No similar products found, using category average")
                category = SmartMatcher.get_category_from_name(product_name)
                model_info = get_or_train_category_model(category, target_price=scraped_price)
                if scraped_price:
                    matched_product = f"{category.title()} Category (price-bucketed)"
                    model_source = 'category_price_bucket'
                else:
                    matched_product = f"{category.title()} Category"
                    model_source = 'category'
        
        product_data = model_info['data']
        model = model_info['model']
        
        # STEP 4: Determine current price
        available_market_prices = observed_market_prices

        if scraped_price:
            current_price = scraped_price
            print(f"Using scraped price: {current_price}")
        elif available_market_prices:
            current_price = float(np.mean(available_market_prices))
            print(f"Using marketplace average price: {current_price}")
        else:
            # Use average from similar products
            current_price = float(product_data['price'].mean())
            print(f"Using estimated price: {current_price}")

        # STEP 5: Get current day (use latest from dataset)
        current_day = int(product_data.iloc[-1]['days_since_start'])
        
        # STEP 6: Predict future prices
        predictions = predict_future_prices(
            model,
            current_day,
            future_days=[7, 15, 30, 60, 90, 120, 150, 180, 210]
        )
        
        # STEP 7: Adjust predictions based on actual current price
        # Scale predictions relative to current price
        if scraped_price:
            avg_historical_price = float(product_data['price'].mean())
            scale_factor = current_price / avg_historical_price
            predictions = {k: v * scale_factor for k, v in predictions.items()}
        
        # STEP 8: Make buying decision
        recommendation = make_buying_decision(current_price, predictions)
        recommendation['confidence'] = float(model_info.get('r2', 0.70))
        
        # STEP 9: Calculate statistics
        prices = product_data['price'].values
        statistics = {
            'avg_price': float(np.mean(prices)),
            'min_price': float(np.min(prices)),
            'max_price': float(np.max(prices)),
            'volatility': calculate_volatility(prices),
            'r2_score': float(model_info.get('r2', 0.70)),
            'trend': 'decreasing' if model_info.get('slope', 0) < 0 else 'increasing'
        }
        
        # STEP 10: Generate product image URL
        image_url = scraped_image_url or generate_product_image_url(product_name, source)
        
        print("\nAnalysis complete")
        print(f"  Current Price: {current_price}")
        print(f"  Recommendation: {recommendation['action']}")
        print(f"  Model Source: {model_source}")
        
        # Return response
        return jsonify({
            'success': True,
            'product': {
                'name': product_name,
                'matched_product': matched_product,
                'current_price': current_price,
                'source': source,
                'category': SmartMatcher.get_category_from_name(product_name),
                'image_url': image_url,
                'model_source': model_source,
                'price_scraped': scraped_price is not None,
                'marketplace_prices': marketplace_prices,
                'similar_products': similar_products[:3] if similar_products else []
            },
            'predictions': predictions,
            'recommendation': recommendation,
            'statistics': statistics
        })
        
    except Exception as e:
        print(f"Error in analyze_product: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_available_products():
    """Get list of available products."""
    try:
        if DF_CLEAN is None:
            return jsonify({'error': 'Dataset not loaded'}), 500
        
        product_counts = DF_CLEAN['product_name'].value_counts()
        products = [
            {
                'name': name,
                'data_points': int(count)
            }
            for name, count in product_counts.head(50).items()
        ]
        
        return jsonify({
            'total_products': len(product_counts),
            'products': products
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/initialize', methods=['POST'])
def initialize_system():
    """Initialize the system with dataset."""
    global DF_CLEAN, FIRST_DATE, MODELS_CACHE, CATEGORY_MODELS_CACHE
    
    try:
        data = request.get_json()
        filepath = data.get('filepath', 'data.csv')
        
        print(f"Loading data from {filepath}...")
        df, first_date = load_and_preprocess_data(filepath)
        DF_CLEAN = aggregate_by_product_and_date(df)
        FIRST_DATE = first_date
        
        MODELS_CACHE = {}
        CATEGORY_MODELS_CACHE = {}
        
        return jsonify({
            'success': True,
            'message': 'System initialized successfully',
            'records': len(DF_CLEAN),
            'unique_products': int(DF_CLEAN['product_name'].nunique())
        })
        
    except Exception as e:
        print(f"Error initializing system: {e}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_or_train_model(product_name):
    """Get cached model or train new one."""
    if product_name in MODELS_CACHE:
        return MODELS_CACHE[product_name]
    
    model_info = train_price_model(DF_CLEAN, product_name)
    MODELS_CACHE[product_name] = model_info
    return model_info

def get_or_train_category_model(category, target_price=None):
    """Get cached category model or train new one."""
    bucket_key = None
    if target_price and target_price > 0:
        bucket_key = int(target_price // 5000)  # 5k INR buckets
    cache_key = f"{category}:{bucket_key}" if bucket_key is not None else category

    if cache_key in CATEGORY_MODELS_CACHE:
        return CATEGORY_MODELS_CACHE[cache_key]
    
    # Train on category data
    df_category = DF_CLEAN.copy()
    df_category['category'] = df_category['product_name'].apply(
        lambda x: SmartMatcher.get_category_from_name(x)
    )
    
    category_data = df_category[df_category['category'] == category]

    # Narrow to similar price band if current price is known
    if target_price and target_price > 0 and len(category_data) > 0:
        means = category_data.groupby('product_name')['price'].mean().reset_index()
        lower = target_price * 0.6
        upper = target_price * 1.4
        matched_names = means[(means['price'] >= lower) & (means['price'] <= upper)]['product_name'].tolist()
        if len(matched_names) >= 2:
            category_data = category_data[category_data['product_name'].isin(matched_names)]
    
    if len(category_data) < 10:
        # Fallback to all data
        category_data = DF_CLEAN
    
    # Aggregate by date
    agg_data = category_data.groupby(['date', 'days_since_start']).agg({
        'price': 'mean'
    }).reset_index()
    
    X = agg_data[['days_since_start']].values
    y = agg_data['price'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    model_info = {
        'model': model,
        'data': agg_data,
        'r2': model.score(X, y),
        'slope': model.coef_[0]
    }
    
    CATEGORY_MODELS_CACHE[cache_key] = model_info
    return model_info

def get_nearest_product_by_price(target_price):
    """Find dataset product whose mean price is nearest to target price."""
    if target_price is None or target_price <= 0 or DF_CLEAN is None or len(DF_CLEAN) == 0:
        return None

    product_means = DF_CLEAN.groupby('product_name')['price'].mean()
    if len(product_means) == 0:
        return None

    nearest_name = (product_means - target_price).abs().idxmin()
    return nearest_name

def calculate_volatility(prices):
    """Calculate price volatility."""
    if len(prices) < 2:
        return 'Unknown'
    
    std = np.std(prices)
    mean = np.mean(prices)
    cv = (std / mean) * 100 if mean > 0 else 0
    
    if cv < 10:
        return 'Low'
    elif cv < 25:
        return 'Medium'
    else:
        return 'High'

def generate_product_image_url(product_name, source):
    """Generate a local SVG placeholder image as data URI."""
    label = (product_name or "Product")[:22]
    source_label = (source or "store").upper()
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>
      <defs>
        <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0%' stop-color='#1e293b'/>
          <stop offset='100%' stop-color='#0f172a'/>
        </linearGradient>
      </defs>
      <rect width='100%' height='100%' fill='url(#bg)'/>
      <rect x='18' y='18' width='264' height='264' rx='16' fill='none' stroke='#334155' stroke-width='2'/>
      <text x='50%' y='47%' text-anchor='middle' fill='#94a3b8' font-size='20' font-family='Arial, sans-serif'>No Image</text>
      <text x='50%' y='57%' text-anchor='middle' fill='#6366f1' font-size='14' font-family='Arial, sans-serif'>{label}</text>
      <text x='50%' y='66%' text-anchor='middle' fill='#64748b' font-size='12' font-family='Arial, sans-serif'>{source_label}</text>
    </svg>
    """.strip()
    return "data:image/svg+xml;utf8," + quote(svg)

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    import os
    
    # Auto-initialize if data file exists
    if os.path.exists('data.csv'):
        print("Auto-initializing with data.csv...")
        try:
            df, first_date = load_and_preprocess_data('data.csv')
            DF_CLEAN = aggregate_by_product_and_date(df)
            FIRST_DATE = first_date
            print(f"Loaded {len(DF_CLEAN)} records")
            print(f"{DF_CLEAN['product_name'].nunique()} unique products")
        except Exception as e:
            print(f"Error loading data: {e}")
    else:
        print("No data.csv found. Please run generate_sample_data.py first")
    
    print("\n🚀 Enhanced Price Predictor API Server")
    print("=" * 60)
    print("Web scraping enabled for Amazon/Flipkart/Myntra")
    print("Smart product matching for any product")
    print("Category fallback predictions enabled")
    print("=" * 60)
    print("📍 API: http://localhost:5000")
    
    app.run(debug=False, host='0.0.0.0', port=5000)


