from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from services.cv_analyzer import cv_analyzer
from services.resume_parser_api import resume_parser_api
router = APIRouter(prefix="/cv", tags=["cv-analysis"])

@router.post("/analyze")
async def analyze_cv_job_match(
    cv_text: str = Form(..., description="Texte du CV"),
    job_description: str = Form(..., description="Description de l'offre d'emploi")
):
    """Analyse la correspondance entre un CV et une offre d'emploi"""
    try:
        print("🎯 Requête d'analyse CV reçue")
        
        if len(cv_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="CV trop court")
        
        if len(job_description.strip()) < 10:
            raise HTTPException(status_code=400, detail="Description d'offre trop courte")
        
        # Analyse complète
        analysis_result = cv_analyzer.analyze_cv_vs_job(cv_text, job_description)
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Erreur dans l'analyse CV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")

@router.get("/test")
async def test_cv_module():
    """Test simple du module CV"""
    return {
        "status": "success",
        "message": "Module CV opérationnel",
        "endpoints": {
            "analyze": "POST /cv/analyze",
            "demo": "GET /cv/demo"
        }
    }

@router.get("/demo")
async def cv_demo_analysis():
    """Démonstration avec des données d'exemple"""
    
    cv_example = """
    DÉVELOPPEUR WEB
    Jean Dupont
    Email: jean.dupont@email.com | Tél: +212 6 12 34 56 78
    
    EXPÉRIENCE
    Développeur Frontend - TechMaroc (2022-2023)
    - Développement d'interfaces avec HTML, CSS, JavaScript
    - Collaboration avec les designers
    - Résolution de bugs
    
    FORMATION
    Licence Informatique - Université Hassan II (2021)
    - Programmation Java, Bases de données SQL
    
    COMPÉTENCES
    - HTML, CSS, JavaScript
    - Java, MySQL, Git
    """
    
    job_example = """
    Développeur Full Stack
    Compétences requises:
    - JavaScript, React, Node.js
    - Bases de données MongoDB
    - APIs RESTful
    - Git et méthodologies Agile
    - Python (un plus)
    
    Missions:
    - Développement d'applications web complètes
    - Collaboration équipe frontend/backend
    """
    
    analysis = cv_analyzer.analyze_cv_vs_job(cv_example, job_example)
    
    return {
        "demo": True,
        "cv_example_preview": cv_example[:100] + "...",
        "job_example_preview": job_example[:100] + "...", 
        "analysis": analysis
    }

@router.get("/skills")
async def get_available_skills():
    """Retourne la liste des compétences reconnues"""
    return {
        "technical_skills": cv_analyzer.technical_skills,
        "total_skills": len(cv_analyzer.technical_skills)
    }
@router.post("/analyze-upload")
async def analyze_cv_upload(
    cv_file: UploadFile = File(..., description="CV (PDF, DOCX, TXT)"),
    job_description: str = Form(..., description="Description de l'offre d'emploi")
):
    """Analyse CV avec extraction via ResumeParser.app API"""
    try:
        print(f"📄 Analyse CV: {cv_file.filename}")
        
        # Parse CV using ResumeParser.app API
        api_response = resume_parser_api.parse_cv_with_resumeparser(cv_file)
        
        if not api_response.get("success"):
            raise HTTPException(status_code=400, detail=api_response.get("error", "Erreur parsing CV"))
        
        # Extract text from API response
        cv_text = resume_parser_api.get_cv_text_from_api_response(api_response)
        
        if len(cv_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="CV trop court ou illisible")
        
        # Use API-provided sections if available, otherwise extract from text
        cv_sections = {
            "experience": "\n".join([str(exp) for exp in api_response.get("experience", [])]),
            "education": "\n".join([str(edu) for edu in api_response.get("education", [])]),
            "skills": ", ".join(api_response.get("skills", [])),
            "summary": api_response.get("summary", ""),
            "contact": str(api_response.get("contact", {})),
            "projects": "",
            "languages": "",
            "certifications": ""
        }
        
        # Analyse CV vs Job Description
        analysis_result = cv_analyzer.analyze_cv_vs_job(cv_text, job_description)
        
        # Add API-provided sections to result
        analysis_result["cv_sections"] = {k: v[:300] + "..." if len(v) > 300 else v 
                                          for k, v in cv_sections.items()}
        analysis_result["filename"] = cv_file.filename
        analysis_result["api_skills"] = api_response.get("skills", [])
        analysis_result["api_experience"] = api_response.get("experience", [])
        
        print(f"✅ Analyse terminée - Score: {analysis_result['match_score']}")
        print(f"   Compétences CV: {analysis_result['summary']['cv_skills_count']}")
        print(f"   Compétences Offre: {analysis_result['summary']['job_skills_count']}")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Erreur analyse CV: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")