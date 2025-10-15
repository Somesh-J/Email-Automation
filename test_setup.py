"""
Test script to verify Email Automation API setup
Run this script to check if all components are configured correctly
"""

import asyncio
import sys
from pathlib import Path

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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

async def check_environment():
    """Check if .env file exists and has required variables"""
    print_header("1. Checking Environment Configuration")
    
    env_file = Path(".env")
    if not env_file.exists():
        print_status(".env file not found", "error")
        print_status("Please copy .env.example to .env and configure it", "warning")
        return False
    
    print_status(".env file found", "success")
    
    # Check for required environment variables
    required_vars = [
        "USE_MONGODB",
        "MONGO_DB_NAME",
        "SENDGRID_API_KEY",
        "FROM_EMAIL",
        "IMAP_USERNAME",
        "IMAP_PASSWORD"
    ]
    
    try:
        with open(".env", "r", encoding="utf-8") as f:
            env_content = f.read()
        
        missing_vars = []
        for var in required_vars:
            if f"{var}=" not in env_content or f"{var}=your-" in env_content or f"{var}=" in env_content and env_content.split(f"{var}=")[1].split("\n")[0].strip() == "":
                missing_vars.append(var)
        
        if missing_vars:
            print_status(f"Missing or unconfigured variables: {', '.join(missing_vars)}", "warning")
            return False
        else:
            print_status("All required environment variables are set", "success")
            return True
    except Exception as e:
        print_status(f"Error reading .env file: {e}", "error")
        return False

async def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("2. Checking Python Dependencies")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "motor",
        "pymongo",
        "beanie",
        "sendgrid",
        "aioimaplib",
        "pydantic",
        "pydantic_settings"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace(".", "_") if "." in package else package)
            print_status(f"{package} is installed", "success")
        except ImportError:
            print_status(f"{package} is NOT installed", "error")
            missing_packages.append(package)
    
    if missing_packages:
        print_status(f"\nTo install missing packages, run:", "warning")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    else:
        print_status("\nAll required packages are installed", "success")
        return True

async def check_mongodb():
    """Check MongoDB connection"""
    print_header("3. Checking MongoDB Connection")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from core.config import settings
        
        # Build connection string
        if settings.MONGO_URL:
            connection_string = settings.MONGO_URL
        else:
            if settings.MONGO_USERNAME and settings.MONGO_PASSWORD:
                auth_part = f"{settings.MONGO_USERNAME}:{settings.MONGO_PASSWORD}@"
            else:
                auth_part = ""
            connection_string = f"mongodb://{auth_part}{settings.MONGO_HOST}:{settings.MONGO_PORT}"
        
        print_status(f"Connecting to MongoDB at {settings.MONGO_HOST}:{settings.MONGO_PORT}", "info")
        
        # Try to connect
        client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        
        print_status("MongoDB connection successful", "success")
        print_status(f"Database: {settings.MONGO_DB_NAME}", "info")
        
        client.close()
        return True
        
    except Exception as e:
        print_status(f"MongoDB connection failed: {e}", "error")
        print_status("Make sure MongoDB is running and accessible", "warning")
        return False

async def check_sendgrid():
    """Check SendGrid configuration"""
    print_header("4. Checking SendGrid Configuration")
    
    try:
        from core.config import settings
        
        if not settings.SENDGRID_API_KEY or "your-" in settings.SENDGRID_API_KEY:
            print_status("SendGrid API key not configured", "error")
            return False
        
        print_status("SendGrid API key is configured", "success")
        print_status(f"From Email: {settings.FROM_EMAIL}", "info")
        print_status(f"From Name: {settings.FROM_NAME}", "info")
        
        # Note: We don't actually test sending here to avoid quota usage
        print_status("Note: SendGrid connection not tested to save quota", "warning")
        return True
        
    except Exception as e:
        print_status(f"Error checking SendGrid: {e}", "error")
        return False

async def check_email_config():
    """Check email configuration"""
    print_header("5. Checking Email Configuration")
    
    try:
        from core.config import settings
        
        if not settings.IMAP_USERNAME or "your-" in settings.IMAP_USERNAME:
            print_status("IMAP username not configured", "error")
            return False
        
        if not settings.IMAP_PASSWORD or "your-" in settings.IMAP_PASSWORD:
            print_status("IMAP password not configured", "error")
            return False
        
        print_status(f"IMAP Server: {settings.IMAP_SERVER}:{settings.IMAP_PORT}", "success")
        print_status(f"IMAP Username: {settings.IMAP_USERNAME}", "info")
        print_status("IMAP Password is configured", "success")
        
        # Note: We don't actually test IMAP connection here
        print_status("Note: IMAP connection not tested (will be tested on app start)", "warning")
        return True
        
    except Exception as e:
        print_status(f"Error checking email config: {e}", "error")
        return False

async def check_ai_config():
    """Check AI configuration"""
    print_header("6. Checking AI Configuration")
    
    try:
        from core.config import settings
        
        if settings.AI_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY or "your-" in settings.GEMINI_API_KEY:
                print_status("Gemini API key not configured", "warning")
                print_status("AI replies will not work", "warning")
                return False
            else:
                print_status("Gemini API key is configured", "success")
                return True
        elif settings.AI_PROVIDER == "openai":
            if not settings.OPENAI_API_KEY or "your-" in settings.OPENAI_API_KEY:
                print_status("OpenAI API key not configured", "warning")
                print_status("AI replies will not work", "warning")
                return False
            else:
                print_status("OpenAI API key is configured", "success")
                return True
        else:
            print_status(f"Unknown AI provider: {settings.AI_PROVIDER}", "warning")
            return False
        
    except Exception as e:
        print_status(f"Error checking AI config: {e}", "error")
        return False

async def check_file_structure():
    """Check if all required files exist"""
    print_header("7. Checking File Structure")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "core/config.py",
        "core/database.py",
        "core/mongo_models.py",
        "core/logger.py",
        "core/security.py",
        "services/email_service.py",
        "services/sendgrid_service.py",
        "services/ai_service.py",
        "services/email_monitor.py",
        "api/models.py",
        "api/routes/email_processing.py",
        "api/routes/domain_management.py",
        "api/routes/bulk_email.py",
        "api/routes/templates.py",
        "api/routes/monitoring.py",
        "api/routes/health.py",
        "api/routes/analytics.py",
        "api/routes/settings.py"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print_status(f"{file}", "success")
        else:
            print_status(f"{file} - MISSING", "error")
            all_exist = False
    
    return all_exist

# Note: Test email functionality moved to dedicated send_test_email.py script
# Use: python send_test_email.py

async def main():
    """Main test function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  Email Automation API - Setup Verification")
    print("=" * 60)
    print(f"{Colors.END}\n")
    
    results = {
        "environment": await check_environment(),
        "dependencies": await check_dependencies(),
        "mongodb": await check_mongodb(),
        "sendgrid": await check_sendgrid(),
        "email": await check_email_config(),
        "ai": await check_ai_config(),
        "files": await check_file_structure()
    }
    
    # Print summary
    print_header("Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "success" if result else "error"
        print_status(f"{check.capitalize()}: {'PASSED' if result else 'FAILED'}", status)
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} checks passed{Colors.END}\n")
    
    # Print summary
    print_header("Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "success" if result else "error"
        print_status(f"{check.capitalize()}: {'PASSED' if result else 'FAILED'}", status)
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} checks passed{Colors.END}\n")
    
    # Suggest next steps
    if passed >= 5:  # At least 5/7 checks passed (excluding sendgrid if using resend)
        print_status("✅ Setup looks good!", "success")
        print_status("\nTo send test emails, run:", "info")
        print(f"  python send_test_email.py\n")
    
    if passed == total:
        print_status("All checks passed! Your setup is ready.", "success")
        print_status("\nTo start the server, run:", "info")
        print(f"  python main.py")
        print(f"  or")
        print(f"  uvicorn main:app --reload --host 0.0.0.0 --port 8000\n")
        return True
    else:
        print_status(f"{total - passed} checks failed. Please fix the issues above.", "error")
        print_status("\nRefer to QUICKSTART.md for detailed setup instructions\n", "info")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}\n")
        sys.exit(1)
