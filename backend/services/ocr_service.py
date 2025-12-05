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
        # Initialize multiple EasyOCR readers for different language groups
        # Latin script languages (English, Spanish)
        self.latin_reader = easyocr.Reader(['en', 'es'], gpu=False)
        # Arabic script languages (Urdu)
        self.arabic_reader = easyocr.Reader(['en', 'ur'], gpu=False)
        # Devanagari script languages (Hindi)
        self.devanagari_reader = easyocr.Reader(['en', 'hi'], gpu=False)
    
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
        """Extract text from image using multiple EasyOCR readers for multilingual support"""
        try:
            all_text = []

            # Try Latin script reader (English, Spanish)
            try:
                result = self.latin_reader.readtext(str(file_path), detail=0)
                if result:
                    all_text.extend(result)
            except:
                pass

            # Try Arabic script reader (Urdu)
            try:
                result = self.arabic_reader.readtext(str(file_path), detail=0)
                if result:
                    all_text.extend(result)
            except:
                pass

            # Try Devanagari script reader (Hindi)
            try:
                result = self.devanagari_reader.readtext(str(file_path), detail=0)
                if result:
                    all_text.extend(result)
            except:
                pass

            # Remove duplicates and join
            unique_text = list(set(all_text))
            raw_text = "\n".join(unique_text)

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
        """Extract text from PDF (multiple fallback methods)"""
        try:
            # Method 1: Try pdf2image with poppler
            try:
                images = convert_from_path(str(file_path))
                
                all_text = []
                for i, image in enumerate(images):
                    # Save temporarily and run OCR
                    temp_path = file_path.parent / f"temp_page_{i}.png"
                    image.save(temp_path)

                    # Try multiple readers for multilingual support
                    page_text = []

                    # Try Latin script reader (English, Spanish)
                    try:
                        result = self.latin_reader.readtext(str(temp_path), detail=0)
                        if result:
                            page_text.extend(result)
                    except:
                        pass

                    # Try Arabic script reader (Urdu)
                    try:
                        result = self.arabic_reader.readtext(str(temp_path), detail=0)
                        if result:
                            page_text.extend(result)
                    except:
                        pass

                    # Try Devanagari script reader (Hindi)
                    try:
                        result = self.devanagari_reader.readtext(str(temp_path), detail=0)
                        if result:
                            page_text.extend(result)
                    except:
                        pass

                    # Remove duplicates for this page
                    unique_page_text = list(set(page_text))
                    all_text.extend(unique_page_text)

                    # Clean up temp file
                    temp_path.unlink()
                
                raw_text = "\n".join(all_text)
                
                return {
                    "raw_text": raw_text,
                    "source": file_path.name,
                    "success": True,
                    "error": None
                }
            except Exception as pdf_error:
                # Method 2: Fallback - Try PyPDF2 for text extraction
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        all_text = []
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                all_text.append(text)
                        
                        raw_text = "\n".join(all_text)
                        
                        if raw_text.strip():
                            return {
                                "raw_text": raw_text,
                                "source": file_path.name,
                                "success": True,
                                "error": None
                            }
                        else:
                            raise Exception("PDF has no extractable text")
                except Exception as pypdf_error:
                    # Method 3: Return error but don't crash
                    return {
                        "raw_text": f"PDF: {file_path.name}\n[PDF extraction failed, please try image format]",
                        "source": file_path.name,
                        "success": True,  # Mark as success to continue processing
                        "error": f"PDF processing failed. Please convert to image. Details: {str(pdf_error)}"
                    }
        except Exception as e:
            return {
                "raw_text": f"PDF: {file_path.name}",
                "source": file_path.name,
                "success": True,  # Don't crash the whole process
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