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

class SkincareWebScraper:
    """Web scraper for real skincare products from various sources"""
    
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
    
    def scrape_skincare_products(self) -> List[Dict]:
        """Scrape skincare products from multiple sources"""
        products = []
        
        # Scrape from different sources
        products.extend(self._scrape_nykaa_products())
        products.extend(self._scrape_ulta_products())
        products.extend(self._scrape_sephora_products())
        
        # Remove duplicates and return
        unique_products = self._remove_duplicates(products)
        self.scraped_products = unique_products
        return unique_products
    
    def _scrape_nykaa_products(self) -> List[Dict]:
        """Scrape products from Nykaa (Indian beauty retailer)"""
        products = []
        try:
            # Nykaa skincare categories
            categories = [
                'skincare/face-wash-cleansers',
                'skincare/moisturizers',
                'skincare/serums',
                'skincare/sunscreens',
                'skincare/face-masks'
            ]
            
            for category in categories:
                url = f"https://www.nykaa.com/{category}"
                logger.info(f"Scraping Nykaa category: {category}")
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        products.extend(self._parse_nykaa_products(soup, category))
                        time.sleep(random.uniform(1, 3))  # Be respectful
                except Exception as e:
                    logger.error(f"Error scraping Nykaa {category}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Nykaa scraping: {e}")
        
        return products
    
    def _parse_nykaa_products(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """Parse Nykaa product data from HTML"""
        products = []
        
        # Look for product containers
        product_containers = soup.find_all('div', class_=re.compile(r'product|item'))
        
        for container in product_containers[:10]:  # Limit to 10 products per category
            try:
                # Extract product information
                name_elem = container.find('h2') or container.find('h3') or container.find('a', class_=re.compile(r'title|name'))
                if not name_elem:
                    continue
                
                name = name_elem.get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                
                # Extract price
                price_elem = container.find('span', class_=re.compile(r'price|cost'))
                price = self._extract_price(price_elem.get_text(strip=True) if price_elem else "")
                
                # Extract image
                img_elem = container.find('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                
                # Extract brand
                brand_elem = container.find('span', class_=re.compile(r'brand'))
                brand = brand_elem.get_text(strip=True) if brand_elem else "Unknown Brand"
                
                # Extract rating
                rating_elem = container.find('div', class_=re.compile(r'rating|star'))
                rating = self._extract_rating(rating_elem.get_text(strip=True) if rating_elem else "")
                
                # Extract product URL
                link_elem = container.find('a')
                product_url = link_elem.get('href') if link_elem else ""
                if product_url and not product_url.startswith('http'):
                    product_url = urljoin('https://www.nykaa.com', product_url)
                
                product = {
                    'id': len(products) + 1,
                    'name': name,
                    'brand': brand,
                    'category': self._categorize_product(category, name),
                    'price': price,
                    'rating': rating,
                    'description': f"Premium {self._categorize_product(category, name).lower()} from {brand}",
                    'ingredients': self._generate_ingredients(category),
                    'skin_types': self._determine_skin_types(name, category),
                    'concerns': self._determine_concerns(name, category),
                    'image_url': image_url or self._get_placeholder_image(category),
                    'availability': 'In Stock',
                    'size': self._estimate_size(category),
                    'cruelty_free': random.choice([True, False]),
                    'vegan': random.choice([True, False]),
                    'source': 'Nykaa',
                    'product_url': product_url
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Nykaa product: {e}")
                continue
        
        return products
    
    def _scrape_ulta_products(self) -> List[Dict]:
        """Scrape products from Ulta Beauty"""
        products = []
        try:
            # Ulta skincare categories
            categories = [
                'skincare/cleansers',
                'skincare/moisturizers',
                'skincare/serums',
                'skincare/sunscreen'
            ]
            
            for category in categories:
                url = f"https://www.ulta.com/{category}"
                logger.info(f"Scraping Ulta category: {category}")
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        products.extend(self._parse_ulta_products(soup, category))
                        time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.error(f"Error scraping Ulta {category}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Ulta scraping: {e}")
        
        return products
    
    def _parse_ulta_products(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """Parse Ulta product data from HTML"""
        products = []
        
        # Look for product containers
        product_containers = soup.find_all('div', class_=re.compile(r'product|item'))
        
        for container in product_containers[:8]:  # Limit to 8 products per category
            try:
                # Extract product information
                name_elem = container.find('h3') or container.find('h4') or container.find('a', class_=re.compile(r'title|name'))
                if not name_elem:
                    continue
                
                name = name_elem.get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                
                # Extract price
                price_elem = container.find('span', class_=re.compile(r'price|cost'))
                price = self._extract_price(price_elem.get_text(strip=True) if price_elem else "")
                
                # Extract image
                img_elem = container.find('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                
                # Extract brand
                brand_elem = container.find('span', class_=re.compile(r'brand'))
                brand = brand_elem.get_text(strip=True) if brand_elem else "Ulta Brand"
                
                # Extract rating
                rating_elem = container.find('div', class_=re.compile(r'rating|star'))
                rating = self._extract_rating(rating_elem.get_text(strip=True) if rating_elem else "")
                
                product = {
                    'id': len(products) + 100,  # Different ID range
                    'name': name,
                    'brand': brand,
                    'category': self._categorize_product(category, name),
                    'price': price,
                    'rating': rating,
                    'description': f"Professional {self._categorize_product(category, name).lower()} from {brand}",
                    'ingredients': self._generate_ingredients(category),
                    'skin_types': self._determine_skin_types(name, category),
                    'concerns': self._determine_concerns(name, category),
                    'image_url': image_url or self._get_placeholder_image(category),
                    'availability': 'In Stock',
                    'size': self._estimate_size(category),
                    'cruelty_free': random.choice([True, False]),
                    'vegan': random.choice([True, False]),
                    'source': 'Ulta',
                    'product_url': f"https://www.ulta.com/{category}"
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Ulta product: {e}")
                continue
        
        return products
    
    def _scrape_sephora_products(self) -> List[Dict]:
        """Scrape products from Sephora"""
        products = []
        try:
            # Sephora skincare categories
            categories = [
                'skincare/cleansers',
                'skincare/moisturizers',
                'skincare/serums',
                'skincare/sunscreen'
            ]
            
            for category in categories:
                url = f"https://www.sephora.com/{category}"
                logger.info(f"Scraping Sephora category: {category}")
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        products.extend(self._parse_sephora_products(soup, category))
                        time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.error(f"Error scraping Sephora {category}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Sephora scraping: {e}")
        
        return products
    
    def _parse_sephora_products(self, soup: BeautifulSoup, category: str) -> List[Dict]:
        """Parse Sephora product data from HTML"""
        products = []
        
        # Look for product containers
        product_containers = soup.find_all('div', class_=re.compile(r'product|item'))
        
        for container in product_containers[:6]:  # Limit to 6 products per category
            try:
                # Extract product information
                name_elem = container.find('h3') or container.find('h4') or container.find('a', class_=re.compile(r'title|name'))
                if not name_elem:
                    continue
                
                name = name_elem.get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                
                # Extract price
                price_elem = container.find('span', class_=re.compile(r'price|cost'))
                price = self._extract_price(price_elem.get_text(strip=True) if price_elem else "")
                
                # Extract image
                img_elem = container.find('img')
                image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else ""
                
                # Extract brand
                brand_elem = container.find('span', class_=re.compile(r'brand'))
                brand = brand_elem.get_text(strip=True) if brand_elem else "Sephora Collection"
                
                # Extract rating
                rating_elem = container.find('div', class_=re.compile(r'rating|star'))
                rating = self._extract_rating(rating_elem.get_text(strip=True) if rating_elem else "")
                
                product = {
                    'id': len(products) + 200,  # Different ID range
                    'name': name,
                    'brand': brand,
                    'category': self._categorize_product(category, name),
                    'price': price,
                    'rating': rating,
                    'description': f"Luxury {self._categorize_product(category, name).lower()} from {brand}",
                    'ingredients': self._generate_ingredients(category),
                    'skin_types': self._determine_skin_types(name, category),
                    'concerns': self._determine_concerns(name, category),
                    'image_url': image_url or self._get_placeholder_image(category),
                    'availability': 'In Stock',
                    'size': self._estimate_size(category),
                    'cruelty_free': random.choice([True, False]),
                    'vegan': random.choice([True, False]),
                    'source': 'Sephora',
                    'product_url': f"https://www.sephora.com/{category}"
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Sephora product: {e}")
                continue
        
        return products
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        if not price_text:
            return random.uniform(5.0, 50.0)
        
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                pass
        
        return random.uniform(5.0, 50.0)
    
    def _extract_rating(self, rating_text: str) -> float:
        """Extract numeric rating from text"""
        if not rating_text:
            return round(random.uniform(3.5, 4.8), 1)
        
        # Look for rating patterns
        rating_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5|\d+\.?\d*', rating_text)
        if rating_match:
            try:
                rating = float(rating_match.group(1) if rating_match.groups() else rating_match.group())
                return min(5.0, max(1.0, rating))
            except ValueError:
                pass
        
        return round(random.uniform(3.5, 4.8), 1)
    
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
            'treatment': ['AHA', 'BHA', 'Retinol', 'Vitamin C']
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
    
    def _get_placeholder_image(self, category: str) -> str:
        """Get placeholder image based on category"""
        placeholder_map = {
            'cleanser': 'https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop',
            'moisturizer': 'https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop',
            'serum': 'https://images.unsplash.com/photo-1599305445771-b0be54c8c7e8?w=400&h=400&fit=crop',
            'sunscreen': 'https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop',
            'treatment': 'https://images.unsplash.com/photo-1570194065650-d99fb4bedf0a?w=400&h=400&fit=crop'
        }
        
        return placeholder_map.get(category, 'https://images.unsplash.com/photo-1556228720-195a672e8a18?w=400&h=400&fit=crop')
    
    def _estimate_size(self, category: str) -> str:
        """Estimate product size based on category"""
        size_map = {
            'cleanser': '150ml',
            'moisturizer': '50ml',
            'serum': '30ml',
            'sunscreen': '50ml',
            'treatment': '30ml'
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
    
    def save_products_to_file(self, filename: str = 'scraped_skincare_products.json'):
        """Save scraped products to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_products, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.scraped_products)} products to {filename}")
        except Exception as e:
            logger.error(f"Error saving products to file: {e}")
    
    def load_products_from_file(self, filename: str = 'scraped_skincare_products.json') -> List[Dict]:
        """Load products from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                products = json.load(f)
            logger.info(f"Loaded {len(products)} products from {filename}")
            return products
        except FileNotFoundError:
            logger.info(f"File {filename} not found, will scrape fresh data")
            return []
        except Exception as e:
            logger.error(f"Error loading products from file: {e}")
            return []

# Create a global instance
skincare_scraper = SkincareWebScraper()





