# 📧 Chevron SQ - Email Notification Module

The Email Notification Module sends beautiful HTML email notifications when web scraping is complete. This module is designed to integrate seamlessly with the Chevron SQ analytics platform.

##  Features

- **Beautiful HTML Email Templates** - Professional, responsive email design
- **SMTP Integration** - Works with Gmail, Outlook, and other SMTP providers
- **Comprehensive Logging** - Detailed logs for debugging and monitoring
- **Test Functions** - Built-in testing capabilities for development
- **Error Handling** - Graceful failure handling with detailed error messages

## Prerequisites

- Python 3.7+
- Required packages: `smtplib`, `email`, `dotenv`
- SMTP email account (Gmail recommended)

## Setup & Configuration

### 1. Environment Variables

Create a `.env` file in your backend directory with the following variables:

```env
# SMTP Configuration (Required for sending emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Test Email (Optional - for testing purposes)
NOTIFICATION_EMAIL=test@example.com
```

### 2. Gmail Setup (Recommended)

If using Gmail, you'll need to:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password in `SMTP_PASSWORD`

### 3. Install Dependencies

```bash
pip install python-dotenv
```

## Testing the Email Function

### Method 1: Run the module directly
```bash
cd backend
python email_notification.py
```

### Method 2: Use the test function
```bash
cd backend
python -c "from email_notification import test_email_function; test_email_function()"
```

### Method 3: Custom test script
```python
from email_notification import send_completion_email

# Sample test data
test_results = {
    'total_pages_crawled': 25,
    'results': {
        'cng_fleet': {'found': True},
        'emission_goals': {'found': True},
        'clean_energy_partner': {'found': False}
    },
    'company_name': 'Test Company'
}

# Send test email
success = send_completion_email("Test Company", test_results)
print(f"Email sent: {success}")
```

## Usage Examples

### Basic Usage
```python
from email_notification import send_completion_email

# After scraping completes
scraping_data = {
    "total_pages_crawled": 45,
    "results": {
        "cng_fleet": {"found": True, "confidence": 0.95},
        "emission_goals": {"found": True, "confidence": 0.88},
        "clean_energy_partner": {"found": False}
    },
    "company_name": "Tesla Inc"
}

# Send notification email
email_success = send_completion_email("Tesla Inc", scraping_data)

if email_success:
    print(" Email notification sent!")
else:
    print("Email sending failed")
```
This is just a an example of the scraping data, please update based on the information obtained from the scraping data function.
Otherwise we could just send the LLM summarization in this email!!
### Integration with Web Scraper
```python
def complete_company_analysis(company_name):
    # Run web scraping
    scraping_results = run_web_scraper(company_name)
    
    # Send email notification
    email_sent = send_completion_email(company_name, scraping_results)
    
    return {
        'scraping_complete': True,
        'email_sent': email_sent,
        'results': scraping_results
    }
```
    Codelab Developers, talk to Alex to discuss on how to implement this
## 🔧 Function Reference

### `send_completion_email(company_name, scraping_results)`
Main function to send completion notification emails.

**Parameters:**
- `company_name` (str): Name of the company that was scraped
- `scraping_results` (dict): Complete results from the web scraper

**Returns:**
- `bool`: True if email sent successfully, False otherwise

### `get_recipient_email()`
 **CLIENT SWEs: This function needs implementation!**

Currently returns test email from environment variables. Must be implemented to extract email from Microsoft Edge browser.

### `test_email_function()`
Built-in test function for development and debugging.

##  Email Template Features

The generated emails include:
- **Company name** prominently displayed
- **Metrics summary** (pages crawled, criteria found)
- **Professional styling** with responsive design
- **Unique report ID** for tracking
- **Timestamp** of report generation
- **Call-to-action** button for viewing results

## Troubleshooting

### Common Issues

**1. Authentication Error**
```
 SMTP sending failed: (535, '5.7.8 Username and Password not accepted')
```
**Solution:** Check Gmail app password, ensure 2FA is enabled

**2. No Recipient Email**
```
 No recipient email configured. Email notification skipped.
```
**Solution:** Set `NOTIFICATION_EMAIL` in `.env` or implement `get_recipient_email()`

**3. SMTP Connection Error**
```
SMTP sending failed: [Errno 11001] getaddrinfo failed
```
**Solution:** Check internet connection and SMTP server settings

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

##  Security Best Practices

1. **Never commit credentials** to version control
2. **Use app passwords** instead of main account passwords
3. **Rotate passwords** regularly
4. **Limit SMTP account** permissions to email only
5. **Use environment variables** for all sensitive data

##  TODO for CLIENT SWEs

- [ ] Implement `get_recipient_email()` function
- [ ] Add browser integration for email extraction
- [ ] Configure production SMTP settings
- [ ] Add email template customization options
- [ ] Implement email delivery tracking

## Integration Points

This module integrates with:
- **Web Scraper Module** - Receives scraping results
- **Microsoft Edge Browser** - Should extract user email
- **Main Application** - Called after scraping completion
- **Logging System** - Provides detailed operation logs

## Support

For issues with this module:
1. Check the troubleshooting section above
2. Verify environment variable configuration
3. Test with the built-in test function
4. Check application logs for detailed error messages

---

**Last Updated:** December 2024  
**Version:** 1.0  
**Dependencies:** Python 3.7+, python-dotenv 