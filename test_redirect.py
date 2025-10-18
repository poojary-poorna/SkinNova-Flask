#!/usr/bin/env python3
"""
Test script to verify the makeup recommendation redirect functionality
"""
import requests
import sys

def test_redirect_page():
    """Test if the makeup recommendation redirect page is working"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Test the redirect page
        print("Testing makeup recommendation redirect page...")
        response = requests.get(f"{base_url}/makeup-recommendation-redirect")
        
        if response.status_code == 200:
            print("✅ Redirect page is accessible")
            print(f"   Status code: {response.status_code}")
            
            # Check if the page contains expected content
            content = response.text
            expected_elements = [
                "Get Your Perfect Makeup Recommendations",
                "What You'll Get",
                "Your Beauty Journey Starts Here",
                "Personalized Recommendations",
                "Perfect Color Matches"
            ]
            
            missing_elements = []
            for element in expected_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ All expected content elements found")
            else:
                print("❌ Missing content elements:")
                for element in missing_elements:
                    print(f"   - {element}")
        else:
            print(f"❌ Redirect page not accessible")
            print(f"   Status code: {response.status_code}")
            return False
            
        # Test other related endpoints
        print("\nTesting related endpoints...")
        
        endpoints_to_test = [
            "/makeup-quiz",
            "/makeup-recommendations", 
            "/login",
            "/register"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{base_url}{endpoint}", allow_redirects=False)
                if response.status_code in [200, 302]:  # 302 for login redirects
                    print(f"✅ {endpoint} - Status: {response.status_code}")
                else:
                    print(f"❌ {endpoint} - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the Flask application")
        print("   Make sure the Flask app is running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("SkinNova Makeup Recommendation Redirect Test")
    print("=" * 50)
    
    success = test_redirect_page()
    
    if success:
        print("\n✅ All tests passed!")
        print("\nYou can now access the makeup recommendation redirect page at:")
        print("http://127.0.0.1:5000/makeup-recommendation-redirect")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)