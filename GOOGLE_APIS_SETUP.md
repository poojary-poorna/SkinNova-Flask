# 🌟 Google APIs Integration for SkinNova

This document explains how to set up and use Google's free APIs for real-time dermatologist location services in SkinNova.

## 🚀 Quick Start

### 1. Run the Setup Script
```bash
python setup_google_apis.py
```

### 2. Configure Your API Keys
Follow the instructions provided by the setup script to get your Google API keys.

### 3. Run the Application
```bash
python run.py
```

## 🔑 Required Google APIs

### Google Places API
- **Purpose**: Search for dermatologists near a location
- **Free Tier**: $200/month credit (approximately 40,000 requests)
- **Features**: 
  - Nearby search for medical facilities
  - Place details (ratings, hours, contact info)
  - Real-time business status

### Google Geocoding API
- **Purpose**: Convert addresses to coordinates
- **Free Tier**: $200/month credit (approximately 40,000 requests)
- **Features**:
  - Address to lat/lng conversion
  - Reverse geocoding
  - Address validation

## 🛠️ Setup Instructions

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your project ID

### Step 2: Enable APIs
1. Navigate to "APIs & Services" → "Library"
2. Search and enable:
   - **Places API**
   - **Geocoding API**

### Step 3: Create API Key
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the generated API key

### Step 4: Secure Your API Key
1. Click on the API key to edit it
2. Set **Application restrictions**:
   - Choose "HTTP referrers"
   - Add: `http://localhost:5000/*`
   - Add: `https://yourdomain.com/*` (for production)
3. Set **API restrictions**:
   - Choose "Restrict key"
   - Select "Places API" and "Geocoding API"

### Step 5: Configure Environment
1. Copy `.env.example` to `.env`
2. Add your API keys:
```env
GOOGLE_PLACES_API_KEY=your_actual_places_api_key
GOOGLE_GEOCODING_API_KEY=your_actual_geocoding_api_key
```

## 🎯 Features

### Real-Time Location Services
- **GPS Location**: Use device GPS for precise location
- **Address Search**: Search by city, zip code, or full address
- **Auto-Refresh**: Results update every 5 minutes
- **Fallback**: Graceful fallback when location services fail

### Enhanced Dermatologist Search
- **Google Places Integration**: Real dermatologist data from Google
- **Ratings & Reviews**: Display Google ratings and reviews
- **Business Hours**: Show if clinic is currently open/closed
- **Contact Information**: Phone numbers and addresses
- **Distance Calculation**: Accurate distance from user location

### Advanced UI Features
- **Location Display**: Show current search location
- **Status Badges**: Open/Closed status indicators
- **Rating Badges**: Google ratings display
- **More Info**: Detailed place information
- **Directions**: Direct Google Maps integration

## 🔧 API Endpoints

### `/api/dermatologists`
Search for dermatologists near a location.

**Parameters:**
- `lat` (float): Latitude
- `lng` (float): Longitude
- `address` (string): Address to geocode
- `radius` (int): Search radius in meters (default: 5000)

**Example:**
```javascript
// Using coordinates
fetch('/api/dermatologists?lat=19.0450&lng=72.8620&radius=5000')

// Using address
fetch('/api/dermatologists?address=Mumbai, India&radius=10000')
```

### `/api/geocode`
Convert address to coordinates.

**Parameters:**
- `address` (string): Address to geocode

**Example:**
```javascript
fetch('/api/geocode?address=New York, NY')
```

### `/api/place-details`
Get detailed information about a specific place.

**Parameters:**
- `place_id` (string): Google Places place ID

**Example:**
```javascript
fetch('/api/place-details?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4')
```

## 💰 Cost Management

### Free Tier Limits
- **Places API**: ~40,000 requests/month
- **Geocoding API**: ~40,000 requests/month
- **Total**: ~80,000 requests/month free

### Cost Optimization
1. **Caching**: Results are cached for 5 minutes
2. **Radius Limiting**: Default 5km radius reduces API calls
3. **Error Handling**: Graceful fallbacks prevent unnecessary calls
4. **User Location**: Only search when user requests

### Monitoring Usage
1. Go to Google Cloud Console
2. Navigate to "APIs & Services" → "Quotas"
3. Monitor your API usage
4. Set up billing alerts

## 🚨 Error Handling

### Common Issues
1. **API Key Not Set**: Application shows warning message
2. **Quota Exceeded**: Falls back to sample data
3. **Network Error**: Shows error message to user
4. **Invalid Address**: Prompts user to try again

### Fallback Mechanisms
- **Sample Data**: Shows featured dermatologists when API fails
- **Default Location**: Uses Mumbai, India as fallback
- **Error Messages**: Clear error messages for users
- **Retry Logic**: Automatic retry for transient errors

## 🔒 Security Best Practices

### API Key Security
1. **Environment Variables**: Never commit API keys to code
2. **Restrictions**: Use HTTP referrer and API restrictions
3. **Rotation**: Regularly rotate API keys
4. **Monitoring**: Monitor API usage for anomalies

### Production Deployment
1. **HTTPS Only**: Use HTTPS in production
2. **Domain Restrictions**: Restrict to your domain only
3. **Rate Limiting**: Implement rate limiting
4. **Logging**: Log API usage for monitoring

## 🧪 Testing

### Test Your Setup
```bash
# Test geocoding
curl "http://localhost:5000/api/geocode?address=New York, NY"

# Test dermatologist search
curl "http://localhost:5000/api/dermatologists?lat=40.7128&lng=-74.0060"

# Test place details (replace with actual place_id)
curl "http://localhost:5000/api/place-details?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4"
```

### Validation Script
```bash
python setup_google_apis.py
```

## 📱 Mobile Support

### Geolocation API
- **High Accuracy**: Uses GPS when available
- **Timeout Handling**: 10-second timeout with fallback
- **Permission Handling**: Graceful permission request
- **Offline Support**: Cached results when offline

### Responsive Design
- **Mobile-First**: Optimized for mobile devices
- **Touch-Friendly**: Large buttons and touch targets
- **Fast Loading**: Optimized for mobile networks
- **Progressive Enhancement**: Works without JavaScript

## 🎨 Theme Integration

### Dark Theme (Neon)
- **Glowing Effects**: Neon-style location indicators
- **Electric Colors**: Cyan and magenta accents
- **Animated Elements**: Pulsing location buttons
- **High Contrast**: Easy to read in dark environments

### Light Theme (Pastel)
- **Soft Colors**: Pastel pink and mint green
- **Subtle Shadows**: Gentle depth effects
- **Clean Design**: Minimalist location interface
- **Warm Feel**: Inviting and friendly appearance

## 🚀 Future Enhancements

### Planned Features
1. **Map Integration**: Interactive Google Maps display
2. **Appointment Booking**: Direct booking integration
3. **Reviews Display**: Show Google reviews
4. **Photo Gallery**: Display clinic photos
5. **Real-Time Updates**: WebSocket for live updates

### API Extensions
1. **Directions API**: Turn-by-turn directions
2. **Street View API**: Virtual clinic tours
3. **Maps JavaScript API**: Interactive maps
4. **Places Autocomplete**: Smart address suggestions

## 📞 Support

### Troubleshooting
1. **Check API Keys**: Ensure keys are correctly set
2. **Verify Billing**: Check Google Cloud billing
3. **Test Endpoints**: Use curl to test API endpoints
4. **Check Logs**: Review application logs for errors

### Getting Help
1. **Google Cloud Support**: For API-related issues
2. **SkinNova Documentation**: For application-specific help
3. **GitHub Issues**: For bug reports and feature requests
4. **Community Forum**: For user discussions

---

**Happy coding! 🌟** Your SkinNova application now has powerful real-time location services powered by Google's APIs.





