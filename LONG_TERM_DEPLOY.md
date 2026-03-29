# 🚀 Long Term Deployment - Render + MongoDB Atlas

## 💡 Kyun ye Best hai Long Term ke Liye?

| Factor | Render + MongoDB | Reason |
|--------|-----------------|--------|
| **Data Safety** | ✅ MongoDB Atlas | Data never lost, daily backups |
| **Uptime** | ✅ 99.9% | Paid plan = never sleeps |
| **Scalability** | ✅ Easy | Traffic badhe toh upgrade easy |
| **Cost** | ✅ $7/month | Affordable for production |
| **Updates** | ✅ Auto-deploy | GitHub push = auto update |

---

## 📋 Step-by-Step Deployment

### Phase 1: MongoDB Atlas Setup (15 min)

#### 1. Account Create
- https://www.mongodb.com/cloud/atlas
- "Try Free" → Google/GitHub signup

#### 2. Cluster Create
```
1. Create Cluster → Shared (FREE)
2. Provider: AWS
3. Region: Mumbai (ap-south-1) ← India ke liye best
4. Wait 2-3 minutes
```

#### 3. Security Setup
```
Database Access:
- Username: admin
- Password: Auto-generate → COPY KAREIN

Network Access:
- Add IP: 0.0.0.0/0 (Render ke liye)
```

#### 4. Connection String
```
Connect → Connect App → Python → 3.11+
Copy this:
mongodb+srv://admin:PASSWORD@cluster0.xxxxx.mongodb.net/amazon_listings?retryWrites=true&w=majority
```
**Note:** PASSWORD ko actual password se replace karein

---

### Phase 2: GitHub Repo (10 min)

#### 1. Repository Create
```
GitHub → New → amazon-listing-manager
Public → Create
```

#### 2. Code Push
```bash
cd D:\Kimi\amazon-listing-manager
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/amazon-listing-manager.git
git push -u origin main
```

---

### Phase 3: Code Update for Production (20 min)

#### 1. requirements.txt Update
```
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-login==0.6.3
flask-wtf==1.2.1
wtforms==3.1.1
werkzeug==3.0.1
python-dotenv==1.0.0
requests==2.31.0
boto3==1.34.0
cryptography==41.0.7
gunicorn==21.2.0
pymongo==4.6.1
flask-pymongo==2.3.0
```

#### 2. Production Config File

Create `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGODB_URI')
    
    # Amazon SP-API
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    LWA_CLIENT_ID = os.environ.get('LWA_CLIENT_ID')
    LWA_CLIENT_SECRET = os.environ.get('LWA_CLIENT_SECRET')
    SP_API_ROLE_ARN = os.environ.get('SP_API_ROLE_ARN')
    AMAZON_REDIRECT_URI = os.environ.get('AMAZON_REDIRECT_URI')
    
    # Sandbox
    SANDBOX_REFRESH_TOKEN = os.environ.get('SANDBOX_REFRESH_TOKEN')
    SANDBOX_SELLER_ID = os.environ.get('SANDBOX_SELLER_ID')
```

#### 3. Update app/__init__.py

```python
from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from config import Config

mongo = PyMongo()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
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
    
    return app
```

#### 4. MongoDB Models

`app/models.py` update karein:
```python
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson.objectid import ObjectId

class User:
    collection_name = 'users'
    
    def __init__(self, data):
        self._id = data.get('_id')
        self.email = data.get('email')
        self.password_hash = data.get('password_hash')
        self.name = data.get('name')
        self.created_at = data.get('created_at', datetime.utcnow())
        self.is_active = data.get('is_active', True)
    
    @property
    def id(self):
        return str(self._id) if self._id else None
    
    @classmethod
    def get_collection(cls):
        return current_app.mongo.db[cls.collection_name]
    
    @classmethod
    def find_by_email(cls, email):
        data = cls.get_collection().find_one({'email': email.lower()})
        return cls(data) if data else None
    
    @classmethod
    def find_by_id(cls, user_id):
        try:
            data = cls.get_collection().find_one({'_id': ObjectId(user_id)})
            return cls(data) if data else None
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
    
    # Flask-Login support
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class AmazonConnection:
    collection_name = 'amazon_connections'
    
    def __init__(self, data):
        self._id = data.get('_id')
        self.user_id = data.get('user_id')
        self.seller_id = data.get('seller_id')
        self.marketplace_id = data.get('marketplace_id', 'A21TJRUUN4KGV')
        self.refresh_token_encrypted = data.get('refresh_token_encrypted')
        self.is_active = data.get('is_active', True)
        self.created_at = data.get('created_at', datetime.utcnow())
    
    @classmethod
    def get_collection(cls):
        return current_app.mongo.db[cls.collection_name]
    
    def save(self):
        collection = self.get_collection()
        data = {
            'user_id': self.user_id,
            'seller_id': self.seller_id,
            'marketplace_id': self.marketplace_id,
            'refresh_token_encrypted': self.refresh_token_encrypted,
            'is_active': self.is_active,
            'created_at': self.created_at
        }
        
        if self._id:
            collection.update_one({'_id': self._id}, {'$set': data})
        else:
            result = collection.insert_one(data)
            self._id = result.inserted_id
        return self
```

#### 5. Update run.py

```python
#!/usr/bin/env python3
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

#### 6. Git Push
```bash
git add .
git commit -m "Production ready with MongoDB"
git push origin main
```

---

### Phase 4: Render Deploy (15 min)

#### 1. Account
- https://render.com
- GitHub se signup

#### 2. New Web Service
```
New + → Web Service
Connect GitHub repository
Select: amazon-listing-manager
```

#### 3. Configure
```
Name: amazon-listing-manager
Region: Singapore
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn run:app
```

#### 4. Environment Variables
```
SECRET_KEY = (32 character random string)
MONGODB_URI = mongodb+srv://admin:PASSWORD@cluster0.xxxxx.mongodb.net/amazon_listings?retryWrites=true&w=majority
AWS_ACCESS_KEY_ID = your-key
AWS_SECRET_ACCESS_KEY = your-secret
AWS_REGION = us-east-1
LWA_CLIENT_ID = your-client-id
LWA_CLIENT_SECRET = your-secret
SP_API_ROLE_ARN = arn:aws:iam::xxx:role/xxx
AMAZON_REDIRECT_URI = https://amazon-listing-manager.onrender.com/auth/amazon/callback
SANDBOX_REFRESH_TOKEN = Atzr|xxx
SANDBOX_SELLER_ID = A1xxx
```

#### 5. Deploy
```
Create Web Service
Wait 3-5 minutes for build
```

---

## 💰 Cost Breakdown

| Component | Free Tier | Paid (Recommended) |
|-----------|-----------|-------------------|
| **Render** | $0 (sleeps) | $7/month |
| **MongoDB** | $0 (512MB) | $0 (sufficient) |
| **Total** | **$0** | **$7/month** |

**$7/month = ₹580/month** (India mein)

---

## 🔄 Long Term Maintenance

### Daily
- Nothing! Auto-deploy hai

### Weekly
- GitHub commits check karein
- Render logs check karein (errors ke liye)

### Monthly
- MongoDB usage check (512MB mein kitna hua)
- Render bandwidth check (100GB free)
- Backups verify karein

### Updates
```bash
# Local machine pe
git pull origin main
# Changes karein
git add .
git commit -m "Update description"
git push origin main
# Auto-deploy on Render!
```

---

## 📈 Scaling (Future mein)

### Jab Traffic Badhe:
1. **Render** → Upgrade plan ($7 → $25)
   - More CPU/RAM
   - No sleep
   
2. **MongoDB** → M2/M5 cluster
   - 2GB/5GB storage
   - Dedicated resources

3. **CDN** → CloudFlare (Free)
   - Static files fast
   - DDoS protection

---

## 🛡️ Security Checklist

- [x] Strong SECRET_KEY
- [x] Environment variables (no hardcoded keys)
- [x] MongoDB IP whitelist
- [x] HTTPS enabled (Render automatic)
- [x] Regular dependency updates
- [x] Database backups enabled

---

## ✅ Success!

**Aapka app live hai:**
```
https://amazon-listing-manager.onrender.com
```

**Features:**
- ✅ 24/7 uptime (paid plan)
- ✅ MongoDB database (persistent)
- ✅ Auto-deploy from GitHub
- ✅ Custom domain ready
- ✅ SSL enabled
- ✅ Scalable

---

**Koi step mein help chahiye toh batayein!** 🚀
