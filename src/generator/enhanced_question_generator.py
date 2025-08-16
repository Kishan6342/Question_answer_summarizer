from langchain.output_parsers import PydanticOutputParser
from src.models.question_schemas import MCQQuestion, FillBlankQuestion
from src.llm.groq_client import get_groq_llm
from src.config.settings import settings
from src.common.logger import get_logger
from src.common.custom_exception import CustomException
import json
import re

class EnhancedQuestionGenerator:
    def __init__(self):
        self.llm = get_groq_llm()
        self.logger = get_logger(self.__class__.__name__)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from response text that might contain extra content"""
        try:
            # Find JSON content between first { and last }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON structure found in response")
            
            json_str = response_text[start_idx:end_idx]
            
            # Validate it's proper JSON
            json.loads(json_str)
            
            return json_str
        except Exception as e:
            self.logger.error(f"Failed to extract JSON: {str(e)}")
            raise ValueError(f"Invalid JSON structure: {str(e)}")
    
    def _create_mcq_prompt(self, content: str, difficulty: str) -> str:
        """Create MCQ prompt based on PDF content"""
        return f"""
Based on the following document content, generate a {difficulty} level multiple-choice question.

Content:
{content[:6000]}

Requirements:
- Create exactly 4 options (A, B, C, D)
- Only one option should be correct
- Question should test understanding of the content
- Difficulty level: {difficulty}

IMPORTANT: Respond with ONLY valid JSON in this exact format. Do not add any explanations or additional text:

{{
    "question": "Your question here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "The correct option"
}}
"""
    
    def _create_fillblank_prompt(self, content: str, difficulty: str) -> str:
        """Create fill-in-the-blank prompt based on PDF content"""
        return f"""
Based on the following document content, generate a {difficulty} level fill-in-the-blank question.

Content:
{content[:6000]}

Requirements:
- Use '___' to indicate the blank
- Question should test knowledge from the content
- Difficulty level: {difficulty}

IMPORTANT: Respond with ONLY valid JSON in this exact format. Do not add any explanations or additional text:

{{
    "question": "Your question with ___ blank",
    "answer": "The correct answer for the blank"
}}
"""
    
    def _retry_and_parse(self, prompt: str, parser, max_retries: int = 3):
        """Retry question generation with improved error handling"""
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(prompt)
                
                # Extract JSON from response
                json_content = self._extract_json_from_response(response.content)
                
                # Parse using the extracted JSON
                parsed = parser.parse(json_content)
                return parsed
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise CustomException(f"Generation failed after {max_retries} attempts", e)
    
    def generate_mcq_from_content(self, content: str, difficulty: str = 'medium') -> MCQQuestion:
        """Generate MCQ question based on PDF content"""
        try:
            parser = PydanticOutputParser(pydantic_object=MCQQuestion)
            prompt = self._create_mcq_prompt(content, difficulty)
            
            question = self._retry_and_parse(prompt, parser)
            
            # Validate MCQ structure
            if len(question.options) != 4:
                raise ValueError(f"Expected 4 options, got {len(question.options)}")
            
            if question.correct_answer not in question.options:
                raise ValueError("Correct answer not found in options")
            
            self.logger.info(f"Generated {difficulty} MCQ question from content")
            return question
            
        except Exception as e:
            self.logger.error(f"Failed to generate MCQ from content: {str(e)}")
            raise CustomException("MCQ generation from content failed", e)
    
    def generate_fillblank_from_content(self, content: str, difficulty: str = 'medium') -> FillBlankQuestion:
        """Generate fill-in-the-blank question based on PDF content"""
        try:
            parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)
            prompt = self._create_fillblank_prompt(content, difficulty)
            
            question = self._retry_and_parse(prompt, parser)
            
            # Validate fill-in-the-blank structure
            if "___" not in question.question:
                raise ValueError("Fill-in-the-blank should contain '___'")
            
            self.logger.info(f"Generated {difficulty} fill-in-the-blank question from content")
            return question
            
        except Exception as e:
            self.logger.error(f"Failed to generate fill-in-the-blank from content: {str(e)}")
            raise CustomException("Fill-in-the-blank generation from content failed", e)
