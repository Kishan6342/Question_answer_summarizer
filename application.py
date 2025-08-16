import os
import streamlit as st
from dotenv import load_dotenv

from src.utils.helpers import QuizManager, rerun
from src.generator.enhanced_question_generator import EnhancedQuestionGenerator
from src.utils.pdf_processor import PDFProcessor
from src.generator.pdf_summarizer import PDFSummarizer

load_dotenv()

def main():
    st.set_page_config(
        page_title="PDF Study Buddy AI", 
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize session state
    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = QuizManager()
    
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    
    if 'pdf_processed' not in st.session_state:
        st.session_state.pdf_processed = False
    
    if 'pdf_summarized' not in st.session_state:
        st.session_state.pdf_summarized = False
    
    # Main title
    st.title("📚 PDF Study Buddy AI")
    st.markdown("Upload a PDF, get a summary, and generate custom quiz questions!")
    
    # Sidebar for PDF upload and settings
    st.sidebar.header("📄 PDF Upload")
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document (max 15 pages)"
    )
    
    if uploaded_file is not None:
        # Process PDF
        if st.sidebar.button("📊 Process PDF"):
            with st.spinner("Processing PDF..."):
                try:
                    processor = PDFProcessor()
                    
                    # Validate and extract text
                    processor.validate_pdf(uploaded_file)
                    pdf_text = processor.extract_text_from_pdf(uploaded_file)
                    
                    # Generate summary
                    summarizer = PDFSummarizer()
                    summary = summarizer.summarize_pdf_content(pdf_text)
                    
                    # Store in session state
                    st.session_state.quiz_manager.set_pdf_content(pdf_text, summary)
                    st.session_state.pdf_processed = True
                    st.session_state.pdf_summarized = True
                    
                    st.sidebar.success("✅ PDF processed successfully!")
                    rerun()
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Error processing PDF: {str(e)}")
    
    # Display PDF summary if available
    if st.session_state.pdf_summarized and st.session_state.quiz_manager.pdf_summary:
        st.header("📋 Document Summary")
        summary = st.session_state.quiz_manager.pdf_summary
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"📖 {summary.title}")
            st.write(summary.summary)
            
            with st.expander("🔍 Key Points"):
                for i, point in enumerate(summary.key_points, 1):
                    st.write(f"{i}. {point}")
        
        with col2:
            st.subheader("🏷️ Topics Covered")
            for topic in summary.topics:
                st.write(f"• {topic}")
        
        st.markdown("---")
    
    # Quiz generation settings
    if st.session_state.pdf_processed:
        st.sidebar.header("🎯 Quiz Settings")
        
        question_type = st.sidebar.selectbox(
            "Select Question Type",
            ["Multiple Choice", "Fill in the Blank"],
            index=0
        )
        
        difficulty = st.sidebar.selectbox(
            "Difficulty Level",
            ["Easy", "Medium", "Hard"],
            index=1
        )
        
        num_questions = st.sidebar.number_input(
            "Number of Questions",
            min_value=1, 
            max_value=10, 
            value=5
        )
        
        if st.sidebar.button("🎯 Generate Quiz"):
            st.session_state.quiz_submitted = False
            
            with st.spinner("Generating quiz questions..."):
                try:
                    generator = EnhancedQuestionGenerator()
                    success = st.session_state.quiz_manager.generate_questions_from_pdf(
                        generator, question_type, difficulty, num_questions
                    )
                    
                    st.session_state.quiz_generated = success
                    
                    if success:
                        st.sidebar.success("✅ Quiz generated successfully!")
                    
                    rerun()
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Error generating quiz: {str(e)}")
    
    # Display quiz
    if st.session_state.quiz_generated and st.session_state.quiz_manager.questions:
        st.header("🎯 Quiz Time!")
        st.write(f"Answer all {len(st.session_state.quiz_manager.questions)} questions and submit when ready.")
        
        st.session_state.quiz_manager.attempt_quiz()
        
        if st.button("✅ Submit Quiz", type="primary"):
            # Check if all questions are answered
            unanswered = [i+1 for i, ans in enumerate(st.session_state.quiz_manager.user_answers) if ans is None or ans == ""]
            
            if unanswered:
                st.warning(f"⚠️ Please answer question(s): {', '.join(map(str, unanswered))}")
            else:
                st.session_state.quiz_manager.evaluate_quiz()
                st.session_state.quiz_submitted = True
                rerun()
    
    # Display results
    if st.session_state.quiz_submitted:
        st.header("📊 Quiz Results")
        
        results_df = st.session_state.quiz_manager.generate_result_dataframe()
        
        if not results_df.empty:
            # Score overview
            correct_count = results_df["is_correct"].sum()
            total_questions = len(results_df)
            score_percentage = (correct_count / total_questions) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{score_percentage:.1f}%")
            with col2:
                st.metric("Correct", f"{correct_count}/{total_questions}")
            with col3:
                if score_percentage >= 80:
                    st.success("🎉 Excellent!")
                elif score_percentage >= 60:
                    st.info("👍 Good job!")
                else:
                    st.warning("📚 Keep studying!")
            
            st.markdown("---")
            
            # Detailed results
            for _, result in results_df.iterrows():
                question_num = result['question_number']
                
                if result['is_correct']:
                    st.success(f"✅ **Question {question_num}**: {result['question']}")
                else:
                    st.error(f"❌ **Question {question_num}**: {result['question']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Your answer:** {result['user_answer']}")
                    with col2:
                        st.write(f"**Correct answer:** {result['correct_answer']}")
                
                st.markdown("---")
            
            # Save results
            if st.button("💾 Save Results"):
                saved_file = st.session_state.quiz_manager.save_to_csv()
                if saved_file:
                    with open(saved_file, 'rb') as f:
                        st.download_button(
                            label="📥 Download Results",
                            data=f.read(),
                            file_name=os.path.basename(saved_file),
                            mime='text/csv'
                        )
                else:
                    st.warning("⚠️ No results available to save")
    
    # Instructions
    if not st.session_state.pdf_processed:
        st.info("""
        📝 **How to use:**
        1. Upload a PDF document using the sidebar
        2. Click "Process PDF" to extract and summarize content
        3. Configure quiz settings (question type, difficulty, number of questions)
        4. Generate and complete your custom quiz!
        """)

if __name__ == "__main__":
    main()
