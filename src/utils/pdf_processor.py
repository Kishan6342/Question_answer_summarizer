import PyPDF2
from typing import Optional
from src.common.logger import get_logger
from src.common.custom_exception import CustomException

class PDFProcessor:
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text content from uploaded PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            
            # Extract text from all pages
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n"
                    text_content += page_text
                except Exception as e:
                    self.logger.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            if not text_content.strip():
                raise ValueError("No text content found in PDF")
            
            self.logger.info(f"Successfully extracted text from PDF ({len(text_content)} characters)")
            return text_content.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to process PDF: {str(e)}")
            raise CustomException("PDF processing failed", e)
    
    def validate_pdf(self, pdf_file) -> bool:
        """Validate if the uploaded file is a valid PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            
            if num_pages == 0:
                raise ValueError("PDF has no pages")
            
            if num_pages > 15:  # Limit for performance
                raise ValueError(f"PDF has too many pages ({num_pages}). Maximum allowed: 15")
            
            self.logger.info(f"PDF validation successful: {num_pages} pages")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF validation failed: {str(e)}")
            raise CustomException("PDF validation failed", e)
