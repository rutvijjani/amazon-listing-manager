# Amazon Listing Manager - Setup Guide

## Step 1: Environment Variables Configure Karein

`.env` file open karein aur ye values fill karein:

### AWS Credentials (IAM User se)
```env
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
```

### LWA Credentials (Amazon Developer Console se)
```env
LWA_CLIENT_ID=amzn1.application-oa2-client.xxxxxxxxxxxxxxxxxxxxxxx
LWA_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### SP-API Role ARN (AWS IAM > Roles se)
```env
SP_API_ROLE_ARN=arn:aws:iam::123456789012:role/YourSPAPIRole
```

### Token Encryption Key Generate Karein
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Output ko copy karke `.env` mein paste karein:
```env
TOKEN_ENCRYPTION_KEY=generated-key-here
```

---

## Step 2: App Run Karein

### Pehli Baar Setup:
```bash
# Virtual environment create karein
python -m venv venv

# Activate karein (Windows)
venv\Scripts\activate

# Dependencies install karein
pip install -r requirements.txt
```

### App Start Karein:
```bash
python run.py
```

Browser mein open karein: **http://localhost:5000**

---

## Step 3: Amazon Developer Console mein OAuth Settings

1. **Amazon Developer Console** par jayein
2. **Apps & Services > Develop Apps** par click karein
3. Apni app select karein
4. Ye settings ensure karein:

| Setting | Value |
|---------|-------|
| OAuth Login URI | `http://localhost:5000/auth/amazon/callback` |
| OAuth Redirect URI | `http://localhost:5000/auth/amazon/callback` |
| OAuth Grant Type | `Auth Code Grant` |

5. **App Settings** mein ye scopes add karein:
   - ✅ `sellingpartnerapi::read_product_catalog`
   - ✅ `sellingpartnerapi::listings_write`
   - ✅ `sellingpartnerapi::inventory_write`
   - ✅ `sellingpartnerapi::pricing_write`

---

## Step 4: App Use Karein

### 1. Register/Login
- http://localhost:5000 par jayein
- Account create karein

### 2. Amazon Account Connect Karein
- Top right menu > "Amazon Settings" par click karein
- "Connect Amazon Account" button par click karein
- Apna Amazon Seller account se login karein
- Authorization dein
- **Seller ID** enter karein (Amazon Seller Central se mil sakta hai)

### 3. Listings Search Karein
- "Listings" > "Search Listings" par jayein
- Keywords ya ASIN se search karein

### 4. Single Listing Update Karein
- Search results mein "Edit" par click karein
- Price, Inventory, ya Content update karein

### 5. Bulk Update (CSV)
- "Bulk Update" par jayein
- Template download karein
- CSV fill karein
- Upload karein

---

## Common Issues & Solutions

### Issue: "Access Denied" Error
**Solution:** IAM Role permissions check karein:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/YOUR_IAM_USER"
            }
        }
    ]
}
```

### Issue: "Invalid Client" Error
**Solution:** `.env` mein `LWA_CLIENT_ID` aur `LWA_CLIENT_SECRET` check karein. Ye Amazon Developer Console se exact copy karein.

### Issue: "Redirect URI Mismatch"
**Solution:** Ensure `AMAZON_REDIRECT_URI` same hai jo Amazon Developer Console mein configure kiya hai.

---

## Sandbox vs Production

### Sandbox Testing:
Amazon SP-API sandbox endpoints automatic use hote hain jab app register nahi hota. 

### Production:
Jab app approved ho jaaye toh production endpoints use honge automatically.

---

## Important Security Notes

1. **`.env` file ko kabhi Git par push mat karein!** (already `.gitignore` mein hai)
2. Production mein `FLASK_ENV=production` set karein
3. Strong `SECRET_KEY` use karein
4. HTTPS use karein production mein

---

## Support

Agar koi issue aaye toh:
1. Flask console errors check karein
2. `logs/` directory check karein (create karna padega)
3. Amazon SP-API documentation refer karein

**App ready hai! 🎉**
