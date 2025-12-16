"""
Search Routes
Routes for job search with natural language queries and clarification flow
"""
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from services.builder.generator_standard import generate_structured_resume
from services.assistant import career_assistant
from services.llm_assistant import career_coach
from services.cv_analyzer import cv_analyzer
from services.resume_parser_api import resume_parser_api
from routes.job_routes import job_matcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SearchRequest(BaseModel):
    query: str
    session_id: str


class ClarifyRequest(BaseModel):
    session_id: str
    answer: str


router = APIRouter(prefix="/api", tags=["assistant-v2"])


# Dans la fonction _llm_chat_message de search_routes.py
def _llm_chat_message(user_query: str) -> Optional[str]:
    """Génère un message conversationnel via Gemini."""
    try:
        analysis = career_coach.coach_thinking(user_query)
        if isinstance(analysis, dict) and analysis.get("response"):
            return analysis["response"]
        if isinstance(analysis, str):
            return analysis
    except Exception as e:
        print(f"⚠️ Erreur Gemini dans search_routes: {e}")
        return None
    return None


def _run_search_flow(user_query: str, session_id: str) -> Dict:
    """Exécute le pipeline de recherche et formate la réponse contractuelle"""
    search_queries = career_assistant.generate_search_queries(user_query)
    job_results = career_assistant.build_job_results(job_matcher, search_queries, top_k=5)
    assistant_response = career_assistant.generate_response(user_query, job_results)

    # Si le titre existe dans le dataset, enrichir avec un message LLM conversationnel
    llm_message = None
    if job_matcher and (job_matcher.has_job_title(user_query) or job_matcher.semantic_match_title(user_query)):
        llm_message = _llm_chat_message(user_query)

    payload = {
        "clarify": False,
        "search_queries": search_queries,
        "results": assistant_response,
        "metadata": {
            "source": "assistant_v2",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    if llm_message:
        payload["assistant_message"] = llm_message

    career_assistant.update_session_results(session_id, payload)
    return payload


@router.post("/search")
async def search(request: SearchRequest):
    """Search for jobs using natural language query"""
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")

    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if career_assistant.is_ambiguous(user_query):
        question = career_assistant.build_clarification_question(user_query)
        career_assistant.save_session(request.session_id, user_query, question)
        return {"clarify": True, "question": question}

    career_assistant.save_session(request.session_id, user_query, "")
    return _run_search_flow(user_query, request.session_id)


@router.post("/clarify")
async def clarify(request: ClarifyRequest):
    """Clarify ambiguous search query"""
    session = career_assistant.get_session(request.session_id)
    # Si aucune session trouvée, traiter la réponse comme une nouvelle requête
    if not session:
        career_assistant.save_session(request.session_id, request.answer, "")
        return _run_search_flow(request.answer, request.session_id)

    refined_query = f"{session['original_query']} {request.answer}".strip()

    # Si correspondance directe ou sémantique dans le dataset, on répond directement
    if job_matcher.has_job_title(refined_query) or job_matcher.semantic_match_title(refined_query):
        return _run_search_flow(refined_query, request.session_id)

    # Sinon, demander une clarification supplémentaire (variée)
    question = career_assistant.build_clarification_question(refined_query)
    career_assistant.save_session(request.session_id, session['original_query'], question)
    return {"clarify": True, "question": question}


@router.get("/results")
async def last_results(session_id: str):
    """Get last search results for a session"""
    session = career_assistant.get_session(session_id)
    if not session or not session.get("last_results"):
        raise HTTPException(status_code=404, detail="No results stored for this session")
    return session["last_results"]

@router.post("/generate-resume")
async def generate_resume(resume_data: dict):
    """API endpoint to generate resume"""
    try:
        doc_bytes = generate_structured_resume(resume_data)
        return StreamingResponse(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=resume.docx"}
        )
    except Exception as e:
        return {"success": False, "error": str(e)}  # 
        
# --- CV Analyzer Endpoint ---
@router.post("/cv_analyser")
async def cv_analyser(
    cv_file: Optional[UploadFile] = File(None, description="CV (PDF, DOCX, TXT)"),
    cv_text: str = Form("", description="Texte du CV (optionnel si fichier)"),
    job_description: str = Form("", description="Description de l'offre"),
    session_id: str = Form("", description="Session ID")
):
    """Analyse CV vs JD et retourne un score de matching normalisé."""
    try:
        if (not cv_file and not cv_text.strip()) or not job_description.strip():
            return {"success": False, "error": "Missing CV or Job Description"}

        # Extraction texte CV via ResumeParser.app API
        if cv_file:
            api_response = resume_parser_api.parse_cv_with_resumeparser(cv_file)
            if not api_response.get("success"):
                return {"success": False, "error": api_response.get("error", "Erreur parsing CV")}
            cv_text_clean = resume_parser_api.get_cv_text_from_api_response(api_response)
            # Use API-provided skills if available
            api_skills = api_response.get("skills", [])
        else:
            cv_text_clean = cv_text.strip()
            api_skills = []

        jd_clean = job_description.strip()

        # Embeddings via TF-IDF (légère) et similarité cosinus
        vectorizer = TfidfVectorizer(max_features=1500, ngram_range=(1, 2), stop_words="english")
        vectors = vectorizer.fit_transform([cv_text_clean, jd_clean])
        semantic_similarity = float(cosine_similarity(vectors[0:1], vectors[1:2])[0][0])

        # Skills - Use API-provided skills if available, otherwise extract from text
        if api_skills:
            cv_skills = api_skills
        else:
            cv_skills = cv_analyzer.extract_skills_from_text(cv_text_clean)
        job_skills = cv_analyzer.extract_skills_from_job_description(jd_clean)
        
        # Use intelligent matching instead of simple set intersection
        matched_skills = []
        matched_cv_skills = set()
        
        for job_skill in job_skills:
            for cv_skill in cv_skills:
                if cv_skill in matched_cv_skills:
                    continue
                # Use intelligent matching (normalization + synonym mapping + semantic)
                norm_job = cv_analyzer.synonym_mapper.normalize_skill(job_skill)
                norm_cv = cv_analyzer.synonym_mapper.normalize_skill(cv_skill)
                
                # Check if they match (exact, synonym, or semantic)
                if norm_cv == norm_job or cv_analyzer.skill_matcher.match_skills(cv_skill, job_skill, semantic_threshold=0.7):
                    matched_skills.append(job_skill)
                    matched_cv_skills.add(cv_skill)
                    break
        
        missing_skills = [s for s in job_skills if s not in matched_skills]
        skills_match = len(matched_skills) / len(job_skills) if job_skills else 0.0
        coverage_percentage = round(skills_match * 100, 1)

        # Experience alignment (heuristique simple)
        exp_markers = ["senior", "junior", "lead", "manager", "intern", "alternance", "stage", "experience", "expérience", "years"]

        def exp_score(text: str) -> float:
            t = text.lower()
            hits = sum(1 for m in exp_markers if m in t)
            return min(1.0, hits / 5.0)

        experience_alignment = (exp_score(cv_text_clean) + exp_score(jd_clean)) / 2.0

        # Score final pondéré
        final_score = 0.6 * semantic_similarity + 0.2 * skills_match + 0.2 * experience_alignment
        final_score_pct = round(final_score * 100, 2)

        response = {
            "success": True,
            "score": final_score_pct,
            "cv_keywords": cv_skills[:30],
            "job_keywords": job_skills[:30],
            "matched_skills": matched_skills[:30],
            "missing_skills": missing_skills[:30],
            "coverage": f"{coverage_percentage}%",
            "coverage_percentage": coverage_percentage,
            "metadata": {
                "source": "cv_analyser_v1",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Persister dans la session
        if session_id:
            career_assistant.update_session_results(session_id, response)

        return response

    except Exception as e:
        return {"success": False, "error": str(e)}
