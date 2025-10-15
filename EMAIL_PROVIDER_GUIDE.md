# Email Provider Setup Guide

## Choosing Your Email Provider

This application supports two email sending providers:
1. **SendGrid** - Industry standard, established
2. **Resend** - Modern, developer-friendly

## 📊 Provider Comparison

| Feature | SendGrid | Resend |
|---------|----------|--------|
| **Free Tier** | 100 emails/day | 100 emails/day, 3,000/month |
| **Pricing** | $19.95/mo for 50K | $20/mo for 50K |
| **Deliverability** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Very Good |
| **API Quality** | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Documentation** | ⭐⭐⭐⭐ Comprehensive | ⭐⭐⭐⭐⭐ Excellent |
| **Setup Difficulty** | Medium | Easy |
| **Dashboard** | Complex | Simple |
| **Analytics** | Detailed | Basic |
| **Reputation** | Established (15+ years) | New (2023) |

## 🚀 Quick Setup

### Option 1: Using SendGrid

#### Step 1: Create SendGrid Account
1. Go to https://sendgrid.com
2. Sign up for free account
3. Verify your email address

#### Step 2: Get API Key
1. Log in to SendGrid dashboard
2. Go to **Settings** > **API Keys**
3. Click **Create API Key**
4. Choose **Full Access** or **Restricted Access** (with Mail Send permission)
5. Copy the API key (you won't see it again!)

#### Step 3: Verify Sender Email
1. Go to **Settings** > **Sender Authentication**
2. Choose **Single Sender Verification** (for free tier)
3. Enter your email address and details
4. Verify the email sent to you

#### Step 4: Configure .env
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=your-verified-email@domain.com
FROM_NAME=Your Name
```

### Option 2: Using Resend

#### Step 1: Create Resend Account
1. Go to https://resend.com
2. Sign up (GitHub OAuth available)
3. Verify your email

#### Step 2: Get API Key
1. Go to **API Keys** section
2. Click **Create API Key**
3. Give it a name (e.g., "Production")
4. Choose permissions (Full Access recommended)
5. Copy the API key (starts with `re_`)

#### Step 3: Add Domain (Optional but Recommended)
1. Go to **Domains** section
2. Click **Add Domain**
3. Enter your domain name
4. Add DNS records provided by Resend
5. Wait for verification (usually a few minutes)

**For testing without a domain:**
- Use `onboarding@resend.dev` as FROM_EMAIL
- Limited to 100 emails total

#### Step 4: Configure .env
```env
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your App Name
```

## 📝 Configuration Examples

### Complete .env for SendGrid
```env
# Email Provider
EMAIL_PROVIDER=sendgrid

# SendGrid Configuration
SENDGRID_API_KEY=SG.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Email Automation System

# Leave Resend empty
RESEND_API_KEY=
```

### Complete .env for Resend
```env
# Email Provider
EMAIL_PROVIDER=resend

# Resend Configuration
RESEND_API_KEY=re_123456789_AbCdEfGhIjKlMnOpQrStUvWxYz
FROM_EMAIL=hello@yourdomain.com
FROM_NAME=Your Company

# Leave SendGrid empty
SENDGRID_API_KEY=
```

## 🧪 Testing Your Setup

### Test with Python Script
```python
# test_email.py
import asyncio
from services.email_sender import email_sender_service

async def test():
    result = await email_sender_service.send_email(
        to_email="your-test@email.com",
        subject="Test Email",
        content="This is a test email from the automation system!"
    )
    print(result)

asyncio.run(test())
```

### Test with API
```bash
# Start the server
python main.py

# Send test email via API
curl -X POST "http://localhost:8000/api/v1/bulk/test" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test!"
  }'
```

### Test with Setup Script
```bash
python test_setup.py
```

## 🔄 Switching Providers

To switch between providers:

1. **Update .env file:**
   ```env
   # Change from sendgrid to resend
   EMAIL_PROVIDER=resend
   ```

2. **Restart the application:**
   ```bash
   # Stop the server (Ctrl+C)
   # Start again
   python main.py
   ```

3. **Verify switch:**
   ```bash
   curl http://localhost:8000/api/v1/health/email
   ```

## 📊 Feature Support

### SendGrid Features
✅ Single email sending  
✅ Bulk email sending  
✅ HTML emails  
✅ Attachments  
✅ Templates (SendGrid templates)  
✅ Delivery status tracking  
✅ Detailed analytics  
✅ Webhooks  

### Resend Features
✅ Single email sending  
✅ Bulk email sending  
✅ HTML emails  
✅ React Email support  
✅ Delivery status tracking  
✅ Simple API  
⚠️ Templates (different implementation)  
⚠️ Limited analytics  

## 💰 Pricing Details

### SendGrid Pricing (as of 2025)
- **Free:** 100 emails/day forever
- **Essentials:** $19.95/mo - 50,000 emails
- **Pro:** $89.95/mo - 100,000 emails
- **Premier:** Custom pricing

### Resend Pricing (as of 2025)
- **Free:** 100 emails/day, 3,000/month
- **Pro:** $20/mo - 50,000 emails
- **Business:** Custom pricing

## 🎯 Recommendations

### Use **SendGrid** if you:
- ✅ Need enterprise-grade reliability
- ✅ Require detailed analytics and reporting
- ✅ Want established reputation for deliverability
- ✅ Need advanced features like A/B testing
- ✅ Have budget for paid plans

### Use **Resend** if you:
- ✅ Want modern, developer-friendly API
- ✅ Need better free tier (3,000/month vs 3,000/month)
- ✅ Prefer simpler setup and configuration
- ✅ Use React for email templates
- ✅ Want cleaner, more intuitive dashboard

## 🔍 Troubleshooting

### SendGrid Issues

**Problem: "Forbidden" error**
- Solution: Check API key has Mail Send permission
- Verify sender email is authenticated

**Problem: Emails not received**
- Check spam folder
- Verify sender authentication (SPF, DKIM)
- Review SendGrid activity logs

**Problem: Rate limit exceeded**
- Upgrade plan or reduce send rate
- Implement proper rate limiting in code

### Resend Issues

**Problem: "Invalid API key"**
- Verify API key starts with `re_`
- Check API key is active in dashboard

**Problem: "Domain not verified"**
- Add DNS records to your domain
- Wait for verification (can take 24-48 hours)
- Use onboarding@resend.dev for testing

**Problem: Emails not sending**
- Check logs for specific error messages
- Verify FROM_EMAIL matches verified domain
- Ensure API key has send permissions

## 📚 Additional Resources

### SendGrid
- Documentation: https://docs.sendgrid.com
- API Reference: https://docs.sendgrid.com/api-reference
- Status Page: https://status.sendgrid.com
- Support: https://support.sendgrid.com

### Resend
- Documentation: https://resend.com/docs
- API Reference: https://resend.com/docs/api-reference
- Examples: https://resend.com/examples
- Discord: https://resend.com/discord

## 🔐 Security Best Practices

1. **Never commit API keys to git**
   - Use .env file (already in .gitignore)
   - Use environment variables in production

2. **Rotate API keys regularly**
   - Create new keys periodically
   - Delete old unused keys

3. **Use restricted permissions**
   - Only grant Mail Send permission
   - Avoid Full Access keys when possible

4. **Monitor usage**
   - Check dashboards regularly
   - Set up alerts for unusual activity

5. **Verify sender domains**
   - Always verify domains you send from
   - Use SPF, DKIM, DMARC records

## 🆘 Getting Help

If you encounter issues:

1. Check the logs: `logs/app.log`
2. Run diagnostics: `python test_setup.py`
3. Check provider status pages
4. Review API documentation
5. Open an issue on GitHub

---

**Need help choosing?** Start with **Resend** for its better free tier and simpler setup, then migrate to **SendGrid** if you need enterprise features.
