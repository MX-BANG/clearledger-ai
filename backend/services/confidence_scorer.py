"""
MVP 3: Confidence Scoring + Error Flagging
Analyzes extracted data and flags potential issues
"""

from typing import Dict, List
import re
from datetime import datetime

class ConfidenceScorer:
    
    @staticmethod
    def analyze_entry(entry: dict) -> Dict[str, any]:
        """
        Analyze a transaction entry and return flags/warnings
        Returns: {
            "flags": List[str],
            "warnings": List[str],
            "overall_confidence": float,
            "needs_review": bool
        }
        """
        flags = []
        warnings = []
        
        # Check date validity
        date_flag = ConfidenceScorer._check_date(entry.get("date", ""))
        if date_flag:
            flags.append(date_flag)
        
        # Check amount
        amount_flag = ConfidenceScorer._check_amount(entry.get("amount", 0))
        if amount_flag:
            flags.append(amount_flag)
        
        # Check vendor
        vendor_flag = ConfidenceScorer._check_vendor(entry.get("vendor", ""))
        if vendor_flag:
            flags.append(vendor_flag)
        
        # Check confidence scores
        confidence = entry.get("confidence", {})
        for field, score in confidence.items():
            if score < 0.5:
                warnings.append(f"{field.capitalize()} has low confidence ({score:.0%}). Please review.")
        
        # Calculate overall confidence
        overall_confidence = sum(confidence.values()) / len(confidence) if confidence else 0.0
        
        # Determine if needs review
        needs_review = (
            len(flags) > 0 or
            overall_confidence < 0.7 or
            entry.get("amount", 0) == 0
        )
        
        return {
            "flags": flags,
            "warnings": warnings,
            "overall_confidence": overall_confidence,
            "needs_review": needs_review
        }
    
    @staticmethod
    def _check_date(date_str: str) -> str:
        """Check if date is valid"""
        if not date_str:
            return "⚠️ Date is missing"
        
        try:
            # Try parsing the date
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if date is in future
            if parsed_date > datetime.now():
                return "⚠️ Date is in the future. Please verify."
            
            # Check if date is too old (more than 2 years)
            if (datetime.now() - parsed_date).days > 730:
                return "⚠️ Date is more than 2 years old. Please verify."
            
        except ValueError:
            return "❌ Date format is invalid. Expected YYYY-MM-DD."
        
        return None
    
    @staticmethod
    def _check_amount(amount: float) -> str:
        """Check if amount is valid"""
        if amount == 0:
            return "❌ Amount is zero or missing"
        
        if amount < 0:
            return "❌ Amount is negative"
        
        if amount > 1000000:  # 1 million PKR
            return "⚠️ Amount seems unusually high. Please verify."
        
        return None
    
    @staticmethod
    def _check_vendor(vendor: str) -> str:
        """Check if vendor name is valid"""
        if not vendor or vendor.lower() == "unknown":
            return "⚠️ Vendor name is unknown or missing"
        
        # Check for gibberish (too many special characters)
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', vendor))
        if special_chars > len(vendor) * 0.3:
            return "⚠️ Vendor name contains unusual characters. OCR may have failed."
        
        # Check for very long vendor names (likely OCR error)
        if len(vendor) > 50:
            return "⚠️ Vendor name is unusually long. Please verify."
        
        return None
    
    @staticmethod
    def get_confidence_level(score: float) -> str:
        """Convert confidence score to human-readable level"""
        if score >= 0.9:
            return "🟢 High"
        elif score >= 0.7:
            return "🟡 Medium"
        elif score >= 0.5:
            return "🟠 Low"
        else:
            return "🔴 Very Low"