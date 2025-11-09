"""
Admin Demo Mode System
Allows administrators to enable unlimited widget usage for testing/debugging
"""
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app import db

logger = logging.getLogger(__name__)


class AdminSettings(db.Model):
    """Global admin settings for the widget system"""
    __tablename__ = 'admin_settings'
    
    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AdminSetting {self.setting_key}={self.setting_value}>"


class DemoModeManager:
    """Manage demo mode settings"""
    
    DEMO_MODE_KEY = 'widget_demo_mode_enabled'
    DEMO_ACCOUNTS_KEY = 'widget_demo_mode_accounts'
    
    @staticmethod
    def is_demo_mode_enabled() -> bool:
        """Check if demo mode is globally enabled"""
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_MODE_KEY
        ).first()
        
        if setting:
            return setting.setting_value.lower() in ['true', '1', 'yes', 'enabled']
        
        return False
    
    @staticmethod
    def enable_demo_mode(admin_email: str = 'admin'):
        """Enable demo mode (unlimited usage for all users)"""
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_MODE_KEY
        ).first()
        
        if setting:
            setting.setting_value = 'true'
            setting.updated_by = admin_email
            setting.updated_at = datetime.utcnow()
        else:
            setting = AdminSettings(
                setting_key=DemoModeManager.DEMO_MODE_KEY,
                setting_value='true',
                description='Enable unlimited usage for all users (testing/debugging)',
                updated_by=admin_email
            )
            db.session.add(setting)
        
        db.session.commit()
        logger.info(f"✅ Demo mode ENABLED by {admin_email}")
        return True
    
    @staticmethod
    def disable_demo_mode(admin_email: str = 'admin'):
        """Disable demo mode (normal usage limits apply)"""
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_MODE_KEY
        ).first()
        
        if setting:
            setting.setting_value = 'false'
            setting.updated_by = admin_email
            setting.updated_at = datetime.utcnow()
            db.session.commit()
        
        logger.info(f"🛑 Demo mode DISABLED by {admin_email}")
        return True
    
    @staticmethod
    def add_demo_account(neon_one_account_id: str, reason: str = '', admin_email: str = 'admin'):
        """
        Add specific account to demo whitelist (unlimited usage even when demo mode off)
        Useful for: beta testers, debugging helpers, VIP members
        """
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_ACCOUNTS_KEY
        ).first()
        
        # Get current whitelist
        if setting:
            accounts = setting.setting_value.split(',')
            accounts = [a.strip() for a in accounts if a.strip()]
        else:
            accounts = []
        
        # Add new account if not already there
        if neon_one_account_id not in accounts:
            accounts.append(neon_one_account_id)
            
            if setting:
                setting.setting_value = ','.join(accounts)
                setting.updated_by = admin_email
                setting.updated_at = datetime.utcnow()
            else:
                setting = AdminSettings(
                    setting_key=DemoModeManager.DEMO_ACCOUNTS_KEY,
                    setting_value=','.join(accounts),
                    description=f'Accounts with unlimited access: {reason}',
                    updated_by=admin_email
                )
                db.session.add(setting)
            
            db.session.commit()
            logger.info(f"✅ Added demo account: {neon_one_account_id} (reason: {reason})")
            return True
        
        return False
    
    @staticmethod
    def remove_demo_account(neon_one_account_id: str, admin_email: str = 'admin'):
        """Remove account from demo whitelist"""
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_ACCOUNTS_KEY
        ).first()
        
        if not setting:
            return False
        
        accounts = setting.setting_value.split(',')
        accounts = [a.strip() for a in accounts if a.strip()]
        
        if neon_one_account_id in accounts:
            accounts.remove(neon_one_account_id)
            setting.setting_value = ','.join(accounts)
            setting.updated_by = admin_email
            setting.updated_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"🛑 Removed demo account: {neon_one_account_id}")
            return True
        
        return False
    
    @staticmethod
    def is_demo_account(neon_one_account_id: str) -> bool:
        """Check if specific account has demo privileges"""
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_ACCOUNTS_KEY
        ).first()
        
        if not setting:
            return False
        
        accounts = setting.setting_value.split(',')
        accounts = [a.strip() for a in accounts if a.strip()]
        
        return neon_one_account_id in accounts
    
    @staticmethod
    def get_demo_accounts() -> list:
        """Get list of all demo accounts"""
        setting = AdminSettings.query.filter_by(
            setting_key=DemoModeManager.DEMO_ACCOUNTS_KEY
        ).first()
        
        if not setting:
            return []
        
        accounts = setting.setting_value.split(',')
        return [a.strip() for a in accounts if a.strip()]
    
    @staticmethod
    def check_unlimited_access(neon_one_account_id: str = None) -> bool:
        """
        Check if user has unlimited access (either demo mode OR whitelisted account)
        
        Returns True if:
        - Demo mode is globally enabled, OR
        - Account is on demo whitelist
        """
        # Global demo mode
        if DemoModeManager.is_demo_mode_enabled():
            return True
        
        # Individual account whitelist
        if neon_one_account_id and DemoModeManager.is_demo_account(neon_one_account_id):
            return True
        
        return False
    
    @staticmethod
    def get_status() -> dict:
        """Get current demo mode status"""
        return {
            'demo_mode_enabled': DemoModeManager.is_demo_mode_enabled(),
            'demo_accounts': DemoModeManager.get_demo_accounts(),
            'demo_account_count': len(DemoModeManager.get_demo_accounts())
        }


# Singleton instance
demo_mode = DemoModeManager()
