#!/usr/bin/env python3
"""
Setup script for Google APIs configuration
This script helps you set up Google Places API and Geocoding API keys
"""

import os
import sys

def create_env_file():
    """Create .env file with Google API configuration"""
    env_content = """# Google API Configuration
# Get your API keys from: https://console.cloud.google.com/

# Google Places API Key (Required for dermatologist search)
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here

# Google Geocoding API Key (Required for address to coordinates conversion)
GOOGLE_GEOCODING_API_KEY=your_google_geocoding_api_key_here

# Flask Environment
FLASK_ENV=development
SECRET_KEY=skinnova_secret_key_2024
"""
    
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("❌ Setup cancelled.")
            return False
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    return True

def print_setup_instructions():
    """Print detailed setup instructions"""
    print("\n" + "="*60)
    print("🔧 GOOGLE APIS SETUP INSTRUCTIONS")
    print("="*60)
    print()
    print("1. 🌐 Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. 📝 Create a new project or select existing one")
    print()
    print("3. 🔑 Enable the following APIs:")
    print("   • Places API")
    print("   • Geocoding API")
    print()
    print("4. 🔐 Create API credentials:")
    print("   • Go to 'Credentials' in the left menu")
    print("   • Click 'Create Credentials' → 'API Key'")
    print("   • Copy the generated API key")
    print()
    print("5. 🛡️  Secure your API key:")
    print("   • Click on the API key to edit it")
    print("   • Set 'Application restrictions' to 'HTTP referrers'")
    print("   • Add your domain: http://localhost:5000/*")
    print("   • Set 'API restrictions' to 'Restrict key'")
    print("   • Select 'Places API' and 'Geocoding API'")
    print()
    print("6. 📝 Update your .env file:")
    print("   • Replace 'your_google_places_api_key_here' with your Places API key")
    print("   • Replace 'your_google_geocoding_api_key_here' with your Geocoding API key")
    print()
    print("7. 🚀 Run the application:")
    print("   python run.py")
    print()
    print("="*60)

def validate_setup():
    """Validate the current setup"""
    print("\n🔍 VALIDATING SETUP...")
    print("-" * 30)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    # Check if config can be loaded
    try:
        from config import Config
        places_key = Config.GOOGLE_PLACES_API_KEY
        geocoding_key = Config.GOOGLE_GEOCODING_API_KEY
        
        if not places_key or places_key == 'your_google_places_api_key_here':
            print("❌ Google Places API key not configured")
            return False
        
        if not geocoding_key or geocoding_key == 'your_google_geocoding_api_key_here':
            print("❌ Google Geocoding API key not configured")
            return False
        
        print("✅ Google API keys are configured")
        return True
        
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        return False

def main():
    """Main setup function"""
    print("🌟 SkinNova - Google APIs Setup")
    print("=" * 40)
    
    # Create .env file
    if create_env_file():
        print_setup_instructions()
        
        # Wait for user to configure
        input("\nPress Enter after you've configured your API keys...")
        
        # Validate setup
        if validate_setup():
            print("\n🎉 Setup completed successfully!")
            print("You can now run: python run.py")
        else:
            print("\n⚠️  Setup incomplete. Please check your configuration.")
    else:
        print("\n❌ Setup failed.")

if __name__ == "__main__":
    main()





