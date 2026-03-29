# 🚀 Amazon Listing Manager - Deployment Ready

## 📦 What's Included

```
amazon-listing-manager/
├── app/                    # Main Flask application
├── venv/                   # Virtual environment (created after setup)
├── .env                    # Configuration file (created by you)
├── run.py                  # Entry point
├── start.bat               # Windows startup script
├── setup.py                # Setup wizard
├── requirements.txt        # Python dependencies
├── DEPLOY.md              # Deployment guide
└── README.md              # Full documentation
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Double Click
```
start.bat
```

### Step 2: Configure
```
python setup.py
```
Ya manually `.env` file edit karein

### Step 3: Run
```
python run.py
```

---

## 🔧 Configuration

### Sandbox Mode (Testing)
1. Amazon Developer Console se credentials download karein
2. `.env` file mein fill karein:
```env
SANDBOX_REFRESH_TOKEN=Atzr|...
SANDBOX_SELLER_ID=A1...
```

### Production Mode
1. OAuth app configure karein
2. IAM role setup karein
3. `.env` mein production credentials

---

## 🌐 Access URLs

| URL | Description |
|-----|-------------|
| http://localhost:5000 | Local access |
| http://192.168.x.x:5000 | Network access |

---

## 📝 Usage Flow

1. **Register** → http://localhost:5000/auth/register
2. **Login** → Email/Password
3. **Connect Amazon** → Settings > Amazon Settings
4. **Search Listings** → Listings > Search
5. **Update** → Edit individual or Bulk CSV

---

## 🚀 Deployment Options

| Platform | Difficulty | Cost | Best For |
|----------|-----------|------|----------|
| PythonAnywhere | Easy | Free | Testing/Small use |
| Heroku | Easy | Free/Paid | Quick deploy |
| VPS (AWS/DigitalOcean) | Medium | Paid | Production |
| Docker | Medium | Varies | Scalable |

See `DEPLOY.md` for detailed instructions.

---

## 🛠️ Troubleshooting

### App won't start
```bash
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database errors
```bash
# Delete and recreate database
del app.db
python run.py
```

### Amazon connection fails
- Check `.env` credentials
- Verify Seller ID
- Check IAM role permissions

---

## 🔒 Security Checklist

- [ ] Strong SECRET_KEY in production
- [ ] HTTPS enabled
- [ ] .env file in .gitignore
- [ ] Database backups scheduled
- [ ] Rate limiting enabled

---

## 📞 Support

Errors? Check:
1. Flask debug output
2. Browser console
3. Network tab for API errors

---

**Ready to deploy! 🎉**

Choose your deployment method from DEPLOY.md and get started!
