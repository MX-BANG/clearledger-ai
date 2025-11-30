"""
MVP 4: Duplicate Detection Engine
Identifies potential duplicate transactions
"""

from typing import List, Dict
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta

class DuplicateDetector:
    
    @staticmethod
    def find_duplicates(new_entry: dict, existing_entries: List[dict], threshold: int = 85) -> List[Dict]:
        """
        Find potential duplicates of a new entry against existing entries
        
        Args:
            new_entry: The new transaction to check
            existing_entries: List of existing transactions
            threshold: Similarity threshold (0-100)
        
        Returns:
            List of potential duplicate matches with similarity scores
        """
        duplicates = []
        
        for existing in existing_entries:
            similarity = DuplicateDetector._calculate_similarity(new_entry, existing)
            
            if similarity["overall"] >= threshold:
                duplicates.append({
                    "entry_id": existing.get("id"),
                    "entry": existing,
                    "similarity_score": similarity["overall"],
                    "matching_fields": similarity["details"]
                })
        
        # Sort by similarity score (highest first)
        duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return duplicates
    
    @staticmethod
    def _calculate_similarity(entry1: dict, entry2: dict) -> Dict:
        """
        Calculate similarity between two entries
        Returns overall score and detailed breakdown
        """
        scores = {}
        
        # Amount similarity (exact match gets 100, within 5% gets partial score)
        amount1 = entry1.get("amount", 0)
        amount2 = entry2.get("amount", 0)
        
        if amount1 == amount2:
            scores["amount"] = 100
        elif amount1 > 0 and amount2 > 0:
            diff_percent = abs(amount1 - amount2) / max(amount1, amount2) * 100
            scores["amount"] = max(0, 100 - diff_percent * 2)
        else:
            scores["amount"] = 0
        
        # Vendor similarity (fuzzy string matching)
        vendor1 = entry1.get("vendor", "").lower()
        vendor2 = entry2.get("vendor", "").lower()
        scores["vendor"] = fuzz.ratio(vendor1, vendor2)
        
        # Date similarity (same day = 100, within 3 days = partial)
        date1 = DuplicateDetector._parse_date(entry1.get("date", ""))
        date2 = DuplicateDetector._parse_date(entry2.get("date", ""))
        
        if date1 and date2:
            days_diff = abs((date1 - date2).days)
            if days_diff == 0:
                scores["date"] = 100
            elif days_diff <= 3:
                scores["date"] = max(0, 100 - days_diff * 25)
            else:
                scores["date"] = 0
        else:
            scores["date"] = 0
        
        # Category similarity
        cat1 = entry1.get("category", "").lower()
        cat2 = entry2.get("category", "").lower()
        scores["category"] = 100 if cat1 == cat2 else 0
        
        # Calculate overall score (weighted average)
        weights = {
            "amount": 0.35,
            "vendor": 0.35,
            "date": 0.25,
            "category": 0.05
        }
        
        overall = sum(scores[field] * weights[field] for field in weights)
        
        return {
            "overall": overall,
            "details": scores
        }
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
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
        
        for i, dup in enumerate(duplicates[:3], 1):  # Show top 3
            entry = dup["entry"]
            score = dup["similarity_score"]
            summary += f"\n{i}. Entry #{entry.get('id')} - {entry.get('vendor')} "
            summary += f"({entry.get('amount')} {entry.get('currency')}) "
            summary += f"- Similarity: {score:.0f}%"
        
        return summary