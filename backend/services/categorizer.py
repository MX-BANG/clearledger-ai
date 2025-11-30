"""
MVP 5: Categorization Engine
Auto-assigns categories based on vendor names and keywords
"""

from backend.config import CATEGORY_KEYWORDS
from typing import Tuple

class Categorizer:
    
    @staticmethod
    def categorize(vendor: str, notes: str = "") -> Tuple[str, float]:
        """
        Categorize a transaction based on vendor name and notes
        
        Returns:
            (category, confidence_score)
        """
        vendor_lower = vendor.lower()
        notes_lower = notes.lower() if notes else ""
        combined_text = f"{vendor_lower} {notes_lower}"
        
        # Track matches for each category
        category_scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            if category == "Other":
                continue
            
            score = 0
            matches = 0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Exact match in vendor name (highest priority)
                if keyword_lower in vendor_lower:
                    score += 10
                    matches += 1
                
                # Partial match in combined text
                elif keyword_lower in combined_text:
                    score += 5
                    matches += 1
            
            if matches > 0:
                category_scores[category] = (score, matches)
        
        # If no matches, return "Other" with low confidence
        if not category_scores:
            return "Other", 0.3
        
        # Get category with highest score
        best_category = max(category_scores.items(), key=lambda x: (x[1][0], x[1][1]))
        category = best_category[0]
        score, matches = best_category[1]
        
        # Calculate confidence (0.0 to 1.0)
        # More matches and higher scores = higher confidence
        confidence = min(0.95, 0.6 + (matches * 0.1) + (score * 0.01))
        
        return category, confidence
    
    @staticmethod
    def get_all_categories() -> list:
        """Get list of all available categories"""
        return list(CATEGORY_KEYWORDS.keys())
    
    @staticmethod
    def suggest_category(vendor: str, amount: float = None) -> dict:
        """
        Get category suggestion with reasoning
        """
        category, confidence = Categorizer.categorize(vendor)
        
        # Find which keywords matched
        matched_keywords = []
        vendor_lower = vendor.lower()
        
        if category != "Other":
            for keyword in CATEGORY_KEYWORDS[category]:
                if keyword.lower() in vendor_lower:
                    matched_keywords.append(keyword)
        
        return {
            "category": category,
            "confidence": confidence,
            "reasoning": f"Matched keywords: {', '.join(matched_keywords)}" if matched_keywords else "No strong matches found",
            "alternative_categories": Categorizer._get_alternatives(vendor)
        }
    
    @staticmethod
    def _get_alternatives(vendor: str) -> list:
        """Get alternative category suggestions"""
        vendor_lower = vendor.lower()
        alternatives = []
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            if category == "Other":
                continue
            
            for keyword in keywords:
                if keyword.lower() in vendor_lower:
                    alternatives.append(category)
                    break
        
        return alternatives[:3]  # Return top 3 alternatives