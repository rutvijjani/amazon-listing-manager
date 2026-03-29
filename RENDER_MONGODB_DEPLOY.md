# 🚀 Render + MongoDB Atlas Deployment Guide

## 💡 Kya hai Render?
- **Free** hosting with auto-deploy from GitHub
- **Custom domain** support (free subdomain)
- **SSL** automatic
- **Never sleeps** (unlike PythonAnywhere free tier)
- **Perfect** for production apps

## 💡 Kya hai MongoDB Atlas?
- **Free** 512 MB database (M0 cluster)
- **Cloud** hosted (24/7 available)
- **Fast** - SSD storage
- **Secure** - built-in encryption

---

## 📋 Step 1: MongoDB Atlas Setup (10 min)

### A. Account Create
1. **Website jayein:** https://www.mongodb.com/cloud/atlas
2. **"Try Free"** click karein
3. Google/GitHub se signup karein

### B. Cluster Create
1. **"Create a cluster"** click karein
2. **"Shared Cluster (FREE)"** select karein → **"Create"**
3. Provider: **AWS**
4. Region: **Mumbai (ap-south-1)** ← India ke liye best
5. **"Create Cluster"** (takes 1-3 minutes)

### C. Database Access Setup
1. Left sidebar → **"Database Access"**
2. **"Add New Database User"**
3. Username: `admin`
4. Password: **Auto-generate** click karein → **Copy karein** (save karein!)
5. **"Add User"**

### D. Network Access
1. Left sidebar → **"Network Access"**
2. **"Add IP Address"**
3. **"Allow Access from Anywhere"** (0.0.0.0/0) ← Render ke liye necessary
4. **"Confirm"**

### E. Connection String Get Karein
1. Clusters page par **"Connect"** click karein
2. **"Connect your application"**
3. Driver: **Python**
4. Version: **3.11 or later**
5. **Connection string copy karein:**

```
mongodb+srv://admin:PASSWORD@cluster0.xxxxx.mongodb.net/amazon_listing_manager?retryWrites=true&w=majority
```

**⚠️ Note:** `PASSWORD` ko actual password se replace karein

---

## 📁 Step 2: GitHub Repository Create (5 min)

### A. GitHub Account
1. **GitHub.com** par jayein
2. Naya repository create karein: `amazon-listing-manager`
3. **Public** rakhein (free hai)

### B. Project Upload
Apne computer mein:

```bash
cd D:\Kimi\amazon-listing-manager

# Git initialize
git init

# Sab files add karein
git add .

# Commit karein
git commit -m "Initial commit"

# GitHub se link karein (replace USERNAME)
git remote add origin https://github.com/USERNAME/amazon-listing-manager.git

# Push karein
git push -u origin main
```

Ya **GitHub Desktop** use karein (easier for Windows)

---

## ⚙️ Step 3: Code Update for MongoDB (10 min)

### A. MongoDB Support Add Karein

`requirements.txt` mein add karein:
```
pymongo==4.6.1
flask-pymongo==2.3.0
```

### B. Database Config Update

`app/__init__.py` mein changes:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pymongo import PyMongo  # Add this
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()
mongo = PyMongo()  # Add this

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # Check if MongoDB URL exists
    mongo_uri = os.getenv('MONGODB_URI')
    
    if mongo_uri:
        # Use MongoDB
        app.config['MONGO_URI'] = mongo_uri
        mongo.init_app(app)
        print("✅ Using MongoDB Atlas")
    else:
        # Use SQLite (fallback)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        print("✅ Using SQLite")
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Blueprints register
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.listings import bp as listings_bp
    from app.routes.api import bp as api_bp
    from app.routes.sandbox import bp as sandbox_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(listings_bp, url_prefix='/listings')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(sandbox_bp)
    
    # Create SQLite tables if using SQLite
    if not mongo_uri:
        with app.app_context():
            db.create_all()
    
    return app
```

### C. Models Update for MongoDB

`app/models_mongo.py` create karein:

```python
"""
MongoDB Models for Amazon Listing Manager
"""

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId
import json

class User:
    """User model for MongoDB"""
    
    def __init__(self, user_data):
        self._id = user_data.get('_id')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        self.name = user_data.get('name')
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.is_active = user_data.get('is_active', True)
    
    @property
    def id(self):
        return str(self._id)
    
    @staticmethod
    def get_collection():
        return current_app.mongo.db.users
    
    @classmethod
    def find_by_email(cls, email):
        collection = cls.get_collection()
        user_data = collection.find_one({'email': email.lower()})
        return cls(user_data) if user_data else None
    
    @classmethod
    def find_by_id(cls, user_id):
        collection = cls.get_collection()
        try:
            user_data = collection.find_one({'_id': ObjectId(user_id)})
            return cls(user_data) if user_data else None
        except:
            return None
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        collection = self.get_collection()
        data = {
            'email': self.email.lower(),
            'password_hash': self.password_hash,
            'name': self.name,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
        
        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self
    
    def has_amazon_connection(self):
        collection = AmazonConnection.get_collection()
        return collection.count_documents({
            'user_id': self.id,
            'is_active': True
        }) > 0
    
    def get_active_connection(self):
        collection = AmazonConnection.get_collection()
        conn_data = collection.find_one({
            'user_id': self.id,
            'is_active': True
        })
        return AmazonConnection(conn_data) if conn_data else None
    
    # Flask-Login requirements
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)


class AmazonConnection:
    """Amazon Connection model for MongoDB"""
    
    def __init__(self, data):
        self._id = data.get('_id')
        self.user_id = data.get('user_id')
        self.seller_id = data.get('seller_id')
        self.marketplace_id = data.get('marketplace_id', 'A21TJRUUN4KGV')
        self.marketplace_name = data.get('marketplace_name', 'Amazon.in')
        self.refresh_token_encrypted = data.get('refresh_token_encrypted')
        self.access_token_encrypted = data.get('access_token_encrypted')
        self.is_active = data.get('is_active', True)
        self.created_at = data.get('created_at', datetime.utcnow())
    
    @staticmethod
    def get_collection():
        return current_app.mongo.db.amazon_connections
    
    def save(self):
        collection = self.get_collection()
        data = {
            'user_id': self.user_id,
            'seller_id': self.seller_id,
            'marketplace_id': self.marketplace_id,
            'marketplace_name': self.marketplace_name,
            'refresh_token_encrypted': self.refresh_token_encrypted,
            'access_token_encrypted': self.access_token_encrypted,
            'is_active': self.is_active,
            'created_at': self.created_at
        }
        
        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self


class UpdateLog:
    """Update Log model for MongoDB"""
    
    @staticmethod
    def get_collection():
        return current_app.mongo.db.update_logs
    
    @classmethod
    def create(cls, user_id, asin, sku, operation, request_payload, status='PENDING'):
        collection = cls.get_collection()
        data = {
            'user_id': user_id,
            'asin': asin,
            'sku': sku,
            'operation': operation,
            'request_payload': request_payload,
            'status': status,
            'created_at': datetime.utcnow()
        }
        return collection.insert_one(data)
```

---

## 🚀 Step 4: Render Deploy (10 min)

### A. Account Create
1. **Render.com** par jayein
2. GitHub se signup karein

### B. New Web Service Create
1. Dashboard par **"New +"** → **"Web Service"**
2. **GitHub account connect** karein
3. **Repository select:** `amazon-listing-manager`
4. **"Connect"** click karein

### C. Configure Service

**Basic Settings:**
- Name: `amazon-listing-manager`
- Region: `Singapore` (India ke liye closest)
- Branch: `main`
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn run:app`

**⚠️ Important:** Free plan mein:
- Web service sleeps after 15 mins of inactivity
- First request thoda slow hoga (cold start)

### D. Environment Variables Add

**"Environment"** tab click karein → **"Add Environment Variable"**

One by one add karein:

```
SECRET_KEY=your-super-secret-key-here
MONGODB_URI=mongodb+srv://admin:PASSWORD@cluster0.xxxxx.mongodb.net/amazon_listing_manager?retryWrites=true&w=majority
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
LWA_CLIENT_ID=your-client-id
LWA_CLIENT_SECRET=your-secret
SP_API_ROLE_ARN=arn:aws:iam::xxx:role/xxx
AMAZON_REDIRECT_URI=https://amazon-listing-manager.onrender.com/auth/amazon/callback
SANDBOX_REFRESH_TOKEN=Atzr|xxx
SANDBOX_SELLER_ID=A1xxx
```

### E. Deploy

**"Create Web Service"** click karein

Build process start hoga (2-3 minutes)

---

## ✅ Step 5: App Live!

### URL Check Karein
**"Render Dashboard"** → Aapki service → **URL:**
```
https://amazon-listing-manager.onrender.com
```

### Test Karein
1. URL open karein
2. Register karein
3. Settings → Amazon Settings
4. Sandbox connect karein

---

## 🔧 Common Issues

### Issue 1: "Module not found"
**Solution:** `requirements.txt` mein sab packages add hain ya check karein

### Issue 2: "MongoDB connection failed"
**Solution:**
- MongoDB Atlas mein Network Access: 0.0.0.0/0 add karein
- Password correct hai ya check karein
- Connection string mein `<password>` replace kiya hai ya check karein

### Issue 3: App sleeps
**Solution:** Normal hai free tier mein. First request slow hoga.

UptimeRobot se ping karwa sakte hain awake rakhne ke liye (optional)

### Issue 4: Database wiped
**Solution:** MongoDB Atlas mein data persistent hai. SQLite mein hota ye issue.

---

## 📊 Render Free vs Paid

| Feature | Free | Paid ($7/month) |
|---------|------|-----------------|
| Sleep | After 15 min | Never |
| Bandwidth | 100 GB | Unlimited |
| Builds | 500 min/month | Unlimited |
| Custom Domain | Yes | Yes |

---

## 🎉 Benefits of Render + MongoDB

✅ **Never sleeps** (paid) ya auto-wake (free)
✅ **Fast** - SSD + global CDN
✅ **Automatic deploy** - GitHub push se auto-update
✅ **Database persistent** - MongoDB Atlas
✅ **SSL** - Automatic HTTPS
✅ **Custom domain** - Free support

---

## 🚀 Next Steps

1. **GitHub repo create** karein
2. **Code push** karein
3. **MongoDB Atlas** setup karein
4. **Render** par deploy karein

**Koi step mein problem aaye toh screenshot bhejein!** 🎉
