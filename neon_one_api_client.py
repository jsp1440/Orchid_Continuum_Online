"""Neon One API client for member management integration"""
import os
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NeonOneClient:
    """Client for Neon One CRM API"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEON_ONE_API_KEY')
        self.org_id = os.environ.get('NEON_ONE_ORG_ID')
        self.base_url = 'https://api.neoncrm.com/v2'
        
        if not self.api_key:
            logger.warning("Neon One API key not configured")
    
    def authenticate(self):
        """Authenticate and get access token"""
        if not self.api_key:
            return None
            
        try:
            response = requests.post(
                f'{self.base_url}/authenticate',
                headers={'Authorization': f'Basic {self.api_key}'},
                json={'orgId': self.org_id}
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Neon One auth failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Neon One API error: {str(e)}")
            return None
    
    def get_member_info(self, email):
        """Get member information by email"""
        token = self.authenticate()
        if not token:
            return None
        
        try:
            response = requests.get(
                f'{self.base_url}/accounts',
                headers={'Authorization': f'Bearer {token}'},
                params={'email': email}
            )
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('accounts', [])
                return accounts[0] if accounts else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch member: {str(e)}")
            return None
    
    def log_activity(self, email, activity_type, description):
        """Log BloomBuilder activity to member's Neon One record"""
        token = self.authenticate()
        if not token:
            return False
        
        member = self.get_member_info(email)
        if not member:
            logger.warning(f"Member not found in Neon One: {email}")
            return False
        
        try:
            response = requests.post(
                f'{self.base_url}/activities',
                headers={'Authorization': f'Bearer {token}'},
                json={
                    'accountId': member['accountId'],
                    'activityType': activity_type,
                    'activityDate': datetime.now().isoformat(),
                    'description': description
                }
            )
            
            return response.status_code == 201
            
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
            return False

# Global instance
neon_client = NeonOneClient()

