"""
MVP 4: Duplicate Detection Engine (Improved)
Identifies potential duplicate transactions with better accuracy
"""

from typing import List, Dict, Optional
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuplicateDetector:
    
    @staticmethod
    def find_duplicates(new_entry: dict, existing_entries: List[dict], threshold: int = 70) -> List[Dict]:
        """
        Find potential duplicates of a new entry against existing entries
        
        Args:
            new_entry: The new transaction to check
            existing_entries: List of existing transactions
            threshold: Similarity threshold (0-100), lowered to 70 for better detection
        
        Returns:
            List of potential duplicate matches with similarity scores
        """
        duplicates = []
        
        logger.info(f"Checking new entry for duplicates:")
        logger.info(f"  Vendor: {new_entry.get('vendor')}")
        logger.info(f"  Amount: {new_entry.get('amount') or new_entry.get('income') or new_entry.get('expense')}")
        logger.info(f"  Date: {new_entry.get('date')}")
        logger.info(f"Against {len(existing_entries)} existing entries")
        
        for existing in existing_entries:
            similarity = DuplicateDetector._calculate_similarity(new_entry, existing)
            
            logger.debug(f"Comparing with entry {existing.get('id')}:")
            logger.debug(f"  Overall: {similarity['overall']:.1f}%")
            logger.debug(f"  Details: {similarity['details']}")
            
            if similarity["overall"] >= threshold:
                logger.info(f"✓ DUPLICATE FOUND! Entry {existing.get('id')} - Score: {similarity['overall']:.1f}%")
                duplicates.append({
                    "entry_id": existing.get("id"),
                    "entry": existing,
                    "similarity_score": similarity["overall"],
                    "matching_fields": similarity["details"]
                })
            elif similarity["overall"] >= threshold - 10:
                logger.info(f"⚠ Near-duplicate: Entry {existing.get('id')} - Score: {similarity['overall']:.1f}%")
        
        # Sort by similarity score (highest first)
        duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(f"Total duplicates found: {len(duplicates)}")
        return duplicates
    
    @staticmethod
    def _calculate_similarity(entry1: dict, entry2: dict) -> Dict:
        """
        Calculate similarity between two entries
        Returns overall score and detailed breakdown
        """
        scores = {}
        
        # Amount similarity - FIXED to handle all cases properly
        amount1 = DuplicateDetector._get_amount(entry1)
        amount2 = DuplicateDetector._get_amount(entry2)

        if amount1 is None or amount2 is None:
            scores["amount"] = 0
        elif amount1 == amount2:
            scores["amount"] = 100
        elif amount1 != 0 and amount2 != 0:
            # Calculate percentage difference
            diff_percent = abs(amount1 - amount2) / max(abs(amount1), abs(amount2)) * 100
            if diff_percent <= 1:  # Within 1%
                scores["amount"] = 100
            elif diff_percent <= 5:  # Within 5%
                scores["amount"] = 90
            elif diff_percent <= 10:  # Within 10%
                scores["amount"] = 70
            else:
                scores["amount"] = max(0, 100 - diff_percent * 1.5)
        else:
            scores["amount"] = 0
        
        # Vendor similarity (fuzzy string matching) - handles missing fields
        vendor1 = str(entry1.get("vendor") or entry1.get("merchant") or entry1.get("description") or "").strip().lower()
        vendor2 = str(entry2.get("vendor") or entry2.get("merchant") or entry2.get("description") or "").strip().lower()
        
        if vendor1 and vendor2:
            scores["vendor"] = fuzz.ratio(vendor1, vendor2)
        else:
            scores["vendor"] = 0
        
        # Date similarity - FIXED with multiple format support
        date1 = DuplicateDetector._parse_date(entry1.get("date", ""))
        date2 = DuplicateDetector._parse_date(entry2.get("date", ""))
        
        if date1 and date2:
            days_diff = abs((date1 - date2).days)
            if days_diff == 0:
                scores["date"] = 100
            elif days_diff == 1:
                scores["date"] = 85
            elif days_diff == 2:
                scores["date"] = 70
            elif days_diff == 3:
                scores["date"] = 50
            else:
                scores["date"] = max(0, 100 - days_diff * 15)
        else:
            scores["date"] = 0
        
        # Category similarity
        cat1 = str(entry1.get("category", "")).strip().lower()
        cat2 = str(entry2.get("category", "")).strip().lower()
        
        if cat1 and cat2:
            scores["category"] = 100 if cat1 == cat2 else 0
        else:
            scores["category"] = 0
        
        # Calculate overall score (weighted average)
        weights = {
            "amount": 0.40,  # 40% weight on amount
            "vendor": 0.40,  # 40% weight on vendor
            "date": 0.15,    # 15% weight on date
            "category": 0.05 # 5% weight on category
        }
        
        overall = sum(scores[field] * weights[field] for field in weights)
        
        return {
            "overall": overall,
            "details": scores
        }
    
    @staticmethod
    def _get_amount(entry: dict) -> Optional[float]:
        """Extract amount from entry, handling multiple field names"""
        # Try different field names
        amount = entry.get("income") or entry.get("expense") or entry.get("amount")
        
        if amount is None:
            return None
        
        try:
            return float(amount)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object - supports multiple formats"""
        if not date_str:
            return None
        
        # Try multiple date formats
        date_formats = [
            "%Y-%m-%d",           # 2024-01-15
            "%d/%m/%Y",           # 15/01/2024
            "%m/%d/%Y",           # 01/15/2024
            "%Y/%m/%d",           # 2024/01/15
            "%d-%m-%Y",           # 15-01-2024
            "%Y.%m.%d",           # 2024.01.15
            "%d.%m.%Y",           # 15.01.2024
            "%Y%m%d",             # 20240115
            "%B %d, %Y",          # January 15, 2024
            "%b %d, %Y",          # Jan 15, 2024
            "%d %B %Y",           # 15 January 2024
            "%d %b %Y",           # 15 Jan 2024
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        
        # Try parsing ISO format with time
        try:
            return datetime.fromisoformat(str(date_str).strip().replace('Z', '+00:00'))
        except:
            pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    @staticmethod
    def mark_as_duplicate(entry: dict, original_id: int) -> dict:
        """Mark an entry as duplicate"""
        entry["is_duplicate"] = True
        entry["duplicate_of"] = original_id
        return entry
    
    @staticmethod
    def get_duplicate_summary(duplicates: List[Dict]) -> str:
        """Generate human-readable duplicate summary"""
        if not duplicates:
            return "No duplicates found"
        
        summary = f"Found {len(duplicates)} potential duplicate(s):\n"
        
        for i, dup in enumerate(duplicates[:5], 1):  # Show top 5 instead of 3
            entry = dup["entry"]
            score = dup["similarity_score"]
            details = dup["matching_fields"]
            
            # Get amount from entry
            amount = entry.get("income") or entry.get("expense") or entry.get("amount", "N/A")
            currency = entry.get("currency", "")
            
            summary += f"\n{i}. Entry #{entry.get('id')} - {entry.get('vendor', 'Unknown')} "
            summary += f"({amount} {currency}) "
            summary += f"on {entry.get('date', 'N/A')}"
            summary += f"\n   Similarity: {score:.1f}% "
            summary += f"(Amount: {details.get('amount', 0):.0f}%, "
            summary += f"Vendor: {details.get('vendor', 0):.0f}%, "
            summary += f"Date: {details.get('date', 0):.0f}%)"
        
        if len(duplicates) > 5:
            summary += f"\n... and {len(duplicates) - 5} more"
        
        return summary
    
    @staticmethod
    def batch_check_duplicates(entries: List[dict], threshold: int = 70) -> Dict[int, List[Dict]]:
        """
        Check all entries against each other for duplicates
        Useful for finding duplicates in existing dataset
        
        Returns:
            Dictionary mapping entry_id to list of its duplicates
        """
        duplicate_map = {}
        
        for i, entry in enumerate(entries):
            # Check against all other entries (except itself)
            other_entries = entries[:i] + entries[i+1:]
            
            duplicates = DuplicateDetector.find_duplicates(entry, other_entries, threshold)
            
            if duplicates:
                duplicate_map[entry.get("id", i)] = duplicates
        
        return duplicate_map