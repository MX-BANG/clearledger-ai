"""
MVP 2: AI Data Structuring Engine
Converts raw text into structured transaction data using Google Gemini
"""

import google.generativeai as genai
from backend.config import GEMINI_API_KEY, DEFAULT_CURRENCY
import json
import re
from datetime import datetime

class AIStructuringService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def structure_text(self, raw_text: str, source_file: str) -> dict:
        """
        Convert raw OCR text into structured transaction data
        """
        
        prompt = f"""
You are an expert bookkeeping AI. Extract transaction information from the following text.

Raw Text:
{raw_text}

Extract and return ONLY a valid JSON object with these fields:
- date: in YYYY-MM-DD format
- vendor: company or merchant name
- amount: numeric value only (no currency symbols)
- currency: currency code (default: {DEFAULT_CURRENCY})
- category: one of [Food, Fuel, Transport, Utilities, Rent, Office, Other]
- notes: brief description
- confidence: object with confidence scores (0.0-1.0) for {{vendor, amount, date, category}}

Rules:
- If date is unclear, use today's date and set confidence.date to 0.4
- Fix common OCR mistakes (e.g., "12ll" → "1211")
- If amount has multiple values, pick the total
- Be conservative with confidence scores

Return ONLY valid JSON, no markdown or explanations.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up markdown code blocks if present
            result_text = re.sub(r'```json\s*|\s*```', '', result_text)
            
            # Parse JSON
            structured_data = json.loads(result_text)
            
            # Validate and set defaults
            structured_data = self._validate_and_fix(structured_data, raw_text, source_file)
            
            return structured_data
            
        except json.JSONDecodeError as e:
            # Fallback: try to extract manually
            return self._manual_extraction(raw_text, source_file)
        except Exception as e:
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "vendor": "Unknown",
                "amount": 0.0,
                "currency": DEFAULT_CURRENCY,
                "category": "Other",
                "notes": f"AI extraction failed: {str(e)}",
                "confidence": {
                    "vendor": 0.1,
                    "amount": 0.1,
                    "date": 0.1,
                    "category": 0.1
                },
                "source_file": source_file,
                "raw_text": raw_text,
                "needs_review": True
            }
    
    def _validate_and_fix(self, data: dict, raw_text: str, source_file: str) -> dict:
        """Validate and fix structured data"""
        
        # Ensure all required fields exist
        defaults = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "vendor": "Unknown",
            "amount": 0.0,
            "currency": DEFAULT_CURRENCY,
            "category": "Other",
            "notes": "",
            "confidence": {
                "vendor": 0.5,
                "amount": 0.5,
                "date": 0.5,
                "category": 0.5
            }
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        # Add metadata
        data["source_file"] = source_file
        data["raw_text"] = raw_text
        
        # Determine if needs review (low confidence)
        avg_confidence = sum(data["confidence"].values()) / len(data["confidence"])
        data["needs_review"] = avg_confidence < 0.7 or data["amount"] == 0
        
        return data
    
    def _manual_extraction(self, raw_text: str, source_file: str) -> dict:
        """Fallback manual extraction using regex"""
        
        result = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "vendor": "Unknown",
            "amount": 0.0,
            "currency": DEFAULT_CURRENCY,
            "category": "Other",
            "notes": "",
            "confidence": {
                "vendor": 0.3,
                "amount": 0.3,
                "date": 0.3,
                "category": 0.3
            },
            "source_file": source_file,
            "raw_text": raw_text,
            "needs_review": True
        }
        
        # Try to find amount
        amount_patterns = [
            r'(?:PKR|RS|Rs\.?)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:PKR|RS|Rs\.?)',
            r'Total:?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    result["amount"] = float(amount_str)
                    result["confidence"]["amount"] = 0.6
                    break
                except ValueError:
                    pass
        
        # Try to find date
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, raw_text)
            if match:
                result["date"] = match.group(1)
                result["confidence"]["date"] = 0.5
                break
        
        return result