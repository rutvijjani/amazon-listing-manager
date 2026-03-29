# AWS IAM Setup for Amazon SP-API

## 📋 Overview
Amazon SP-API use karne ke liye AWS credentials chahiye:
- AWS Access Key ID
- AWS Secret Access Key  
- IAM Role ARN

**Ye sab FREE hai!**

---

## Step 1: AWS Account Create (Agar nahi hai toh)

1. **https://aws.amazon.com** par jayein
2. **"Create an AWS Account"** click karein
3. Email, password, account name fill karein
4. **"Continue"**
5. Personal information fill karein
6. Credit card add karein (verification ke liye, charge nahi hoga)
7. **"Free Tier"** select karein
8. Phone verification complete karein
9. **Basic Plan (Free)** select karein

**Note:** Free tier mein SP-API ke liye koi charges nahi hote!

---

## Step 2: IAM User Create

### 2.1 AWS Console Login
1. **https://console.aws.amazon.com** par jayein
2. Login karein

### 2.2 IAM Service Open Karein
```
Top search box mein type: IAM
"IAM" (Identity and Access Management) select karein
```

### 2.3 User Create Karein
```
Left sidebar → "Users" → "Add users"
```

**User details:**
```
User name: spapi-user
Click: "Next"
```

**Permissions:**
```
"Attach policies directly" select karein
Search: "IAMFullAccess"
Checkbox: ☑ IAMFullAccess
Click: "Next"
Click: "Create user"
```

### 2.4 Access Keys Create Karein

1. **Users list** mein **"spapi-user"** click karein
2. **"Security credentials"** tab click karein
3. **"Create access key"** click karein
4. **"Command Line Interface (CLI)"** select karein
5. Checkbox: ☑ I understand...
6. **"Next"** → **"Create access key"**

**⚠️ IMPORTANT: Ye keys COPY karein aur save karein!**

```
Access key ID: AKIA... (Yeh save karein - Render mein chahiye!)
Secret access key: xxxxx... (Yeh save karein - Render mein chahiye!)
```

**Note:** Secret key baad mein nahi dikhega, isliye abhi save karein!

---

## Step 3: IAM Role Create (SP-API ke liye)

### 3.1 Roles Page
```
Left sidebar → "Roles" → "Create role"
```

### 3.2 Trusted Entity
```
"AWS service" select karein
"EC2" select karein
Click: "Next"
```

### 3.3 Permissions
```
Search: "IAMReadOnlyAccess"
Checkbox: ☑ IAMReadOnlyAccess

Search: "AmazonEC2ReadOnlyAccess"  
Checkbox: ☑ AmazonEC2ReadOnlyAccess

Click: "Next"
```

### 3.4 Role Details
```
Role name: SPAPIRole
Role description: Role for Amazon Selling Partner API
Click: "Create role"
```

### 3.5 Role ARN Copy Karein

1. **Roles list** mein **"SPAPIRole"** click karein
2. **Top right** mein **"ARN"** copy karein:

```
arn:aws:iam::123456789012:role/SPAPIRole
```

**⚠️ Ye ARN save karein - Render mein chahiye!**

---

## Step 4: Trust Relationship Update (Important!)

### 4.1 Role Edit Karein
```
Roles → SPAPIRole → "Trust relationships" tab
"Edit trust policy" click karein
```

### 4.2 Policy Replace Karein

**Current policy hata ke yeh paste karein:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/spapi-user"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Replace `YOUR_ACCOUNT_ID`:**
- AWS Console top right mein account name ke neeche 12-digit number
- Example: `123456789012`

### 4.3 Save Karein
```
"Update policy" click karein
```

---

## Step 5: Summary - Render Ke Liye

Ab aapke paas ye credentials hain:

| Variable | Value |
|----------|-------|
| `AWS_ACCESS_KEY_ID` | AKIA... (Step 2.4 se) |
| `AWS_SECRET_ACCESS_KEY` | xxxxx... (Step 2.4 se) |
| `AWS_REGION` | us-east-1 |
| `SP_API_ROLE_ARN` | arn:aws:iam::...:role/SPAPIRole (Step 3.5 se) |

**Ye sab Render Environment Variables mein add karein!**

---

## 🎯 Quick Checklist

- [ ] AWS account created
- [ ] IAM user "spapi-user" created
- [ ] Access keys generated and saved
- [ ] IAM role "SPAPIRole" created
- [ ] Role ARN copied
- [ ] Trust policy updated

---

## 🆘 Common Issues

### Issue: "Access Denied"
**Solution:** IAM user ko "IAMFullAccess" policy attach karein

### Issue: "Role cannot be assumed"
**Solution:** Trust policy mein correct user ARN hai ya check karein

### Issue: "Invalid AWS credentials"
**Solution:** Access key aur secret key correctly copy kiye hain ya check karein

---

**Ready? Step 1 se shuru karein!** 🚀

Koi step mein problem aaye toh screenshot bhejein!
