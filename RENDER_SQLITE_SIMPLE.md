# 🚀 Render Deployment - Simple Method (SQLite)

## ⚡ Overview
Agar aapko abhi **simple setup** chahiye bina MongoDB ke, toh Render + SQLite use karein.

**Note:** Render free mein filesystem temporary hota hai (daily reset), isliye SQLite data daily reset hoga. Testing ke liye okay hai, production ke liye PostgreSQL better hai.

---

## 📋 Simple Steps (No MongoDB)

### Step 1: GitHub Repo Create
```
1. GitHub.com par jayein
2. New repository → "amazon-listing-manager"
3. Public select karein
```

### Step 2: Code Upload
```bash
cd D:\Kimi\amazon-listing-manager
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/amazon-listing-manager.git
git push -u origin main
```

### Step 3: Render Deploy
```
1. Render.com par jayein
2. "New +" → "Web Service"
3. GitHub connect karein
4. Repository select karein
5. Settings:
   - Name: amazon-listing-manager
   - Region: Singapore
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn run:app
```

### Step 4: Environment Variables
```
SECRET_KEY=your-super-secret-key-32-chars-long
DATABASE_URL=sqlite:///tmp/app.db
TOKEN_ENCRYPTION_KEY=your-key
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
# ... baaki sab credentials
```

### Step 5: Done!
URL milega: `https://amazon-listing-manager.onrender.com`

---

## ⚠️ Important Note

**SQLite on Render Free:**
- Daily data reset hota hai
- Har 24 hours baad database fresh hota
- Testing ke liye okay
- Production ke liye **PostgreSQL** use karein

---

## 🎯 Better Solution: Render PostgreSQL (Free)

Render free PostgreSQL bhi offer karta hai (90 days valid).

### PostgreSQL Setup:
```
1. Render Dashboard → "New +" → "PostgreSQL"
2. Name: amazon-listing-db
3. Region: Singapore
4. Free plan select karein
5. "Create"
6. Connection string copy karein
```

### .env mein:
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**SQLite se better hai!** Data permanent rahega.

---

## 💡 Recommendation

| Use Case | Database | Duration |
|----------|----------|----------|
| Testing only | SQLite | Temporary |
| Production | PostgreSQL | 90 days free |
| Long term | MongoDB Atlas | Forever free (512MB) |

**Best combination:** Render + MongoDB Atlas (donon free forever!)

---

Full guide: `RENDER_MONGODB_DEPLOY.md`
