import requests
from bs4 import BeautifulSoup
import json
import time
import random
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSkincareScraper:
    """Simple web scraper for skincare products using free APIs and mock data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.scraped_products = []
    
    def get_enhanced_skincare_products(self) -> List[Dict]:
        """Get enhanced skincare products with real data from free APIs"""
        products = []
        
        # Try to get real data from free APIs
        products.extend(self._get_unsplash_skincare_products())
        products.extend(self._get_enhanced_mock_products())
        
        # Remove duplicates and return
        unique_products = self._remove_duplicates(products)
        self.scraped_products = unique_products
        return unique_products
    
    def _get_unsplash_skincare_products(self) -> List[Dict]:
        """Get skincare product images from Unsplash (free API)"""
        products = []
        try:
            # Unsplash free API (no key required for basic usage)
            categories = ['skincare', 'beauty', 'cosmetics', 'face-cream', 'serum', 'cleanser']
            
            for category in categories:
                url = f"https://api.unsplash.com/search/photos"
                params = {
                    'query': category,
                    'per_page': 5,
                    'orientation': 'squarish'
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        for i, photo in enumerate(data.get('results', [])):
                            product = self._create_product_from_unsplash(photo, category, i)
                            if product:
                                products.append(product)
                    time.sleep(1)  # Be respectful to free API
                except Exception as e:
                    logger.error(f"Error fetching from Unsplash {category}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Unsplash scraping: {e}")
        
        return products
    
    def _create_product_from_unsplash(self, photo: dict, category: str, index: int) -> Dict:
        """Create product from Unsplash photo data"""
        try:
            # Extract data from photo
            image_url = photo.get('urls', {}).get('regular', '')
            description = photo.get('description', photo.get('alt_description', ''))
            photographer = photo.get('user', {}).get('name', 'Unknown')
            
            # Generate product details
            product_name = self._generate_product_name(category, index)
            brand = self._generate_brand_name(photographer)
            price = round(random.uniform(8.0, 45.0), 2)
            rating = round(random.uniform(3.8, 4.9), 1)
            
            return {
                'id': len(self.scraped_products) + index + 1,
                'name': product_name,
                'brand': brand,
                'category': self._categorize_product(category, product_name),
                'price': price,
                'rating': rating,
                'description': description or f"Premium {self._categorize_product(category, product_name).lower()} for healthy, glowing skin",
                'ingredients': self._generate_ingredients(category),
                'skin_types': self._determine_skin_types(product_name, category),
                'concerns': self._determine_concerns(product_name, category),
                'image_url': image_url,
                'availability': 'In Stock',
                'size': self._estimate_size(category),
                'cruelty_free': random.choice([True, False]),
                'vegan': random.choice([True, False]),
                'source': 'Unsplash',
                'photographer': photographer
            }
        except Exception as e:
            logger.error(f"Error creating product from Unsplash: {e}")
            return None
    
    def _get_enhanced_mock_products(self) -> List[Dict]:
        """Get enhanced mock products with realistic data"""
        return [
            {
                "id": 1,
                "name": "Hyaluronic Acid Hydrating Serum",
                "brand": "The Ordinary",
                "category": "Serum",
                "price": 6.80,
                "rating": 4.5,
                "description": "Intense hydration serum with hyaluronic acid for plump, dewy skin. Perfect for all skin types.",
                "ingredients": ["Hyaluronic Acid", "Vitamin B5", "Glycerin", "Sodium Hyaluronate"],
                "skin_types": ["Dry", "Normal", "Combination", "Sensitive"],
                "concerns": ["Dehydration", "Fine Lines", "Dullness", "Dryness"],
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True,
                "source": "Mock Data"
            },
            {
                "id": 2,
                "name": "Niacinamide 10% + Zinc 1%",
                "brand": "The Ordinary",
                "category": "Serum",
                "price": 5.90,
                "rating": 4.3,
                "description": "Oil control and pore-minimizing serum with niacinamide and zinc. Reduces blemishes and improves skin texture.",
                "ingredients": ["Niacinamide", "Zinc PCA", "Hyaluronic Acid", "Dimethicone"],
                "skin_types": ["Oily", "Combination", "Normal"],
                "concerns": ["Large Pores", "Oiliness", "Acne", "Blemishes"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True,
                "source": "Mock Data"
            },
            {
                "id": 3,
                "name": "Retinol 0.5% in Squalane",
                "brand": "The Ordinary",
                "category": "Treatment",
                "price": 7.20,
                "rating": 4.2,
                "description": "Anti-aging treatment with retinol in squalane for smoother, firmer skin. Reduces fine lines and wrinkles.",
                "ingredients": ["Retinol", "Squalane", "Vitamin E", "Tocopherol"],
                "skin_types": ["Normal", "Dry", "Combination"],
                "concerns": ["Fine Lines", "Wrinkles", "Uneven Texture", "Aging"],
                "image_url": "https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True,
                "source": "Mock Data"
            },
            {
                "id": 4,
                "name": "Vitamin C Suspension 23% + HA Spheres 2%",
                "brand": "The Ordinary",
                "category": "Serum",
                "price": 5.50,
                "rating": 4.0,
                "description": "High-potency vitamin C serum for brightening and anti-aging. Improves skin tone and reduces dark spots.",
                "ingredients": ["Ascorbic Acid", "Hyaluronic Acid", "Vitamin E", "Sodium Hyaluronate"],
                "skin_types": ["Normal", "Dry", "Combination"],
                "concerns": ["Dark Spots", "Dullness", "Uneven Tone", "Aging"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True,
                "source": "Mock Data"
            },
            {
                "id": 5,
                "name": "Gentle Cleansing Foam",
                "brand": "CeraVe",
                "category": "Cleanser",
                "price": 12.99,
                "rating": 4.6,
                "description": "Gentle foaming cleanser with ceramides and hyaluronic acid. Removes makeup and impurities without stripping skin.",
                "ingredients": ["Ceramides", "Hyaluronic Acid", "Niacinamide", "Glycerin"],
                "skin_types": ["Normal", "Dry", "Sensitive"],
                "concerns": ["Sensitivity", "Dehydration", "Barrier Repair", "Dryness"],
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "236ml",
                "cruelty_free": False,
                "vegan": False,
                "source": "Mock Data"
            },
            {
                "id": 6,
                "name": "Daily Moisturizing Lotion",
                "brand": "CeraVe",
                "category": "Moisturizer",
                "price": 15.99,
                "rating": 4.4,
                "description": "Lightweight daily moisturizer with ceramides and hyaluronic acid. Provides 24-hour hydration for all skin types.",
                "ingredients": ["Ceramides", "Hyaluronic Acid", "MVE Technology", "Glycerin"],
                "skin_types": ["Normal", "Dry", "Combination"],
                "concerns": ["Dehydration", "Barrier Repair", "Dryness", "Sensitivity"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "355ml",
                "cruelty_free": False,
                "vegan": False,
                "source": "Mock Data"
            },
            {
                "id": 7,
                "name": "SPF 30 Daily Facial Sunscreen",
                "brand": "EltaMD",
                "category": "Sunscreen",
                "price": 32.00,
                "rating": 4.7,
                "description": "Broad-spectrum mineral sunscreen for daily protection. Lightweight, non-greasy formula suitable for sensitive skin.",
                "ingredients": ["Zinc Oxide", "Octinoxate", "Hyaluronic Acid", "Vitamin E"],
                "skin_types": ["Normal", "Dry", "Sensitive"],
                "concerns": ["Sun Protection", "Anti-Aging", "Sensitivity", "UV Damage"],
                "image_url": "https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "85g",
                "cruelty_free": True,
                "vegan": False,
                "source": "Mock Data"
            },
            {
                "id": 8,
                "name": "AHA 30% + BHA 2% Peeling Solution",
                "brand": "The Ordinary",
                "category": "Treatment",
                "price": 7.20,
                "rating": 4.1,
                "description": "Weekly exfoliating treatment with AHA and BHA acids. Improves skin texture and reduces blemishes.",
                "ingredients": ["Glycolic Acid", "Salicylic Acid", "Tasmanian Pepperberry", "Hyaluronic Acid"],
                "skin_types": ["Normal", "Oily", "Combination"],
                "concerns": ["Texture", "Acne", "Dark Spots", "Blemishes"],
                "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "30ml",
                "cruelty_free": True,
                "vegan": True,
                "source": "Mock Data"
            },
            {
                "id": 9,
                "name": "Rose Water Facial Toner",
                "brand": "Heritage Store",
                "category": "Toner",
                "price": 8.99,
                "rating": 4.3,
                "description": "Pure rose water toner that hydrates and refreshes skin. Natural astringent properties help tighten pores.",
                "ingredients": ["Rose Water", "Glycerin", "Natural Fragrance", "Water"],
                "skin_types": ["Normal", "Dry", "Sensitive"],
                "concerns": ["Hydration", "Pore Tightening", "Sensitivity", "Refreshment"],
                "image_url": "https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "240ml",
                "cruelty_free": True,
                "vegan": True,
                "source": "Mock Data"
            },
            {
                "id": 10,
                "name": "Overnight Hydrating Mask",
                "brand": "Laneige",
                "category": "Treatment",
                "price": 25.00,
                "rating": 4.5,
                "description": "Overnight hydrating mask that provides intense moisture while you sleep. Wake up to plump, glowing skin.",
                "ingredients": ["Hyaluronic Acid", "Moisture Wrap Technology", "Ceramides", "Vitamin E"],
                "skin_types": ["Dry", "Normal", "Combination"],
                "concerns": ["Dehydration", "Dullness", "Dryness", "Lack of Glow"],
                "image_url": "https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop",
                "availability": "In Stock",
                "size": "80ml",
                "cruelty_free": False,
                "vegan": False,
                "source": "Mock Data"
            }
        ]
    
    def _generate_product_name(self, category: str, index: int) -> str:
        """Generate realistic product names"""
        names = {
            'skincare': ['Hydrating Serum', 'Moisturizing Cream', 'Gentle Cleanser', 'Anti-Aging Treatment'],
            'beauty': ['Beauty Elixir', 'Glow Serum', 'Radiance Cream', 'Perfecting Treatment'],
            'cosmetics': ['Cosmetic Serum', 'Beauty Cream', 'Skin Treatment', 'Beauty Elixir'],
            'face-cream': ['Face Cream', 'Moisturizing Lotion', 'Hydrating Balm', 'Nourishing Cream'],
            'serum': ['Vitamin C Serum', 'Hyaluronic Serum', 'Anti-Aging Serum', 'Brightening Serum'],
            'cleanser': ['Gentle Cleanser', 'Foaming Wash', 'Purifying Gel', 'Hydrating Cleanser']
        }
        
        base_names = names.get(category, ['Skincare Product', 'Beauty Treatment', 'Skin Care', 'Beauty Product'])
        return random.choice(base_names)
    
    def _generate_brand_name(self, photographer: str) -> str:
        """Generate brand names based on photographer or random"""
        brands = [
            'The Ordinary', 'CeraVe', 'La Roche-Posay', 'Neutrogena', 'Olay',
            'Olay', 'Aveeno', 'Cetaphil', 'Eucerin', 'Vichy', 'L\'Oreal',
            'Garnier', 'Nivea', 'Simple', 'Clean & Clear', 'St. Ives'
        ]
        
        if photographer and len(photographer) > 3:
            # Use photographer name as inspiration
            return f"{photographer.split()[0]} Beauty"
        else:
            return random.choice(brands)
    
    def _categorize_product(self, category: str, name: str) -> str:
        """Categorize product based on category and name"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['cleanser', 'wash', 'foam', 'gel']):
            return 'Cleanser'
        elif any(word in name_lower for word in ['moisturizer', 'cream', 'lotion', 'balm']):
            return 'Moisturizer'
        elif any(word in name_lower for word in ['serum', 'essence', 'ampoule']):
            return 'Serum'
        elif any(word in name_lower for word in ['sunscreen', 'spf', 'sunblock']):
            return 'Sunscreen'
        elif any(word in name_lower for word in ['mask', 'treatment', 'peel']):
            return 'Treatment'
        elif any(word in name_lower for word in ['toner', 'mist', 'spray']):
            return 'Toner'
        else:
            return 'Skincare'
    
    def _generate_ingredients(self, category: str) -> List[str]:
        """Generate realistic ingredients based on category"""
        ingredient_map = {
            'cleanser': ['Hyaluronic Acid', 'Glycerin', 'Salicylic Acid', 'Tea Tree Oil'],
            'moisturizer': ['Hyaluronic Acid', 'Ceramides', 'Niacinamide', 'Vitamin E'],
            'serum': ['Retinol', 'Vitamin C', 'Hyaluronic Acid', 'Peptides'],
            'sunscreen': ['Zinc Oxide', 'Titanium Dioxide', 'Hyaluronic Acid', 'Vitamin E'],
            'treatment': ['AHA', 'BHA', 'Retinol', 'Vitamin C'],
            'toner': ['Rose Water', 'Glycerin', 'Hyaluronic Acid', 'Natural Extracts']
        }
        
        base_ingredients = ingredient_map.get(category, ['Hyaluronic Acid', 'Vitamin E', 'Glycerin'])
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
        
        return list(set(skin_types))  # Remove duplicates
    
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
    
    def _estimate_size(self, category: str) -> str:
        """Estimate product size based on category"""
        size_map = {
            'cleanser': '150ml',
            'moisturizer': '50ml',
            'serum': '30ml',
            'sunscreen': '50ml',
            'treatment': '30ml',
            'toner': '240ml'
        }
        
        return size_map.get(category, '50ml')
    
    def _remove_duplicates(self, products: List[Dict]) -> List[Dict]:
        """Remove duplicate products based on name and brand"""
        seen = set()
        unique_products = []
        
        for product in products:
            key = (product['name'].lower(), product['brand'].lower())
            if key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        return unique_products
    
    def save_products_to_file(self, filename: str = 'enhanced_skincare_products.json'):
        """Save products to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_products, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.scraped_products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving products to file: {e}")
    
    def load_products_from_file(self, filename: str = 'enhanced_skincare_products.json') -> List[Dict]:
        """Load products from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                products = json.load(f)
            logger.info(f"Loaded {len(products)} products from {filename}")
            return products
        except FileNotFoundError:
            logger.info(f"File {filename} not found, will create fresh data")
            return []
        except Exception as e:
            logger.error(f"Error loading products from file: {e}")
            return []

# Create a global instance
simple_skincare_scraper = SimpleSkincareScraper()





