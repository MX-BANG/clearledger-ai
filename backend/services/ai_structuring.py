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
        Supports multiple languages (English, Urdu, Roman Urdu, etc.)
        """
        
        # Check if this is CSV/structured data
        if self._is_structured_data(raw_text):
            return self._parse_structured_data(raw_text, source_file)
        
        # Detect if text might be in another language and needs translation
        detected_language = self._detect_language(raw_text)
        
        # Get today's date for explicit use in prompt
        today_date = datetime.now().strftime("%Y-%m-%d")

        # Otherwise, process as receipt/invoice/message with multi-language support
        prompt = f"""
Extract transaction data from this text. The text may be in English, Urdu, Roman Urdu, or mixed languages.

Text:
{raw_text[:2000]}

Detected Language: {detected_language}

Instructions:
1. Translate/understand the text if needed
2. Extract transaction information
3. **CRITICAL: Determine if this is INCOME or EXPENSE**
   - INCOME keywords: received, salary, payment received, credited, income, mila, aya, deposit, refund
   - EXPENSE keywords: paid, spent, purchased, transferred, debited, expense, diya, bheja, kharcha, buy
4. Common patterns:
   - "pay kiye" / "paid" = EXPENSE
   - "transfer" / "bheja" = EXPENSE
   - "received" / "mila" = INCOME
   - "salary" = INCOME
   - Receipts from stores = EXPENSE
   - Money coming to you = INCOME

Return ONLY valid JSON with these exact fields:
{{"date":"YYYY-MM-DD","vendor":"name","amount":number,"transaction_type":"income|expense","currency":"{DEFAULT_CURRENCY}","category":"Food|Fuel|Transport|Utilities|Rent|Office|Salary|Other","notes":"brief description in English","confidence":{{"vendor":0.9,"amount":0.9,"date":0.9,"category":0.9,"transaction_type":0.9}}}}

Rules:
- **CRITICAL DATE RULE: Only use dates that are EXPLICITLY present in the text**
- **If NO date appears anywhere in the text, use today's upload date: {today_date} and set confidence.date to 0.3**
- Do NOT assume, guess, or hallucinate any dates (including 2023, 2024, or any other year)
- Do NOT infer dates from context, file names, or metadata
- Extract amount (look for numbers)
- Identify vendor/person name
- **MUST classify as income or expense**
- Translate notes to English
- Be conservative with confidence scores
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
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the input text"""
        # Simple language detection based on character patterns
        text_sample = text[:200].lower()
        
        # Check for Urdu script (Unicode range)
        urdu_chars = sum(1 for c in text_sample if '\u0600' <= c <= '\u06FF')
        
        # Check for Roman Urdu keywords
        roman_urdu_keywords = ['kiye', 'bheja', 'diye', 'mila', 'ko', 'se', 'ka', 'ki', 'ne', 'usko', 'isko']
        roman_urdu_found = sum(1 for keyword in roman_urdu_keywords if keyword in text_sample)
        
        # Check for common payment keywords in various languages
        if urdu_chars > 5:
            return "Urdu (اردو)"
        elif roman_urdu_found >= 2:
            return "Roman Urdu / Hinglish"
        else:
            return "English or Mixed"
    
    def _parse_structured_data(self, text: str, source_file: str) -> dict:
        """Parse CSV/Excel structured data"""

        # Get today's date for explicit use in prompt
        today_date = datetime.now().strftime("%Y-%m-%d")

        # Use AI to understand the CSV structure
        prompt = f"""
This is structured data from a spreadsheet/CSV. Extract ONE transaction.

Data:
{text[:1500]}

Return ONLY valid JSON with these exact fields:
{{"date":"YYYY-MM-DD","vendor":"name","amount":number,"currency":"{DEFAULT_CURRENCY}","category":"Food|Fuel|Transport|Utilities|Rent|Office|Other","notes":"brief note","confidence":{{"vendor":0.8,"amount":0.9,"date":0.8,"category":0.7}}}}

Rules:
- **IMPORTANT: If NO date is found in the data, use today's date: {today_date} and set confidence.date to 0.3**
- Only extract dates that are explicitly present in the data
- Do NOT assume or hallucinate dates
- Look for columns like: date, vendor/merchant/name, amount/price/total, description/notes.
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
            "transaction_type": "expense",  # Default to expense
            "currency": DEFAULT_CURRENCY,
            "category": "Other",
            "notes": "",
            "confidence": {
                "vendor": 0.5,
                "amount": 0.5,
                "date": 0.5,
                "category": 0.5,
                "transaction_type": 0.5
            }
        }
        
        # Track if date was missing or auto-filled
        date_was_missing = False
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
                if key == "date":
                    date_was_missing = True
        
        # Classify income vs expense if not provided
        if "transaction_type" not in data or data["transaction_type"] not in ["income", "expense"]:
            data["transaction_type"] = self._classify_transaction_type(raw_text, data.get("category", ""), data.get("notes", ""))
        
        # Split amount into income/expense
        amount = data.get("amount", 0.0)
        if data["transaction_type"] == "income":
            data["income"] = amount
            data["expense"] = 0.0
        else:
            data["income"] = 0.0
            data["expense"] = amount
        
        # Check if date looks auto-filled (today's date with low confidence)
        today = datetime.now().strftime("%Y-%m-%d")
        if data["date"] == today and data["confidence"]["date"] < 0.6:
            date_was_missing = True
            data["confidence"]["date"] = 0.3  # Lower confidence for assumed date
            if data["notes"]:
                data["notes"] = f"[Date assumed: {today}] {data['notes']}"
            else:
                data["notes"] = f"Date not found in image, assumed today's date ({today})"
        
        # Add metadata
        data["source_file"] = source_file
        data["raw_text"] = raw_text
        
        # Determine if needs review
        avg_confidence = sum(data["confidence"].values()) / len(data["confidence"])
        data["needs_review"] = (
            avg_confidence < 0.7 or 
            data["amount"] == 0 or 
            date_was_missing  # IMPORTANT: Flag for review if date was missing
        )
        
        return data
    
    def _classify_transaction_type(self, raw_text: str, category: str, notes: str) -> str:
        """Classify transaction as income or expense based on keywords"""
        text_combined = f"{raw_text} {category} {notes}".lower()
        
        # Income keywords
        income_keywords = ['received', 'salary', 'income', 'credited', 'deposit', 'refund', 'mila', 'aya', 'payment received']
        
        # Expense keywords
        expense_keywords = ['paid', 'spent', 'purchase', 'transferred', 'debited', 'expense', 'diya', 'bheja', 'kharcha', 'buy', 'bought']
        
        # Check for income indicators
        income_score = sum(1 for keyword in income_keywords if keyword in text_combined)
        expense_score = sum(1 for keyword in expense_keywords if keyword in text_combined)
        
        # Default to expense unless clear income indicators
        if income_score > expense_score:
            return "income"
        else:
            return "expense"
    
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