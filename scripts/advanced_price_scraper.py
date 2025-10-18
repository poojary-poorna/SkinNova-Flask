import os
import re
import csv
import time
import json
import random
import logging
import sqlite3
import pathlib
from urllib.parse import quote_plus, urljoin, urlparse
from flask import Flask, jsonify, request, send_file

import requests
from bs4 import BeautifulSoup
import pandas as pd

# Optional: playwright for JS rendered pages
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False

# ----------------- Configuration -----------------
BASE_DIR = pathlib.Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "skincare.db"
PRODUCTS_CSV = BASE_DIR / "products.csv"
OUT_CSV = BASE_DIR / "price_comparison.csv"
IMAGES_DIR = BASE_DIR / "images"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}

SITES = {
    "nykaa": "https://www.nykaa.com/search/result?q={}",
    "amazon": "https://www.amazon.in/s?k={}",
    "flipkart": "https://www.flipkart.com/search?q={}"
}

# Rate limiting
MIN_DELAY = 1.8
MAX_DELAY = 3.5

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Ensure images dir exists
os.makedirs(IMAGES_DIR, exist_ok=True)

app = Flask(__name__)

# ----------------- DB helpers -----------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            brand TEXT,
            name TEXT,
            site TEXT,
            product_title TEXT,
            price INTEGER,
            currency TEXT,
            image_url TEXT,
            product_url TEXT,
            scraped_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_record(rec):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (category,brand,name,site,product_title,price,currency,image_url,product_url,scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        rec.get('category'), rec.get('brand'), rec.get('name'), rec.get('site'), rec.get('product_title'),
        rec.get('price'), rec.get('currency'), rec.get('image_url'), rec.get('product_url')
    ))
    conn.commit()
    conn.close()


# ----------------- util helpers -----------------

def slugify_filename(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    return s.strip("_")[:180]


def clean_price(p):
    if not p:
        return None
    # Remove non-digit except dot
    digits = re.sub(r"[^0-9]", "", str(p))
    try:
        if digits == "":
            return None
        return int(digits)
    except Exception:
        return None


def download_image(url, filepath):
    try:
        if not url:
            return False
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return True
        return False
    except Exception as e:
        logger.warning(f"Image download failed for {url}: {e}")
        return False


# ----------------- scraping parsers -----------------

def parse_nykaa_search(soup):
    # Nykaa uses varying classes; try multiple fallbacks
    # Return tuple of (product_url, image_url, title, price_text)
    selectors = [
        ("div.MerchantDesktop-productCard", "a", "img", ".post-card__content-price .price"),
        ("div.product-card", "a", "img", ".price"),
        ("div[data-testid='product-card']", "a", "img", ".price")
    ]
    for sel, a_sel, img_sel, price_sel in selectors:
        card = soup.select_one(sel)
        if card:
            try:
                link = card.select_one(a_sel)
                href = link.get('href') if link else None
                if href and href.startswith("/"):
                    product_url = urljoin("https://www.nykaa.com", href)
                else:
                    product_url = href
                img = card.select_one(img_sel)
                img_url = img.get('src') or img.get('data-src') if img else None
                price_tag = card.select_one(price_sel)
                price_text = price_tag.get_text(strip=True) if price_tag else None
                title = card.get_text(separator=" ", strip=True)[:220]
                return product_url, img_url, title, price_text
            except Exception:
                continue
    return None, None, None, None


def parse_amazon_search(soup):
    try:
        card = soup.select_one("div.s-main-slot div[data-component-type='s-search-result']")
        if not card:
            return None, None, None, None
        link = card.select_one("a.a-link-normal.s-no-outline") or card.select_one("a.a-link-normal")
        href = link.get('href') if link else None
        product_url = urljoin("https://www.amazon.in", href) if href else None
        img = card.select_one("img.s-image")
        img_url = img.get('src') if img else None
        price_whole = card.select_one("span.a-price-whole")
        price_frac = card.select_one("span.a-price-fraction")
        if price_whole:
            price_text = price_whole.get_text(strip=True) + (price_frac.get_text(strip=True) if price_frac else "")
        else:
            price_text = None
        title = card.select_one("h2").get_text(strip=True) if card.select_one('h2') else None
        return product_url, img_url, title, price_text
    except Exception as e:
        logger.debug("Amazon parse error: %s", e)
        return None, None, None, None


def parse_flipkart_search(soup):
    try:
        # try common product link selectors in order
        link = soup.select_one("a._1fQZEK") or soup.select_one("a.s1Q9rs") or soup.select_one("a._2rpwqI")
        if not link:
            # try product card container
            card = soup.select_one("div._13oc-S")
            if card:
                link = card.select_one("a")
        href = link.get('href') if link else None
        product_url = urljoin("https://www.flipkart.com", href) if href else None
        img = soup.select_one("img._396cs4") or soup.select_one("img._2r_T1I")
        img_url = img.get('src') if img else None
        price_tag = soup.select_one("div._30jeq3")
        price_text = price_tag.get_text(strip=True) if price_tag else None
        title = link.get('title') if link and link.get('title') else (soup.select_one('a._1fQZEK') and soup.select_one('a._1fQZEK').get_text(strip=True))
        return product_url, img_url, title, price_text
    except Exception as e:
        logger.debug("Flipkart parse error: %s", e)
        return None, None, None, None


# High-level search and parse

def get_search_page(site, query, render_js=False):
    url = SITES.get(site).format(quote_plus(query))
    logger.info(f"Fetching {site} search for: {query}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        if r.status_code == 200:
            return BeautifulSoup(r.text, 'html.parser')
        # fallback to playwright if available and requested
        if render_js and PLAYWRIGHT_AVAILABLE:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=USER_AGENT)
                page.goto(url, timeout=30000)
                html = page.content()
                browser.close()
                return BeautifulSoup(html, 'html.parser')
    except Exception as e:
        logger.warning(f"Search page fetch failed for {site}: {e}")
    return None


def search_and_extract(site, brand, name):
    query = f"{brand} {name}"
    # Try non-render first
    soup = get_search_page(site, query, render_js=False)
    if not soup and PLAYWRIGHT_AVAILABLE:
        soup = get_search_page(site, query, render_js=True)
    if not soup:
        return None

    if site == 'nykaa':
        product_url, img_url, title, price_text = parse_nykaa_search(soup)
    elif site == 'amazon':
        product_url, img_url, title, price_text = parse_amazon_search(soup)
    elif site == 'flipkart':
        product_url, img_url, title, price_text = parse_flipkart_search(soup)
    else:
        return None

    price = clean_price(price_text)
    return {
        'site': site,
        'product_title': title,
        'price': price,
        'currency': 'INR' if price else None,
        'image_url': img_url,
        'product_url': product_url
    }


# ----------------- CSV / Product list helpers -----------------

def ensure_products_csv():
    if PRODUCTS_CSV.exists():
        logger.info('products.csv found')
        return
    logger.info('products.csv not found — creating sample file with skincare products')
    sample = [
        ("facewash","CeraVe","Foaming Facial Cleanser"),
        ("facewash","CeraVe","Hydrating Cleanser"),
        ("facewash","Cetaphil","Gentle Skin Cleanser"),
        ("facewash","Cetaphil","Oily Skin Cleanser"),
        ("facewash","Dot & Key","Hydrating Face Wash"),
        ("facewash","Dot & Key","Salicylic Acid Face Wash"),
        ("facewash","Himalaya","Purifying Neem Face Wash"),
        ("facewash","Himalaya","Gentle Daily Care Face Wash"),
        ("facewash","Neutrogena","Deep Clean Face Wash"),
        ("facewash","La Roche-Posay","Effaclar Purifying Foaming Gel"),
        ("facewash","Bioderma","Sebium Gel Moussant"),
        ("facewash","Garnier","Men Oil Clear Face Wash"),
        ("facewash","Plum","Green Tea Cleansing Face Wash"),
        ("facewash","Simple","Kind To Skin Moisturizing Face Wash"),
        ("facewash","The Body Shop","Tea Tree Skin Clearing Facial Wash"),
        ("serum","The Ordinary","Niacinamide 10% + Zinc 1%"),
        ("serum","Dot & Key","Vitamin C Serum"),
        ("serum","Cetaphil","Hydrating Serum"),
        ("serum","CeraVe","Hyaluronic Acid Serum"),
        ("serum","The Face Shop","Retinol Serum"),
        ("serum","Klairs","Freshly Juiced Vitamin Drop"),
        ("serum","Minimalist","10% Vitamin C Serum"),
        ("serum","L'Oreal","Revitalift Hyaluronic Acid Serum"),
        ("serum","Mamaearth","Vitamin C Serum"),
        ("serum","Estee Lauder","Advanced Night Repair"),
        ("sunscreen","Neutrogena","UltraSheer Dry-Touch SPF50+"),
        ("sunscreen","La Roche-Posay","Anthelios XL SPF50+"),
        ("sunscreen","Cetaphil","Daily Facial Moisturizer SPF 50+"),
        ("sunscreen","Bioderma","Photoderm Max SPF50+"),
        ("sunscreen","Lotus Herbals","Safe Sun UV Screen"),
        ("sunscreen","Minimalist","Sunscreen SPF50 PA+++"),
        ("sunscreen","Lakme","Sun Expert SPF50 PA+++"),
        ("sunscreen","mCaffeine","Naked & Raw SPF50"),
        ("sunscreen","Mamaearth","Ultra Light Indian SPF50"),
        ("sunscreen","Aveeno","Positively Radiant SPF50"),
        ("moisturizer","CeraVe","Moisturizing Cream"),
        ("moisturizer","Cetaphil","Moisturizing Lotion"),
        ("moisturizer","Neutrogena","Hydro Boost Water Gel"),
        ("moisturizer","Clinique","Moisture Surge"),
        ("moisturizer","Dot & Key","Hyaluronic Moisturizer"),
        ("moisturizer","Lakme","Enrich Moisturizer"),
        ("moisturizer","The Ordinary","NMF + HA"),
        ("moisturizer","Nivea","Nivea Soft Light Moisturizer"),
        ("moisturizer","Kiehl's","Ultra Facial Cream"),
        ("moisturizer","Plum","Hello Aloe Gentle Daily Moisturizer"),
        ("toner","Dot & Key","Pore Minimizing Toner"),
        ("toner","Pixi","Glow Tonic"),
        ("toner","Thayers","Witch Hazel Toner (Rose)"),
        ("toner","The Ordinary","Glycolic Acid 7% Toning Solution"),
        ("toner","Cetaphil","Gentle Skin Toner"),
        ("toner","Kiehl's","Calendula Herbal Extract Toner"),
        ("toner","Neutrogena","Alcohol-Free Toner"),
        ("toner","Plum","Green Tea Alcohol-Free Toner"),
        ("toner","Mamaearth","Hydrating Toner"),
        ("toner","Simple","Soothing Facial Toner")
    ]
    with open(PRODUCTS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'brand', 'name'])
        for row in sample:
            writer.writerow(row)
    logger.info('Sample products.csv created with %d rows', len(sample))


# ----------------- Main update routine -----------------

def run_full_update(save_csv=True, download_images=True, limit=None):
    ensure_products_csv()
    init_db()
    df = pd.read_csv(PRODUCTS_CSV)

    out_rows = []
    total = len(df) if limit is None else min(len(df), limit)
    logger.info('Starting full update for %d products', total)

    for idx, row in df.head(total).iterrows():
        category = row['category']
        brand = row['brand']
        name = row['name']

        for site in ['nykaa', 'amazon', 'flipkart']:
            try:
                data = search_and_extract(site, brand, name)
                # polite delay
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                if data:
                    rec = {
                        'category': category,
                        'brand': brand,
                        'name': name,
                        'site': site,
                        'product_title': data.get('product_title'),
                        'price': data.get('price'),
                        'currency': data.get('currency'),
                        'image_url': data.get('image_url'),
                        'product_url': data.get('product_url')
                    }
                    insert_record(rec)
                    out_rows.append(rec)

                    # download image
                    if download_images and data.get('image_url'):
                        ext = os.path.splitext(urlparse(data.get('image_url')).path)[1] or '.jpg'
                        fname = f"{slugify_filename(category)}{slugify_filename(brand)}{slugify_filename(name)}{site}{ext}"
                        filepath = IMAGES_DIR / fname
                        if not filepath.exists():
                            ok = download_image(data.get('image_url'), filepath)
                            logger.info('Image download %s -> %s', data.get('image_url'), 'OK' if ok else 'FAILED')
                else:
                    out_rows.append({
                        'category': category, 'brand': brand, 'name': name, 'site': site,
                        'product_title': None, 'price': None, 'currency': None, 'image_url': None, 'product_url': None
                    })
            except Exception as e:
                logger.exception('Error scraping %s %s %s', site, brand, name)

    out_df = pd.DataFrame(out_rows)
    if save_csv:
        out_df.to_csv(OUT_CSV, index=False)
        logger.info('Saved %s', OUT_CSV)
    return out_df


# ----------------- Flask routes -----------------

@app.route('/update-prices')
def route_update_prices():
    limit = request.args.get('limit', type=int)
    download_images = request.args.get('download_images', '1') != '0'
    out_df = run_full_update(download_images=download_images, limit=limit)
    return jsonify({'status': 'done', 'rows': len(out_df)})


@app.route('/products')
def route_products():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, category, brand, name, site, product_title, price, currency, image_url, product_url, scraped_at FROM products ORDER BY scraped_at DESC')
    rows = c.fetchall()
    conn.close()
    keys = ['id','category','brand','name','site','product_title','price','currency','image_url','product_url','scraped_at']
    return jsonify([dict(zip(keys, r)) for r in rows])


@app.route('/compare')
def route_compare():
    # supply ?name= (full or partial) and it returns rows grouped by site
    q = request.args.get('name')
    if not q:
        return jsonify({'error': 'supply name query parameter'}), 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, category, brand, name, site, product_title, price, currency, image_url, product_url, scraped_at FROM products WHERE name LIKE ? ORDER BY scraped_at DESC", (f"%{q}%",))
    rows = c.fetchall()
    conn.close()
    keys = ['id','category','brand','name','site','product_title','price','currency','image_url','product_url','scraped_at']
    return jsonify([dict(zip(keys, r)) for r in rows])


@app.route('/download-csv')
def route_download_csv():
    if not OUT_CSV.exists():
        return jsonify({'error': 'CSV not generated yet. Run /update-prices first.'}), 404
    return send_file(str(OUT_CSV), mimetype='text/csv', as_attachment=True, download_name='price_comparison.csv')


# ----------------- CLI -----------------

if __name__ == '__main__':
    init_db()
    ensure_products_csv()
    # create requirements.txt for user convenience
    reqs = [
        'flask', 'requests', 'beautifulsoup4', 'pandas'
    ]
    if PLAYWRIGHT_AVAILABLE:
        reqs.append('playwright')
    with open(BASE_DIR / 'requirements.txt', 'w') as f:
        f.write('\n'.join(reqs))

    print('Flask price scraper ready.')
    print('Open http://127.0.0.1:5000/update-prices to run the scraper (or run this file directly).')
    app.run(debug=True)




