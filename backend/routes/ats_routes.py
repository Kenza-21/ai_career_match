"""
ATS CV Optimizer Routes
Routes for ATS-compliant CV optimization
"""
from datetime import datetime
from typing import Dict, Optional
import os
import tempfile
import base64

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from services.assistant import career_assistant
from services.resume_parser_api import resume_parser_api
from services.gemini_ats_evaluator import gemini_ats_evaluator
from utils.latex_utils import compile_latex_to_pdf
from utils.latex_generator import (
    generate_latex_from_json,
    format_cv_data_from_parser
)


router = APIRouter(prefix="/api", tags=["ats-optimizer"])


@router.post("/ats_cv")
async def ats_cv_optimizer(
    cv_file: Optional[UploadFile] = File(None, description="CV (PDF, DOCX, TXT)"),
    target_role: str = Form("", description="Rôle cible (optionnel)"),
    session_id: str = Form("", description="Session ID")
):
    """
    Fully automated ATS CV optimization pipeline:
    1. Parse CV using ResumeParser.app API
    2. Format data for LaTeX generation
    3. Generate LaTeX document
    4. Compile to PDF using MiKTeX
    5. Return PDF and LaTeX source
    
    All content is preserved without truncation.
    """
    if not cv_file:
        return {"success": False, "error": "Missing CV file."}

    try:
        # Step 1: Parse CV using ResumeParser.app API
        print(f"📄 Parsing CV: {cv_file.filename}")
        api_response = resume_parser_api.parse_cv_with_resumeparser(cv_file)
        
        if not api_response.get("success"):
            return {
                "success": False, 
                "error": api_response.get("error", "Failed to parse CV")
            }
        
        # Step 2: Extract and format parsed data
        parsed_data = api_response.get("data", {}).get("parsed", {})
        print(f"✅ CV parsed successfully: {parsed_data.get('name', 'Unknown')}")
        
        # Step 3: Format CV data for LaTeX generation (preserves ALL content)
        cv_data = format_cv_data_from_parser(parsed_data)
        print(f"📝 Formatted CV data: {len(cv_data.get('experience', []))} experiences, "
              f"{len(cv_data.get('education', []))} education entries")
        
        # Step 4: Generate LaTeX document using modular generator
        print("🔧 Generating LaTeX document...")
        ats_latex = generate_latex_from_json(cv_data)
        print("✅ LaTeX document generated")
        
        # Step 5: Compile LaTeX to PDF automatically
        print("📦 Compiling LaTeX to PDF...")
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = compile_latex_to_pdf(ats_latex, temp_dir)
            
            # Read PDF if compilation succeeded
            pdf_base64 = ""
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
                print(f"✅ PDF compiled successfully: {os.path.getsize(pdf_path)} bytes")
            else:
                print("⚠️ PDF compilation failed or file not found")
            
            response = {
                "success": True,
                "ats_cv_text": ats_latex,
                "ats_latex": ats_latex,
                "pdf_base64": pdf_base64,
                "pdf_available": pdf_base64 != "",
                "download_url": "",
                "metadata": {
                    "source": "resumeparser.app",
                    "format": "latex",
                    "template": "data/ats_resume.tex",
                    "generator": "latex_generator.py",
                    "timestamp": datetime.utcnow().isoformat(),
                    "content_preserved": True,
                    "experience_count": len(cv_data.get("experience", [])),
                    "education_count": len(cv_data.get("education", [])),
                    "skills_count": len(cv_data.get("skills", []))
                }
            }

            if session_id:
                career_assistant.update_session_results(session_id, response)

            return response
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error in ATS CV optimizer: {error_details}")
        return {
            "success": False, 
            "error": str(e),
            "error_details": error_details
        }


@router.post("/ats_evaluate")
async def ats_evaluate_resume(
    cv_file: Optional[UploadFile] = File(None, description="CV (PDF, DOCX, TXT)"),
    cv_text: str = Form("", description="Resume text (optional if file provided)"),
    session_id: str = Form("", description="Session ID")
):
    """
    Evaluate resume using Google Gemini ATS evaluator.
    
    Performs comprehensive ATS-style analysis across 14 categories:
    1. Contact Information
    2. Spelling & Grammar
    3. Personal Pronoun Usage
    4. Skills & Keyword Targeting
    5. Complex or Long Sentences
    6. Generic or Weak Phrases
    7. Passive Voice Usage
    8. Quantified Achievements
    9. Required Resume Sections
    10. AI-Generated Language Detection
    11. Repeated Action Verbs
    12. Visual Formatting / Readability
    13. Personal Information / Bias Triggers
    14. Other Strengths and Weaknesses
    
    Returns ATS_Score (0-100) and detailed feedback for each category.
    """
    try:
        resume_text = ""
        
        # Extract resume text from file or use provided text
        if cv_file:
            print(f"📄 Parsing CV for evaluation: {cv_file.filename}")
            api_response = resume_parser_api.parse_cv_with_resumeparser(cv_file)
            
            if not api_response.get("success"):
                return {
                    "success": False,
                    "error": api_response.get("error", "Failed to parse CV")
                }
            
            # Extract text from API response
            resume_text = resume_parser_api.get_cv_text_from_api_response(api_response)
            
        elif cv_text and cv_text.strip():
            resume_text = cv_text.strip()
        else:
            return {
                "success": False,
                "error": "Either CV file or resume text must be provided"
            }
        
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "success": False,
                "error": "Resume text is too short or empty"
            }
        
        # Evaluate resume using Gemini
        print("🔍 Evaluating resume with Google Gemini ATS evaluator...")
        evaluation_result = gemini_ats_evaluator.evaluate_resume(resume_text)
        
        if not evaluation_result.get("success"):
            return evaluation_result
        
        # Prepare response
        response = {
            "success": True,
            "ats_score": evaluation_result.get("ats_score", 0),
            "evaluation": evaluation_result.get("evaluation", {}),
            "metadata": {
                "source": "google_gemini",
                "model": "gemini-1.5-pro",
                "timestamp": datetime.utcnow().isoformat(),
                "resume_length": len(resume_text)
            }
        }
        
        # Persist in session if session_id provided
        if session_id:
            career_assistant.update_session_results(session_id, response)
        
        return response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error in ATS evaluation: {error_details}")
        return {
            "success": False,
            "error": str(e),
            "error_details": error_details
        }

