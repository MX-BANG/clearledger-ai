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
        # Using flash-lite for faster responses
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={
                'temperature': 0.1,
                'top_p': 1,
                'max_output_tokens': 2048,
            }
        )
    
    def structure_text(self, raw_text: str, source_file: str) -> dict:
        """
        Convert raw OCR text into structured transaction data
        Handles both receipts and CSV/Excel data
        """
        
        # Check if this is CSV/structured data
        if self._is_structured_data(raw_text):
            return self._parse_structured_data(raw_text, source_file)
        
        # Otherwise, process as receipt/invoice
        prompt = f"""
Extract transaction data from this receipt/invoice text.

Text:
{raw_text[:2000]}

Return ONLY valid JSON with these exact fields:
{{"date":"YYYY-MM-DD","vendor":"name","amount":number,"currency":"{DEFAULT_CURRENCY}","category":"Food|Fuel|Transport|Utilities|Rent|Office|Other","notes":"brief note","confidence":{{"vendor":0.9,"amount":0.9,"date":0.9,"category":0.9}}}}

Rules: If unclear, use today's date. Fix OCR errors. Pick total amount. Conservative confidence scores.
"""
        
        try:
            # Add timeout and retry logic
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    result_text = response.text.strip()
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1 and ("timeout" in str(e).lower() or "504" in str(e)):
                        time.sleep(2)  # Wait 2 seconds before retry
                        continue
                    raise  # Re-raise if not timeout or last attempt
            
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
            return self._get_empty_result(source_file, f"AI extraction failed: {str(e)}")
    
    def _is_structured_data(self, text: str) -> bool:
        """Check if text is from CSV/Excel (structured data)"""
        # Look for common CSV patterns
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check if first line looks like headers
        first_line = lines[0].lower()
        csv_indicators = ['date', 'amount', 'vendor', 'description', 'price', 'total', 'category']
        
        # Also check for dict-like structure from pandas
        if text.strip().startswith('{') and ':' in text:
            return True
        
        return any(indicator in first_line for indicator in csv_indicators)
    
    def _parse_structured_data(self, text: str, source_file: str) -> dict:
        """Parse CSV/Excel structured data"""
        
        # Use AI to understand the CSV structure
        prompt = f"""
This is structured data from a spreadsheet/CSV. Extract ONE transaction.

Data:
{text[:1500]}

Return ONLY valid JSON with these exact fields:
{{"date":"YYYY-MM-DD","vendor":"name","amount":number,"currency":"{DEFAULT_CURRENCY}","category":"Food|Fuel|Transport|Utilities|Rent|Office|Other","notes":"brief note","confidence":{{"vendor":0.8,"amount":0.9,"date":0.8,"category":0.7}}}}

Look for columns like: date, vendor/merchant/name, amount/price/total, description/notes.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            result_text = re.sub(r'```json\s*|\s*```', '', result_text)
            structured_data = json.loads(result_text)
            return self._validate_and_fix(structured_data, text[:500], source_file)
        except Exception as e:
            return self._get_empty_result(source_file, f"CSV parsing failed: {str(e)}")
    
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
    
    def _get_empty_result(self, source_file: str, error_msg: str) -> dict:
        """Return empty result structure"""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "vendor": "Unknown",
            "amount": 0.0,
            "currency": DEFAULT_CURRENCY,
            "category": "Other",
            "notes": error_msg,
            "confidence": {
                "vendor": 0.1,
                "amount": 0.1,
                "date": 0.1,
                "category": 0.1
            },
            "source_file": source_file,
            "raw_text": "",
            "needs_review": True
        }