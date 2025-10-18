import pandas as pd
import json
import random
import os
import subprocess
import logging
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedSkincareService:
    def __init__(self, products_csv="products.csv", db_path="skincare.db"):
        self.products_csv = products_csv
        self.db_path = db_path
        self.categories = ["Facewash", "Serum", "Sunscreen", "Moisturizer", "Toner"]
        self.skin_types = ["Dry", "Oily", "Normal", "Combination", "Sensitive"]
        self.concerns = ["Acne", "Aging", "Dark Spots", "Dehydration", "Redness", "Texture", "Dullness", "Pores"]
        
        # Initialize database
        self._init_db()
        
        # Load products data after attributes are defined
        self.products_df = self._load_products_data()
        
        logger.info(f"✅ Advanced Skincare Service initialized with {len(self.products_df)} products")

    def _init_db(self):
        """Initialize the SQLite database for price data"""
        conn = sqlite3.connect(self.db_path)
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

    def _load_products_data(self):
        """Load products from CSV and generate enhanced details"""
        try:
            if not os.path.exists(self.products_csv):
                logger.warning(f"Products CSV not found: {self.products_csv}")
                return pd.DataFrame()
            
            df = pd.read_csv(self.products_csv)
            logger.info(f"✅ Loaded {len(df)} products from {self.products_csv}")
            
            # Generate enhanced product details
            enhanced_products = []
            for idx, row in df.iterrows():
                product_id = idx + 1
                details = self._generate_product_details(row['name'], row['brand'], row['category'])
                
                enhanced_product = {
                    'id': product_id,
                    'category': row['category'].title(),
                    'brand': row['brand'],
                    'name': row['name'],
                    'description': details['description'],
                    'ingredients': details['ingredients'],
                    'skin_types': details['skin_types'],
                    'concerns': details['concerns'],
                    'rating': details['rating'],
                    'size': details['size'],
                    'availability': details['availability'],
                    'badges': details['badges'],
                    'image_url': details['image_url'],
                    'price_range': details['price_range']
                }
                enhanced_products.append(enhanced_product)
            
            return pd.DataFrame(enhanced_products)
            
        except Exception as e:
            logger.error(f"Error loading products data: {e}")
            return pd.DataFrame()

    def _generate_product_details(self, product_name, brand, category):
        """Generate realistic product details"""
        # Product descriptions based on category
        descriptions = {
            'facewash': [
                f"Gentle {product_name.lower()} that effectively removes dirt, oil, and makeup while maintaining your skin's natural moisture balance.",
                f"Deep cleansing {product_name.lower()} with natural ingredients that purify and refresh your skin without over-drying.",
                f"Daily {product_name.lower()} formulated to cleanse and prepare your skin for the rest of your skincare routine."
            ],
            'serum': [
                f"Concentrated {product_name.lower()} that delivers active ingredients deep into your skin for maximum effectiveness.",
                f"Lightweight {product_name.lower()} that absorbs quickly and provides targeted treatment for specific skin concerns.",
                f"Professional-grade {product_name.lower()} with high-potency ingredients for visible results."
            ],
            'sunscreen': [
                f"Broad-spectrum {product_name.lower()} that protects against UVA and UVB rays while being gentle on sensitive skin.",
                f"Lightweight {product_name.lower()} that provides superior sun protection without leaving a white cast.",
                f"Daily {product_name.lower()} that shields your skin from harmful UV radiation and environmental damage."
            ],
            'moisturizer': [
                f"Rich {product_name.lower()} that deeply hydrates and nourishes your skin for a healthy, radiant complexion.",
                f"Lightweight {product_name.lower()} that provides long-lasting moisture without feeling heavy or greasy.",
                f"Daily {product_name.lower()} that locks in moisture and helps maintain your skin's natural barrier."
            ],
            'toner': [
                f"Refreshing {product_name.lower()} that balances your skin's pH and prepares it for better product absorption.",
                f"Gentle {product_name.lower()} that removes residual impurities and tightens pores for smoother skin.",
                f"Daily {product_name.lower()} that refreshes and revitalizes your skin while maintaining its natural balance."
            ]
        }
        
        # Common ingredients by category
        ingredients_by_category = {
            'facewash': ['Glycerin', 'Salicylic Acid', 'Tea Tree Oil', 'Aloe Vera', 'Vitamin E'],
            'serum': ['Hyaluronic Acid', 'Vitamin C', 'Niacinamide', 'Retinol', 'Peptides'],
            'sunscreen': ['Zinc Oxide', 'Titanium Dioxide', 'Avobenzone', 'Octinoxate', 'Vitamin E'],
            'moisturizer': ['Hyaluronic Acid', 'Ceramides', 'Shea Butter', 'Jojoba Oil', 'Glycerin'],
            'toner': ['Witch Hazel', 'Rose Water', 'Glycolic Acid', 'Salicylic Acid', 'Aloe Vera']
        }
        
        # Generate random details
        description = random.choice(descriptions.get(category.lower(), descriptions['facewash']))
        ingredients = random.sample(ingredients_by_category.get(category.lower(), ingredients_by_category['facewash']), 
                                  random.randint(3, 5))
        skin_types = random.sample(self.skin_types, random.randint(2, 4))
        concerns = random.sample(self.concerns, random.randint(1, 3))
        rating = round(random.uniform(3.5, 4.8), 1)
        size = random.choice(['30ml', '50ml', '100ml', '150ml', '200ml'])
        availability = random.choice(['In Stock', 'Limited Stock', 'In Stock'])
        
        # Generate badges
        badges = []
        if random.random() > 0.7:
            badges.append('Best Seller')
        if random.random() > 0.8:
            badges.append('Cruelty Free')
        if random.random() > 0.6:
            badges.append('Dermatologist Recommended')
        
        # Generate price range based on category (in INR)
        price_ranges = {
            'facewash': (200, 800),
            'serum': (500, 2000),
            'sunscreen': (300, 1200),
            'moisturizer': (400, 1500),
            'toner': (250, 900)
        }
        min_price, max_price = price_ranges.get(category.lower(), (200, 1000))
        price_range = f"₹{min_price} - ₹{max_price}"
        
        # Generate image URL (placeholder for now)
        image_url = f"https://images.unsplash.com/photo-{random.randint(1500000000000, 1600000000000)}-{random.randint(100000, 999999)}?w=400&h=400&fit=crop&crop=center"
        
        return {
            'description': description,
            'ingredients': ingredients,
            'skin_types': skin_types,
            'concerns': concerns,
            'rating': rating,
            'size': size,
            'availability': availability,
            'badges': badges,
            'image_url': image_url,
            'price_range': price_range
        }

    def get_skincare_products(self, category=None, skin_type=None, concern=None, price_range=None):
        """Get filtered skincare products"""
        try:
            filtered_df = self.products_df.copy()
            
            if category:
                filtered_df = filtered_df[filtered_df['category'].str.contains(category, case=False, na=False)]
            
            if skin_type:
                filtered_df = filtered_df[filtered_df['skin_types'].apply(
                    lambda x: skin_type in x if isinstance(x, list) else False
                )]
            
            if concern:
                filtered_df = filtered_df[filtered_df['concerns'].apply(
                    lambda x: concern in x if isinstance(x, list) else False
                )]
            
            return filtered_df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting skincare products: {e}")
            return []

    def get_product_by_id(self, product_id):
        """Get a specific product by ID"""
        try:
            product = self.products_df[self.products_df['id'] == product_id]
            if not product.empty:
                return product.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting product by ID: {e}")
            return None

    def search_products(self, query):
        """Search products by name, brand, or ingredients"""
        try:
            if not query:
                return []
            
            query_lower = query.lower()
            results = self.products_df[
                (self.products_df['name'].str.contains(query_lower, case=False, na=False)) |
                (self.products_df['brand'].str.contains(query_lower, case=False, na=False)) |
                (self.products_df['description'].str.contains(query_lower, case=False, na=False))
            ]
            
            return results.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []

    def get_categories(self):
        """Get all available categories"""
        return self.categories

    def get_skin_types(self):
        """Get all available skin types"""
        return self.skin_types

    def get_concerns(self):
        """Get all available skin concerns"""
        return self.concerns

    def get_recommendations(self, skin_type, concerns):
        """Get personalized product recommendations"""
        try:
            if not skin_type or not concerns:
                return []
            
            # Filter products that match skin type and concerns
            recommendations = self.products_df[
                (self.products_df['skin_types'].apply(
                    lambda x: skin_type in x if isinstance(x, list) else False
                )) &
                (self.products_df['concerns'].apply(
                    lambda x: any(concern in x for concern in concerns) if isinstance(x, list) else False
                ))
            ]
            
            # Sort by rating and return top recommendations
            recommendations = recommendations.sort_values('rating', ascending=False)
            return recommendations.head(10).to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    def get_price_comparison(self, product_id):
        """Get price comparison data from database"""
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return []
            
            # Query the database for price data
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                SELECT site, product_title, price, currency, image_url, product_url, scraped_at
                FROM products 
                WHERE brand = ? AND name = ?
                ORDER BY scraped_at DESC
            ''', (product['brand'], product['name']))
            
            rows = c.fetchall()
            conn.close()
            
            price_data = []
            for row in rows:
                site, title, price, currency, image_url, product_url, scraped_at = row
                price_data.append({
                    'site': site,
                    'title': title,
                    'price': price,
                    'currency': currency,
                    'image_url': image_url,
                    'product_url': product_url,
                    'scraped_at': scraped_at
                })
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting price comparison: {e}")
            return []

    def refresh_price_data(self):
        """Run the advanced price scraper to update price data"""
        try:
            logger.info("🔄 Starting price data refresh...")
            
            # Run the advanced price scraper
            script_path = os.path.join(os.path.dirname(__file__), "advanced_price_scraper.py")
            
            # Import and run the scraper
            import advanced_price_scraper
            result = advanced_price_scraper.run_full_update(save_csv=True, download_images=True, limit=10)
            
            logger.info(f"✅ Price data refresh completed. Updated {len(result)} records.")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing price data: {e}")
            return False

    def get_all_products_from_db(self):
        """Get all products from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                SELECT id, category, brand, name, site, product_title, price, currency, image_url, product_url, scraped_at
                FROM products 
                ORDER BY scraped_at DESC
            ''')
            
            rows = c.fetchall()
            conn.close()
            
            products = []
            for row in rows:
                products.append({
                    'id': row[0],
                    'category': row[1],
                    'brand': row[2],
                    'name': row[3],
                    'site': row[4],
                    'product_title': row[5],
                    'price': row[6],
                    'currency': row[7],
                    'image_url': row[8],
                    'product_url': row[9],
                    'scraped_at': row[10]
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting products from database: {e}")
            return []

# Create global instance
advanced_skincare_service = AdvancedSkincareService()
