<<<<<<< HEAD
# SkinNova-Flask
=======
<<<<<<< HEAD
# SkinNova-Flask
=======
<<<<<<< HEAD
# SkinNova-Flask
=======
<<<<<<< HEAD
# SKINNOVA
=======
# SkinNova - Smart Beauty Assistant Platform

SkinNova is a comprehensive beauty assistant platform that provides personalized skincare and makeup recommendations based on users' unique skin profiles. Built with Flask, SQLite, HTML, CSS, and JavaScript.

## Features

### 🌟 Core Features
- **Skin Assessment Quiz**: Identify skin type, concerns, and preferences
- **Makeup Recommendations**: Get tailored makeup suggestions based on skin undertone
- **Color Analysis**: Discover perfect color palettes for clothing and jewelry
- **Price Comparison**: Compare product prices across Amazon, Nykaa, and Sephora
- **Dermatologist Finder**: Locate nearby skin specialists using location services
- **Video Tutorials**: Watch personalized YouTube tutorials based on skin concerns

### 🎨 User Interface
- Modern, responsive design with gradient aesthetics
- Interactive quizzes with progress indicators
- Product filtering and search functionality
- Mobile-first responsive layout
- Smooth animations and transitions

### 🔧 Technical Features
- User authentication and session management
- SQLite database with comprehensive product catalog
- AJAX-powered interactive features
- Price comparison API integration ready
- Google Maps API integration for dermatologist finder
- YouTube API integration for tutorial recommendations

## Technology Stack

- **Backend**: Python Flask 2.3.3
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS with CSS Variables, Flexbox, Grid
- **Icons**: Font Awesome 6.0
- **Fonts**: Inter (Google Fonts)

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### 1. Clone or Download the Project
```bash
# If using git
git clone [repository-url]
cd SkinNova-Flask

# Or download and extract the project folder
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install Flask==2.3.3
pip install requests==2.31.0

# Or install from requirements file (if available)
pip install -r requirements-new.txt
```

### 4. Initialize the Database
```bash
python database.py
```

This will create the SQLite database and populate it with sample products and dermatologist data.

### 5. Run the Application
```bash
python app.py
```

The application will start on `http://127.0.0.1:5000` (or `http://localhost:5000`)

## Project Structure

```
SkinNova-Flask/
│
├── app.py                      # Main Flask application
├── database.py                 # Database setup and sample data
├── requirements-new.txt        # Python dependencies
├── README.md                   # This file
│
├── database/                   # Database files
│   └── skinnova.db            # SQLite database (created after first run)
│
├── static/                     # Static files
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   ├── js/
│   │   └── main.js            # JavaScript functionality
│   └── images/                # Product images (placeholder)
│
└── templates/                  # HTML templates
    ├── base.html              # Base template
    ├── index.html             # Homepage
    ├── login.html             # Login page
    ├── register.html          # Registration page
    ├── dashboard.html         # User dashboard
    ├── skin_quiz.html         # Skin assessment quiz
    └── skincare_recommendations.html  # Product recommendations
```

## Usage Guide

### 1. Create Account
1. Visit the homepage
2. Click "Get Started" or "Register"
3. Fill in your username, email, and password
4. Click "Create Account"

### 2. Take Skin Assessment
1. After logging in, go to your dashboard
2. Click "Start Quiz" on the Skin Assessment card
3. Answer questions about your skin type, concerns, and preferences
4. Submit to get personalized recommendations

### 3. View Recommendations
1. After completing the quiz, you'll be redirected to your skincare recommendations
2. Browse products filtered by your skin profile
3. Use the search and filter options to find specific products
4. Click "Compare Prices" to see pricing across different platforms

### 4. Additional Features
- **Makeup Quiz**: Determine your skin undertone for makeup recommendations
- **Color Analysis**: Find your perfect color palette
- **Find Dermatologists**: Locate nearby specialists (requires location permission)
- **Tutorials**: Watch recommended videos based on your skin concerns

## Customization

### Adding New Products
Edit `database.py` and add products to the `skincare_products` or `makeup_products` lists, then run:
```bash
python database.py
```

### Styling Changes
Modify `static/css/style.css` to customize colors, fonts, and layout. The CSS uses custom properties (variables) for easy theme customization:
```css
:root {
    --primary: #e91e63;      /* Main brand color */
    --secondary: #9c27b0;    /* Secondary color */
    --accent: #00bcd4;       /* Accent color */
    /* ... other variables */
}
```

### Adding New Pages
1. Create a new HTML template in the `templates/` folder
2. Add the route in `app.py`
3. Update navigation in `base.html`

## API Integration

### Price Comparison
The application includes placeholder endpoints for price comparison. To integrate with real APIs:
1. Sign up for e-commerce platform APIs (Amazon Product Advertising API, etc.)
2. Update the `price_compare` route in `app.py`
3. Add API credentials to environment variables

### Google Maps (Dermatologist Finder)
1. Get a Google Maps API key
2. Update the `find_dermatologists` route in `app.py`
3. Add the API key to your environment variables

### YouTube API (Tutorials)
1. Get a YouTube Data API key
2. Update the `tutorials` route in `app.py`
3. Replace sample video data with real YouTube API calls

## Security Considerations

### For Production Deployment:
1. **Change the secret key** in `app.py`:
   ```python
   app.secret_key = 'your-secure-secret-key-here'
   ```

2. **Use environment variables** for sensitive data:
   ```python
   import os
   app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')
   ```

3. **Use a production database** (PostgreSQL, MySQL) instead of SQLite

4. **Enable HTTPS** and secure headers

5. **Implement rate limiting** and input validation

## Troubleshooting

### Common Issues:

**Database errors:**
```bash
# Recreate the database
python database.py
```

**Import errors:**
```bash
# Make sure Flask is installed
pip install Flask==2.3.3
```

**Port already in use:**
```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

**CSS/JS not loading:**
- Make sure Flask is serving static files correctly
- Check browser console for 404 errors
- Clear browser cache

## Contributing

1. Fork the project
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions:
- Check the troubleshooting section above
- Review the code comments for implementation details
- Create an issue in the project repository

## Future Enhancements

- User product reviews and ratings
- Wishlist and favorites functionality
- Social sharing features
- Mobile app development
- Machine learning for better recommendations
- Integration with more e-commerce platforms
- Multi-language support
- Advanced skin analysis using camera/AI

---

**SkinNova** - Your Smart Beauty Assistant Platform 💄✨
>>>>>>> 725b0a4 (Initial Commit)
>>>>>>> ec446c8 (Initial Commit)
>>>>>>> 3459762 (Initial Commit)
>>>>>>> 636395d (Initial Commit)
