# Email Automation FastAPI Application

A modern, scalable email automation system built with FastAPI, supporting both PostgreSQL and MongoDB databases.

## Features

- **Multi-Database Support**: Choose between PostgreSQL (SQLAlchemy) or MongoDB (Beanie ODM)
- **Email Processing**: IMAP email monitoring, parsing, and automatic responses
- **AI Integration**: AI-powered email replies using Google Gemini or OpenAI
- **Bulk Email**: Send bulk emails with template support and job tracking
- **Domain Management**: Manage allowed/blocked domains with custom rules
- **Monitoring**: Real-time system health monitoring and analytics
- **Template System**: Customizable email templates with variable support
- **API Security**: API key authentication, rate limiting, and CORS support
- **Analytics**: Comprehensive email analytics and reporting

## Database Support

### PostgreSQL (Default)
- Uses SQLAlchemy with async support
- Structured relational data with ACID compliance
- Automatic table creation and migrations

### MongoDB
- Uses Beanie ODM (async MongoDB object document mapper)
- Flexible document-based storage
- Automatic index creation and data validation

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# Database Configuration
USE_MONGODB=false  # Set to true for MongoDB, false for PostgreSQL

# PostgreSQL Settings (if USE_MONGODB=false)
DATABASE_URL=postgresql://user:password@localhost:5432/email_automation
DB_HOST=localhost
DB_PORT=5432
DB_NAME=email_automation
DB_USER=postgres
DB_PASSWORD=password

# MongoDB Settings (if USE_MONGODB=true)
MONGO_URL=mongodb://localhost:27017/email_automation
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=email_automation
MONGO_USERNAME=
MONGO_PASSWORD=
MONGO_AUTH_DB=admin
MONGO_USE_SSL=false

# Email Configuration
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USE_SSL=true
IMAP_USERNAME=your-email@gmail.com
IMAP_PASSWORD=your-app-password

# SendGrid Configuration
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your App Name

# AI Configuration
AI_PROVIDER=gemini  # or openai
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# Security
SECRET_KEY=your-secret-key-change-in-production
VALID_API_KEYS=["key1", "key2", "key3"]

# App Configuration
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd email-automation

# Install dependencies
pip install -r requirements.txt

# Set up database (choose one)

# For PostgreSQL:
# Create database and user
sudo -u postgres psql
CREATE DATABASE email_automation;
CREATE USER email_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE email_automation TO email_user;

# For MongoDB:
# Install MongoDB and start the service
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 3. Run the Application

```bash
# Start the FastAPI server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the provided script
python main.py
```

The application will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- **Bulk Operations:** `/api/v1/bulk/`
- **Analytics:** `/api/v1/analytics/`
- **Health Checks:** `/api/v1/health/`
- **Settings:** `/api/v1/settings/`

## Configuration

Set up environment variables in `.env`:

```bash
# Database
DATABASE_URL=sqlite:///./email_automation.db

# Email Settings
IMAP_SERVER=imap.gmail.com
EMAIL_ADDRESS=your-email@example.com
EMAIL_PASSWORD=your-password

# AI Services
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key

# Security
API_KEYS=["your-api-key"]
```

## Integration Example

```python
import requests

# Configure client
headers = {"X-API-Key": "your-api-key"}
base_url = "http://localhost:8000/api/v1"

# Ingest emails
response = requests.post(f"{base_url}/emails/ingest", headers=headers)
print(response.json())

# Get analytics
response = requests.get(f"{base_url}/analytics/overview", headers=headers)
print(response.json())
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
```

## Deployment

### Docker

```bash
docker build -t email-automation .
docker run -p 8000:8000 email-automation
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## License

MIT License - see LICENSE file for details.

## Support

- 📖 **Documentation:** Available at `/docs` and `/redoc`
- 🏥 **Health Checks:** `/api/v1/health/status`
- 📊 **Metrics:** `/api/v1/health/metrics`

---

Built with ❤️ By Somesh.
