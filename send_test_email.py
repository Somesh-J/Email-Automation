"""
Simple script to send test emails to verify email functionality
"""

import asyncio
import sys
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="info"):
    """Print colored status message"""
    if status == "success":
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == "error":
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    else:
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def print_header(message):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

async def send_test_emails():
    """Send test emails to verify email functionality"""
    
    test_recipient = "someshj777@gmail.com"
    
    try:
        # Import after function definition to avoid circular imports
        from core.config import settings
        
        print_header("📧 Email Automation - Test Email Sender")
        
        # Check which email provider is configured
        email_provider = settings.EMAIL_PROVIDER.lower()
        print_status(f"Email Provider: {email_provider}", "info")
        print_status(f"From Email: {settings.FROM_EMAIL}", "info")
        print_status(f"From Name: {settings.FROM_NAME}", "info")
        print_status(f"Test Recipient: {test_recipient}", "info")
        print()
        
        if email_provider == "resend":
            from services.resend_service import ResendService
            
            if not settings.RESEND_API_KEY:
                print_status("❌ Resend API key not configured in .env file", "error")
                print_status("Please set RESEND_API_KEY in your .env file", "warning")
                return False
            
            print_status("Initializing Resend email service...", "info")
            resend_service = ResendService()
            print_status("Resend service initialized successfully ✓", "success")
            print()
            
            # Test 1: Simple text email
            print_header("Test #1: Sending Simple Text Email")
            print_status(f"Preparing email...", "info")
            
            result1 = await resend_service.send_email(
                to_email=test_recipient,
                subject="✅ Test Email #1 - Simple Text",
                content="""Hello!

This is a test email from your Email Automation API.

If you received this, your email setup is working correctly!

System Details:
- Provider: Resend
- From: {from_email}
- API: Email Automation API v1.0
- Sent: {date}

Best regards,
Email Automation System""".format(
                    from_email=settings.FROM_EMAIL,
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                from_email=settings.FROM_EMAIL,
                from_name=settings.FROM_NAME,
                content_type="text/plain"
            )
            
            if result1 and result1.get('success'):
                print_status(f"✅ Test email #1 sent successfully!", "success")
                print_status(f"   Message ID: {result1.get('message_id')}", "info")
            else:
                print_status("❌ Failed to send test email #1", "error")
                print_status(f"   Error: {result1.get('error', 'Unknown error')}", "warning")
                return False
            
            print()
            await asyncio.sleep(2)  # Small delay between emails
            
            # Test 2: HTML email
            print_header("Test #2: Sending HTML Formatted Email")
            print_status(f"Preparing HTML email...", "info")
            
            html_body = """
            <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 30px;
                            border-radius: 10px 10px 0 0;
                            text-align: center;
                        }}
                        .content {{
                            background-color: #ffffff;
                            padding: 30px;
                            border: 1px solid #e0e0e0;
                        }}
                        .info-box {{
                            background-color: #f0f7ff;
                            padding: 20px;
                            border-left: 4px solid #4CAF50;
                            margin: 20px 0;
                            border-radius: 5px;
                        }}
                        .footer {{
                            background-color: #f5f5f5;
                            padding: 20px;
                            text-align: center;
                            font-size: 12px;
                            color: #666;
                            border-radius: 0 0 10px 10px;
                        }}
                        ul {{
                            list-style: none;
                            padding: 0;
                        }}
                        li {{
                            padding: 5px 0;
                        }}
                        li:before {{
                            content: "✓ ";
                            color: #4CAF50;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1 style="margin: 0;">✅ Test Email #2</h1>
                        <p style="margin: 10px 0 0 0;">HTML Format Test</p>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: #667eea;">Hello from Email Automation!</h2>
                        <p>This is a <strong>beautifully formatted HTML email</strong> sent from your <em>Email Automation API</em>.</p>
                        
                        <div class="info-box">
                            <h3 style="margin-top: 0; color: #4CAF50;">✅ System Status: Active</h3>
                            <ul>
                                <li>Email Provider: Resend</li>
                                <li>From: {from_email}</li>
                                <li>Status: Working</li>
                                <li>HTML Support: Enabled</li>
                                <li>Sent: {date}</li>
                            </ul>
                        </div>
                        
                        <p>If you can see this beautifully formatted email, your email automation system is configured correctly and supports HTML emails!</p>
                        
                        <p style="margin-top: 30px;">
                            <strong>Next Steps:</strong><br>
                            • Your email system is working correctly<br>
                            • You can now send both plain text and HTML emails<br>
                            • Check the API documentation for more features
                        </p>
                    </div>
                    
                    <div class="footer">
                        This is an automated test email from Email Automation API<br>
                        Powered by Resend • MongoDB • FastAPI<br>
                        {date}
                    </div>
                </body>
            </html>
            """.format(
                from_email=settings.FROM_EMAIL,
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            result2 = await resend_service.send_email(
                to_email=test_recipient,
                subject="✅ Test Email #2 - HTML Format",
                content=html_body,
                from_email=settings.FROM_EMAIL,
                from_name=settings.FROM_NAME,
                content_type="text/html"
            )
            
            if result2 and result2.get('success'):
                print_status(f"✅ Test email #2 sent successfully!", "success")
                print_status(f"   Message ID: {result2.get('message_id')}", "info")
            else:
                print_status("❌ Failed to send test email #2", "error")
                print_status(f"   Error: {result2.get('error', 'Unknown error')}", "warning")
                return False
            
            print()
            await asyncio.sleep(2)  # Small delay between emails
            
            # Test 3: Email with custom reply-to
            print_header("Test #3: Sending Email with Reply-To Header")
            print_status(f"Preparing email with reply-to header...", "info")
            
            result3 = await resend_service.send_email(
                to_email=test_recipient,
                subject="✅ Test Email #3 - With Reply-To Header",
                content="""Hello!

This is test email #3 with a custom Reply-To header.

Try replying to this email - your reply should go to: {from_email}

Features tested:
✓ Simple text email
✓ HTML formatted email
✓ Custom Reply-To header
✓ From name customization

Your email automation system is fully functional!

Best regards,
{from_name}

---
Sent: {date}
System: Email Automation API v1.0
Provider: Resend""".format(
                    from_email=settings.FROM_EMAIL,
                    from_name=settings.FROM_NAME,
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                from_email=settings.FROM_EMAIL,
                from_name=settings.FROM_NAME,
                content_type="text/plain",
                reply_to=settings.FROM_EMAIL
            )
            
            if result3 and result3.get('success'):
                print_status(f"✅ Test email #3 sent successfully!", "success")
                print_status(f"   Message ID: {result3.get('message_id')}", "info")
            else:
                print_status("❌ Failed to send test email #3", "error")
                print_status(f"   Error: {result3.get('error', 'Unknown error')}", "warning")
                return False
            
            print()
            print_header("🎉 Success! All Test Emails Sent")
            print_status(f"✅ Successfully sent 3 test emails to {test_recipient}", "success")
            print_status(f"📬 Check your inbox (and spam/junk folder)", "info")
            print_status(f"⏰ Emails should arrive within 1-2 minutes", "info")
            print()
            return True
            
        elif email_provider == "sendgrid":
            from services.sendgrid_service import SendGridService
            
            if not settings.SENDGRID_API_KEY:
                print_status("❌ SendGrid API key not configured in .env file", "error")
                print_status("Please set SENDGRID_API_KEY in your .env file", "warning")
                return False
            
            print_status("Initializing SendGrid email service...", "info")
            sendgrid_service = SendGridService()
            print()
            
            # Send test email via SendGrid
            print_header("Sending Test Email via SendGrid")
            print_status(f"Preparing email...", "info")
            
            result = await sendgrid_service.send_email(
                to_email=test_recipient,
                subject="✅ Test Email - SendGrid",
                body="""Hello!

This is a test email from your Email Automation API using SendGrid.

If you received this, your SendGrid setup is working correctly!

System Details:
- Provider: SendGrid
- From: {from_email}
- API: Email Automation API v1.0
- Sent: {date}

Best regards,
Email Automation System""".format(
                    from_email=settings.FROM_EMAIL,
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            
            if result:
                print_status(f"✅ Test email sent successfully via SendGrid!", "success")
                print_status(f"📬 Check {test_recipient} inbox (and spam folder)", "info")
                return True
            else:
                print_status("❌ Failed to send test email via SendGrid", "error")
                return False
        else:
            print_status(f"❌ Unknown email provider: {email_provider}", "error")
            print_status(f"Supported providers: resend, sendgrid", "warning")
            return False
            
    except ImportError as e:
        print_status(f"❌ Import error: {e}", "error")
        print_status("Make sure all dependencies are installed: pip install -r requirements.txt", "warning")
        return False
    except Exception as e:
        print_status(f"❌ Error sending test emails: {e}", "error")
        import traceback
        print(f"\n{Colors.RED}{traceback.format_exc()}{Colors.END}")
        return False

async def main():
    """Main function"""
    try:
        success = await send_test_emails()
        
        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Email test completed successfully!{Colors.END}\n")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Email test failed. Please check the errors above.{Colors.END}\n")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}\n")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
