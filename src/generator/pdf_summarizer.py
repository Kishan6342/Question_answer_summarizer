from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.llm.groq_client import get_groq_llm
from src.common.logger import get_logger
from src.common.custom_exception import CustomException

class PDFSummary(BaseModel):
    title: str = Field(description="The main title or topic of the document")
    key_points: list[str] = Field(description="List of 5-8 key points from the document")
    summary: str = Field(description="A comprehensive summary of the document (200-300 words)")
    topics: list[str] = Field(description="List of main topics covered in the document")

class PDFSummarizer:
    def __init__(self):
        self.llm = get_groq_llm()
        self.logger = get_logger(self.__class__.__name__)
    
    def summarize_pdf_content(self, pdf_text: str) -> PDFSummary:
        """Generate a comprehensive summary of the PDF content"""
        try:
            parser = PydanticOutputParser(pydantic_object=PDFSummary)
            
            prompt = f"""
            Please analyze the following document content and provide a comprehensive summary:

            Document Content:
            {pdf_text[:8000]}  # Limit content to avoid token limits

            Instructions:
            1. Extract the main title or topic of the document
            2. Identify 5-8 key points that capture the essence of the document
            3. Write a comprehensive summary (200-300 words)
            4. List the main topics covered

            {parser.get_format_instructions()}
            """
            
            self.logger.info("Generating PDF summary...")
            response = self.llm.invoke(prompt)
            summary = parser.parse(response.content)
            
            self.logger.info("Successfully generated PDF summary")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to summarize PDF: {str(e)}")
            raise CustomException("PDF summarization failed", e)
