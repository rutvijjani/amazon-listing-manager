# 🚀 Render + MongoDB Atlas Deployment Guide

## 💡 Why This Combo?
- **Render**: Free hosting, auto-deploy from GitHub
- **MongoDB Atlas**: Free 512MB database (forever)
- **Total Cost**: ₹0

---

## 📋 Step 1: MongoDB Atlas (10 min)

### 1.1 Account Create
- https://www.mongodb.com/cloud/atlas
- "Try Free" → Google/GitHub signup

### 1.2 Cluster Create
```
1. "Create" button
2. "Shared Cluster (FREE)"
3. Provider: AWS
4. Region: Mumbai (ap-south-1) ← Best for India
5. Wait 2-3 minutes
```

### 1.3 Security Setup
```
Database Access:
- Username: admin
- Password: Auto-generate → COPY AND SAVE

Network Access:
- Add IP: 0.0.0.0/0 (for Render)
```

### 1.4 Get Connection String
```
Connect → Connect App → Python → 3.11+
Copy the connection string
```

**⚠️ Save this string - you'll need it in Render!**

---

## 📋 Step 2: GitHub Setup

Already done! Your code is at:
```
https://github.com/rutvijjani/amazon-listing-manager
```

---

## 📋 Step 3: Render Deploy (15 min)

### 3.1 Account
- https://render.com
- Sign up with GitHub

### 3.2 New Web Service
```
New + → Web Service
Connect GitHub → Select: amazon-listing-manager
```

### 3.3 Configure
```
Name: amazon-listing-manager
Region: Singapore
Branch: master
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn run:app
Plan: Free
```

### 3.4 Environment Variables

**Click "Environment" tab and add these:**

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (Generate: python -c "import secrets; print(secrets.token_urlsafe(32))") |
| `MONGODB_URI` | (Your MongoDB connection string from Step 1.4) |
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Key |
| `AWS_REGION` | us-east-1 |
| `LWA_CLIENT_ID` | Your Amazon LWA Client ID |
| `LWA_CLIENT_SECRET` | Your Amazon LWA Secret |
| `SP_API_ROLE_ARN` | Your AWS IAM Role ARN |
| `AMAZON_REDIRECT_URI` | https://amazon-listing-manager.onrender.com/auth/amazon/callback |
| `SANDBOX_REFRESH_TOKEN` | Your Sandbox Refresh Token |
| `SANDBOX_SELLER_ID` | Your Sandbox Seller ID |

### 3.5 Deploy
```
Click: Create Web Service
Wait: 3-5 minutes for build
```

---

## ✅ Done!

**Your app is live at:**
```
https://amazon-listing-manager.onrender.com
```

---

## ⚠️ Free Tier Limitations

| Feature | Limit |
|---------|-------|
| Sleep | After 15 min inactivity |
| First visit | 30-60 sec delay |
| Database | 512 MB (sufficient) |
| Bandwidth | 100 GB/month |

**To avoid sleep:** Upgrade to Paid ($7/month)

---

## 🔄 Updates

When you update code locally:
```bash
git add .
git commit -m "Your changes"
git push origin master
```

Auto-deploys to Render!

---

**Need help? Check the logs in Render dashboard!** 🚀
