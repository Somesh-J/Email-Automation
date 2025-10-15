# � Email Automation API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://www.mongodb.com/)

A production-ready email automation system built with FastAPI and MongoDB, featuring AI-powered auto-replies, bulk email sending, and comprehensive email management.

## ✨ Key Features

- 📧 **Email Management** - IMAP integration for receiving emails, SendGrid/Resend for sending
- 🤖 **AI Auto-Replies** - Powered by Google Gemini or OpenAI
- 🎯 **Domain Whitelist/Blacklist** - Control who can interact with your system
- 📬 **Bulk Email Sending** - Send to thousands with template support
- 📊 **Analytics & Monitoring** - Real-time dashboards and email metrics
- 🔒 **Secure** - API key authentication with rate limiting

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Somesh-J/Email-Automation.git
cd Email-Automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your credentials
notepad .env
```

**Required Configuration:**

```env
# MongoDB
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/

# Email Provider (choose one: resend or sendgrid)
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key_here
# OR
# SENDGRID_API_KEY=SG.your_api_key_here

# Email Settings
FROM_EMAIL=your-email@yourdomain.com
FROM_NAME=Your Name

# IMAP (for receiving emails)
IMAP_USERNAME=your-email@gmail.com
IMAP_PASSWORD=your-16-char-app-password

# AI (optional)
GEMINI_API_KEY=your-gemini-api-key

# Security
VALID_API_KEYS=["dev-key-123","test-key-456","prod-key-789"]
```

> **📖 Email Provider Setup:** See [EMAIL_PROVIDER_GUIDE.md](EMAIL_PROVIDER_GUIDE.md) for detailed instructions on setting up Resend or SendGrid.

### 3. Verify Setup

```bash
python test_setup.py
```

This checks all configurations and sends test emails to verify everything works.

### 4. Start the Server

```bash
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/v1/health/status

## 📚 API Endpoints

### Core Endpoints

```http
# Email Management
POST   /api/v1/email/ingest           # Receive email
GET    /api/v1/email/list             # List emails
POST   /api/v1/email/ai-reply         # Generate AI reply

# Domain Management
GET    /api/v1/domains/               # List domains
POST   /api/v1/domains/               # Add domain

# Bulk Email
POST   /api/v1/bulk/send              # Send bulk emails
GET    /api/v1/bulk/jobs              # List jobs

# Monitoring
GET    /api/v1/monitor/status         # Monitoring status
POST   /api/v1/monitor/start          # Start monitoring

# Health & Analytics
GET    /api/v1/health/status          # System health
GET    /api/v1/analytics/dashboard    # Dashboard stats
```

### Authentication

All endpoints require an API key:

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/domains/
```

## � Usage Examples

### Send Test Email

```bash
python send_test_email.py
```

### Send Bulk Email via API

```bash
curl -X POST "http://localhost:8000/api/v1/bulk/send" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Campaign",
    "subject": "Welcome!",
    "body": "Hello, thanks for joining!",
    "recipients": ["user1@example.com", "user2@example.com"]
  }'
```

### Add Allowed Domain

```bash
curl -X POST "http://localhost:8000/api/v1/domains/" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "is_allowed": true,
    "auto_reply_enabled": true
  }'
```

## 📁 Project Structure

```
Email-Automation/
├── api/                      # API routes and models
│   ├── models.py
│   └── routes/
├── core/                     # Core functionality
│   ├── config.py            # Configuration
│   ├── database.py          # MongoDB manager
│   ├── mongo_models.py      # Data models
│   ├── logger.py
│   └── security.py
├── services/                 # Business logic
│   ├── ai_service.py
│   ├── email_service.py
│   ├── sendgrid_service.py
│   ├── resend_service.py
│   └── email_monitor.py
├── .env.example             # Environment template
├── main.py                  # Application entry
├── requirements.txt
├── test_setup.py           # Setup verification
└── send_test_email.py      # Email testing tool
```

## �️ Technology Stack

- **FastAPI** - Modern Python web framework
- **MongoDB + Beanie** - NoSQL database with ODM
- **Resend/SendGrid** - Email sending services
- **Google Gemini/OpenAI** - AI-powered responses
- **AIOIMAPLIB** - IMAP email receiving
- **Pydantic V2** - Data validation

## 📖 Documentation

- **[EMAIL_PROVIDER_GUIDE.md](EMAIL_PROVIDER_GUIDE.md)** - Email provider setup (Resend/SendGrid)
- **Interactive Docs** - http://localhost:8000/docs (when running)

## 🔒 Security

- ✅ API key authentication
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Input validation
- ✅ Secure credential storage (.env)

**Important:** Never commit `.env` file or credentials to Git!

## 🚀 Production Deployment

1. Use MongoDB Atlas for database
2. Set strong `SECRET_KEY` and API keys
3. Enable HTTPS with reverse proxy
4. Configure CORS for your domain
5. Set up monitoring and alerts

## 🧪 Testing

```bash
# Verify setup
python test_setup.py

# Send test emails
python send_test_email.py

# Interactive API testing
# Visit http://localhost:8000/docs
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 👨‍💻 Author

**Somesh J**
- GitHub: [@Somesh-J](https://github.com/Somesh-J)
- Email: someshj777@gmail.com
- linkedin: [Somesh J](https://www.linkedin.com/in/somesh-j/)