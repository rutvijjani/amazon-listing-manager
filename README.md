# Amazon Listing Manager

A web-based application for managing Amazon product listings through the Selling Partner API (SP-API). Supports multiple sellers, partial updates, and bulk operations.

## Features

- **Multi-Seller Support**: Multiple Amazon sellers can connect their accounts
- **Partial Listing Updates**: Update only specific fields (price, inventory, content)
- **Bulk Operations**: CSV upload for mass updates
- **Real-time Search**: Search products by keywords or ASINs
- **Update Logs**: Complete audit trail of all changes
- **Secure Token Storage**: Encrypted OAuth token storage

## Supported Operations

### Price Updates
- Regular price
- Sale price with date range
- Currency support (INR, USD, EUR, GBP)

### Inventory Updates
- Available quantity
- Fulfillment channel (FBM/FBA)

### Content Updates
- Product title
- Description
- Bullet points (5 max)
- Search terms

## Tech Stack

- **Backend**: Python 3.8+, Flask
- **Frontend**: HTML, Bootstrap 5, Vanilla JavaScript
- **Database**: SQLite (dev), PostgreSQL (production)
- **API**: Amazon Selling Partner API (SP-API)

## Prerequisites

1. Python 3.8 or higher
2. Amazon Seller Central account with Professional plan
3. Amazon Developer account with SP-API access
4. AWS IAM credentials

## Installation

### 1. Clone/Extract the Project

```bash
cd amazon-listing-manager
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Flask
SECRET_KEY=your-super-secret-key

# Amazon SP-API
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
LWA_CLIENT_ID=amzn1.application-oa2-client....
LWA_CLIENT_SECRET=...
SP_API_ROLE_ARN=arn:aws:iam::...:role/YourSPAPIRole
AMAZON_REDIRECT_URI=http://localhost:5000/auth/amazon/callback

# Optional: Generate with python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TOKEN_ENCRYPTION_KEY=your-encryption-key
```

### 5. Run the Application

```bash
python run.py
```

The app will be available at: http://localhost:5000

## Local QA

Before pushing to Render, run the local smoke suite:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_local_qa.ps1
```

What it checks:
- app boots and `/health` responds
- register/login flow still works
- Amazon settings page loads
- manual update page loads for a connected seller
- bulk update page loads for a connected seller
- listing search failures render a user-facing message instead of raw 500s

If the script says the local venv is broken, recreate it and reinstall dependencies:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Amazon SP-API Setup

### 1. Register as Amazon Developer

1. Go to [Amazon Developer Console](https://developer.amazon.com/)
2. Create a developer account
3. Navigate to "Selling Partner API"

### 2. Create SP-API Application

1. Go to Apps & Services > Develop Apps
2. Click "Add new app"
3. Fill in details:
   - App name: "Listing Manager"
   - API type: "Selling Partner API"
   - OAuth Login URI: `http://localhost:5000/auth/amazon/callback`
   - OAuth Redirect URI: `http://localhost:5000/auth/amazon/callback`
4. Select required roles:
   - Product Catalog
   - Listings Write
   - Inventory Write
   - Pricing Write

### 3. AWS IAM Setup

1. Create IAM Policy for SP-API:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "execute-api:Invoke",
            "Resource": "arn:aws:execute-api:*:*:*"
        }
    ]
}
```

2. Create IAM Role:
   - Trusted entity: `arn:aws:iam::...:user/your-iam-user`
   - Attach the policy created above

3. Get Role ARN from role summary page

### 4. Get LWA Credentials

From your app in Developer Console:
- Client ID (LWA_CLIENT_ID)
- Client Secret (LWA_CLIENT_SECRET)

## Usage

### 1. Register/Login

1. Open http://localhost:5000
2. Register a new account or login
3. You'll see the dashboard

### 2. Connect Amazon Account

1. Go to "Amazon Settings" from the dropdown menu
2. Select your marketplace (e.g., Amazon.in)
3. Login with your Amazon Seller credentials
4. Enter your Seller ID (found in Seller Central)

### 3. Search Listings

1. Go to "Listings" > "Search Listings"
2. Enter keywords or ASINs
3. View and manage your products

### 4. Update Single Listing

1. Search for a product
2. Click "Edit" on the desired product
3. Update price, inventory, or content
4. Click update button

### 5. Bulk Update

1. Go to "Listings" > "Bulk Update"
2. Download the appropriate template
3. Fill in your data (SKU is required)
4. Upload the CSV file
5. Monitor the progress

## CSV Templates

### Price Update Template
```csv
sku,price,currency,sale_price
SKU001,999.00,INR,899.00
SKU002,1499.00,INR,
```

### Inventory Update Template
```csv
sku,quantity,fulfillment_channel
SKU001,100,DEFAULT
SKU002,50,AMAZON
```

### Content Update Template
```csv
sku,title,description,bullet_points
SKU001,New Title,New Description,Point 1|Point 2|Point 3
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/amazon/connect` - Initiate Amazon OAuth
- `GET /auth/amazon/callback` - OAuth callback

### Listings
- `GET /listings/search?q=keywords` - Search listings
- `GET /listings/item/<asin>` - Get item details
- `GET /listings/edit/<sku>` - Edit listing form
- `POST /listings/edit/<sku>` - Update listing
- `GET /listings/bulk-update` - Bulk update form
- `POST /listings/bulk-update` - Process bulk update
- `GET /listings/logs` - View update logs

### API (AJAX)
- `GET /api/search-items?q=query` - Search items (JSON)
- `GET /api/item/<asin>` - Get item details (JSON)
- `POST /api/update-price` - Update price (JSON)
- `POST /api/update-inventory` - Update inventory (JSON)
- `GET /api/stats` - Get dashboard stats

## Production Deployment

### Environment Variables

Update for production:
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=strong-random-key
AMAZON_REDIRECT_URI=https://yourdomain.com/auth/amazon/callback
```

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

## Troubleshooting

### "Amazon account not connected" error
- Check if you've completed the OAuth flow
- Verify Seller ID is entered correctly

### "Access Denied" error
- Verify AWS credentials are correct
- Check IAM role has proper permissions
- Ensure SP-API application is approved

### "Token expired" error
- Tokens refresh automatically
- If persistent, disconnect and reconnect Amazon account

### Rate Limiting
Amazon SP-API has rate limits. If you hit limits:
- Reduce bulk update batch size
- Add delays between requests
- Use feeds API for large batches

## Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Token Encryption**: Refresh tokens are encrypted at rest
3. **Session Security**: Use secure cookies in production
4. **Input Validation**: All user inputs are validated
5. **Rate Limiting**: Implement rate limiting for production

## Marketplaces Supported

| Marketplace ID | Name |
|---------------|------|
| A21TJRUUN4KGV | India |
| ATVPDKIKX0DER | United States |
| A1F83G8C2ARO7P | United Kingdom |
| A1PA6795UKMFR9 | Germany |
| APJ6JRA9NG5V4 | Italy |
| A13V1IB3VIYZZH | France |
| A1RKKUPIHCS9HS | Spain |
| A2EUQ1WTGCTBG2 | Canada |
| A1VC38T7YXB528 | Japan |
| A39IBJ37TRP1C6 | Australia |

And many more...

## License

MIT License

## Support

For issues and feature requests, please create an issue in the repository.

## Disclaimer

This is an unofficial tool and is not affiliated with Amazon. Use at your own risk. Always test thoroughly before making bulk updates to live listings.

