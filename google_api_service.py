import requests
import json
from typing import List, Dict, Optional, Tuple
from config import Config

class GooglePlacesService:
    """Service class for Google Places API integration"""
    
    def __init__(self):
        self.places_api_key = Config.GOOGLE_PLACES_API_KEY
        self.geocoding_api_key = Config.GOOGLE_GEOCODING_API_KEY
        self.places_base_url = Config.GOOGLE_PLACES_BASE_URL
        self.geocoding_base_url = Config.GOOGLE_GEOCODING_BASE_URL
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to latitude and longitude coordinates
        
        Args:
            address: Address string to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not self.geocoding_api_key:
            return None
            
        try:
            url = f"{self.geocoding_base_url}/json"
            params = {
                'address': address,
                'key': self.geocoding_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return (location['lat'], location['lng'])
            else:
                print(f"Geocoding failed: {data.get('status', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            print(f"Geocoding request failed: {e}")
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def search_dermatologists(self, lat: float, lng: float, radius: int = 5000) -> List[Dict]:
        """
        Search for dermatologists near the given coordinates
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters (max 50000)
            
        Returns:
            List of dermatologist information dictionaries
        """
        if not self.places_api_key:
            return self._get_fallback_dermatologists(lat, lng)
        
        try:
            # Search for dermatologists using Google Places API
            url = f"{self.places_base_url}/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': min(radius, 50000),  # Google's max radius is 50000m
                'type': 'doctor',
                'keyword': 'dermatologist',
                'key': self.places_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                dermatologists = []
                for place in data['results']:
                    dermatologist = self._format_dermatologist_data(place, lat, lng)
                    if dermatologist:
                        dermatologists.append(dermatologist)
                
                # Sort by distance
                dermatologists.sort(key=lambda x: x.get('distance', float('inf')))
                return dermatologists[:10]  # Return top 10 results
            else:
                print(f"Places API error: {data.get('status', 'Unknown error')}")
                return self._get_fallback_dermatologists(lat, lng)
                
        except requests.RequestException as e:
            print(f"Places API request failed: {e}")
            return self._get_fallback_dermatologists(lat, lng)
        except Exception as e:
            print(f"Places API error: {e}")
            return self._get_fallback_dermatologists(lat, lng)
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific place
        
        Args:
            place_id: Google Places place ID
            
        Returns:
            Detailed place information or None if failed
        """
        if not self.places_api_key:
            return None
            
        try:
            url = f"{self.places_base_url}/details/json"
            params = {
                'place_id': place_id,
                'fields': 'name,formatted_address,formatted_phone_number,rating,reviews,opening_hours,website',
                'key': self.places_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                return data['result']
            else:
                print(f"Place details API error: {data.get('status', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            print(f"Place details request failed: {e}")
            return None
        except Exception as e:
            print(f"Place details error: {e}")
            return None
    
    def _format_dermatologist_data(self, place: Dict, user_lat: float, user_lng: float) -> Optional[Dict]:
        """
        Format Google Places API result into dermatologist data
        
        Args:
            place: Place data from Google Places API
            user_lat: User's latitude for distance calculation
            user_lng: User's longitude for distance calculation
            
        Returns:
            Formatted dermatologist data or None if invalid
        """
        try:
            # Calculate distance
            distance = self._calculate_distance(
                user_lat, user_lng,
                place['geometry']['location']['lat'],
                place['geometry']['location']['lng']
            )
            
            # Extract name and clean it
            name = place.get('name', 'Dermatology Clinic')
            
            # Check if it's actually a dermatologist (basic keyword check)
            name_lower = name.lower()
            if not any(keyword in name_lower for keyword in ['dermat', 'skin', 'clinic', 'medical', 'health']):
                return None
            
            return {
                'name': name,
                'address': place.get('vicinity', 'Address not available'),
                'phone': place.get('formatted_phone_number', 'N/A'),
                'rating': place.get('rating', None),
                'lat': place['geometry']['location']['lat'],
                'lng': place['geometry']['location']['lng'],
                'distance': distance,
                'place_id': place.get('place_id'),
                'is_open': place.get('opening_hours', {}).get('open_now', None),
                'price_level': place.get('price_level', None)
            }
            
        except Exception as e:
            print(f"Error formatting dermatologist data: {e}")
            return None
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lng1: First coordinate
            lat2, lng2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        import math
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        return c * r
    
    def _get_fallback_dermatologists(self, lat: float, lng: float) -> List[Dict]:
        """
        Get fallback dermatologist data when API is unavailable
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            List of fallback dermatologist data
        """
        return [
            {
                'name': 'Dermatology Clinic',
                'address': 'Near your location',
                'phone': 'N/A',
                'rating': None,
                'lat': lat,
                'lng': lng,
                'distance': 0.0,
                'place_id': None,
                'is_open': None,
                'price_level': None
            }
        ]

# Create a global instance
google_places_service = GooglePlacesService()





