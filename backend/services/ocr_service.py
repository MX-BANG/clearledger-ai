"""
MVP 1: Multi-Input Data Extraction
Extracts raw text from images, PDFs, and structured files
"""

import easyocr
from PIL import Image
import pandas as pd
from pathlib import Path
from typing import Dict, Any
import pytesseract
from pdf2image import convert_from_path

class OCRService:
    def __init__(self):
        # Initialize EasyOCR (English and Urdu for Pakistan)
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text from various file types
        Returns: {
            "raw_text": str,
            "source": str,
            "success": bool,
            "error": str (if any)
        }
        """
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension in ['.jpg', '.jpeg', '.png']:
                return self._extract_from_image(file_path)
            elif file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.csv':
                return self._extract_from_csv(file_path)
            elif file_extension == '.xlsx':
                return self._extract_from_excel(file_path)
            else:
                return {
                    "raw_text": "",
                    "source": str(file_path),
                    "success": False,
                    "error": f"Unsupported file type: {file_extension}"
                }
        except Exception as e:
            return {
                "raw_text": "",
                "source": str(file_path),
                "success": False,
                "error": str(e)
            }
    
    def _extract_from_image(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from image using EasyOCR"""
        try:
            # Use EasyOCR
            result = self.reader.readtext(str(file_path), detail=0)
            raw_text = "\n".join(result)
            
            return {
                "raw_text": raw_text,
                "source": file_path.name,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "raw_text": "",
                "source": file_path.name,
                "success": False,
                "error": f"OCR failed: {str(e)}"
            }
    
    def _extract_from_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF (convert to images first)"""
        try:
            # Convert PDF to images
            images = convert_from_path(str(file_path))
            
            all_text = []
            for i, image in enumerate(images):
                # Save temporarily and run OCR
                temp_path = file_path.parent / f"temp_page_{i}.png"
                image.save(temp_path)
                
                result = self.reader.readtext(str(temp_path), detail=0)
                all_text.extend(result)
                
                # Clean up temp file
                temp_path.unlink()
            
            raw_text = "\n".join(all_text)
            
            return {
                "raw_text": raw_text,
                "source": file_path.name,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "raw_text": "",
                "source": file_path.name,
                "success": False,
                "error": f"PDF extraction failed: {str(e)}"
            }
    
    def _extract_from_csv(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from CSV"""
        try:
            df = pd.read_csv(file_path)
            # Convert entire CSV to text representation
            raw_text = df.to_string()
            
            return {
                "raw_text": raw_text,
                "source": file_path.name,
                "success": True,
                "error": None,
                "dataframe": df  # Extra: return structured data
            }
        except Exception as e:
            return {
                "raw_text": "",
                "source": file_path.name,
                "success": False,
                "error": f"CSV parsing failed: {str(e)}"
            }
    
    def _extract_from_excel(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from Excel"""
        try:
            df = pd.read_excel(file_path)
            raw_text = df.to_string()
            
            return {
                "raw_text": raw_text,
                "source": file_path.name,
                "success": True,
                "error": None,
                "dataframe": df
            }
        except Exception as e:
            return {
                "raw_text": "",
                "source": file_path.name,
                "success": False,
                "error": f"Excel parsing failed: {str(e)}"
            }