# Email Automation FastAPI Project

## Project Overview

This is a comprehensive FastAPI-based email automation system designed for easy integration into any platform or codebase. The application provides robust email processing, AI-powered reply generation, bulk email capabilities, and comprehensive monitoring.

## Key Features

- **Async Email Processing**: Handle IMAP email operations asynchronously
- **AI-Powered Replies**: Generate intelligent responses using Gemini or OpenAI
- **Bulk Email Management**: Send and track bulk email campaigns
- **Domain Management**: Manage multiple email domains and accounts
- **Real-time Monitoring**: Monitor email processing and system health
- **Analytics & Reporting**: Detailed analytics and exportable reports
- **Template Management**: Create and manage email templates
- **Security**: API key authentication, rate limiting, and input validation
- **Modular Architecture**: Easy to integrate and extend

## Project Structure

```
email-automation/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── core/                       # Core functionality
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py            # Database models and connection
│   ├── logger.py              # Logging configuration
│   └── security.py            # Authentication and security
├── services/                   # Business logic services
│   ├── __init__.py
│   ├── email_service.py       # Email IMAP operations
│   ├── ai_service.py          # AI reply generation
│   ├── sendgrid_service.py    # SendGrid integration
│   └── email_monitor.py       # Email monitoring service
└── api/                       # API layer
    ├── __init__.py
    ├── models.py              # Pydantic models
    └── routes/                # API route handlers
        ├── __init__.py
        ├── email_processing.py
        ├── health.py
        ├── domain_management.py
        ├── monitoring.py
        ├── bulk_email.py
        ├── analytics.py
        ├── settings.py
        └── templates.py
```

## API Endpoints

### Core Email Operations
- `GET /api/v1/emails/` - List emails with filtering
- `GET /api/v1/emails/{email_id}` - Get specific email details
- `POST /api/v1/emails/ingest` - Ingest emails from IMAP
- `POST /api/v1/emails/{email_id}/reply` - Send manual reply
- `POST /api/v1/emails/{email_id}/ai-reply` - Generate AI reply
- `POST /api/v1/emails/{email_id}/sentiment` - Analyze sentiment
- `POST /api/v1/emails/search` - Search emails
- `GET /api/v1/emails/stats` - Get email statistics
- `PUT /api/v1/emails/{email_id}/mark-read` - Mark email as read

### Health & Monitoring
- `GET /api/v1/health/status` - System health status
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/metrics` - System metrics
- `POST /api/v1/health/test-services` - Test service connections

### Domain Management
- `GET /api/v1/domains/` - List domains
- `POST /api/v1/domains/` - Add domain
- `GET /api/v1/domains/{domain_id}` - Get domain details
- `PUT /api/v1/domains/{domain_id}` - Update domain
- `DELETE /api/v1/domains/{domain_id}` - Delete domain
- `POST /api/v1/domains/bulk-add` - Add multiple domains
- `POST /api/v1/domains/{domain_id}/check` - Check domain connection
- `GET /api/v1/domains/{domain_id}/stats` - Domain statistics

### Email Monitoring
- `GET /api/v1/monitoring/status` - Monitoring status
- `POST /api/v1/monitoring/start` - Start monitoring
- `POST /api/v1/monitoring/stop` - Stop monitoring
- `POST /api/v1/monitoring/restart` - Restart monitoring
- `POST /api/v1/monitoring/force-check` - Force email check
- `GET /api/v1/monitoring/settings` - Get monitoring settings
- `PUT /api/v1/monitoring/settings` - Update monitoring settings
- `GET /api/v1/monitoring/health` - Monitoring service health

### Bulk Email Operations
- `POST /api/v1/bulk/send` - Send bulk emails
- `GET /api/v1/bulk/jobs` - List bulk email jobs
- `GET /api/v1/bulk/jobs/{job_id}` - Get job details
- `GET /api/v1/bulk/jobs/{job_id}/status` - Get job status
- `POST /api/v1/bulk/jobs/{job_id}/cancel` - Cancel job
- `GET /api/v1/bulk/stats` - Bulk email statistics
- `POST /api/v1/bulk/validate-recipients` - Validate email list

### Analytics & Reporting
- `GET /api/v1/analytics/overview` - Analytics overview
- `GET /api/v1/analytics/daily` - Daily statistics
- `GET /api/v1/analytics/domain/{domain_id}` - Domain analytics
- `GET /api/v1/analytics/performance` - Performance metrics
- `GET /api/v1/analytics/export` - Export analytics data

### Settings Management
- `GET /api/v1/settings/` - Get system settings
- `PUT /api/v1/settings/` - Update system settings
- `GET /api/v1/settings/email` - Get email settings
- `PUT /api/v1/settings/email` - Update email settings
- `GET /api/v1/settings/ai` - Get AI settings
- `PUT /api/v1/settings/ai` - Update AI settings
- `GET /api/v1/settings/security` - Get security settings
- `PUT /api/v1/settings/security` - Update security settings
- `GET /api/v1/settings/defaults` - Get default settings
- `POST /api/v1/settings/reset` - Reset to defaults

### Template Management
- `GET /api/v1/templates/` - List templates
- `POST /api/v1/templates/` - Create template
- `GET /api/v1/templates/{template_id}` - Get template
- `PUT /api/v1/templates/{template_id}` - Update template
- `DELETE /api/v1/templates/{template_id}` - Delete template
- `GET /api/v1/templates/categories/list` - List categories
- `POST /api/v1/templates/{template_id}/duplicate` - Duplicate template
- `POST /api/v1/templates/{template_id}/test` - Test template
- `POST /api/v1/templates/import` - Import templates

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./email_automation.db

# Email Configuration
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USE_SSL=true
EMAIL_ADDRESS=your-email@example.com
EMAIL_PASSWORD=your-app-password

# SendGrid
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@example.com
FROM_NAME=Email Automation

# AI Services
AI_PROVIDER=gemini  # or openai
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key

# Security
SECRET_KEY=your-secret-key
API_KEYS=["key1","key2","key3"]
ALLOWED_ORIGINS=["http://localhost:3000","https://yourapp.com"]

# Application Settings
EMAIL_CHECK_INTERVAL=30
ENABLE_AUTO_REPLY=true
MAX_EMAILS_PER_CHECK=50
BULK_EMAIL_BATCH_SIZE=10
BULK_EMAIL_DELAY=1.0
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600
```

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with the required environment variables (see Configuration section).

### 3. Initialize Database

The database will be automatically initialized on first run.

### 4. Run the Application

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

All API endpoints require authentication using an API key. Include the API key in the request header:

```
X-API-Key: your-api-key-here
```

## Rate Limiting

API requests are rate limited to prevent abuse. Default limits:
- 100 requests per hour per API key
- Configurable via settings endpoints

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
  "success": false,
  "error": "Error description",
  "details": {
    "field": "specific error details"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

## Integration Examples

### Python Integration

```python
import requests

# Configure API client
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY}

# Ingest emails
response = requests.post(f"{API_BASE_URL}/emails/ingest", headers=headers)
print(response.json())

# Send bulk emails
bulk_data = {
    "recipients": ["user1@example.com", "user2@example.com"],
    "subject": "Newsletter",
    "body": "Hello from our newsletter!"
}
response = requests.post(f"{API_BASE_URL}/bulk/send", json=bulk_data, headers=headers)
print(response.json())
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'X-API-Key': 'your-api-key'
  }
});

// Get email statistics
async function getEmailStats() {
  try {
    const response = await apiClient.get('/emails/stats');
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Send AI reply
async function sendAiReply(emailId) {
  try {
    const response = await apiClient.post(`/emails/${emailId}/ai-reply`);
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}
```

## Database Schema

The application uses SQLAlchemy with the following main models:

- **EmailDB**: Stores email data and metadata
- **DomainDB**: Manages email domains and accounts
- **EmailTemplateDB**: Email templates for bulk sending
- **BulkEmailJobDB**: Tracks bulk email campaigns
- **MonitoringLogDB**: System monitoring logs
- **ApiKeyDB**: API key management
- **SystemSettingsDB**: Application settings

## Monitoring & Logging

### Health Checks

The application provides multiple health check endpoints:
- `/api/v1/health/live` - Basic liveness check
- `/api/v1/health/ready` - Readiness check with dependencies
- `/api/v1/health/status` - Detailed system status

### Logging

Comprehensive logging is implemented with different levels:
- **INFO**: General application flow
- **WARNING**: Potential issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information

Logs include structured data for easy parsing and monitoring.

## Security Features

- **API Key Authentication**: Secure access control
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: Comprehensive request validation
- **CORS Configuration**: Secure cross-origin requests
- **Error Sanitization**: Safe error message exposure

## Performance Considerations

- **Async Operations**: Non-blocking I/O for better concurrency
- **Database Optimization**: Efficient queries and indexing
- **Background Tasks**: Long-running operations don't block requests
- **Caching**: Strategic caching for frequently accessed data
- **Batch Processing**: Efficient bulk operations

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment-Specific Configuration

- **Development**: Debug mode, detailed logging
- **Staging**: Production-like setup with test data
- **Production**: Optimized settings, secure configuration

## Troubleshooting

### Common Issues

1. **IMAP Connection Errors**
   - Verify email credentials
   - Check IMAP server settings
   - Ensure app passwords are used for Gmail

2. **AI Service Errors**
   - Verify API keys
   - Check service availability
   - Monitor rate limits

3. **Database Issues**
   - Check database URL
   - Verify permissions
   - Review migration status

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

## Contributing

This project follows modular architecture principles:
- Each service is independent and testable
- Clear separation of concerns
- Comprehensive error handling
- Extensive documentation

## Support

For issues and support:
- Check the logs for detailed error information
- Review the API documentation at `/docs`
- Use health check endpoints to diagnose system issues

---

*This documentation was auto-generated for the Email Automation FastAPI Project.*
