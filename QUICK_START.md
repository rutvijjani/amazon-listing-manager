# Quick Start - Sandbox Mode (5 Minutes)

## Aapke paas jo hai:
✅ Amazon Developer Console with Sandbox apps  
✅ "View sandbox credentials" link available

## Chahiye:
⬜ Sandbox credentials file download karna  
⬜ .env file mein values fill karna  
⬜ App run karna

---

## Step 1: Credentials Download (2 min)

### Screenshot mein jo dikh raha hai usme se:
1. **"Basics"** app ke saamne **"View sandbox credentials"** click karein
2. JSON file download hogi ya values dikh jayengi

### Copy karein ye values:
```
refresh_token  →  Atzr|IwEB...
access_key_id  →  AKIA...
secret_key     →  abcd1234...
role_arn       →  arn:aws:iam::123456789012:role/...
seller_id      →  A1XXXXXXXXXX
```

---

## Step 2: .env File Fill (2 min)

`amazon-listing-manager/.env` file open karein aur fill karein:

```env
# =====================================
# YEH VALUES SANDBOX FILE SE COPY KAREIN
# =====================================
AWS_ACCESS_KEY_ID=AKIA...(access_key_id)
AWS_SECRET_ACCESS_KEY=abcd1234...(secret_key)
SP_API_ROLE_ARN=arn:aws:iam::123456789012:role/...(role_arn)

SANDBOX_REFRESH_TOKEN=Atzr|IwEB...(refresh_token)
SANDBOX_SELLER_ID=A1XXXXXXXXXX...(seller_id)
SANDBOX_MARKETPLACE_ID=A21TJRUUN4KGV  # India ke liye

# =====================================
# YEH VALUES AMAZON DEVELOPER CONSOLE SE
# =====================================
LWA_CLIENT_ID=amzn1.application-oa2-client...(App ki ID)
LWA_CLIENT_SECRET=...(App ka secret)

# =====================================
# YEH GENERATE KAREIN (Ek baar)
# =====================================
TOKEN_ENCRYPTION_KEY=(python se generate karein - neeche dekhein)
```

### Encryption Key Generate:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Output copy karke `TOKEN_ENCRYPTION_KEY=` ke aage paste karein.

---

## Step 3: App Run (1 min)

```bash
# CMD ya Terminal mein:
cd amazon-listing-manager

# Pehli baar setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# App start
python run.py
```

Browser mein: http://localhost:5000

---

## Step 4: Connect Karein

1. **Register** karein (email, password)
2. **Login** karein
3. Dashboard par **"Quick Sandbox Connect"** button click karein
4. Done! 🎉

---

## Screenshot mein Check karein:

### Agar "View" link dikh raha hai "AB basic" app mein:
→ Pehle "Edit App" click karein, fir "View sandbox credentials"

### Agar "View sandbox credentials" dikh raha hai:
→ Seedha click karein aur values copy karein

---

## Common Errors:

| Error | Solution |
|-------|----------|
| `SANDBOX_REFRESH_TOKEN not configured` | .env mein value fill karein |
| `Module not found` | `pip install -r requirements.txt` |
| `Access denied` | Credentials check karein, refresh token expiry ho sakta hai |

---

## Production Mode mein Kab?

Jab aap ready ho live listings manage karne ke liye:
1. Draft app ko Edit karein
2. OAuth configure karein
3. `.env` mein production credentials daale

**Abhi ke liye Sandbox testing perfect hai!** ✅
