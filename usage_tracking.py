"""
Usage Tracking and Credit System for Culture Sheet Widget
Manages visitor limits, member credits, and automatic resets
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean
from sqlalchemy.sql import func
from app import db

logger = logging.getLogger(__name__)


class CultureSheetUsage(db.Model):
    """Track culture sheet generation usage per user/visitor"""
    __tablename__ = 'culture_sheet_usage'
    
    id = Column(Integer, primary_key=True)
    
    # Identification (use either neon_one_account_id OR ip_address)
    neon_one_account_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    
    # Membership info
    membership_tier = Column(String(20), nullable=False, default='visitor')  # visitor, member, life_member
    membership_status = Column(String(20), default='active')
    
    # Usage tracking
    sheets_generated = Column(Integer, default=0)
    sheets_with_ai_artwork = Column(Integer, default=0)
    last_generation_date = Column(DateTime)
    last_reset_date = Column(Date, default=func.current_date())
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        identifier = self.neon_one_account_id or self.ip_address
        return f"<CultureSheetUsage {identifier}: {self.sheets_generated} sheets, tier={self.membership_tier}>"


class UsageTracker:
    """Service for tracking and enforcing usage limits"""
    
    # Credit limits per tier
    LIMITS = {
        'visitor': {
            'sheets_per_month': 3,
            'ai_artwork': False,
            'reset_period': 'monthly'
        },
        'member': {
            'sheets_per_year': 100,
            'ai_artwork': True,
            'reset_period': 'yearly'
        },
        'life_member': {
            'sheets_per_day': 50,  # Anti-abuse limit
            'ai_artwork': True,
            'reset_period': 'daily'
        }
    }
    
    def get_or_create_usage_record(
        self, 
        neon_one_account_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        membership_tier: str = 'visitor'
    ) -> CultureSheetUsage:
        """Get existing usage record or create new one"""
        
        # Try to find existing record
        if neon_one_account_id:
            usage = CultureSheetUsage.query.filter_by(
                neon_one_account_id=neon_one_account_id
            ).first()
        elif ip_address:
            usage = CultureSheetUsage.query.filter_by(
                ip_address=ip_address
            ).first()
        else:
            raise ValueError("Must provide either neon_one_account_id or ip_address")
        
        # Create new record if doesn't exist
        if not usage:
            usage = CultureSheetUsage(
                neon_one_account_id=neon_one_account_id,
                ip_address=ip_address,
                membership_tier=membership_tier,
                sheets_generated=0,
                sheets_with_ai_artwork=0,
                last_reset_date=datetime.utcnow().date()
            )
            db.session.add(usage)
            db.session.commit()
        else:
            # Update tier if changed
            if usage.membership_tier != membership_tier:
                usage.membership_tier = membership_tier
                db.session.commit()
        
        return usage
    
    def check_and_reset_if_needed(self, usage: CultureSheetUsage) -> CultureSheetUsage:
        """Check if usage period has expired and reset if needed"""
        
        tier_limits = self.LIMITS.get(usage.membership_tier, self.LIMITS['visitor'])
        reset_period = tier_limits['reset_period']
        
        today = datetime.utcnow().date()
        last_reset = usage.last_reset_date
        
        should_reset = False
        
        if reset_period == 'daily':
            should_reset = last_reset < today
        elif reset_period == 'monthly':
            # Reset if different month
            should_reset = (last_reset.year != today.year or 
                          last_reset.month != today.month)
        elif reset_period == 'yearly':
            # Reset if different year
            should_reset = last_reset.year != today.year
        
        if should_reset:
            logger.info(f"Resetting usage for {usage.neon_one_account_id or usage.ip_address}")
            usage.sheets_generated = 0
            usage.sheets_with_ai_artwork = 0
            usage.last_reset_date = today
            db.session.commit()
        
        return usage
    
    def check_usage_limit(
        self,
        neon_one_account_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        membership_tier: str = 'visitor',
        with_ai_artwork: bool = False
    ) -> Dict[str, Any]:
        """
        Check if user has credits remaining
        
        Returns:
            {
                'allowed': bool,
                'remaining': int,
                'limit': int,
                'tier': str,
                'message': str,
                'upgrade_prompt': bool,
                'demo_mode': bool
            }
        """
        
        # Check for demo mode / unlimited access
        from admin_demo_mode import demo_mode
        
        has_unlimited = demo_mode.check_unlimited_access(neon_one_account_id)
        
        if has_unlimited:
            logger.info(f"✨ Demo/unlimited access granted for {neon_one_account_id or ip_address}")
            return {
                'allowed': True,
                'remaining': 999999,
                'limit': 999999,
                'tier': membership_tier,
                'message': '🎉 Demo Mode Active - Unlimited Access!',
                'upgrade_prompt': False,
                'ai_artwork_allowed': True,
                'demo_mode': True,
                'usage_record_id': None  # Will be set when recorded
            }
        
        # Get or create usage record
        usage = self.get_or_create_usage_record(
            neon_one_account_id=neon_one_account_id,
            ip_address=ip_address,
            membership_tier=membership_tier
        )
        
        # Check if reset needed
        usage = self.check_and_reset_if_needed(usage)
        
        # Get limits for tier
        tier_limits = self.LIMITS.get(membership_tier, self.LIMITS['visitor'])
        
        # Determine applicable limit
        if membership_tier == 'visitor':
            limit = tier_limits['sheets_per_month']
            period = 'month'
        elif membership_tier == 'member':
            limit = tier_limits['sheets_per_year']
            period = 'year'
        else:  # life_member
            limit = tier_limits['sheets_per_day']
            period = 'day'
        
        # Check if AI artwork allowed
        ai_allowed = tier_limits.get('ai_artwork', False)
        
        # Calculate remaining
        remaining = max(0, limit - usage.sheets_generated)
        
        # Determine if allowed
        allowed = remaining > 0
        
        # Generate appropriate message
        if allowed:
            message = f"You have {remaining} of {limit} sheets remaining this {period}"
        else:
            if membership_tier == 'visitor':
                message = "You've reached your free limit. Become a member for 100 sheets/year!"
            elif membership_tier == 'member':
                message = f"You've used all {limit} sheets this {period}. Upgrade to Life Member for unlimited!"
            else:
                message = f"Daily limit reached ({limit} sheets/day). Try again tomorrow!"
        
        return {
            'allowed': allowed,
            'remaining': remaining,
            'limit': limit,
            'tier': membership_tier,
            'message': message,
            'upgrade_prompt': not allowed and membership_tier in ['visitor', 'member'],
            'ai_artwork_allowed': ai_allowed and (with_ai_artwork if allowed else False),
            'usage_record_id': usage.id,
            'demo_mode': False
        }
    
    def record_generation(
        self,
        usage_record_id: int,
        with_ai_artwork: bool = False
    ) -> bool:
        """Record that a culture sheet was generated"""
        
        usage = CultureSheetUsage.query.get(usage_record_id)
        if not usage:
            logger.error(f"Usage record {usage_record_id} not found")
            return False
        
        usage.sheets_generated += 1
        if with_ai_artwork:
            usage.sheets_with_ai_artwork += 1
        usage.last_generation_date = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Recorded generation for {usage.neon_one_account_id or usage.ip_address}: "
                   f"{usage.sheets_generated} total")
        
        return True
    
    def get_usage_stats(
        self,
        neon_one_account_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed usage statistics"""
        
        if neon_one_account_id:
            usage = CultureSheetUsage.query.filter_by(
                neon_one_account_id=neon_one_account_id
            ).first()
        elif ip_address:
            usage = CultureSheetUsage.query.filter_by(
                ip_address=ip_address
            ).first()
        else:
            return {'error': 'Must provide identifier'}
        
        if not usage:
            return {'error': 'No usage record found'}
        
        usage = self.check_and_reset_if_needed(usage)
        
        tier_limits = self.LIMITS.get(usage.membership_tier, self.LIMITS['visitor'])
        
        if usage.membership_tier == 'visitor':
            limit = tier_limits['sheets_per_month']
        elif usage.membership_tier == 'member':
            limit = tier_limits['sheets_per_year']
        else:
            limit = tier_limits['sheets_per_day']
        
        return {
            'tier': usage.membership_tier,
            'sheets_generated': usage.sheets_generated,
            'sheets_with_ai': usage.sheets_with_ai_artwork,
            'limit': limit,
            'remaining': max(0, limit - usage.sheets_generated),
            'last_generation': usage.last_generation_date,
            'last_reset': usage.last_reset_date,
            'created_at': usage.created_at
        }


# Singleton instance
usage_tracker = UsageTracker()
