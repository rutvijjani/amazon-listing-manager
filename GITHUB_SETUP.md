# GitHub Setup - Step by Step

## 🎯 Goal: Code ko GitHub pe upload karna

---

## Step 1: GitHub Account Check

1. **https://github.com** par jayein
2. Login karein (agar account nahi hai toh signup karein)

---

## Step 2: New Repository Create

1. **Green "+" button** (top right) ya **"New"** button click karein
2. **"New repository"** select karein

### Fill karein:
```
Repository name: amazon-listing-manager
Description: Amazon Listing Manager with SP-API integration
Public (select karein - FREE hai)
```

3. **"Create repository"** click karein

**Note:** "Initialize with README" UNCHECK karein (kyunki code already hai)

---

## Step 3: Code Upload

### Command Prompt (CMD) mein:

```bash
# Project folder mein jayein
cd D:\Kimi\amazon-listing-manager

# Check if git already initialized
dir /a

# Agar .git folder hai toh skip karein, nahi hai toh:
git init

# Sab files add karein
git add .

# Commit karein
git commit -m "Initial commit for Render deployment"

# GitHub se connect (USERNAME ko aapka GitHub username se replace karein)
git remote add origin https://github.com/USERNAME/amazon-listing-manager.git

# Push karein
git push -u origin main
```

### Agar Error Aaye:

**Error 1: "already initialized"**
```bash
# Ignore karein, next step karein
```

**Error 2: "main" nahi mila**
```bash
git branch -m master main
git push -u origin main
```

**Error 3: "Authentication failed"**
```bash
# Browser mein login karein
# Ya Personal Access Token use karein
```

---

## Step 4: Verify

1. **GitHub par refresh** karein
2. **Sab files dikhne chahiye** (app/, run.py, requirements.txt, etc.)

---

## ✅ Done! GitHub Ready

Ab **Render** pe deploy karein!

**GitHub repo URL milega:**
```
https://github.com/USERNAME/amazon-listing-manager
```

**Is URL ko save karein - Render mein chahiye!**
