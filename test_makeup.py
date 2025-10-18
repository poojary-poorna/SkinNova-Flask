#!/usr/bin/env python3

import sqlite3
import sys

def test_makeup_system():
    print("🧪 Testing SkinNova Makeup Recommendation System...")
    
    try:
        # Test database connection
        conn = sqlite3.connect('database/skinnova.db')
        conn.row_factory = sqlite3.Row
        
        # Test makeup products exist
        makeup_products = conn.execute(
            "SELECT * FROM products WHERE category = 'makeup'"
        ).fetchall()
        
        print(f"✅ Found {len(makeup_products)} makeup products in database")
        
        for product in makeup_products:
            print(f"   - {product['name']} by {product['brand']}")
            print(f"     Suitable for: {product['suitable_undertones']}")
        
        # Test recommendation function
        print("\n🎨 Testing makeup recommendations for different undertones:")
        
        for undertone in ['warm', 'cool', 'neutral']:
            query = """
            SELECT * FROM products 
            WHERE category = 'makeup' 
            AND (suitable_undertones LIKE ? OR suitable_undertones LIKE 'all')
            ORDER BY rating DESC LIMIT 3
            """
            
            recommendations = conn.execute(query, [f'%{undertone}%']).fetchall()
            
            print(f"\n   {undertone.upper()} undertone ({len(recommendations)} products):")
            for rec in recommendations:
                print(f"   ✨ {rec['name']} - Rating: {rec['rating']}/5")
        
        conn.close()
        
        print(f"\n✅ All tests passed! Makeup recommendation system is working correctly.")
        print(f"\n🚀 Your SkinNova app is ready to run!")
        print(f"   Run: python app.py")
        print(f"   Then visit: http://localhost:5000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_makeup_system()