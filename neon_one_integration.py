"""
Neon One CRM Integration Service
Handles membership verification and tier checking
"""
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NeonOneService:
    """Service for interacting with Neon One CRM API"""
    
    def __init__(self):
        self.api_key = os.environ.get("NEON_ONE_API_KEY")
        self.org_id = os.environ.get("NEON_ONE_ORG_ID", "fivecitiesorchidsociety")
        self.base_url = "https://api.neoncrm.com/v2"
        
        if not self.api_key:
            logger.warning("NEON_ONE_API_KEY not set - membership features will be limited")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Neon One API"""
        if not self.api_key:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Neon One API error: {e}")
            return None
    
    def get_account_by_email(self, email: str) -> Optional[Dict]:
        """Look up account by email address"""
        try:
            result = self._make_request(f"accounts/search?searchFields=email&searchValue={email}")
            if result and result.get('accounts'):
                return result['accounts'][0]  # Return first match
            return None
        except Exception as e:
            logger.error(f"Error looking up account by email: {e}")
            return None
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account details by Neon One account ID"""
        try:
            return self._make_request(f"accounts/{account_id}")
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            return None
    
    def get_membership_info(self, account_id: str) -> Dict[str, Any]:
        """
        Get membership tier and status for an account
        
        Returns:
            {
                'tier': 'visitor' | 'member' | 'life_member',
                'status': 'active' | 'expired' | 'none',
                'expiration_date': datetime or None,
                'account_id': str
            }
        """
        try:
            account = self.get_account_by_id(account_id)
            
            if not account:
                return {
                    'tier': 'visitor',
                    'status': 'none',
                    'expiration_date': None,
                    'account_id': None
                }
            
            # Check for memberships
            memberships = account.get('individualAccount', {}).get('memberships', [])
            
            if not memberships:
                return {
                    'tier': 'visitor',
                    'status': 'none',
                    'expiration_date': None,
                    'account_id': account_id
                }
            
            # Get active membership
            active_membership = None
            for membership in memberships:
                if membership.get('status') == 'ACTIVE':
                    active_membership = membership
                    break
            
            if not active_membership:
                return {
                    'tier': 'visitor',
                    'status': 'expired',
                    'expiration_date': None,
                    'account_id': account_id
                }
            
            # Determine tier based on membership level
            membership_name = active_membership.get('membershipLevel', {}).get('name', '').lower()
            
            # Check if life member
            if 'life' in membership_name:
                tier = 'life_member'
            else:
                tier = 'member'
            
            # Get expiration date
            expiration_str = active_membership.get('termEndDate')
            expiration_date = None
            if expiration_str:
                try:
                    expiration_date = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
                except:
                    pass
            
            return {
                'tier': tier,
                'status': 'active',
                'expiration_date': expiration_date,
                'account_id': account_id,
                'membership_name': active_membership.get('membershipLevel', {}).get('name')
            }
            
        except Exception as e:
            logger.error(f"Error getting membership info: {e}")
            return {
                'tier': 'visitor',
                'status': 'error',
                'expiration_date': None,
                'account_id': account_id
            }
    
    def verify_member_access(self, account_id: str = None, email: str = None) -> Dict[str, Any]:
        """
        Verify if user has member access and what tier
        Can use either account_id or email
        """
        if not account_id and email:
            account = self.get_account_by_email(email)
            if account:
                account_id = account.get('accountId')
        
        if not account_id:
            return {
                'has_access': False,
                'tier': 'visitor',
                'reason': 'No account found'
            }
        
        membership_info = self.get_membership_info(account_id)
        
        has_access = membership_info['status'] == 'active'
        
        return {
            'has_access': has_access,
            'tier': membership_info['tier'],
            'status': membership_info['status'],
            'expiration_date': membership_info.get('expiration_date'),
            'account_id': account_id
        }


# Singleton instance
neon_one_service = NeonOneService()
