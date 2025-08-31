"""
Chevron SQ - Email Notification Module

This module handles sending email notifications when web scraping is complete.
The email system uses SMTP (Gmail recommended) and sends beautifully formatted HTML emails.

CLIENT SWEs: You must implement the email assignment logic to get the recipient email
from Microsoft Edge browser as specified in requirements.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional

# Load environment variables from project root
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

# Configure logging
logger = logging.getLogger(__name__)

def get_dashboard_url() -> str:
    """Get the dashboard URL from environment variable or default to localhost"""
    return os.getenv('DASHBOARD_URL', 'http://localhost:3000')

def send_completion_email(company_name: str, scraping_results: Dict[str, Any]) -> bool:
    """
    Send a beautiful HTML email notification when company scraping is complete.
    
    This is the main function you'll call after scraping is done.
    
    Args:
        company_name (str): Name of the company that was scraped (e.g., "Tesla Inc")
        scraping_results (Dict[str, Any]): Complete results from the web scraper
            Expected format:
            {
                "total_pages_crawled": 45,
                "results": {...},  # Criteria findings
                "company_name": "Tesla Inc",
                # ... other scraper data
            }
    
    Returns:
        bool: True if email sent successfully, False otherwise
    
    Example Usage:
        # After scraping completes
        scraping_data = run_company_scrape("Tesla")
        email_success = send_completion_email("Tesla", scraping_data)
        
        if email_success:
            logger.info("Email notification sent!")
        else:
            logger.error("Email sending failed")
    """
    
    try:
        logger.info(f"Starting email notification for {company_name}")
        
        # STEP 1: Get recipient email address
        recipient_email = get_recipient_email()
        
        if not recipient_email:
            logger.warning(" No recipient email configured. Email notification skipped.")
            logger.info("CLIENT SWEs: Please implement get_recipient_email() function")
            return False
        
        # STEP 2: Get SMTP configuration
        smtp_config = get_smtp_configuration()
        
        if not smtp_config['valid']:
            logger.warning("SMTP not configured. Email notification skipped.")
            logger.info("CLIENT SWEs: Please configure SMTP settings in environment variables")
            return False
        
        # STEP 3: Generate beautiful email content
        logger.info(f"Generating email template for {company_name}")
        email_html = generate_email_template(company_name, scraping_results)
        
        # STEP 4: Send the email
        logger.info(f"Sending email to {recipient_email}")
        success = send_email_via_smtp(
            recipient_email=recipient_email,
            subject=f"✅ {company_name} Analysis Complete - Ready to View!",
            html_content=email_html,
            smtp_config=smtp_config
        )
        
        if success:
            logger.info(f"Email notification sent successfully for {company_name}")
            return True
        else:
            logger.error(f"Failed to send email notification for {company_name}")
            return False
            
    except Exception as e:
        logger.error(f"Email notification error for {company_name}: {str(e)}")
        return False

def get_recipient_email() -> Optional[str]:
    """
    Get the recipient email address for notifications.
    
    CLIENT SWEs: THIS FUNCTION MUST BE IMPLEMENTED!
    
    Per requirements, you need to implement logic to extract the email
    from Microsoft Edge browser since "the browser already has the email".
    
    Returns:
        Optional[str]: Email address if found, None otherwise
    
    For testing purposes, you can set NOTIFICATION_EMAIL in your .env file:
    NOTIFICATION_EMAIL=test@example.com
    """
    
    # For testing: Check if test email is set in environment
    test_email = os.getenv('NOTIFICATION_EMAIL')
    if test_email:
        logger.info(f"📧 Using test email: {test_email}")
        return test_email
    
    # CLIENT SWEs: IMPLEMENT EMAIL EXTRACTION FROM MICROSOFT EDGE BROWSER HERE
    # Possible approaches:
    # 1. Browser extension integration
    # 2. Windows registry access for Edge profile data
    # 3. Browser local storage/cookies access
    # 4. Active Directory integration
    # 5. User session management
    
    # PLACEHOLDER: Currently returns None until CLIENT SWEs implement
    logger.warning("🚧 get_recipient_email() not implemented by CLIENT SWEs")
    logger.info("💡 Set NOTIFICATION_EMAIL environment variable for testing")
    return None

def get_smtp_configuration() -> Dict[str, Any]:
    """
    Get SMTP server configuration from environment variables.
    
    Expected environment variables:
    - SMTP_SERVER (default: smtp.gmail.com)
    - SMTP_PORT (default: 587)
    - SMTP_USERNAME (required)
    - SMTP_PASSWORD (required)
    
    Returns:
        Dict containing SMTP configuration and validity status
    """
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    valid = bool(smtp_username and smtp_password)
    
    return {
        'server': smtp_server,
        'port': smtp_port,
        'username': smtp_username,
        'password': smtp_password,
        'valid': valid
    }

def generate_email_template(company_name: str, scraping_results: Dict[str, Any]) -> str:
    """
    Generate an HTML email template for completed company analysis.
    
    Args:
        company_name (str): Name of the company
        scraping_results (Dict): Results from web scraper
        
    Returns:
        str: HTML email content
    """
    
    # Extract score if available
    overall_score = ""
    if scraping_results.get('overall_score', {}).get('overall_score_percentage') is not None:
        score = scraping_results['overall_score']['overall_score_percentage']
        overall_score = f"<p><strong>Sustainability Score:</strong> {score}%</p>"
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analysis Ready - {company_name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 25px;
                color: #2c3e50;
            }}
            .message {{
                font-size: 16px;
                margin: 20px 0;
            }}
            .company-name {{
                font-weight: bold;
                color: #3498db;
                font-size: 18px;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #3498db;
                color: white !important;
                padding: 12px 25px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .score {{
                background-color: #e8f5e8;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                text-align: center;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 14px;
                color: #7f8c8d;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🎉 Company Analysis Complete!</h2>
            </div>
            
            <div class="message">
                <p>Hello,</p>
                
                <p>Great news! The sustainability analysis for <span class="company-name">{company_name}</span> has been completed successfully.</p>
                
                {overall_score}
                
                <p><strong>Your detailed report is now ready to view in the Chevron SQ Dashboard.</strong></p>
                
                <div style="text-align: center;">
                    <a href="{get_dashboard_url()}/dashboard" class="cta-button">View Dashboard</a>
                </div>
                
                <p>The analysis includes:</p>
                <ul>
                    <li>✅ CNG Fleet Assessment</li>
                    <li>✅ Emissions Reporting Analysis</li>
                    <li>✅ Sustainability Metrics</li>
                    <li>✅ Clean Energy Partnerships</li>
                    <li>✅ Overall Adoption Score</li>
                </ul>
                
                <p>You can now review the detailed findings, save the report, or compare with other companies.</p>
            </div>
            
            <div class="footer">
                <p>Thank you for using Chevron SQ Analytics Platform</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template

def send_email_via_smtp(recipient_email: str, subject: str, html_content: str, smtp_config: Dict[str, Any]) -> bool:
    """
    Send email using SMTP server.
    
    Args:
        recipient_email (str): Email address to send to
        subject (str): Email subject line
        html_content (str): HTML email content
        smtp_config (Dict): SMTP server configuration
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_config['username']
        msg['To'] = recipient_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send via SMTP
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()  # Enable encryption
            server.login(smtp_config['username'], smtp_config['password'])
            server.sendmail(smtp_config['username'], recipient_email, msg.as_string())
        
        logger.info(f" Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"SMTP sending failed: {str(e)}")
        return False

def test_email_function():
    """
    Test function to verify email functionality during development.
    
    Usage:
        python -c "from email_notification import test_email_function; test_email_function()"
    """
    
    # Sample scraping results for testing
    test_results = {
        'total_pages_crawled': 45,
        'results': {
            'cng_fleet': {'found': True},
            'emission_goals': {'found': True},
            'clean_energy_partner': {'found': False}
        },
        'company_name': 'Tesla Inc'
    }
    
    logger.info("Testing email notification function...")
    success = send_completion_email("Tesla Inc", test_results)
    
    if success:
        logger.info("Email test successful!")
    else:
        logger.error("Email test failed. Check configuration.")
        logger.error("Make sure to set NOTIFICATION_EMAIL, SMTP_USERNAME, and SMTP_PASSWORD in your .env file")
    
    return success

if __name__ == "__main__":
    # Run test when script is executed directly
    logger.info("Chevron SQ Email Notification Module")
    logger.info("=====================================")
    test_email_function() 