import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import List, Optional, Tuple
from src.models.question_schemas import MCQQuestion, FillBlankQuestion
from src.common.logger import get_logger

class SimpleRetriever:
    """Simple text-based retriever for RAG functionality"""
    
    def __init__(self, chunks: List[str]):
        self.chunks = chunks
        self.logger = get_logger(self.__class__.__name__)
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[int, str, float]]:
        """Retrieve top-k most relevant chunks for a query"""
        query_words = set(query.lower().split())
        scores = []
        
        for i, chunk in enumerate(self.chunks):
            chunk_words = set(chunk.lower().split())
            # Simple similarity: intersection over union + keyword matching
            intersection = query_words.intersection(chunk_words)
            union = query_words.union(chunk_words)
            
            # Calculate similarity score
            jaccard_score = len(intersection) / len(union) if union else 0
            keyword_bonus = sum(1 for word in query_words if word in chunk.lower()) / len(query_words)
            
            final_score = jaccard_score + (keyword_bonus * 0.5)
            scores.append((final_score, i, chunk))
        
        # Sort by score and return top-k
        scores.sort(reverse=True, key=lambda x: x[0])
        top_chunks = [(idx, chunk, score) for score, idx, chunk in scores[:top_k] if score > 0]
        
        self.logger.info(f"Retrieved {len(top_chunks)} relevant chunks for query")
        return top_chunks

class QuizManager:
    def __init__(self):
        self.questions: List = []
        self.user_answers: List = []
        self.question_type: str = ""
        self.pdf_content: str = ""
        self.pdf_summary = None
        self.logger = get_logger(self.__class__.__name__)
        self.retriever: Optional[SimpleRetriever] = None
        self.content_chunks: List[str] = []

    def set_pdf_content(self, content: str, summary=None):
        """Store PDF content and summary"""
        self.pdf_content = content
        self.pdf_summary = summary
        self.logger.info("PDF content stored in quiz manager")

    def build_retriever(self, num_chunks: int = 10):
        """Build retriever from PDF content for RAG functionality"""
        if not self.pdf_content:
            self.logger.warning("No PDF content available for building retriever")
            return False
            
        try:
            # Create content chunks for retrieval
            self.content_chunks = self._split_content_for_retrieval(self.pdf_content, num_chunks)
            self.retriever = SimpleRetriever(self.content_chunks)
            self.logger.info(f"Retriever built with {len(self.content_chunks)} chunks")
            return True
        except Exception as e:
            self.logger.error(f"Failed to build retriever: {str(e)}")
            return False

    def _split_content_for_retrieval(self, content: str, num_chunks: int) -> List[str]:
        """Split content into overlapping chunks for better retrieval"""
        sentences = content.replace('\n', ' ').split('. ')
        if len(sentences) <= num_chunks:
            return sentences
        
        chunk_size = max(len(sentences) // num_chunks, 3)
        overlap = max(chunk_size // 3, 1)  # 30% overlap
        
        chunks = []
        for i in range(0, len(sentences), chunk_size - overlap):
            chunk_sentences = sentences[i:i + chunk_size]
            chunk = '. '.join(chunk_sentences)
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks

    def get_rag_response(self, query: str, llm) -> Tuple[str, List[Tuple[int, str, float]]]:
        """Generate RAG-based response for user query"""
        if not self.retriever:
            return "Please process a PDF first to enable chat functionality.", []
        
        try:
            # Retrieve relevant chunks
            retrieved_chunks = self.retriever.retrieve(query, top_k=3)
            
            if not retrieved_chunks:
                return "I couldn't find relevant information in the document to answer your question.", []
            
            # Construct grounded prompt
            context = "\n\n".join([f"Context {i+1}: {chunk}" for i, (_, chunk, _) in enumerate(retrieved_chunks)])
            
            prompt = f"""Based on the following context from the document, please answer the user's question. If the answer is not clearly supported by the context, say so.

Context:
{context}

Question: {query}

Answer: Provide a clear, accurate answer based on the context above. If you reference specific information, mention which context section it comes from."""

            # Get LLM response
            response = llm.invoke(prompt)
            
            return response.content, retrieved_chunks
            
        except Exception as e:
            self.logger.error(f"Failed to generate RAG response: {str(e)}")
            return f"Error generating response: {str(e)}", []

    def generate_questions_from_pdf(self, generator, question_type: str, difficulty: str, num_questions: int) -> bool:
        """Generate questions based on PDF content"""
        try:
            if not self.pdf_content:
                raise ValueError("No PDF content available for question generation")

            self.questions = []
            self.question_type = question_type

            # Split content into chunks for variety
            content_chunks = self._split_content(self.pdf_content, num_questions)

            for i in range(num_questions):
                chunk = content_chunks[i % len(content_chunks)]
                if question_type == "Multiple Choice":
                    question = generator.generate_mcq_from_content(chunk, difficulty.lower())
                elif question_type == "Fill in the Blank":
                    question = generator.generate_fillblank_from_content(chunk, difficulty.lower())
                else:
                    raise ValueError(f"Unsupported question type: {question_type}")

                self.questions.append(question)
                self.logger.info(f"Generated question {i+1}/{num_questions}")

            self.user_answers = [None] * len(self.questions)
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate questions from PDF: {str(e)}")
            st.error(f"Error generating questions: {str(e)}")
            return False

    def _split_content(self, content: str, num_parts: int) -> List[str]:
        """Split content into chunks for question generation"""
        words = content.split()
        chunk_size = max(len(words) // num_parts, 100) # Minimum 100 words per chunk
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        return chunks if chunks else [content]

    def attempt_quiz(self):
        """Display quiz interface for answering questions"""
        if not self.questions:
            st.warning("No questions available. Please generate questions first.")
            return

        for i, question in enumerate(self.questions):
            st.subheader(f"Question {i+1}")

            if self.question_type == "Multiple Choice":
                st.write(question.question)
                selected_option = st.radio(
                    "Choose your answer:",
                    question.options,
                    key=f"q_{i}",
                    index=None
                )
                self.user_answers[i] = selected_option

            elif self.question_type == "Fill in the Blank":
                st.write(question.question)
                user_input = st.text_input(
                    "Your answer:",
                    key=f"q_{i}",
                    placeholder="Enter your answer here"
                )
                self.user_answers[i] = user_input.strip() if user_input else None

            st.markdown("---")

    def evaluate_quiz(self):
        """Evaluate user answers and calculate results"""
        if not self.questions or not self.user_answers:
            st.error("No quiz data available for evaluation.")
            return

        self.results = []

        for i, (question, user_answer) in enumerate(zip(self.questions, self.user_answers)):
            if self.question_type == "Multiple Choice":
                is_correct = user_answer == question.correct_answer
                correct_answer = question.correct_answer
            elif self.question_type == "Fill in the Blank":
                is_correct = user_answer and user_answer.lower().strip() == question.answer.lower().strip()
                correct_answer = question.answer
            else:
                is_correct = False
                correct_answer = "Unknown"

            self.results.append({
                'question_number': i + 1,
                'question': question.question,
                'user_answer': user_answer or "No answer",
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })

    def generate_result_dataframe(self) -> pd.DataFrame:
        """Generate pandas DataFrame with quiz results"""
        if hasattr(self, 'results') and self.results:
            return pd.DataFrame(self.results)
        return pd.DataFrame()

    def save_to_csv(self) -> Optional[str]:
        """Save quiz results to CSV file"""
        try:
            if not hasattr(self, 'results') or not self.results:
                return None

            df = self.generate_result_dataframe()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quiz_results_{timestamp}.csv"

            # Add summary information
            summary_data = {
                'total_questions': len(self.results),
                'correct_answers': sum(1 for r in self.results if r['is_correct']),
                'score_percentage': round((sum(1 for r in self.results if r['is_correct']) / len(self.results)) * 100, 2),
                'question_type': self.question_type,
                'timestamp': datetime.now().isoformat()
            }

            # Save both detailed results and summary
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                f.write("# Quiz Summary\n")
                for key, value in summary_data.items():
                    f.write(f"# {key}: {value}\n")
                f.write("\n")

                df.to_csv(filename, mode='a', index=False)

            return filename

        except Exception as e:
            self.logger.error(f"Failed to save results to CSV: {str(e)}")
            st.error(f"Error saving results: {str(e)}")
            return None

def rerun():
    """Trigger Streamlit rerun"""
    st.rerun()
