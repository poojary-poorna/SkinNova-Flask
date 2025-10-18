from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import requests
import json
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from config import Config
from google_api_service import google_places_service
from advanced_skincare_service import advanced_skincare_service
from functools import wraps

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Database configuration
DATABASE = Config.DATABASE

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure tables exist as early as possible to avoid runtime errors
try:
    from database import create_tables as _create_tables_early
    _create_tables_early()
except Exception:
    pass

def ensure_user_role_column():
    """Ensure the users table has a 'role' column (default 'user')."""
    try:
        conn = get_db_connection()
        cols = conn.execute("PRAGMA table_info(users)").fetchall()
        colnames = {c[1] for c in cols}
        if 'role' not in colnames:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            conn.commit()
        conn.close()
    except Exception:
        # If users table does not exist yet, it will be created later by database init paths
        pass

ensure_user_role_column()

def is_admin_configured() -> bool:
    """Return True if at least one admin user exists."""
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT COUNT(1) AS c FROM users WHERE role = 'admin'").fetchone()
        conn.close()
        return (row and row['c'] and int(row['c']) > 0)
    except Exception:
        return False

@app.context_processor
def inject_flags():
    """Inject global flags for templates."""
    try:
        return {'admin_setup_needed': not is_admin_configured()}
    except Exception:
        return {'admin_setup_needed': False}

def init_db():
    """Initialize database tables"""
    from database import create_tables, populate_sample_data
    create_tables()
    populate_sample_data()

@app.before_request
def ensure_db_ready():
    """Initialize DB tables once per process for Flask 3.x (no before_first_request)."""
    if not app.config.get('DB_READY'):
        try:
            from database import create_tables
            create_tables()
        except Exception:
            pass
        app.config['DB_READY'] = True

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapper

# Admin utilities
def save_uploaded_file(file_storage, subdir='uploads'):
    os.makedirs(os.path.join('static', subdir), exist_ok=True)
    filename = secure_filename(file_storage.filename)
    rel_path = os.path.join(subdir, filename).replace('\\','/')
    abs_path = os.path.join('static', rel_path)
    file_storage.save(abs_path)
    return f"/static/{rel_path}"

def get_product_recommendations(skin_type, skin_concerns, preferences):
    """Get skincare product recommendations based on user profile"""
    conn = get_db_connection()
    
    # Build query based on skin profile
    query = """
    SELECT * FROM products 
    WHERE category = 'skincare' 
    AND (suitable_skin_types LIKE ? OR suitable_skin_types LIKE 'all')
    """
    params = [f'%{skin_type}%']
    
    # Add concern-based filtering
    if skin_concerns:
        concern_conditions = []
        for concern in skin_concerns:
            concern_conditions.append("target_concerns LIKE ?")
            params.append(f'%{concern}%')
        if concern_conditions:
            query += " AND (" + " OR ".join(concern_conditions) + ")"
    
    query += " ORDER BY rating DESC LIMIT 10"
    
    products = conn.execute(query, params).fetchall()
    conn.close()
    return products

def get_makeup_recommendations(skin_undertone, preferences):
    """Get makeup product recommendations using makeup_catalog (no undertone filter available).
    Returns rows with fields similar to products for template compatibility.
    """
    conn = get_db_connection()
    # Optionally filter by categories from preferences if available
    category_filter = None
    if preferences:
        # Map common preference keywords to categories
        pref_map = {
            'lipstick': 'lipstick', 'lips': 'lipstick',
            'foundation': 'foundation',
            'eyeshadow': 'eyeshadow', 'eye': 'eyeshadow',
            'blush': 'blush',
            'mascara': 'mascara'
        }
        for p in preferences:
            key = p.lower()
            if key in pref_map:
                category_filter = pref_map[key]
                break
    if category_filter:
        rows = conn.execute('SELECT * FROM makeup_catalog WHERE category = ? ORDER BY brand, name', (category_filter,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM makeup_catalog ORDER BY category, brand, name').fetchall()
    conn.close()
    return rows

def get_color_analysis_results(answers):
    """Analyze color preferences and return color palette recommendations"""
    # Simple color analysis logic
    score_warm = 0
    score_cool = 0
    score_neutral = 0
    
    # Analyze answers (simplified logic)
    for answer in answers:
        if answer in ['gold', 'yellow', 'orange', 'red', 'brown']:
            score_warm += 1
        elif answer in ['silver', 'blue', 'purple', 'pink', 'black']:
            score_cool += 1
        else:
            score_neutral += 1
    
    if score_warm > score_cool and score_warm > score_neutral:
        return {
            'season': 'warm',
            'colors': ['Coral', 'Peach', 'Gold', 'Olive Green', 'Rust', 'Cream'],
            'avoid': ['Icy Blue', 'Silver', 'Pure White', 'Fuchsia']
        }
    elif score_cool > score_warm and score_cool > score_neutral:
        return {
            'season': 'cool',
            'colors': ['Navy Blue', 'Silver', 'Pure White', 'Emerald', 'Fuchsia', 'Black'],
            'avoid': ['Orange', 'Gold', 'Yellow', 'Rust']
        }
    else:
        return {
            'season': 'neutral',
            'colors': ['Soft Pink', 'Grey', 'Beige', 'Lavender', 'Sage Green', 'Dusty Blue'],
            'avoid': ['Very Bright Colors', 'Very Dark Colors']
        }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        
        # Check if user already exists
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            flash('Username or email already exists')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        conn.execute(
            'INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)',
            (username, email, hash_password(password), 'user', datetime.now())
        )
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password_hash = ?',
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role'] if 'role' in user.keys() else 'user'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/login-user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute(
            """
            SELECT * FROM users 
            WHERE username = ? AND password_hash = ? 
              AND (role IS NULL OR role != 'admin')
            """,
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role'] if 'role' in user.keys() else 'user'
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid user credentials')
    return render_template('login_user.html')

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password_hash = ? AND role = \"admin\"',
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials')
    return render_template('login_admin.html')

@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    """One-time admin registration. Disabled automatically once an admin exists."""
    if is_admin_configured():
        flash('Admin already configured. Please use Admin Login.')
        return redirect(url_for('login_admin'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip() or None
        password = request.form.get('password','')
        if not username or not password:
            flash('Username and password are required')
            return render_template('setup_admin.html')
        conn = get_db_connection()
        # prevent duplicate username/email
        existing = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing:
            conn.close()
            flash('Username or email already exists')
            return render_template('setup_admin.html')
        conn.execute(
            'INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)',
            (username, email, hash_password(password), 'admin', datetime.now())
        )
        conn.commit()
        conn.close()
        flash('Admin account created. You can now log in as admin.')
        return redirect(url_for('login_admin'))
    return render_template('setup_admin.html')

@app.route('/register-admin')
def register_admin_alias():
    """Alias to the one-time admin setup page. If admin exists, go to admin login."""
    if is_admin_configured():
        return redirect(url_for('login_admin'))
    return redirect(url_for('setup_admin'))

@app.route('/reset-admin', methods=['GET'])
def reset_admin_confirm():
    """Confirmation page to reset admin accounts."""
    return render_template('reset_admin.html', admin_exists=is_admin_configured())

@app.route('/reset-admin', methods=['POST'])
def reset_admin_execute():
    """Delete all existing admin users and redirect to setup-admin."""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE role = 'admin'")
        conn.commit()
        conn.close()
        session.clear()
        flash('All admin accounts removed. Please create a new admin.')
    except Exception as e:
        flash(f'Failed to reset admins: {e}')
    return redirect(url_for('setup_admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user profile data
    conn = get_db_connection()
    user_profile = conn.execute(
        'SELECT * FROM user_profiles WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    return render_template('dashboard.html', user_profile=user_profile)

@app.route('/api/save-theme', methods=['POST'])
def save_theme():
    """Save user's theme preference"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    theme = data.get('theme', 'light')
    
    if theme not in ['light', 'dark']:
        return jsonify({'error': 'Invalid theme'}), 400
    
    try:
        conn = get_db_connection()
        # Update user profile with theme preference
        conn.execute(
            '''UPDATE user_profiles SET theme_preference = ?, updated_at = ?
               WHERE user_id = ?''',
            (theme, datetime.now(), session['user_id'])
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'theme': theme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/photo-color-analysis')
def photo_color_analysis():
    """Photo-based color analysis page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('photo_color_analysis.html')


@app.route('/skin-quiz', methods=['GET', 'POST'])
def skin_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        skin_type = request.form['skin_type']
        skin_concerns = request.form.getlist('skin_concerns')
        preferences = request.form.getlist('preferences')
        
        # Save quiz results
        conn = get_db_connection()
        
        # Check if profile exists
        existing_profile = conn.execute(
            'SELECT id FROM user_profiles WHERE user_id = ?',
            (session['user_id'],)
        ).fetchone()
        
        if existing_profile:
            conn.execute(
                '''UPDATE user_profiles 
                   SET skin_type = ?, skin_concerns = ?, preferences = ?, updated_at = ?
                   WHERE user_id = ?''',
                (skin_type, ','.join(skin_concerns), ','.join(preferences), 
                 datetime.now(), session['user_id'])
            )
        else:
            conn.execute(
                '''INSERT INTO user_profiles 
                   (user_id, skin_type, skin_concerns, preferences, created_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (session['user_id'], skin_type, ','.join(skin_concerns), 
                 ','.join(preferences), datetime.now())
            )
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('skincare_recommendations'))
    
    return render_template('skin_quiz.html')

@app.route('/skincare-recommendations')
def skincare_recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user profile
    conn = get_db_connection()
    user_profile = conn.execute(
        'SELECT * FROM user_profiles WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if not user_profile:
        return redirect(url_for('skin_quiz'))
    
    # Get recommendations
    skin_concerns = user_profile['skin_concerns'].split(',') if user_profile['skin_concerns'] else []
    preferences = user_profile['preferences'].split(',') if user_profile['preferences'] else []
    
    recommendations = get_product_recommendations(
        user_profile['skin_type'], 
        skin_concerns, 
        preferences
    )
    
    return render_template('skincare_recommendations.html', 
                         recommendations=recommendations,
                         user_profile=user_profile)

@app.route('/makeup-quiz', methods=['GET', 'POST'])
def makeup_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        skin_undertone = request.form['skin_undertone']
        preferences = request.form.getlist('makeup_preferences')
        
        # Update or create user profile
        conn = get_db_connection()
        
        # Check if profile exists
        existing_profile = conn.execute(
            'SELECT id FROM user_profiles WHERE user_id = ?',
            (session['user_id'],)
        ).fetchone()
        
        if existing_profile:
            # Update existing profile
            conn.execute(
                '''UPDATE user_profiles 
                   SET skin_undertone = ?, makeup_preferences = ?, updated_at = ?
                   WHERE user_id = ?''',
                (skin_undertone, ','.join(preferences), datetime.now(), session['user_id'])
            )
        else:
            # Create new profile with makeup data
            conn.execute(
                '''INSERT INTO user_profiles 
                   (user_id, skin_undertone, makeup_preferences, created_at)
                   VALUES (?, ?, ?, ?)''',
                (session['user_id'], skin_undertone, ','.join(preferences), datetime.now())
            )
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('makeup_recommendations'))
    
    return render_template('makeup_quiz.html')

@app.route('/makeup-recommendation-redirect')
def makeup_recommendation_redirect():
    """Redirect page for makeup recommendations"""
    return render_template('makeup_recommendation_redirect.html')

@app.route('/makeup-recommendations')
def makeup_recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user profile
    conn = get_db_connection()
    user_profile = conn.execute(
        'SELECT * FROM user_profiles WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if not user_profile or not user_profile['skin_undertone']:
        return redirect(url_for('makeup_quiz'))
    
    preferences = user_profile['makeup_preferences'].split(',') if user_profile['makeup_preferences'] else []
    
    recommendations = get_makeup_recommendations(
        user_profile['skin_undertone'], 
        preferences
    )
    
    return render_template('makeup_recommendations.html', 
                         recommendations=recommendations,
                         user_profile=user_profile)

@app.route('/color-analysis', methods=['GET', 'POST'])
def color_analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Collect quiz answers
        answers = []
        for i in range(1, 11):  # Assuming 10 questions
            answer = request.form.get(f'question_{i}')
            if answer:
                answers.append(answer)
        
        # Analyze colors
        results = get_color_analysis_results(answers)
        
        # Save results
        conn = get_db_connection()
        conn.execute(
            '''UPDATE user_profiles 
               SET color_season = ?, color_palette = ?, updated_at = ?
               WHERE user_id = ?''',
            (results['season'], json.dumps(results), datetime.now(), session['user_id'])
        )
        conn.commit()
        conn.close()
        
        return render_template('color_results.html', results=results)
    
    return render_template('color_analysis.html')

@app.route('/find-dermatologists')
def find_dermatologists():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dermatologists.html')

def _build_price_for(name: str):
    # Try canonical mapping first
    prices = PRICE_DATA.get(name)
    if prices:
        return prices
    # Unknown -> no prices
    return {'amazon': None, 'nykaa': None, 'flipkart': None}

def _infer_category(n: str) -> str:
    n = n.lower()
    if any(k in n for k in ['facewash','face wash','cleanser','foam','gel']):
        return 'Face Wash'
    if any(k in n for k in ['moisturizer','cream','lotion','gel-cream']):
        return 'Moisturizer'
    if 'serum' in n:
        return 'Serum'
    if 'toner' in n:
        return 'Toner'
    return 'Skincare'

@app.route('/skincare-products')
def skincare_products():
    # Read filters
    q = (request.args.get('q') or '').strip().lower()
    category = (request.args.get('category') or '').strip()
    skin_type = (request.args.get('skin_type') or '').strip()
    concern = (request.args.get('concern') or '').strip()
    price = (request.args.get('price') or '').strip()  # e.g. 'low', 'mid', 'high'

    base = os.path.join('static','images')
    items = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            low = name.lower()
            if not low.endswith(('.jpg','.jpeg','.png','.webp','.gif')):
                continue
            display_name = _normalize_name(name).replace('-', ' ').replace('_', ' ').title()
            canonical = _canonical_product_for_filename(name)
            cat = _infer_category(display_name)
            prices = _build_price_for(canonical)
            numeric = {k: v for k, v in prices.items() if isinstance(v, (int, float))}
            lowest_site = min(numeric, key=numeric.get) if numeric else None
            items.append({
                'name': display_name,
                'canonical': canonical,
                'category': cat,
                'image_url': f"/static/images/{name}",
                'prices': prices,
                'lowest': lowest_site,
                'links': _build_buy_links(canonical),
            })

    # Apply basic filtering
    def in_price_bucket(p):
        if not price:
            return True
        # define buckets by lowest available
        numeric = [v for v in (p['prices'].get('amazon'), p['prices'].get('nykaa'), p['prices'].get('flipkart')) if isinstance(v, (int,float))]
        if not numeric:
            return price == ''
        m = min(numeric)
        if price == 'low':
            return m < 200
        if price == 'mid':
            return 200 <= m <= 400
        if price == 'high':
            return m > 400
        return True

    filtered = []
    for it in items:
        if q and q not in it['name'].lower():
            continue
        if category and it['category'] != category:
            continue
        # skin_type/concern are placeholders for now; keep if provided
        if not in_price_bucket(it):
            continue
        filtered.append(it)

    # Build filter options from data
    categories = sorted({it['category'] for it in items})
    return render_template('skincare_products2.html',
                           items=filtered,
                           categories=categories,
                           q=q, category=category, skin_type=skin_type, concern=concern, price=price)

@app.route('/admin/replace-skincare', methods=['POST'])
@admin_required
def admin_replace_skincare():
    flash('Skincare scrapers are disabled. Use manual image uploads and product CRUD instead.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/load-skincare-seed')
@admin_required
def admin_load_skincare_seed():
    flash('Skincare seed loading is disabled. Manage products manually in Admin > Products.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/enrich-nykaa-images')
@admin_required
def admin_enrich_nykaa_images():
    flash('External image enrichment is disabled for skincare. Use manual images instead.')
    return redirect(url_for('admin_dashboard'))

# ----------------------
# Admin: Skincare purge & manual images
# ----------------------
@app.route('/admin/skincare/purge', methods=['POST'])
@admin_required
def admin_skincare_purge():
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE category='skincare' OR subcategory IN ('facewash','toner','moisturizer','serum')")
    conn.commit(); conn.close()
    flash('All skincare products deleted.')
    return redirect(url_for('admin_products'))

@app.route('/admin/skincare/images', methods=['GET','POST'])
@admin_required
def admin_skincare_images():
    # upload to static/images/skincare_manual
    if request.method == 'POST':
        files = request.files.getlist('images')
        saved = 0
        for f in files:
            if f and f.filename:
                url = save_uploaded_file(f, subdir='images/skincare_manual')
                saved += 1
        flash(f'Uploaded {saved} image(s).')
        return redirect(url_for('admin_skincare_images'))
    # list existing files
    base = os.path.join('static','images','skincare_manual')
    images = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            if name.lower().endswith(('.png','.jpg','.jpeg','.webp','.gif')):
                images.append(f'/static/images/skincare_manual/{name}')
    return render_template('admin_skincare_images.html', images=images)

@app.route('/admin/upload-product-image', methods=['GET', 'POST'])
@admin_required
def upload_product_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        file = request.files.get('image')
        if not sku or not file or file.filename == '':
            flash('Please provide SKU and select an image file')
            return render_template('admin_upload_image.html')
        ext = os.path.splitext(file.filename)[1].lower()
        allowed = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        if ext not in allowed:
            flash('Unsupported file type. Use JPG, PNG, WEBP, or GIF')
            return render_template('admin_upload_image.html')
        os.makedirs(os.path.join('static', 'images', 'makeup'), exist_ok=True)
        filename = secure_filename(f"{sku}{ext}")
        rel_path = os.path.join('images', 'makeup', filename).replace('\\', '/')
        abs_path = os.path.join('static', rel_path)
        file.save(abs_path)
        # Update DB: prefer image_url with local static path for immediate render, and keep image_path too
        conn = get_db_connection()
        conn.execute('''UPDATE makeup_catalog SET image_path = ?, image_url = ? WHERE sku = ?''',
                     (rel_path, f"/static/{rel_path}", sku))
        conn.commit()
        conn.close()
        flash(f'Image uploaded for {sku}!')
        return redirect(url_for('makeup_recommendations'))
    return render_template('admin_upload_image.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin-only dashboard with management links."""
    return render_template('admin_dashboard.html')

# ----------------------
# Admin: Products CRUD
# ----------------------
@app.route('/admin/products')
@admin_required
def admin_products():
    q = request.args.get('q','').strip()
    category = request.args.get('category','').strip()
    skin_type = request.args.get('skin_type','').strip()
    concern = request.args.get('concern','').strip()
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if q:
        sql += " AND (name LIKE ? OR brand LIKE ?)"; params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND (category = ? OR subcategory = ?)"; params += [category, category]
    if skin_type:
        sql += " AND (suitable_skin_types LIKE ?)"; params += [f"%{skin_type}%"]
    if concern:
        sql += " AND (target_concerns LIKE ?)"; params += [f"%{concern}%"]
    sql += " ORDER BY created_at DESC"
    conn = get_db_connection()
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return render_template('admin_products.html', products=rows, q=q, category=category, skin_type=skin_type, concern=concern)

@app.route('/admin/products/new', methods=['GET','POST'])
@admin_required
def admin_product_new():
    if request.method == 'POST':
        form = request.form
        image_url = form.get('image_url') or None
        if 'image_file' in request.files and request.files['image_file'] and request.files['image_file'].filename:
            image_url = save_uploaded_file(request.files['image_file'], subdir='images/products')
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO products (name, brand, category, subcategory, description, price, rating,
                                  suitable_skin_types, target_concerns, suitable_undertones, ingredients,
                                  image_url, amazon_url, nykaa_url, sephora_url)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            form.get('name'), form.get('brand'), form.get('category'), form.get('subcategory'), form.get('description'),
            float(form.get('price') or 0), None,
            form.get('suitable_skin_types'), form.get('target_concerns'), form.get('suitable_undertones'), form.get('ingredients'),
            image_url, form.get('amazon_url'), form.get('nykaa_url'), form.get('sephora_url') or form.get('flipkart_url')
        ))
        conn.commit(); conn.close()
        flash('Product added')
        return redirect(url_for('admin_products'))
    return render_template('admin_product_form.html', mode='new', product=None)

@app.route('/admin/products/<int:pid>/edit', methods=['GET','POST'])
@admin_required
def admin_product_edit(pid):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=?', (pid,)).fetchone()
    if not product:
        conn.close(); flash('Product not found'); return redirect(url_for('admin_products'))
    if request.method == 'POST':
        form = request.form
        image_url = form.get('image_url') or product['image_url']
        if 'image_file' in request.files and request.files['image_file'] and request.files['image_file'].filename:
            image_url = save_uploaded_file(request.files['image_file'], subdir='images/products')
        conn.execute('''
            UPDATE products SET name=?, brand=?, category=?, subcategory=?, description=?, price=?,
                               suitable_skin_types=?, target_concerns=?, suitable_undertones=?, ingredients=?,
                               image_url=?, amazon_url=?, nykaa_url=?, sephora_url=?
            WHERE id=?
        ''', (
            form.get('name'), form.get('brand'), form.get('category'), form.get('subcategory'), form.get('description'),
            float(form.get('price') or 0),
            form.get('suitable_skin_types'), form.get('target_concerns'), form.get('suitable_undertones'), form.get('ingredients'),
            image_url, form.get('amazon_url'), form.get('nykaa_url'), form.get('sephora_url') or form.get('flipkart_url'), pid
        ))
        conn.commit(); conn.close()
        flash('Product updated')
        return redirect(url_for('admin_products'))
    conn.close()
    return render_template('admin_product_form.html', mode='edit', product=product)

@app.route('/admin/products/<int:pid>/delete', methods=['POST'])
@admin_required
def admin_product_delete(pid):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id=?', (pid,))
    conn.commit(); conn.close()
    flash('Product deleted')
    return redirect(url_for('admin_products'))

# ----------------------
# Admin: Reviews
# ----------------------
@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    product_id = request.args.get('product_id')
    conn = get_db_connection()
    if product_id:
        rows = conn.execute('''SELECT pr.*, p.name as product_name, u.username as user_name
                               FROM product_reviews pr
                               JOIN products p ON pr.product_id = p.id
                               JOIN users u ON pr.user_id = u.id
                               WHERE pr.product_id = ? ORDER BY pr.created_at DESC''', (product_id,)).fetchall()
    else:
        rows = conn.execute('''SELECT pr.*, p.name as product_name, u.username as user_name
                               FROM product_reviews pr
                               JOIN products p ON pr.product_id = p.id
                               JOIN users u ON pr.user_id = u.id
                               ORDER BY pr.created_at DESC''').fetchall()
    conn.close()
    return render_template('admin_reviews.html', reviews=rows)

@app.route('/admin/reviews/<int:rid>/delete', methods=['POST'])
@admin_required
def admin_review_delete(rid):
    conn = get_db_connection()
    conn.execute('DELETE FROM product_reviews WHERE id=?', (rid,))
    conn.commit(); conn.close()
    flash('Review deleted')
    return redirect(url_for('admin_reviews'))

# ----------------------
# Admin: Recommendation Rules
# ----------------------
@app.route('/admin/rules', methods=['GET','POST'])
@admin_required
def admin_rules():
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM site_settings WHERE key='recommendation_rules'").fetchone()
    current = row['value'] if row else ''
    if request.method == 'POST':
        rules = request.form.get('rules','')
        if row:
            conn.execute("UPDATE site_settings SET value=? WHERE key='recommendation_rules'", (rules,))
        else:
            conn.execute("INSERT INTO site_settings (key,value) VALUES ('recommendation_rules',?)", (rules,))
        conn.commit(); conn.close(); flash('Rules saved'); return redirect(url_for('admin_rules'))
    conn.close()
    return render_template('admin_rules.html', rules=current)

# ----------------------
# Admin: Blog CRUD
# ----------------------
@app.route('/admin/blog')
@admin_required
def admin_blog_list():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM blog_posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_blog_list.html', posts=posts)

@app.route('/admin/blog/new', methods=['GET','POST'])
@admin_required
def admin_blog_new():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        cover = request.form.get('cover_image') or None
        if 'cover_file' in request.files and request.files['cover_file'] and request.files['cover_file'].filename:
            cover = save_uploaded_file(request.files['cover_file'], subdir='images/blog')
        conn = get_db_connection()
        conn.execute('INSERT INTO blog_posts (title, slug, content, cover_image) VALUES (?,?,?,?)', (title, slug, content, cover))
        conn.commit(); conn.close(); flash('Post created'); return redirect(url_for('admin_blog_list'))
    return render_template('admin_blog_form.html', mode='new', post=None)

@app.route('/admin/blog/<int:bid>/edit', methods=['GET','POST'])
@admin_required
def admin_blog_edit(bid):
    conn = get_db_connection(); post = conn.execute('SELECT * FROM blog_posts WHERE id=?', (bid,)).fetchone()
    if not post:
        conn.close(); flash('Post not found'); return redirect(url_for('admin_blog_list'))
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        cover = request.form.get('cover_image') or post['cover_image']
        if 'cover_file' in request.files and request.files['cover_file'] and request.files['cover_file'].filename:
            cover = save_uploaded_file(request.files['cover_file'], subdir='images/blog')
        conn.execute('UPDATE blog_posts SET title=?, slug=?, content=?, cover_image=?, updated_at=? WHERE id=?', (title, slug, content, cover, datetime.now(), bid))
        conn.commit(); conn.close(); flash('Post updated'); return redirect(url_for('admin_blog_list'))
    conn.close(); return render_template('admin_blog_form.html', mode='edit', post=post)

@app.route('/admin/blog/<int:bid>/delete', methods=['POST'])
@admin_required
def admin_blog_delete(bid):
    conn = get_db_connection(); conn.execute('DELETE FROM blog_posts WHERE id=?', (bid,)); conn.commit(); conn.close(); flash('Post deleted'); return redirect(url_for('admin_blog_list'))

# ----------------------
# Admin: Site Settings
# ----------------------
@app.route('/admin/settings', methods=['GET','POST'])
@admin_required
def admin_settings():
    conn = get_db_connection()
    # load current settings with resilience if table is missing
    try:
        rows = conn.execute('SELECT key, value FROM site_settings').fetchall()
    except sqlite3.OperationalError:
        # create table on the fly and retry
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            rows = conn.execute('SELECT key, value FROM site_settings').fetchall()
        except Exception:
            rows = []
    cur = {row['key']: row['value'] for row in rows}
    if request.method == 'POST':
        theme_color = request.form.get('theme_color') or '#ffc0cb'
        admin_profile = request.form.get('admin_profile') or ''
        logo_url = cur.get('site_logo')
        if 'logo_file' in request.files and request.files['logo_file'] and request.files['logo_file'].filename:
            logo_url = save_uploaded_file(request.files['logo_file'], subdir='images')
        elif request.form.get('logo_url'):
            logo_url = request.form.get('logo_url')
        # upsert helper
        def upsert(k,v):
            if conn.execute('SELECT 1 FROM site_settings WHERE key=?', (k,)).fetchone():
                conn.execute('UPDATE site_settings SET value=? WHERE key=?', (v,k))
            else:
                conn.execute('INSERT INTO site_settings (key,value) VALUES (?,?)', (k,v))
        upsert('theme_color', theme_color)
        upsert('admin_profile', admin_profile)
        if logo_url:
            upsert('site_logo', logo_url)
        conn.commit(); conn.close(); flash('Settings saved')
        return redirect(url_for('admin_settings'))
    conn.close()
    return render_template('admin_settings.html', settings=cur)

# ----------------------
# User: Oily + Face Wash gallery with price comparison
# ----------------------
def _normalize_name(s: str) -> str:
    return os.path.splitext(os.path.basename(s))[0]

def _canonical_product_for_filename(fname: str) -> str:
    n = _normalize_name(fname).lower()
    if 'cetaphil' in n and 'gentle' in n:
        return 'Cetaphil Gentle Skin Cleanser (125 ml)'
    if 'cetaphil' in n and 'oily' in n:
        return 'Cetaphil Oily Skin Cleanser'
    if 'mamaearth' in n and 'ubtan' in n:
        return 'Mamaearth Ubtan Face Wash'
    if 'himalaya' in n and ('neem' in n or 'purifying' in n):
        return 'Himalaya Purifying Neem Face Wash'
    if ('clean' in n and 'clear' in n) and ('oil control' in n or 'foaming' in n or 'facewash' in n or 'face wash' in n):
        return 'Clean & Clear Oil Control Foaming Face Wash'
    if 'wishcare' in n and ('tea tree' in n or ('tea' in n and 'tree' in n)):
        return 'Wishcare Tea Tree Foaming Face Wash'
    # default: title-case of file
    return _normalize_name(fname).replace('-', ' ').replace('_', ' ').title()

PRICE_DATA = {
    'Cetaphil Gentle Skin Cleanser (125 ml)': {'amazon': 364, 'nykaa': 429, 'flipkart': 758},
    'Cetaphil Oily Skin Cleanser': {'amazon': None, 'nykaa': 615, 'flipkart': None},
    'Mamaearth Ubtan Face Wash': {'amazon': 201, 'nykaa': 399, 'flipkart': 247},
    'Himalaya Purifying Neem Face Wash': {'amazon': 179, 'nykaa': 190, 'flipkart': 165},
    'Clean & Clear Oil Control Foaming Face Wash': {'amazon': 160, 'nykaa': 175, 'flipkart': 150},
    'Wishcare Tea Tree Foaming Face Wash': {'amazon': 320, 'nykaa': 349, 'flipkart': 315},
}

def _build_buy_links(product_name: str):
    from urllib.parse import quote_plus
    q = quote_plus(product_name)
    return {
        'amazon': f'https://www.amazon.in/s?k={q}',
        'nykaa': f'https://www.nykaa.com/search?search={q}',
        'flipkart': f'https://www.flipkart.com/search?q={q}',
    }

@app.route('/skincare/oily-facewash')
def oily_facewash_gallery():
    # Scan /static/images/ for candidate face wash images
    base = os.path.join('static','images')
    images = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            low = name.lower()
            if not low.endswith(('.jpg','.jpeg','.png','.webp','.gif')):
                continue
            # heuristic: include common face wash keywords
            if any(k in low for k in ['face wash','facewash','cleanser','oily']):
                images.append(name)
    items = []
    for img in images:
        display_name = _normalize_name(img).replace('-', ' ').replace('_', ' ').title()
        canonical = _canonical_product_for_filename(img)
        prices = PRICE_DATA.get(canonical, {'amazon': None, 'nykaa': None, 'flipkart': None})
        # compute lowest
        numeric = {k: v for k, v in prices.items() if isinstance(v, (int, float))}
        lowest_site = min(numeric, key=numeric.get) if numeric else None
        links = _build_buy_links(canonical)
        items.append({
            'name': display_name,
            'image_url': f"/static/images/{img}",
            'canonical': canonical,
            'prices': prices,
            'lowest': lowest_site,
            'links': links,
        })
    return render_template('oily_facewash.html', items=items)

@app.route('/api/dermatologists')
def api_dermatologists():
    """
    Find nearby dermatologists using Google Places API.
    Supports both coordinates and address search.
    """
    try:
        # Get parameters
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        address = request.args.get('address')
        radius = int(request.args.get('radius', Config.DEFAULT_RADIUS))
        
        # Determine coordinates
        if lat and lng:
            # Use provided coordinates
            try:
                lat = float(lat)
                lng = float(lng)
            except ValueError:
                return jsonify({'error': 'Invalid coordinates'}), 400
        elif address:
            # Geocode the address
            coords = google_places_service.geocode_address(address)
            if coords:
                lat, lng = coords
            else:
                return jsonify({'error': 'Could not find location for the provided address'}), 400
        else:
            # Use default location
            lat, lng = Config.DEFAULT_LAT, Config.DEFAULT_LNG
        
        # Search for dermatologists
        dermatologists = google_places_service.search_dermatologists(lat, lng, radius)
        
        return jsonify(dermatologists)
        
    except Exception as e:
        print(f"Error in dermatologists API: {e}")
        # Return fallback data
        fallback_lat = lat if 'lat' in locals() else Config.DEFAULT_LAT
        fallback_lng = lng if 'lng' in locals() else Config.DEFAULT_LNG
        
        return jsonify([{
            'name': 'Dermatology Clinic',
            'address': 'Please check your location settings',
            'phone': 'N/A',
            'rating': None,
            'lat': fallback_lat,
            'lng': fallback_lng,
            'distance': 0.0,
            'place_id': None,
            'is_open': None,
            'price_level': None
        }])

@app.route('/api/geocode')
def api_geocode():
    """
    Geocode an address to get coordinates.
    """
    address = request.args.get('address')
    if not address:
        return jsonify({'error': 'Address parameter is required'}), 400
    
    coords = google_places_service.geocode_address(address)
    if coords:
        return jsonify({
            'lat': coords[0],
            'lng': coords[1],
            'status': 'success'
        })
    else:
        return jsonify({'error': 'Could not geocode the address'}), 400

@app.route('/api/place-details')
def api_place_details():
    """
    Get detailed information about a specific place.
    """
    place_id = request.args.get('place_id')
    if not place_id:
        return jsonify({'error': 'Place ID parameter is required'}), 400
    
    details = google_places_service.get_place_details(place_id)
    if details:
        return jsonify({
            'status': 'success',
            'result': details
        })
    else:
        return jsonify({'error': 'Could not get place details'}), 400

# Skincare Products API Endpoints
@app.route('/api/skincare/products')
def api_skincare_products():
    """
    Get skincare products with optional filtering.
    """
    try:
        category = request.args.get('category')
        # Support alias 'product_type' for category to match UI terminology
        if not category:
            pt = request.args.get('product_type')
            if pt:
                category = pt
        skin_type = request.args.get('skin_type')
        concern = request.args.get('concern')
        price_min = request.args.get('price_min', type=float)
        price_max = request.args.get('price_max', type=float)
        
        price_range = None
        if price_min is not None and price_max is not None:
            price_range = (price_min, price_max)
        
        products = advanced_skincare_service.get_skincare_products(
            category=category,
            skin_type=skin_type,
            concern=concern,
            price_range=price_range
        )
        
        return jsonify({
            'status': 'success',
            'products': products,
            'total': len(products)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/product/<int:product_id>')
def api_skincare_product_detail(product_id):
    """
    Get detailed information about a specific skincare product.
    """
    try:
        product = advanced_skincare_service.get_product_by_id(product_id)
        if product:
            return jsonify({
                'status': 'success',
                'product': product
            })
        else:
            return jsonify({'error': 'Product not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/search')
def api_skincare_search():
    """
    Search skincare products by query.
    """
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        products = advanced_skincare_service.search_products(query)
        return jsonify({
            'status': 'success',
            'products': products,
            'total': len(products),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/recommendations')
def api_skincare_recommendations():
    """
    Get personalized skincare product recommendations.
    """
    try:
        skin_type = request.args.get('skin_type')
        concerns = request.args.getlist('concerns')
        
        if not skin_type:
            return jsonify({'error': 'Skin type is required'}), 400
        
        recommendations = advanced_skincare_service.get_recommendations(skin_type, concerns)
        return jsonify({
            'status': 'success',
            'recommendations': recommendations,
            'total': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/filters')
def api_skincare_filters():
    """
    Get available filter options for skincare products.
    """
    try:
        return jsonify({
            'status': 'success',
            'filters': {
                'categories': advanced_skincare_service.get_categories(),
                'skin_types': advanced_skincare_service.get_skin_types(),
                'concerns': advanced_skincare_service.get_concerns()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/price-comparison/<int:product_id>')
def api_skincare_price_comparison(product_id):
    """
    Get price comparison data for a specific skincare product.
    """
    try:
        price_data = advanced_skincare_service.get_price_comparison(product_id)
        return jsonify({
            'status': 'success',
            'price_comparison': price_data,
            'total_sites': len(price_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/refresh-prices')
def api_refresh_prices():
    """
    Refresh price comparison data.
    """
    try:
        advanced_skincare_service.refresh_price_data()
        return jsonify({
            'status': 'success',
            'message': 'Price data refreshed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# New advanced scraper endpoints
@app.route('/api/skincare/update-prices')
def api_update_prices():
    """
    Run the advanced price scraper to update price data.
    """
    try:
        limit = request.args.get('limit', type=int)
        download_images = request.args.get('download_images', '1') != '0'
        
        # Import and run the advanced scraper
        import advanced_price_scraper
        result = advanced_price_scraper.run_full_update(
            save_csv=True, 
            download_images=download_images, 
            limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Price update completed. Processed {len(result)} records.',
            'rows_processed': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/scraped-products')
def api_scraped_products():
    """
    Get all products from the scraper database.
    """
    try:
        products = advanced_skincare_service.get_all_products_from_db()
        return jsonify({
            'status': 'success',
            'products': products,
            'total': len(products)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skincare/compare-prices')
def api_compare_prices():
    """
    Compare prices for a specific product name.
    """
    try:
        product_name = request.args.get('name')
        if not product_name:
            return jsonify({'error': 'Product name is required'}), 400
        
        # Import and use the advanced scraper's compare function
        import advanced_price_scraper
        import sqlite3
        
        conn = sqlite3.connect(advanced_price_scraper.DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT id, category, brand, name, site, product_title, price, currency, image_url, product_url, scraped_at 
            FROM products 
            WHERE name LIKE ? 
            ORDER BY scraped_at DESC
        """, (f"%{product_name}%",))
        
        rows = c.fetchall()
        conn.close()
        
        keys = ['id','category','brand','name','site','product_title','price','currency','image_url','product_url','scraped_at']
        products = [dict(zip(keys, r)) for r in rows]
        
        return jsonify({
            'status': 'success',
            'products': products,
            'total': len(products),
            'query': product_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

def get_youtube_videos(api_key, search_query, max_results=6):
    """Fetch videos from YouTube API"""
    try:
        import requests
        url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'maxResults': max_results,
            'key': api_key,
            'order': 'relevance',
            'videoDuration': 'medium'  # 4-20 minutes
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            videos = []
            
            for item in data.get('items', []):
                video = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:150] + '...',
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'published': item['snippet']['publishedAt']
                }
                videos.append(video)
            
            return videos
        else:
            print(f"YouTube API error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return []

@app.route('/tutorials')
def tutorials():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's skin concerns for tutorial recommendations
    conn = get_db_connection()
    user_profile = conn.execute(
        'SELECT skin_concerns FROM user_profiles WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    api_key = "AIzaSyATG2X9e9HaHMM5Nv2ksv3BSUIzmGROnDw"
    recommended_videos = []
    
    # Get personalized videos based on skin concerns
    skin_concerns = []
    if user_profile and user_profile['skin_concerns']:
        skin_concerns = user_profile['skin_concerns'].split(',')
        
        # Map skin concerns to search queries
        concern_queries = {
            'acne': 'skincare acne treatment routine',
            'dullness': 'brightening skincare routine glow',
            'pigmentation': 'dark spots pigmentation skincare',
            'wrinkles': 'anti aging skincare routine',
            'sensitivity': 'sensitive skin care routine',
            'oily': 'oily skin care routine',
            'dry': 'dry skin care routine moisturizing'
        }
        
        # Fetch videos for each concern
        for concern in skin_concerns[:2]:  # Limit to 2 concerns to avoid too many requests
            concern = concern.strip().lower()
            if concern in concern_queries:
                videos = get_youtube_videos(api_key, concern_queries[concern], 3)
                recommended_videos.extend(videos)
    
    # Get general beauty videos if no specific concerns or few videos
    if len(recommended_videos) < 3:
        general_videos = get_youtube_videos(api_key, 'everyday makeup tutorial skincare routine', 6)
        recommended_videos.extend(general_videos)
    
    # Get category-specific videos
    skincare_videos = get_youtube_videos(api_key, 'skincare routine morning evening', 4)
    makeup_videos = get_youtube_videos(api_key, 'makeup tutorial everyday beginner', 4)
    
    return render_template('tutorials.html', 
                         videos=recommended_videos[:6], 
                         skincare_videos=skincare_videos,
                         makeup_videos=makeup_videos)

@app.route('/price-compare/<product_id>')
def price_compare(product_id):
    # Kept for backward compatibility (USD demo)
    price_data = {
        'amazon': {'price': 25.99, 'currency': 'USD', 'url': 'https://amazon.com/product'},
        'nykaa': {'price': 24.50, 'currency': 'USD', 'url': 'https://nykaa.com/product'},
        'sephora': {'price': 27.00, 'currency': 'USD', 'url': 'https://sephora.com/product'}
    }
    return jsonify(price_data)

@app.route('/api/price-compare-sku/<sku>')
def price_compare_sku(sku):
    """Return price comparison in INR for a makeup_catalog SKU"""
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM makeup_catalog WHERE sku = ?', (sku,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'SKU not found'}), 404
    base_price = row['price'] or 0
    brand = row['brand']
    name = row['name']
    variant = row['variant'] or ''
    query_str = f"{brand} {name} {variant}".strip().replace(' ', '+')
    data = {
        'nykaa': {'price': base_price, 'currency': 'INR', 'url': row['retailer_url'] or f'https://www.nykaa.com/search/result/?q={query_str}'},
        'amazon': {'price': int(base_price * 0.98), 'currency': 'INR', 'url': f'https://www.amazon.in/s?k={query_str}'},
        'flipkart': {'price': int(base_price * 0.97), 'currency': 'INR', 'url': f'https://www.flipkart.com/search?q={query_str}'}
    }
    return jsonify(data)

if __name__ == '__main__':
    # Initialize database on first run and ensure new tables
    from database import create_tables as _create_tables
    from database import populate_makeup_catalog_from_csv as _populate_catalog
    from database import enrich_images_from_nykaa as _enrich_images
    # Ensure dashboard background image is in static folder
    try:
        os.makedirs(os.path.join('static', 'images'), exist_ok=True)
        src_img = 'dashboardimage.png'
        dst_img = os.path.join('static', 'images', 'dashboardimage.png')
        if os.path.exists(src_img) and not os.path.exists(dst_img):
            import shutil
            shutil.copyfile(src_img, dst_img)
        # Ensure skincare background image is available
        src_skin = 'skinday.png'
        dst_skin = os.path.join('static', 'images', 'skinday.png')
        if os.path.exists(src_skin) and not os.path.exists(dst_skin):
            shutil.copyfile(src_skin, dst_skin)
        # Ensure dark mode skincare background image is available (handle stray space in filename)
        src_dark_candidates = ['dkbackgroundimage.png', 'dkbackgroundimage.png .png']
        dst_dark = os.path.join('static', 'images', 'dkbackgroundimage.png')
        if not os.path.exists(dst_dark):
            for cand in src_dark_candidates:
                if os.path.exists(cand):
                    shutil.copyfile(cand, dst_dark)
                    break
    except Exception as _bg_err:
        print(f"Note: could not set dashboard background image: {_bg_err}")
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # Safe to call; creates tables if missing
        _create_tables()
    # Replace skincare with seed if present
    try:
        from database import replace_skincare_from_json as _replace_skin
        seed_path = os.path.join('data', 'skincare_seed.json')
        if os.path.exists(seed_path):
            inserted = _replace_skin(seed_path)
            if inserted:
                print(f"✅ Loaded skincare seed items: {inserted}")
            else:
                print("⚠️ No skincare items loaded from seed")
        else:
            print(f"⚠️ Skincare seed file not found: {seed_path}")
    except Exception as e:
        print(f"❌ Failed to load skincare seed: {e}")
    # Ensure makeup catalog is populated
    try:
        _populate_catalog()
        # Try enriching a few images from Nykaa on startup (non-blocking best-effort)
        try:
            updated = _enrich_images(10)
            if updated:
                print(f"Enriched {updated} product images from Nykaa")
        except Exception as ee:
            print(f"Nykaa enrich skipped: {ee}")
    except Exception as e:
        print(f"Warning: failed to populate makeup catalog: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)


