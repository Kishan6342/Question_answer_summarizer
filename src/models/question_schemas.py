from pydantic import BaseModel, Field
from typing import List

class MCQQuestion(BaseModel):
    question: str = Field(description="The multiple choice question")
    options: List[str] = Field(description="List of 4 answer options")
    correct_answer: str = Field(description="The correct answer from the options")

class FillBlankQuestion(BaseModel):
    question: str = Field(description="The fill in the blank question with ___ for blank")
    answer: str = Field(description="The correct answer for the blank")
