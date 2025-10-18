#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def debug_makeup_issue():
    print("🔍 Debugging Makeup Recommendations Issue...")
    
    try:
        # Test database connection
        conn = sqlite3.connect('database/skinnova.db')
        conn.row_factory = sqlite3.Row
        
        print("\n1. Testing database structure...")
        
        # Check user_profiles table structure
        cursor = conn.execute("PRAGMA table_info(user_profiles)")
        columns = cursor.fetchall()
        print("   user_profiles table columns:")
        for col in columns:
            print(f"     - {col[1]} ({col[2]})")
        
        # Check if there are any user profiles
        profiles = conn.execute("SELECT * FROM user_profiles").fetchall()
        print(f"\n   Found {len(profiles)} user profiles in database")
        
        for profile in profiles:
            print(f"     User ID {profile['user_id']}: skin_undertone='{profile['skin_undertone']}', makeup_preferences='{profile['makeup_preferences']}'")
        
        print("\n2. Testing makeup products...")
        
        # Check makeup products
        makeup_products = conn.execute("SELECT * FROM products WHERE category = 'makeup'").fetchall()
        print(f"   Found {len(makeup_products)} makeup products:")
        
        for product in makeup_products:
            print(f"     - {product['name']}: undertones='{product['suitable_undertones']}'")
        
        print("\n3. Testing recommendation function...")
        
        # Test the recommendation query directly
        for undertone in ['warm', 'cool', 'neutral']:
            query = """
            SELECT * FROM products 
            WHERE category = 'makeup' 
            AND (suitable_undertones LIKE ? OR suitable_undertones LIKE 'all')
            ORDER BY rating DESC LIMIT 10
            """
            
            recommendations = conn.execute(query, [f'%{undertone}%']).fetchall()
            print(f"\n   {undertone.upper()} undertone recommendations ({len(recommendations)} found):")
            for rec in recommendations:
                print(f"     ✓ {rec['name']} by {rec['brand']} (rating: {rec['rating']})")
        
        print("\n4. Testing profile creation/update...")
        
        # Simulate the makeup quiz process
        test_user_id = 999  # Use a test user ID
        test_undertone = 'warm'
        test_preferences = ['natural-look', 'long-wearing']
        
        # Check if profile exists
        existing_profile = conn.execute(
            'SELECT id FROM user_profiles WHERE user_id = ?',
            (test_user_id,)
        ).fetchone()
        
        if existing_profile:
            print(f"   Found existing profile for user {test_user_id}")
            conn.execute(
                '''UPDATE user_profiles 
                   SET skin_undertone = ?, makeup_preferences = ?, updated_at = ?
                   WHERE user_id = ?''',
                (test_undertone, ','.join(test_preferences), datetime.now(), test_user_id)
            )
        else:
            print(f"   Creating new profile for user {test_user_id}")
            conn.execute(
                '''INSERT INTO user_profiles 
                   (user_id, skin_undertone, makeup_preferences, created_at)
                   VALUES (?, ?, ?, ?)''',
                (test_user_id, test_undertone, ','.join(test_preferences), datetime.now())
            )
        
        conn.commit()
        
        # Verify the profile was created/updated
        updated_profile = conn.execute(
            'SELECT * FROM user_profiles WHERE user_id = ?',
            (test_user_id,)
        ).fetchone()
        
        if updated_profile:
            print(f"   ✅ Profile saved: undertone='{updated_profile['skin_undertone']}', preferences='{updated_profile['makeup_preferences']}'")
        else:
            print(f"   ❌ Failed to save profile")
        
        conn.close()
        
        print(f"\n✅ Debug complete! If you see makeup products and recommendations above, the system should be working.")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_makeup_issue()