"""Email notification service for BloomBuilder completions"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

def send_bloombuilder_completion_email(user_email, species_name, annotation_count):
    """Send email when user completes BloomBuilder annotations"""
    
    # Check if SendGrid is configured
    sendgrid_key = os.environ.get('SENDGRID_API_KEY')
    if not sendgrid_key:
        logger.warning("SendGrid API key not configured - email not sent")
        return False
    
    try:
        message = Mail(
            from_email='noreply@orchidcontinuum.org',
            to_emails=user_email,
            subject=f'BloomBuilder Complete: {species_name}',
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🌸 BloomBuilder Complete!</h1>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa;">
                    <h2 style="color: #333;">Congratulations!</h2>
                    <p style="font-size: 16px; color: #555;">
                        You've completed your BloomBuilder morphology lab for:
                    </p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #667eea; margin: 0 0 10px 0;">{species_name}</h3>
                        <p style="color: #666; margin: 0;">
                            <strong>{annotation_count}</strong> morphological features annotated
                        </p>
                    </div>
                    
                    <p style="font-size: 14px; color: #555;">
                        Your annotations are now part of The Orchid Continuum's educational database,
                        helping students worldwide learn orchid morphology through interactive digital anatomy.
                    </p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://orchidcontinuum.org/bloombuilder" 
                           style="background: #667eea; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Continue Learning
                        </a>
                    </div>
                </div>
                
                <div style="padding: 20px; text-align: center; color: #999; font-size: 12px;">
                    <p>The Orchid Continuum - Digital Morphology Lab</p>
                    <p>Inspired by NAOCC Orchid-Gami</p>
                </div>
            </body>
            </html>
            """
        )
        
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        logger.info(f"Email sent successfully to {user_email} - Status: {response.status_code}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

