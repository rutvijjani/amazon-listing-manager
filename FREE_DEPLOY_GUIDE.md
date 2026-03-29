# 🚀 FREE Deployment Guide - Render + MongoDB Atlas

## ✅ Kya Milega FREE Mein:
- **MongoDB Atlas**: 512MB storage (lifetime free)
- **Render**: Web hosting (free with sleep)
- **Total Cost**: ₹0

## ⚠️ Limitation:
- App 15 min inactivity ke baad "sleep" hota hai
- First visit mein 30-60 sec lagta hai wake up hone mein
- Uske baad fast chalta hai

---

## 📋 STEP 1: MongoDB Atlas Setup (10 min)

### 1.1 Account Create
```
1. https://cloud.mongodb.com par jayein
2. "Try Free" click karein
3. Google se signup karein
```

### 1.2 Cluster Create
```
1. "Create" button click karein
2. "Shared Cluster (FREE)" select karein
3. Provider: AWS select karein
4. Region: Mumbai (ap-south-1) select karein ← India ke liye best
5. "Create Cluster" click karein
6. 2-3 minute wait karein
```

### 1.3 Database User Create
```
Left Sidebar → "Database Access" → "Add New Database User"

Username: admin
Password: Click "Auto-generate Password" → COPY KAREIN (Notepad mein save karein!)
Click "Add User"
```

### 1.4 Network Access (Important!)
```
Left Sidebar → "Network Access" → "Add IP Address"

Click: "Allow Access from Anywhere"
IP Address: 0.0.0.0/0 (ye Render ke liye necessary hai)
Click "Confirm"
```

### 1.5 Connection String Get Karein
```
1. "Clusters" page par jayein
2. "Connect" button click karein
3. "Connect your application" select karein
4. Driver: Python
5. Version: 3.11 or later
6. Connection string copy karein:

Format:
mongodb+srv://admin:PASSWORD@cluster0.xxxxx.mongodb.net/amazon_listings?retryWrites=true&w=majority

Note: PASSWORD ko aapke actual password se replace karein
```

**🔗 Ye string save karein - Render mein chahiye hoga!**

---

## 📋 STEP 2: GitHub Repository (5 min)

### 2.1 Account Check
```
https://github.com par jayein
Login karein ya account create karein
```

### 2.2 New Repository
```
1. Green "New" button click karein
2. Repository name: amazon-listing-manager
3. Description: Amazon Listing Manager - SP-API integration
4. Public select karein (FREE hai)
5. "Create repository" click karein
```

### 2.3 Code Upload

**Command Prompt open karein:**

```bash
cd D:\Kimi\amazon-listing-manager

# Git initialize
git init

# Files add karein
git add .

# Commit karein
git commit -m "Initial commit for Render deployment"

# GitHub se connect
git remote add origin https://github.com/YOUR_USERNAME/amazon-listing-manager.git

# Push karein
git push -u origin main
```

**Note:** `YOUR_USERNAME` ko aapke GitHub username se replace karein

**Done!** ✅ GitHub pe code upload ho gaya

---

## 📋 STEP 3: Render Deploy (10 min)

### 3.1 Account Create
```
https://render.com par jayein
"Get Started" click karein
GitHub se connect karein
```

### 3.2 New Web Service
```
Dashboard par "New +" button click karein
"Web Service" select karein
```

### 3.3 GitHub Connect
```
"Connect GitHub" click karein
"amazon-listing-manager" repository select karein
"Connect" click karein
```

### 3.4 Configure Service

**Fill karein:**

```
Name: amazon-listing-manager
Region: Singapore (India ke liye closest)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn run:app
Plan: Free
```

### 3.5 Environment Variables (Important!)

**"Environment" tab click karein**

**Add these one by one:**

```
Key: SECRET_KEY
Value: (python -c "import secrets; print(secrets.token_urlsafe(32))" se generate karein)
```

```
Key: MONGODB_URI
Value: (Step 1.5 se copy kiya hua connection string)
```

```
Key: AWS_ACCESS_KEY_ID
Value: (Aapka AWS Access Key)
```

```
Key: AWS_SECRET_ACCESS_KEY
Value: (Aapka AWS Secret Key)
```

```
Key: AWS_REGION
Value: us-east-1
```

```
Key: LWA_CLIENT_ID
Value: (Amazon Developer Console se)
```

```
Key: LWA_CLIENT_SECRET
Value: (Amazon Developer Console se)
```

```
Key: SP_API_ROLE_ARN
Value: (AWS IAM Role ARN)
```

```
Key: AMAZON_REDIRECT_URI
Value: https://amazon-listing-manager.onrender.com/auth/amazon/callback
```

```
Key: SANDBOX_REFRESH_TOKEN
Value: (Amazon Developer Console se sandbox credentials)
```

```
Key: SANDBOX_SELLER_ID
Value: (Sandbox Seller ID)
```

**"Save Changes" click karein**

### 3.6 Deploy!

**"Create Web Service" button click karein**

Build process start hoga (3-5 minutes)

Logs mein dikhega:
- Installing dependencies
- Building app
- Deploying

**"Your service is live" message aane par ready!**

---

## 📋 STEP 4: Test Karein (2 min)

### 4.1 URL Check
```
Render Dashboard mein URL milega:
https://amazon-listing-manager.onrender.com

Browser mein open karein
```

### 4.2 First Visit
```
⚠️ Pehli baar 30-60 sec lag sakta hai (wake up time)
"This service has been suspended" message dikhe toh wait karein

Baad mein fast chalega
```

### 4.3 Register & Test
```
1. Register karein (email/password)
2. Login karein
3. Settings → Amazon Settings
4. Sandbox connect karein
5. Listings search karein
```

---

## 🎉 Done! Aapka App Live Hai!

**URL:** `https://amazon-listing-manager.onrender.com`

**Features:**
- ✅ FREE hosting
- ✅ MongoDB database (data safe)
- ✅ Auto-deploy from GitHub
- ✅ Custom subdomain
- ✅ SSL enabled

---

## 📝 Important Notes

### Sleep Mode
```
15 min inactivity ke baad app "sleep" hota hai
First visit mein 30-60 sec lagta hai
Uske baad fast chalta hai

Solution: Paid plan ($7/month) = Never sleeps
```

### Data Safety
```
✅ MongoDB Atlas mein data safe hai
✅ Daily backups automatic
✅ 512MB free storage (sufficient for small-medium use)
```

### Updates
```
Local machine pe changes karein:
git add .
git commit -m "Update description"
git push origin main

Auto-deploy Render pe!
```

---

## 🆘 Common Issues

### Issue 1: "Build failed"
```bash
Solution: requirements.txt check karein
          Sab packages correctly spelled hai ya check karein
```

### Issue 2: "MongoDB connection failed"
```bash
Solution: 1. MONGODB_URI check karein
          2. Password correctly filled hai ya check karein
          3. MongoDB Atlas mein Network Access: 0.0.0.0/0 hai ya check karein
```

### Issue 3: "App sleeping"
```bash
Solution: Normal hai! First visit mein wait karein
          30-60 sec mein app active ho jayega
```

---

## 🚀 Next Steps

1. ✅ App test karein
2. ✅ Amazon Sandbox connect karein
3. ✅ Listings manage karein
4. ✅ Custom domain add karein (optional)

---

**Koi step mein help chahiye? Main real-time guide kar sakta hoon!** 🎉
