import sqlite3
import os
from datetime import datetime

DATABASE = 'database/skinnova.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create all database tables"""
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User profiles table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            skin_type TEXT,
            skin_concerns TEXT,
            preferences TEXT,
            skin_undertone TEXT,
            makeup_preferences TEXT,
            color_season TEXT,
            color_palette TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Products table (skincare/demo)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            description TEXT,
            price DECIMAL(10,2),
            rating DECIMAL(3,2),
            suitable_skin_types TEXT,
            target_concerns TEXT,
            suitable_undertones TEXT,
            ingredients TEXT,
            image_url TEXT,
            amazon_url TEXT,
            nykaa_url TEXT,
            sephora_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Makeup catalog table (from CSV)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS makeup_catalog (
            sku TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            variant TEXT,
            price INTEGER,
            currency TEXT,
            image_path TEXT,
            image_url TEXT,
            retailer_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Dermatologists table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS dermatologists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            rating DECIMAL(3,2),
            specialization TEXT,
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User quiz results table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_type TEXT NOT NULL,
            answers TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Product reviews table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Site settings key-value store
    conn.execute('''
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Blog posts
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE,
            content TEXT,
            cover_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def ensure_dirs():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    os.makedirs('static/images/makeup', exist_ok=True)
    os.makedirs('static/images/skincare_manual', exist_ok=True)


def populate_makeup_catalog_from_csv(csv_path='data/makeup_catalog.csv'):
    import csv
    ensure_dirs()
    conn = get_db_connection()
    # Create placeholders map
    placeholders = {}
    for cat in ['lipstick','foundation','eyeshadow','blush','mascara','default']:
        rel = f"images/placeholders/{cat}.svg"
        if os.path.exists(os.path.join('static', rel)):
            placeholders[cat] = rel


def enrich_images_from_nykaa(limit=50):
    """Try to set image_url from Nykaa retailer_url by reading og:image. Returns count updated."""
    import requests, re
    from html import unescape
    conn = get_db_connection()
    rows = conn.execute("SELECT sku, retailer_url, image_url FROM makeup_catalog WHERE retailer_url IS NOT NULL AND retailer_url != '' AND (image_url IS NULL OR image_url = '' OR image_url LIKE 'http%images.sample%') LIMIT ?", (limit,)).fetchall()
    updated = 0
    for r in rows:
        try:
            resp = requests.get(r['retailer_url'], timeout=15, headers={'User-Agent':'Mozilla/5.0'})
            html = resp.text
            # Find og:image
            m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if not m:
                m = re.search(r'"image"\s*:\s*\{\s*"url"\s*:\s*"([^"]+)"', html)
            if m:
                url = unescape(m.group(1))
                conn.execute('UPDATE makeup_catalog SET image_url = ? WHERE sku = ?', (url, r['sku']))
                updated += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return updated
    
    # Insert/update rows from CSV (prefer remote image_url; do NOT download)
    if os.path.exists(csv_path):
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                sku = r['sku'].strip()
                category = r.get('category','').strip().lower()
                image_url = (r.get('image_url') or '').strip()
                # only attach placeholder path if there is no remote image_url
                local_path = None if image_url else (placeholders.get(category) or placeholders.get('default'))
                conn.execute('''
                    INSERT OR REPLACE INTO makeup_catalog
                    (sku, category, brand, name, variant, price, currency, image_path, image_url, retailer_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sku, r['category'], r['brand'], r['name'], r.get('variant'), int(r['price'] or 0),
                    r.get('currency','INR'), local_path, image_url, r.get('retailer_url')
                ))
        conn.commit()
    
    # Ensure all existing rows have an image fallback
    rows = conn.execute('SELECT sku, category, image_path, image_url FROM makeup_catalog').fetchall()
    for row in rows:
        if not row['image_path'] and not row['image_url']:
            cat = (row['category'] or '').lower()
            ph = placeholders.get(cat) or placeholders.get('default')
            if ph:
                conn.execute('UPDATE makeup_catalog SET image_path = ? WHERE sku = ?', (ph, row['sku']))
    conn.commit()
    conn.close()


def populate_sample_data():
    """Populate database with sample data (skincare/demo) and makeup catalog"""
    ensure_dirs()
    conn = get_db_connection()

    # Insert demo skincare/makeup only if products table empty
    existing_products = conn.execute('SELECT COUNT(*) as count FROM products').fetchone()
    if existing_products['count'] == 0:
        # Sample skincare products
        skincare_products = [
            ('CeraVe Foaming Facial Cleanser', 'CeraVe', 'skincare', 'cleanser', 
             'Gentle foaming cleanser for normal to oily skin', 12.99, 4.5, 
             'oily,combination,normal', 'acne,excess-oil', '', 
             'Ceramides, Hyaluronic Acid, Niacinamide', 
             '/static/images/cerave-cleanser.jpg', 'https://amazon.com/cerave-cleanser', 
             'https://nykaa.com/cerave-cleanser', 'https://sephora.com/cerave-cleanser'),
            
            ('The Ordinary Niacinamide 10% + Zinc 1%', 'The Ordinary', 'skincare', 'serum',
             'High-strength vitamin and mineral blemish formula', 7.00, 4.2,
             'oily,combination,acne-prone', 'acne,enlarged-pores,oil-control', '',
             'Niacinamide, Zinc PCA', '/static/images/ordinary-niacinamide.jpg',
             'https://amazon.com/ordinary-niacinamide', 'https://nykaa.com/ordinary-niacinamide',
             'https://sephora.com/ordinary-niacinamide'),
            
            ('Neutrogena Hydro Boost Water Gel', 'Neutrogena', 'skincare', 'moisturizer',
             'Oil-free gel moisturizer with hyaluronic acid', 18.99, 4.3,
             'all', 'dryness,dehydration', '',
             'Hyaluronic Acid, Glycerin', '/static/images/neutrogena-hydro.jpg',
             'https://amazon.com/neutrogena-hydro', 'https://nykaa.com/neutrogena-hydro',
             'https://sephora.com/neutrogena-hydro'),
            
            ('La Roche-Posay Toleriane Double Repair Face Moisturizer', 'La Roche-Posay', 'skincare', 'moisturizer',
             'Daily face moisturizer with ceramides and niacinamide', 19.99, 4.6,
             'sensitive,dry,normal', 'sensitivity,dryness,irritation', '',
             'Ceramides, Niacinamide, Thermal Spring Water', '/static/images/lrp-toleriane.jpg',
             'https://amazon.com/lrp-toleriane', 'https://nykaa.com/lrp-toleriane',
             'https://sephora.com/lrp-toleriane'),
            
            ('Vitamin C Brightening Serum', 'SkinCeuticals', 'skincare', 'serum',
             'Antioxidant serum to brighten and protect skin', 166.00, 4.7,
             'all', 'dullness,pigmentation,aging', '',
             'L-Ascorbic Acid, Vitamin E, Ferulic Acid', '/static/images/skinceuticals-vitc.jpg',
             'https://amazon.com/skinceuticals-vitc', 'https://nykaa.com/skinceuticals-vitc',
             'https://sephora.com/skinceuticals-vitc')
        ]
        
        # Sample makeup products (legacy demo)
        makeup_products = [
            ('Fenty Beauty Pro Filt\'r Foundation', 'Fenty Beauty', 'makeup', 'foundation',
             'Soft matte longwear foundation', 36.00, 4.4,
             '', '', 'warm,cool,neutral',
             'Long-wearing, Oil-absorbing', '/static/images/fenty-foundation.jpg',
             'https://amazon.com/fenty-foundation', 'https://nykaa.com/fenty-foundation',
             'https://sephora.com/fenty-foundation'),
            
            ('MAC Ruby Woo Lipstick', 'MAC', 'makeup', 'lipstick',
             'Iconic red matte lipstick', 19.00, 4.3,
             '', '', 'cool,neutral',
             'Matte finish, Long-wearing', '/static/images/mac-ruby-woo.jpg',
             'https://amazon.com/mac-ruby-woo', 'https://nykaa.com/mac-ruby-woo',
             'https://sephora.com/mac-ruby-woo')
        ]
        
        for product in skincare_products:
            conn.execute('''
                INSERT INTO products (name, brand, category, subcategory, description, price, rating, 
                                    suitable_skin_types, target_concerns, suitable_undertones, ingredients, 
                                    image_url, amazon_url, nykaa_url, sephora_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)
        for product in makeup_products:
            conn.execute('''
                INSERT INTO products (name, brand, category, subcategory, description, price, rating, 
                                    suitable_skin_types, target_concerns, suitable_undertones, ingredients, 
                                    image_url, amazon_url, nykaa_url, sephora_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)
        conn.commit()
    conn.close()

    # Populate makeup catalog from CSV
    populate_makeup_catalog_from_csv()

    # Populate dermatologists if empty
    conn = get_db_connection()
    existing_derms = conn.execute('SELECT COUNT(*) as c FROM dermatologists').fetchone()
    if existing_derms['c'] == 0:
        dermatologists = [
            ('Dr. Sarah Johnson', '123 Medical Center Dr, Downtown', '+1-555-0123', 'sarah.johnson@medcenter.com', 4.8, 'Acne Treatment, Anti-Aging', 40.7128, -74.0060),
            ('Dr. Michael Brown', '456 Health Plaza, Midtown', '+1-555-0124', 'michael.brown@healthplaza.com', 4.6, 'Skin Cancer, Dermatitis', 40.7580, -73.9855),
            ('Dr. Emily Davis', '789 Wellness Ave, Uptown', '+1-555-0125', 'emily.davis@wellness.com', 4.9, 'Cosmetic Dermatology, Rosacea', 40.7831, -73.9712),
            ('Dr. James Wilson', '321 Care Street, Brooklyn', '+1-555-0126', 'james.wilson@carestreet.com', 4.7, 'Pediatric Dermatology, Eczema', 40.6782, -73.9442),
            ('Dr. Lisa Anderson', '654 Beauty Blvd, Queens', '+1-555-0127', 'lisa.anderson@beautyblvd.com', 4.5, 'Laser Treatments, Pigmentation', 40.7282, -73.7949)
        ]
        for derm in dermatologists:
            conn.execute('''
                INSERT INTO dermatologists (name, address, phone, email, rating, specialization, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', derm)
        conn.commit()
    conn.close()
    create_tables()
    populate_sample_data()
    print("Database initialized successfully!")


def replace_skincare_from_json(json_path: str) -> int:
    """Replace all skincare records using a provided JSON dataset.

    The JSON format is expected to be:
    {
      "currency": "INR",
      "items": [
        {
          "product_id": "...",
          "skin_type": "oily|dry|sensitive|combination",
          "category": "facewash|toner|moisturizer|serum",
          "brand": "...",
          "product_name": "...",
          "volume": "...",
          "image_url": "http...",
          "links": { "amazon": {"url":"","price":null}, "nykaa": {..}, "flipkart": {..} }
        }, ...
      ]
    }

    Returns number of rows inserted.
    """
    import json
    ensure_dirs()
    conn = get_db_connection()
    create_tables()
    try:
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        conn.close()
        raise

    # Support two formats:
    # 1) Flat { items: [...] }
    # 2) Nested { skin_types: { oily: { facewash:[...], ... }, dry: { ... } } }
    items = data.get('items', [])

    # If nested schema detected, flatten into items
    if not items and isinstance(data.get('skin_types'), dict):
        flattened = []
        skin_types_map = data['skin_types']
        for skin_type_key, categories in skin_types_map.items():
            for subcat_key, products in (categories or {}).items():
                if not isinstance(products, list):
                    continue
                for p in products:
                    links = p.get('links') or {}
                    flattened.append({
                        'product_name': p.get('product_name') or p.get('name'),
                        'brand': p.get('brand'),
                        'category': subcat_key,  # expected by downstream as subcategory
                        'volume': p.get('volume'),
                        'image_url': p.get('image') or p.get('image_url'),
                        'links': {
                            'amazon': {'url': (links.get('amazon') or {}).get('url'), 'price': (links.get('amazon') or {}).get('price')},
                            'nykaa': {'url': (links.get('nykaa') or {}).get('url'), 'price': (links.get('nykaa') or {}).get('price')},
                            'flipkart': {'url': (links.get('flipkart') or {}).get('url'), 'price': (links.get('flipkart') or {}).get('price')},
                        },
                        'skin_type': skin_type_key
                    })
        items = flattened

    # Remove existing skincare rows (both legacy 'skincare' and direct subcategory entries if any)
    conn.execute("DELETE FROM products WHERE category = 'skincare' OR subcategory IN ('facewash','toner','moisturizer','serum')")

    rows_inserted = 0
    for it in items:
        name = it.get('product_name') or it.get('name') or ''
        brand = it.get('brand') or ''
        subcategory = (it.get('category') or '').lower()
        image_url = it.get('image_url') or ''
        links = it.get('links') or {}
        amazon = (links.get('amazon') or {}).get('url') or ''
        nykaa = (links.get('nykaa') or {}).get('url') or ''
        flipkart = (links.get('flipkart') or {}).get('url') or ''
        skin_type = (it.get('skin_type') or '').lower()

        conn.execute('''
            INSERT INTO products (
                name, brand, category, subcategory, description, price, rating,
                suitable_skin_types, target_concerns, suitable_undertones, ingredients,
                image_url, amazon_url, nykaa_url, sephora_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, brand, 'skincare', subcategory, None, None, None,
            skin_type, '', '', None,
            image_url, amazon, nykaa, flipkart
        ))
        rows_inserted += 1

    conn.commit()
    conn.close()
    return rows_inserted

def purge_all_skincare_products() -> int:
    """Delete all skincare products from products table. Returns rows deleted."""
    conn = get_db_connection()
    cur = conn.execute("SELECT COUNT(*) as c FROM products WHERE category='skincare' OR subcategory IN ('facewash','toner','moisturizer','serum')").fetchone()
    to_delete = cur['c'] if cur else 0
    conn.execute("DELETE FROM products WHERE category='skincare' OR subcategory IN ('facewash','toner','moisturizer','serum')")
    conn.commit(); conn.close()
    return int(to_delete)