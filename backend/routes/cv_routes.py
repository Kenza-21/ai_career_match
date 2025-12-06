from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from services.cv_analyzer import cv_analyzer
from utils.cv_parser import CVParser
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
    """Analyse CV avec upload de fichier"""
    try:
        print(f"📄 Upload de CV: {cv_file.filename}")
        
        # Vérifier le type de fichier
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_extension = cv_file.filename.lower().split('.')[-1]
        
        if file_extension not in ['pdf', 'docx', 'txt']:
            raise HTTPException(
                status_code=400, 
                detail=f"Format non supporté. Utilisez: {', '.join(allowed_extensions)}"
            )
        
        # Extraction du texte
        cv_text = CVParser.extract_text_from_cv(cv_file)
        
        if len(cv_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="CV trop court ou impossible à extraire")
        
        print(f"✅ Texte extrait ({len(cv_text)} caractères)")
        
        # Extraction des sections
        cv_sections = CVParser.parse_cv_sections(cv_text)
        print(f"✅ Sections identifiées: {list(cv_sections.keys())}")
        
        # Analyse
        analysis_result = cv_analyzer.analyze_cv_vs_job(cv_text, job_description)
        analysis_result["cv_sections"] = cv_sections
        analysis_result["filename"] = cv_file.filename
        
        print(f"✅ Analyse terminée - Score: {analysis_result['match_score']}")
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur dans l'analyse upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")    