# 🚀 PythonAnywhere Deployment - Step by Step Guide

## ✅ Kya hai PythonAnywhere?
- **Free** hosting for Python apps
- **Reliable** - 24/7 uptime (with daily reboot)
- **Easy** - Browser mein sab kuch hota hai
- **Perfect** for Flask apps

---

## 📋 Step 1: Account Create Karein (2 min)

1. **Website jayein:** https://www.pythonanywhere.com

2. **"Pricing & signup"** click karein

3. **"Create a Beginner account"** click karein

4. **Details fill karein:**
   - Username: aapka username (jaise: rutvik)
   - Email: aapka email
   - Password: strong password

5. **"Create account"** click karein

6. **Email verify karein** (inbox check karein)

---

## 📁 Step 2: Files Upload Karein (5 min)

### A. Project ZIP Banayein

Apne computer mein:
```
amazon-listing-manager folder select karein
Right click → Send to → Compressed (zipped) folder
```

### B. PythonAnywhere mein Upload

1. **Login karein:** https://www.pythonanywhere.com

2. **"Files"** tab click karein (top menu mein)

3. **"Upload a file"** button click karein

4. **ZIP file select karein** aur upload karein

5. **"Open Bash console here"** button click karein

6. **Console mein type karein:**
```bash
unzip amazon-listing-manager.zip
```

7. **Rename karein (agar needed):**
```bash
mv amazon-listing-manager my-flask-app
```

---

## ⚙️ Step 3: Virtual Environment Setup (3 min)

Console mein yeh commands run karein:

```bash
cd my-flask-app

# Virtual environment create
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Dependencies install
pip install -r requirements.txt

# Gunicorn install (production server)
pip install gunicorn
```

**⚠️ Important:** Jab tak `venv` dikhe tab tak sab sahi hai.

---

## 🔧 Step 4: Environment Variables Set (5 min)

### A. .env File Create Karein

Console mein:
```bash
nano .env
```

### B. Yeh content paste karein (Ctrl+Shift+V):

```env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here-32-characters-long

DATABASE_URL=sqlite:///app.db
TOKEN_ENCRYPTION_KEY=your-encryption-key-here

AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

LWA_CLIENT_ID=amzn1.application-oa2-client.xxxxx
LWA_CLIENT_SECRET=...

SP_API_ROLE_ARN=arn:aws:iam::...:role/...
AMAZON_REDIRECT_URI=https://yourusername.pythonanywhere.com/auth/amazon/callback

SANDBOX_REFRESH_TOKEN=Atzr|...
SANDBOX_SELLER_ID=A1...
SANDBOX_MARKETPLACE_ID=A21TJRUUN4KGV
```

**⚠️ Replace karein:**
- `yourusername` → aapka PythonAnywhere username
- Baaki credentials → aapke Amazon credentials

### C. Save karein:
- Ctrl+O (Write Out)
- Enter (Confirm)
- Ctrl+X (Exit)

---

## 🌐 Step 5: Web App Configure (5 min)

### A. Web Tab Open Karein

1. **"Web"** tab click karein (top menu)

2. **"Add a new web app"** click karein

3. **"Next"** click karein

4. **"Flask"** select karein

5. **"Python 3.11"** select karein

6. **Path set karein:**
   - `/home/yourusername/my-flask-app/run.py`
   - (Replace `yourusername` with actual username)

7. **"Next"** click karein

### B. WSGI File Edit Karein

1. Web tab mein **"WSGI configuration file"** link click karein

2. Poora content delete karein aur yeh paste karein:

```python
import sys
import os

# Add project path
path = '/home/yourusername/my-flask-app'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables from .env
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Import Flask app
from run import app as application
```

**⚠️ Replace `yourusername` with actual username**

3. **Save karein** (green button)

### C. Static Files Configure

Web tab mein scroll down:

**"Static files"** section mein:
- URL: `/static/`
- Directory: `/home/yourusername/my-flask-app/app/static`

**"Add"** click karein

---

## 🚀 Step 6: App Start Karein (2 min)

### A. Virtual Environment Set Karein

Web tab mein:

**"Virtualenv"** section:
- Path: `/home/yourusername/my-flask-app/venv`

**"Save"** click karein

### B. Reload Karein

**"Reload"** button click karein (green button)

---

## ✅ Step 7: Test Karein (2 min)

1. **Link copy karein:** `https://yourusername.pythonanywhere.com`

2. **Browser mein open karein**

3. **App dikhna chahiye!**

---

## 🔧 Common Issues & Solutions

### Issue 1: "Module not found"
**Solution:**
```bash
# Console mein
workon yourusername.pythonanywhere.com
pip install -r requirements.txt
```

### Issue 2: "500 Internal Server Error"
**Solution:**
- Web tab mein **"Error log"** check karein
- .env file mein credentials check karein

### Issue 3: "Static files not loading"
**Solution:**
- Web tab mein static files path check karein
- Browser cache clear karein (Ctrl+Shift+R)

### Issue 4: App daily stop hota hai
**Solution:**
- Normal hai! Free tier mein daily reboot hota hai (around 11am UTC)
- Auto-restart hota hai

---

## 🔒 Security Tips

1. **SECRET_KEY** strong hona chahiye:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Debug mode OFF** rakhein production mein

3. **Database backups** lein regularly

---

## 📊 Free Tier Limits

| Feature | Limit |
|---------|-------|
| CPU Time | 100 seconds/day |
| Storage | 512 MB |
| Web Apps | 1 |
| Daily Reboot | Yes (11am UTC) |
| Custom Domain | No |

**Agar zyada chahiye toh Paid plan:** $5/month

---

## 🎉 Success!

Aapka app live hai: `https://yourusername.pythonanywhere.com`

Ab aap:
- Register kar sakte hain
- Amazon connect kar sakte hain
- Listings manage kar sakte hain

---

## 📞 Need Help?

PythonAnywhere forums: https://www.pythonanywhere.com/forums/

**Deploy karne ke baad mujhe bataein, main help karunga!** 🚀
