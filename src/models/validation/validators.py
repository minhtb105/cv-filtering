"""
Validation and Normalization Utilities

Contains utility classes for data validation and normalization used throughout
the CV Intelligence Platform.
"""

import re
import phonenumbers
from datetime import datetime, timezone
from typing import Optional


class PhoneValidator:
    """E.164 phone number validation and normalization"""
    
    @staticmethod
    def normalize_e164(phone: str, region: Optional[str] = "VN") -> Optional[str]:
        """
        Normalize phone to E.164 format: +<country_code><number>
        Examples: "+84912345678", "+12025551234"
        """
        try:
            parsed = phonenumbers.parse(phone, region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
        except:
            return None
    
    @staticmethod
    def validate_e164(phone: str) -> bool:
        """Validate E.164 format"""
        try:
            parsed = phonenumbers.parse(phone, None)  # None vì đã có +
            return phonenumbers.is_valid_number(parsed)
        except:
            return False


class DateValidator:
    """Date format validation and normalization"""
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """Normalize date to YYYY-MM format"""
        if not date_str or date_str.lower() in ['present', 'current', 'ongoing']:
            return None
        
        # Try various date formats
        formats = [
            '%Y-%m',           # 2024-01
            '%Y/%m',           # 2024/01
            '%m/%Y',           # 01/2024
            '%B %Y',           # January 2024
            '%b %Y',           # Jan 2024
            '%Y-%m-%d',        # 2024-01-15
            '%Y/%m/%d',        # 2024/01/15
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime('%Y-%m')
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def compute_months(start_date: str, end_date: Optional[str] = None) -> int:
        """
        Compute duration in months between two dates (YYYY-MM format)
        If end_date is None, use current date
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m')
            end = end_date
            
            if not end:
                end = datetime.now(timezone.utc())
            else:
                end = datetime.strptime(end_date, '%Y-%m')
            
            months = (end.year - start.year) * 12 + (end.month - start.month)
            return max(0, months)
        except (ValueError, AttributeError):
            return 0