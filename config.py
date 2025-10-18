import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for SkinNova application"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'skinnova_secret_key_2024'
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Database configuration
    DATABASE = 'database/skinnova.db'
    
    # Google API configuration
    GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')
    GOOGLE_GEOCODING_API_KEY = os.environ.get('GOOGLE_GEOCODING_API_KEY')
    
    # API endpoints
    GOOGLE_PLACES_BASE_URL = 'https://maps.googleapis.com/maps/api/place'
    GOOGLE_GEOCODING_BASE_URL = 'https://maps.googleapis.com/maps/api/geocode'
    
    # Default location (Mumbai, India)
    DEFAULT_LAT = 19.0450
    DEFAULT_LNG = 72.8620
    DEFAULT_RADIUS = 5000  # 5km radius
    
    @classmethod
    def validate_google_apis(cls):
        """Validate that Google API keys are configured"""
        if not cls.GOOGLE_PLACES_API_KEY:
            print("⚠️  WARNING: GOOGLE_PLACES_API_KEY not found in environment variables")
            print("   Please set your Google Places API key in .env file")
            return False
        if not cls.GOOGLE_GEOCODING_API_KEY:
            print("⚠️  WARNING: GOOGLE_GEOCODING_API_KEY not found in environment variables")
            print("   Please set your Google Geocoding API key in .env file")
            return False
        return True





