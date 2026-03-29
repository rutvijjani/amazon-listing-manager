# Deployment Guide - Amazon Listing Manager

## Local Development (Windows)

### Option 1: Double Click Start (Easiest)
1. `start.bat` file par double-click karein
2. Browser mein jayein: http://localhost:5000

### Option 2: Command Line
```bash
cd amazon-listing-manager
venv\Scripts\activate
python run.py
```

---

## Production Deployment Options

### Option 1: PythonAnywhere (Free Hosting)

1. **Account Create karein:** https://www.pythonanywhere.com

2. **Files Upload karein:**
   - ZIP banayein apne project ki
   - Upload karein Files section mein
   - Extract karein

3. **Virtual Environment Setup:**
```bash
mkvirtualenv --python=/usr/bin/python3.11 venv
pip install -r requirements.txt
```

4. **Web App Configure:**
   - Go to Web tab
   - Add new web app
   - Select Flask
   - Python 3.11
   - Path: `/home/yourusername/amazon-listing-manager/run.py`

5. **.env File Setup:**
   - Production credentials daalein
   - `SECRET_KEY` strong banayein

---

### Option 2: Heroku (Free/Paid)

1. **Files Create karein:**

`Procfile`:
```
web: gunicorn run:app
```

`runtime.txt`:
```
python-3.11.6
```

2. **Deploy karein:**
```bash
# Heroku CLI install karein
heroku login
heroku create your-app-name
git push heroku main
```

3. **Environment Variables:**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set AWS_ACCESS_KEY_ID=your-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-secret
# ... aur baaki sab
```

---

### Option 3: VPS/Dedicated Server (AWS, DigitalOcean, etc.)

1. **Server Setup:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
```

2. **App Setup:**
```bash
cd /var/www
mkdir amazon-listing-manager
cd amazon-listing-manager
# Upload files here

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

3. **Gunicorn Service:**

`/etc/systemd/system/amazon-listing.service`:
```ini
[Unit]
Description=Amazon Listing Manager
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/amazon-listing-manager
Environment="PATH=/var/www/amazon-listing-manager/venv/bin"
EnvironmentFile=/var/www/amazon-listing-manager/.env
ExecStart=/var/www/amazon-listing-manager/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app

[Install]
WantedBy=multi-user.target
```

4. **Nginx Config:**

`/etc/nginx/sites-available/amazon-listing`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /var/www/amazon-listing-manager/app/static;
    }
}
```

5. **Start Services:**
```bash
sudo systemctl start amazon-listing
sudo systemctl enable amazon-listing
sudo nginx -t
sudo systemctl restart nginx
```

---

## Important Production Changes

### 1. .env File Update karein:
```env
FLASK_ENV=production
SECRET_KEY=strong-random-key-here-at-least-32-chars
AMAZON_REDIRECT_URI=https://yourdomain.com/auth/amazon/callback
```

### 2. Database Upgrade karein:
```python
# SQLite se PostgreSQL/MySQL
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### 3. HTTPS Enable karein:
- Let's Encrypt SSL certificate
- Force HTTPS redirect

### 4. Security Headers Add karein:
```python
# app/__init__.py mein add karein
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

---

## Docker Deployment

### Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

### Build & Run:
```bash
docker build -t amazon-listing-manager .
docker run -p 5000:5000 --env-file .env amazon-listing-manager
```

---

## Monitoring

### Health Check Endpoint:
App already has `/` route jo status batata hai.

### Logs Check karein:
```bash
# systemd
cd /var/www/amazon-listing-manager
sudo journalctl -u amazon-listing -f
```

---

## Backup

### Database Backup:
```bash
# SQLite
sqlite3 app.db ".backup backup.db"

# PostgreSQL
pg_dump dbname > backup.sql
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Gunicorn check karein |
| Static files not loading | Nginx config check karein |
| Session lost | SECRET_KEY same hona chahiye |
| Database locked | SQLite mein multiple workers use nahi kar sakte |

---

## Recommended: PythonAnywhere (Free Tier)

Sabse easy aur free option hai. Steps:

1. Sign up: https://www.pythonanywhere.com
2. Upload code via ZIP
3. Create virtual environment
4. Install requirements
5. Create web app
6. Set environment variables
7. Done!

**Free tier mein:**
- 1 web app
- Daily reboot (timezone mein 11am)
- Limited CPU
- SQLite database (sufficient for small use)

---

**Koi specific deployment option chahiye toh batayein!** 🚀
