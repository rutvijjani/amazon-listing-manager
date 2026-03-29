# Sandbox Mode Setup Guide

## Overview
Sandbox mode mein aap **bina OAuth flow** ke direct credentials use kar sakte hain. Ye testing ke liye best hai.

---

## Step 1: Sandbox Credentials Download Karein

### Amazon Developer Console mein:
1. **Apps & Services > Develop Apps** par jayein
2. **"Basics"** ya **"aB"** app ke saamne **"View sandbox credentials"** click karein
3. **Download** karein ya **copy** karein

### Aapko ye milega:
```json
{
  "refresh_token": "Atzr|IwEB...",
  "access_key_id": "AKIA...",
  "secret_key": "abcd1234...",
  "role_arn": "arn:aws:iam::123456789012:role/SandboxRole",
  "seller_id": "A1XXXXXXXXXX"
}
```

---

## Step 2: .env File Update Karein

`.env` file mein yeh values fill karein:

```env
# AWS Credentials (from sandbox file)
AWS_ACCESS_KEY_ID=AKIA... (access_key_id)
AWS_SECRET_ACCESS_KEY=abcd1234... (secret_key)
AWS_REGION=us-east-1

# LWA Credentials (Developer Console se)
LWA_CLIENT_ID=amzn1.application-oa2-client.xxxxx
LWA_CLIENT_SECRET=xxxxx

# Role ARN (from sandbox file)
SP_API_ROLE_ARN=arn:aws:iam::123456789012:role/SandboxRole

# Direct Sandbox Credentials
SANDBOX_REFRESH_TOKEN=Atzr|IwEB...
SANDBOX_SELLER_ID=A1XXXXXXXXXX
SANDBOX_MARKETPLACE_ID=A21TJRUUN4KGV
```

---

## Step 3: App Run Karein

```bash
# Pehli baar setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Encryption key generate karein (ek baar)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Output ko .env mein TOKEN_ENCRYPTION_KEY mein paste karein

# App start karein
python run.py
```

Browser: http://localhost:5000

---

## Step 4: Auto-Connect Feature

Jab aap app mein register/login karein, toh **automatic sandbox connection** ho jayegi. Aapko manually Amazon connect karne ki zarurat nahi!

### Dashboard par aapko dikhayega:
```
✅ Connected: Amazon.in (Sandbox)
Seller ID: A1XXXXXXXXXX
```

---

## Sandbox vs Production

| Feature | Sandbox | Production |
|---------|---------|------------|
| Real data | ❌ Fake data | ✅ Real listings |
| OAuth | ❌ Not needed | ✅ Required |
| Credentials | Direct JSON file | IAM + OAuth flow |
| Testing | ✅ Free testing | Live changes |

---

## Common Issues

### Issue: "Invalid refresh token"
**Solution:** 
- Sandbox credentials expire hote hain, naya download karein
- Ensure `SANDBOX_REFRESH_TOKEN` correct hai

### Issue: "Access Denied"  
**Solution:**
- `AWS_ACCESS_KEY_ID` aur `AWS_SECRET_ACCESS_KEY` check karein
- `SP_API_ROLE_ARN` correct hai ya nahi

### Issue: "Seller ID not found"
**Solution:**
- `SANDBOX_SELLER_ID` fill karein
- Ya auto-connect feature use karein

---

## Production mein Jane ke liye

Jab aap production ready ho:

1. **"AB basic"** app ko **Edit** karein
2. Status **"Draft"** se **"Publish"** karein
3. OAuth settings configure karein
4. `.env` mein production credentials daale

---

## Quick Checklist

- [ ] Sandbox credentials download kiye
- [ ] `.env` file update ki
- [ ] Dependencies install kiye
- [ ] App run ki
- [ ] Dashboard par "Connected" status check kiya

**Ready to test! 🎉**
