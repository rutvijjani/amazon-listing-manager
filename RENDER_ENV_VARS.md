# Render Environment Variables Setup

## 📋 Step-by-Step Guide

### Step 1: Web Service Create Karein

1. **Render Dashboard** par jayein: https://dashboard.render.com
2. **"New +"** button click karein
3. **"Web Service"** select karein
4. **GitHub repo connect** karein: `amazon-listing-manager`
5. **"Connect"** click karein

### Step 2: Basic Settings Fill Karein

```
Name: amazon-listing-manager
Region: Singapore
Branch: master
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn run:app
```

### Step 3: Environment Variables Add Karein

**Niche scroll karein → "Environment" section milega**

**"Add Environment Variable"** button click karein

**Ek-ek karke yeh add karein:**

#### Variable 1: SECRET_KEY
```
Key: SECRET_KEY
Value: (niche se generate karein)
```

**SECRET_KEY Generate karein:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Ya online: https://djecrety.ir/

Example output: `dwefrwef23r23r23r23r23r23r23r23r23r`

---

#### Variable 2: MONGODB_URI
```
Key: MONGODB_URI
Value: mongodb+srv://rnjani911_db_user:PASSWORD@cluster0.gti1gwq.mongodb.net/amazon_listings?retryWrites=true&w=majority
```

**Note:** PASSWORD ko aapka actual password se replace karein

---

#### Variable 3-11: Baaki Credentials

| Key | Value (Aapke credentials) |
|-----|---------------------------|
| `AWS_ACCESS_KEY_ID` | AKIA... |
| `AWS_SECRET_ACCESS_KEY` | xxxxx... |
| `AWS_REGION` | us-east-1 |
| `LWA_CLIENT_ID` | amzn1.application-oa2-client... |
| `LWA_CLIENT_SECRET` | xxxxx... |
| `SP_API_ROLE_ARN` | arn:aws:iam::...:role/... |
| `AMAZON_REDIRECT_URI` | https://amazon-listing-manager.onrender.com/auth/amazon/callback |
| `SANDBOX_REFRESH_TOKEN` | Atzr\|IwEB... |
| `SANDBOX_SELLER_ID` | A1... |

---

### Step 4: Save & Deploy

1. **"Create Web Service"** button click karein
2. **Wait 3-5 minutes** for build
3. **Green tick** = Success!

---

## 📸 Screenshot Reference

```
┌─────────────────────────────────────────┐
│  Environment Variables                  │
│                                         │
│  ┌──────────────┬─────────────────────┐ │
│  │ SECRET_KEY   │ dwefrwef23r...      │ │
│  ├──────────────┼─────────────────────┤ │
│  │ MONGODB_URI  │ mongodb+srv://...   │ │
│  ├──────────────┼─────────────────────┤ │
│  │ AWS_ACCESS_  │ AKIA...             │ │
│  │ KEY_ID       │                     │ │
│  └──────────────┴─────────────────────┘ │
│                                         │
│  [+ Add Environment Variable]           │
└─────────────────────────────────────────┘
```

---

## 🔒 Security Note

**Environment variables Render ke secure vault mein store hote hain:**
- ✅ GitHub pe nahi dikhte
- ✅ Public access nahi hai
- ✅ Encrypted storage

---

## ✅ Verify Karein

Deploy ke baad:
1. **Render Dashboard** → Aapki service
2. **"Environment"** tab click karein
3. Sab variables correctly saved hain ya check karein

---

**Ready? Variables add karein aur deploy karein!** 🚀
