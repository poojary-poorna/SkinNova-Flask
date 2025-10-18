import requests
import json
from typing import List, Dict, Optional
import random
from datetime import datetime
import os
from simple_skincare_scraper import simple_skincare_scraper

class SkincareAPIService:
    """Service class for free skincare products API integration with web scraping"""
    
    def __init__(self):
        # Free APIs for skincare products
        self.unsplash_api = "https://api.unsplash.com/search/photos"
        self.unsplash_access_key = "YOUR_UNSPLASH_ACCESS_KEY"  # Free tier: 50 requests/hour
        self.mock_products = self._get_mock_skincare_products()
        self.scraped_products = self._load_scraped_products()
    
    def _load_scraped_products(self) -> List[Dict]:
        """Load enhanced products from file or create fresh data"""
        try:
            # Try to load from file first
            products = simple_skincare_scraper.load_products_from_file()
            if products:
                return products
            
            # If no file exists, create enhanced data
            print("🔄 Creating enhanced skincare products with real data...")
            products = simple_skincare_scraper.get_enhanced_skincare_products()
            if products:
                simple_skincare_scraper.save_products_to_file()
                print(f"✅ Created {len(products)} enhanced products successfully!")
            else:
                print("⚠️ No products created, using mock data")
                return self.mock_products
            
            return products
        except Exception as e:
            print(f"❌ Error loading enhanced products: {e}")
            return self.mock_products
    
    def _get_mock_skincare_products(self) -> List[Dict]:
        """Mock skincare products data with realistic information"""
        return [
            {
                "id": 1,
                "name": "Hyaluronic Acid Serum",
                "brand": "The Ordinary",
                "category": "Serum",
                "price": 6.80,
                "rating": 4.5,
                "description": "Intense hydration serum with hyaluronic acid for plump, dewy skin",
                "ingredients": ["Hyaluronic Acid", "Vitamin B5", "Glycerin"],
                "skin_types": ["Dry", "Normal", "Combination"],
                "concerns": ["Dehydration", "Fine Lines", "Dullness"],
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True
            },
            {
                "id": 2,
                "name": "Niacinamide 10% + Zinc 1%",
                "brand": "The Ordinary",
                "category": "Serum",
                "price": 5.90,
                "rating": 4.3,
                "description": "Oil control and pore-minimizing serum with niacinamide and zinc",
                "ingredients": ["Niacinamide", "Zinc PCA", "Hyaluronic Acid"],
                "skin_types": ["Oily", "Combination", "Normal"],
                "concerns": ["Large Pores", "Oiliness", "Acne"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True
            },
            {
                "id": 3,
                "name": "Retinol 0.5% in Squalane",
                "brand": "The Ordinary",
                "category": "Treatment",
                "price": 7.20,
                "rating": 4.2,
                "description": "Anti-aging treatment with retinol in squalane for smoother skin",
                "ingredients": ["Retinol", "Squalane", "Vitamin E"],
                "skin_types": ["Normal", "Dry", "Combination"],
                "concerns": ["Fine Lines", "Wrinkles", "Uneven Texture"],
                "image_url": "https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True
            },
            {
                "id": 4,
                "name": "Vitamin C Suspension 23% + HA Spheres 2%",
                "brand": "The Ordinary",
                "category": "Serum",
                "price": 5.50,
                "rating": 4.0,
                "description": "High-potency vitamin C serum for brightening and anti-aging",
                "ingredients": ["Ascorbic Acid", "Hyaluronic Acid", "Vitamin E"],
                "skin_types": ["Normal", "Dry", "Combination"],
                "concerns": ["Dark Spots", "Dullness", "Uneven Tone"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True
            },
            {
                "id": 5,
                "name": "Gentle Cleansing Foam",
                "brand": "CeraVe",
                "category": "Cleanser",
                "price": 12.99,
                "rating": 4.6,
                "description": "Gentle foaming cleanser with ceramides and hyaluronic acid",
                "ingredients": ["Ceramides", "Hyaluronic Acid", "Niacinamide"],
                "skin_types": ["Normal", "Dry", "Sensitive"],
                "concerns": ["Sensitivity", "Dehydration", "Barrier Repair"],
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "236ml",
                "cruelty_free": False,
                "vegan": False
            },
            {
                "id": 6,
                "name": "Daily Moisturizing Lotion",
                "brand": "CeraVe",
                "category": "Moisturizer",
                "price": 15.99,
                "rating": 4.4,
                "description": "Lightweight daily moisturizer with ceramides and hyaluronic acid",
                "ingredients": ["Ceramides", "Hyaluronic Acid", "MVE Technology"],
                "skin_types": ["Normal", "Dry", "Combination"],
                "concerns": ["Dehydration", "Barrier Repair", "Dryness"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "355ml",
                "cruelty_free": False,
                "vegan": False
            },
            {
                "id": 7,
                "name": "SPF 30 Daily Facial Sunscreen",
                "brand": "EltaMD",
                "category": "Sunscreen",
                "price": 32.00,
                "rating": 4.7,
                "description": "Broad-spectrum mineral sunscreen for daily protection",
                "ingredients": ["Zinc Oxide", "Octinoxate", "Hyaluronic Acid"],
                "skin_types": ["Normal", "Dry", "Sensitive"],
                "concerns": ["Sun Protection", "Anti-Aging", "Sensitivity"],
                "image_url": "https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "85g",
                "cruelty_free": True,
                "vegan": False
            },
            {
                "id": 8,
                "name": "AHA 30% + BHA 2% Peeling Solution",
                "brand": "The Ordinary",
                "category": "Treatment",
                "price": 7.20,
                "rating": 4.1,
                "description": "Weekly exfoliating treatment with AHA and BHA acids",
                "ingredients": ["Glycolic Acid", "Salicylic Acid", "Tasmanian Pepperberry"],
                "skin_types": ["Normal", "Oily", "Combination"],
                "concerns": ["Texture", "Acne", "Dark Spots"],
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True
            }
        ]
    
    def get_skincare_products(self, category: str = None, skin_type: str = None, 
                            concern: str = None, price_range: tuple = None) -> List[Dict]:
        """
        Get skincare products with optional filtering
        
        Args:
            category: Product category (Serum, Cleanser, Moisturizer, etc.)
            skin_type: Skin type (Dry, Oily, Normal, Combination, Sensitive)
            concern: Skin concern (Acne, Aging, Dark Spots, etc.)
            price_range: Tuple of (min_price, max_price)
            
        Returns:
            List of filtered skincare products
        """
        # Use scraped products if available, otherwise fall back to mock data
        products = self.scraped_products.copy() if self.scraped_products else self.mock_products.copy()
        
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
        products = self.scraped_products if self.scraped_products else self.mock_products
        for product in products:
            if product['id'] == product_id:
                return product
        return None
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products by name, brand, or ingredients"""
        query = query.lower()
        results = []
        products = self.scraped_products if self.scraped_products else self.mock_products
        
        for product in products:
            if (query in product['name'].lower() or 
                query in product['brand'].lower() or 
                any(query in ingredient.lower() for ingredient in product['ingredients'])):
                results.append(product)
        
        return results
    
    def get_categories(self) -> List[str]:
        """Get all available product categories"""
        categories = set()
        products = self.scraped_products if self.scraped_products else self.mock_products
        for product in products:
            categories.add(product['category'])
        return sorted(list(categories))
    
    def get_skin_types(self) -> List[str]:
        """Get all available skin types"""
        skin_types = set()
        products = self.scraped_products if self.scraped_products else self.mock_products
        for product in products:
            skin_types.update(product['skin_types'])
        return sorted(list(skin_types))
    
    def get_concerns(self) -> List[str]:
        """Get all available skin concerns"""
        concerns = set()
        products = self.scraped_products if self.scraped_products else self.mock_products
        for product in products:
            concerns.update(product['concerns'])
        return sorted(list(concerns))
    
    def get_recommendations(self, skin_type: str, concerns: List[str]) -> List[Dict]:
        """Get personalized product recommendations"""
        recommendations = []
        products = self.scraped_products if self.scraped_products else self.mock_products
        
        for product in products:
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
        return recommendations[:6]  # Return top 6 recommendations

# Create a global instance
skincare_api_service = SkincareAPIService()
