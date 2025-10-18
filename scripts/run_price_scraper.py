#!/usr/bin/env python3
"""
Script to run the price comparison scraper
"""

import subprocess
import sys
import os

def main():
    print("🔄 Starting Price Comparison Scraper...")
    print("=" * 50)
    
    # Check if products.csv exists
    if not os.path.exists('products.csv'):
        print("❌ products.csv not found!")
        print("Please make sure products.csv exists in the current directory.")
        return
    
    # Check if price_compare_scraper.py exists
    if not os.path.exists('price_compare_scraper.py'):
        print("❌ price_compare_scraper.py not found!")
        print("Please make sure price_compare_scraper.py exists in the current directory.")
        return
    
    try:
        # Run the price comparison scraper
        print("📊 Running price comparison scraper...")
        print("This may take a few minutes as we scrape data from multiple sites...")
        print()
        
        result = subprocess.run([sys.executable, 'price_compare_scraper.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Price comparison scraper completed successfully!")
            print("📁 Results saved to price_comparison.csv")
            print()
            print("🔄 Refreshing skincare service...")
            
            # Import and refresh the CSV skincare service
            try:
                from csv_skincare_service import csv_skincare_service
                csv_skincare_service.refresh_price_data()
                print("✅ Skincare service refreshed with new price data!")
            except Exception as e:
                print(f"⚠️ Warning: Could not refresh skincare service: {e}")
                print("You may need to restart the Flask application to see updated prices.")
            
        else:
            print("❌ Price comparison scraper failed!")
            print("Error output:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Price comparison scraper timed out!")
        print("This might be due to slow network or rate limiting.")
        print("You can try running it again later.")
        
    except Exception as e:
        print(f"❌ Error running price comparison scraper: {e}")
    
    print()
    print("=" * 50)
    print("🏁 Price comparison process completed!")
    print("💡 You can now use the skincare section with price comparison features.")

if __name__ == "__main__":
    main()





