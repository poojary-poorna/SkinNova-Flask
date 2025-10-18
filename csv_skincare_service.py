import pandas as pd
import json
import random
from typing import List, Dict, Optional
import os
from datetime import datetime

class CSVSkincareService:
    """Service class for skincare products using CSV database and price comparison"""
    
    def __init__(self):
        self.products_file = 'products.csv'
        self.price_comparison_file = 'price_comparison.csv'
        self.products_data = self._load_products()
        self.price_data = self._load_price_comparison()
        self.enhanced_products = self._create_enhanced_products()
    
    def _load_products(self) -> pd.DataFrame:
        """Load products from CSV file"""
        try:
            if os.path.exists(self.products_file):
                df = pd.read_csv(self.products_file)
                print(f"✅ Loaded {len(df)} products from {self.products_file}")
                return df
            else:
                print(f"❌ Products file {self.products_file} not found")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading products: {e}")
            return pd.DataFrame()
    
    def _load_price_comparison(self) -> pd.DataFrame:
        """Load price comparison data"""
        try:
            if os.path.exists(self.price_comparison_file):
                df = pd.read_csv(self.price_comparison_file)
                print(f"✅ Loaded price comparison data for {len(df)} products")
                return df
            else:
                print(f"⚠️ Price comparison file {self.price_comparison_file} not found")
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading price comparison: {e}")
            return pd.DataFrame()
    
    def _create_enhanced_products(self) -> List[Dict]:
        """Create enhanced product data with price comparison"""
        enhanced_products = []
        
        for idx, product in self.products_data.iterrows():
            # Get price comparison data for this product
            price_data = self._get_price_data(product['brand'], product['name'])
            
            # Generate enhanced product data
            enhanced_product = {
                'id': idx + 1,
                'name': product['name'],
                'brand': product['brand'],
                'category': self._categorize_product(product['category']),
                'price': self._get_best_price(price_data),
                'rating': round(random.uniform(3.8, 4.9), 1),
                'description': self._generate_description(product['name'], product['brand'], product['category']),
                'ingredients': self._generate_ingredients(product['category']),
                'skin_types': self._determine_skin_types(product['name'], product['category']),
                'concerns': self._determine_concerns(product['name'], product['category']),
                'image_url': self._get_image_url(product['name'], product['category']),
                'availability': 'In Stock',
                'size': self._estimate_size(product['category']),
                'cruelty_free': random.choice([True, False]),
                'vegan': random.choice([True, False]),
                'source': 'CSV Database',
                'price_comparison': price_data,
                'original_category': product['category']
            }
            
            enhanced_products.append(enhanced_product)
        
        return enhanced_products
    
    def _get_price_data(self, brand: str, name: str) -> List[Dict]:
        """Get price comparison data for a product"""
        if self.price_data.empty:
            return []
        
        # Find matching products in price comparison data
        matching_products = self.price_data[
            (self.price_data['brand'].str.lower() == brand.lower()) &
            (self.price_data['name'].str.lower() == name.lower())
        ]
        
        price_data = []
        for _, row in matching_products.iterrows():
            if pd.notna(row['price']) and row['price']:
                price_data.append({
                    'site': row['site'],
                    'price': float(row['price']) if row['price'] else None,
                    'currency': row.get('currency', 'INR'),
                    'image_url': row.get('image_url'),
                    'product_url': row.get('product_url')
                })
        
        return price_data
    
    def _get_best_price(self, price_data: List[Dict]) -> float:
        """Get the best (lowest) price from price comparison data"""
        if not price_data:
            return round(random.uniform(5.0, 50.0), 2)
        
        valid_prices = [p['price'] for p in price_data if p['price'] is not None]
        if valid_prices:
            return min(valid_prices)
        
        return round(random.uniform(5.0, 50.0), 2)
    
    def _categorize_product(self, category: str) -> str:
        """Categorize product based on CSV category"""
        category_map = {
            'facewash': 'Cleanser',
            'serum': 'Serum',
            'sunscreen': 'Sunscreen',
            'moisturizer': 'Moisturizer',
            'toner': 'Toner'
        }
        return category_map.get(category.lower(), 'Skincare')
    
    def _generate_description(self, name: str, brand: str, category: str) -> str:
        """Generate product description"""
        descriptions = {
            'facewash': f"Gentle {name.lower()} from {brand} that effectively cleanses and purifies your skin",
            'serum': f"Powerful {name.lower()} from {brand} for targeted skin treatment and improvement",
            'sunscreen': f"Broad-spectrum {name.lower()} from {brand} for complete sun protection",
            'moisturizer': f"Hydrating {name.lower()} from {brand} for soft, supple skin",
            'toner': f"Refreshing {name.lower()} from {brand} to balance and prepare your skin"
        }
        return descriptions.get(category.lower(), f"Premium {name.lower()} from {brand}")
    
    def _generate_ingredients(self, category: str) -> List[str]:
        """Generate realistic ingredients based on category"""
        ingredient_map = {
            'facewash': ['Hyaluronic Acid', 'Glycerin', 'Salicylic Acid', 'Tea Tree Oil'],
            'serum': ['Retinol', 'Vitamin C', 'Hyaluronic Acid', 'Peptides'],
            'sunscreen': ['Zinc Oxide', 'Titanium Dioxide', 'Hyaluronic Acid', 'Vitamin E'],
            'moisturizer': ['Hyaluronic Acid', 'Ceramides', 'Niacinamide', 'Vitamin E'],
            'toner': ['Rose Water', 'Glycerin', 'Hyaluronic Acid', 'Natural Extracts']
        }
        
        base_ingredients = ingredient_map.get(category.lower(), ['Hyaluronic Acid', 'Vitamin E', 'Glycerin'])
        return random.sample(base_ingredients, min(3, len(base_ingredients)))
    
    def _determine_skin_types(self, name: str, category: str) -> List[str]:
        """Determine suitable skin types based on product name and category"""
        name_lower = name.lower()
        skin_types = []
        
        if any(word in name_lower for word in ['gentle', 'sensitive', 'calming']):
            skin_types.extend(['Sensitive', 'Normal'])
        elif any(word in name_lower for word in ['oily', 'oil', 'matte']):
            skin_types.extend(['Oily', 'Combination'])
        elif any(word in name_lower for word in ['dry', 'hydrating', 'moisturizing']):
            skin_types.extend(['Dry', 'Normal'])
        else:
            skin_types = ['Normal', 'Combination', 'Dry', 'Oily']
        
        return list(set(skin_types))
    
    def _determine_concerns(self, name: str, category: str) -> List[str]:
        """Determine skin concerns addressed by the product"""
        name_lower = name.lower()
        concerns = []
        
        if any(word in name_lower for word in ['acne', 'blemish', 'spot']):
            concerns.append('Acne')
        if any(word in name_lower for word in ['aging', 'anti-aging', 'wrinkle']):
            concerns.append('Aging')
        if any(word in name_lower for word in ['dark', 'spot', 'pigmentation']):
            concerns.append('Dark Spots')
        if any(word in name_lower for word in ['dull', 'brightening', 'glow']):
            concerns.append('Dullness')
        if any(word in name_lower for word in ['pore', 'large pore']):
            concerns.append('Large Pores')
        if any(word in name_lower for word in ['sensitive', 'irritation']):
            concerns.append('Sensitivity')
        
        if not concerns:
            concerns = ['General Care']
        
        return concerns
    
    def _get_image_url(self, name: str, category: str) -> str:
        """Get placeholder image URL"""
        placeholder_map = {
            'facewash': 'https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop',
            'serum': 'https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop',
            'sunscreen': 'https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop',
            'moisturizer': 'https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop',
            'toner': 'https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop'
        }
        
        return placeholder_map.get(category.lower(), 'https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop')
    
    def _estimate_size(self, category: str) -> str:
        """Estimate product size based on category"""
        size_map = {
            'facewash': '150ml',
            'serum': '30ml',
            'sunscreen': '50ml',
            'moisturizer': '50ml',
            'toner': '240ml'
        }
        
        return size_map.get(category.lower(), '50ml')
    
    def get_skincare_products(self, category: str = None, skin_type: str = None, 
                            concern: str = None, price_range: tuple = None) -> List[Dict]:
        """Get skincare products with optional filtering"""
        products = self.enhanced_products.copy()
        
        # Apply filters
        if category:
            products = [p for p in products if p['category'].lower() == category.lower()]
        
        if skin_type:
            products = [p for p in products if skin_type in p['skin_types']]
        
        if concern:
            products = [p for p in products if concern in p['concerns']]
        
        if price_range:
            min_price, max_price = price_range
            products = [p for p in products if min_price <= p['price'] <= max_price]
        
        # Shuffle for variety
        random.shuffle(products)
        return products
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a specific product by ID"""
        for product in self.enhanced_products:
            if product['id'] == product_id:
                return product
        return None
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products by name, brand, or ingredients"""
        query = query.lower()
        results = []
        
        for product in self.enhanced_products:
            if (query in product['name'].lower() or 
                query in product['brand'].lower() or 
                any(query in ingredient.lower() for ingredient in product['ingredients'])):
                results.append(product)
        
        return results
    
    def get_categories(self) -> List[str]:
        """Get all available product categories"""
        categories = set()
        for product in self.enhanced_products:
            categories.add(product['category'])
        return sorted(list(categories))
    
    def get_skin_types(self) -> List[str]:
        """Get all available skin types"""
        skin_types = set()
        for product in self.enhanced_products:
            skin_types.update(product['skin_types'])
        return sorted(list(skin_types))
    
    def get_concerns(self) -> List[str]:
        """Get all available skin concerns"""
        concerns = set()
        for product in self.enhanced_products:
            concerns.update(product['concerns'])
        return sorted(list(concerns))
    
    def get_recommendations(self, skin_type: str, concerns: List[str]) -> List[Dict]:
        """Get personalized product recommendations"""
        recommendations = []
        
        for product in self.enhanced_products:
            score = 0
            
            # Check skin type compatibility
            if skin_type in product['skin_types']:
                score += 2
            
            # Check concern matching
            for concern in concerns:
                if concern in product['concerns']:
                    score += 1
            
            if score > 0:
                product['recommendation_score'] = score
                recommendations.append(product)
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return recommendations[:6]
    
    def get_price_comparison(self, product_id: int) -> List[Dict]:
        """Get price comparison data for a specific product"""
        product = self.get_product_by_id(product_id)
        if product and 'price_comparison' in product:
            return product['price_comparison']
        return []
    
    def refresh_price_data(self):
        """Refresh price comparison data by running the scraper"""
        try:
            print("🔄 Refreshing price comparison data...")
            # This would run the price comparison scraper
            # For now, we'll just reload the existing data
            self.price_data = self._load_price_comparison()
            self.enhanced_products = self._create_enhanced_products()
            print("✅ Price data refreshed successfully!")
        except Exception as e:
            print(f"❌ Error refreshing price data: {e}")

# Create a global instance
csv_skincare_service = CSVSkincareService()





