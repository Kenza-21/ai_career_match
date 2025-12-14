from datetime import datetime
from typing import Dict, Optional
import os
import subprocess
import tempfile
import base64

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.assistant import career_assistant
from services.llm_assistant import career_assistant as llm_assistant
from services.cv_analyzer import cv_analyzer
from services.resume_parser_api import resume_parser_api
from routes.job_routes import job_matcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters"""
    if not text:
        return ""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '|': r'\|',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def _load_template() -> str:
    """Load the base LaTeX template from data/ats_resume.tex"""
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ats_resume.tex")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Template not found at {template_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading template: {str(e)}")


def _map_parsed_to_template(parsed_data: Dict) -> Dict:
    """Map ResumeParser.app JSON structure to template variables"""
    contact = parsed_data.get("contact", {})
    
    # Build location string
    location_parts = []
    if contact.get("location_city"):
        location_parts.append(contact["location_city"])
    if contact.get("location_state"):
        location_parts.append(contact["location_state"])
    if contact.get("location_country"):
        location_parts.append(contact["location_country"])
    location = ", ".join(location_parts) if location_parts else ""
    
    # Map experience
    experience_list = []
    for job in parsed_data.get("employment_history", []):
        exp_item = {
            "position": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "start_date": job.get("start_date", ""),
            "end_date": job.get("end_date", "Present"),
            "description": []
        }
        
        # Collect all responsibilities
        responsibilities = job.get("responsibilities", [])
        for resp in responsibilities:
            if isinstance(resp, str):
                exp_item["description"].append(resp)
            elif isinstance(resp, dict):
                # Handle nested roles
                if "responsibilities" in resp:
                    for r in resp.get("responsibilities", []):
                        if isinstance(r, str):
                            exp_item["description"].append(r)
        
        if exp_item["description"]:
            experience_list.append(exp_item)
    
    # Map education
    education_list = []
    for edu in parsed_data.get("education", []):
        edu_item = {
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution_name", ""),
            "details": ""
        }
        # Build details from available fields
        details_parts = []
        if edu.get("institution_country"):
            details_parts.append(edu["institution_country"])
        if edu.get("start_date") or edu.get("end_date"):
            edu_date = f"{edu.get('start_date', '')} - {edu.get('end_date', '')}".strip(" -")
            if edu_date:
                details_parts.append(edu_date)
        edu_item["details"] = " | ".join(details_parts)
        education_list.append(edu_item)
    
    return {
        "name": parsed_data.get("name", ""),
        "title": parsed_data.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": location,
        "summary": parsed_data.get("brief", ""),
        "skills": parsed_data.get("skills", []),
        "experience": experience_list,
        "education": education_list,
        "languages": parsed_data.get("languages", []),
        "certifications": parsed_data.get("courses", [])
    }


# Add these imports at the top if not present
import re
from typing import List
def _render_template(template: str, data: Dict) -> str:
    """Replace template placeholders with actual data for new template format"""
    result = template
    
    # Simple replacements
    result = result.replace("{{ name }}", _escape_latex(data.get("name", "")))
    result = result.replace("{{ location }}", _escape_latex(data.get("location", "")))
    result = result.replace("{{ email }}", _escape_latex(data.get("email", "")))
    result = result.replace("{{ phone }}", _escape_latex(data.get("phone", "")))
    result = result.replace("{{ summary }}", _escape_latex(data.get("summary", "")))
    
    # Education loop - handle empty case
    education_block = ""
    education_items = data.get("education", [])
    
    for edu in education_items[:2]:  # Max 2 education items for space
        degree = _escape_latex(edu.get('degree', ''))
        institution = _escape_latex(edu.get('institution', ''))
        details = _escape_latex(edu.get('details', ''))
        
        if degree or institution:
            education_block += f"\\cventry{{{degree}}}{{{institution}}}{{{details}}}\n"
            if edu != education_items[-1] and len(education_items) > 1:
                education_block += "\\vspace{2pt}\n"
    
    # Replace education loop block
    import re
    edu_pattern = r'\{%\s*for\s+edu\s+in\s+education\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    edu_match = re.search(edu_pattern, result, re.DOTALL)
    if edu_match:
        if education_block:
            result = result.replace(edu_match.group(0), education_block)
        else:
            result = result.replace(edu_match.group(0), "")
    
    # Experience loop
    experience_block = ""
    experience_items = data.get("experience", [])
    
    for exp in experience_items[:2]:  # Max 2 experiences for one page
        position = _escape_latex(exp.get('position', ''))
        company = _escape_latex(exp.get('company', ''))
        location = _escape_latex(exp.get('location', ''))
        start_date = _escape_latex(exp.get('start_date', ''))
        end_date = _escape_latex(exp.get('end_date', 'Present'))
        
        if position and company:
            experience_block += f"\\cventry{{{position}}}{{{start_date} - {end_date}}}{{{company}}}{{{location}}}\n"
            experience_block += "\\begin{itemize}\n"
            
            # Add bullet points (max 3 per experience)
            for item in exp.get("description", [])[:3]:
                if item:
                    escaped_item = _escape_latex(item)
                    if len(escaped_item) > 120:  # Truncate long items
                        escaped_item = escaped_item[:117] + "..."
                    experience_block += f"    \\item {escaped_item}\n"
            
            experience_block += "\\end{itemize}\n"
            if exp != experience_items[-1] and len(experience_items) > 1:
                experience_block += "\\vspace{3pt}\n"
    
    # Replace experience loop block
    exp_pattern = r'\{%\s*for\s+exp\s+in\s+experience\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    exp_match = re.search(exp_pattern, result, re.DOTALL)
    if exp_match:
        if experience_block:
            result = result.replace(exp_match.group(0), experience_block)
        else:
            result = result.replace(exp_match.group(0), "")
    
    # Skills - format as pipe-separated list
    skills = data.get("skills", [])
    if len(skills) > 15:  # Limit skills for space
        skills = skills[:15]
    
    skills_text = ""
    for i, skill in enumerate(skills):
        if skill:
            skills_text += _escape_latex(skill)
            if i < len(skills) - 1:
                skills_text += " | "
    
    # Replace skills block
    skills_pattern = r'\{%\s*for\s+skill\s+in\s+skills\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    skills_match = re.search(skills_pattern, result, re.DOTALL)
    if skills_match:
        if skills_text:
            # Find the {{ skill }} placeholder in the loop
            inner_text = skills_match.group(1)
            if "{{ skill }}" in inner_text:
                # Replace the entire loop with the formatted skills text
                result = result.replace(skills_match.group(0), f"\\noindent\n{skills_text}")
            else:
                # Direct replacement
                result = result.replace(skills_match.group(0), skills_text)
        else:
            result = result.replace(skills_match.group(0), "")
    
    # Languages - format as pipe-separated list
    languages = data.get("languages", [])
    if len(languages) > 3:  # Limit languages
        languages = languages[:3]
    
    languages_text = ""
    for i, lang in enumerate(languages):
        if lang:
            languages_text += _escape_latex(lang)
            if i < len(languages) - 1:
                languages_text += " | "
    
    # Replace languages block
    lang_pattern = r'\{%\s*for\s+lang\s+in\s+languages\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    lang_match = re.search(lang_pattern, result, re.DOTALL)
    if lang_match:
        if languages_text:
            inner_text = lang_match.group(1)
            if "{{ lang }}" in inner_text:
                result = result.replace(lang_match.group(0), f"\\noindent\n{languages_text}")
            else:
                result = result.replace(lang_match.group(0), languages_text)
        else:
            result = result.replace(lang_match.group(0), "")
    
    # Certifications loop
    cert_block = ""
    certifications = data.get("certifications", [])
    
    for cert in certifications[:3]:  # Max 3 certifications
        if cert:
            escaped_cert = _escape_latex(cert)
            if len(escaped_cert) > 80:  # Truncate long certifications
                escaped_cert = escaped_cert[:77] + "..."
            cert_block += f"    \\item {escaped_cert}\n"
    
    # Replace certifications loop block
    cert_pattern = r'\{%\s*for\s+cert\s+in\s+certifications\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    cert_match = re.search(cert_pattern, result, re.DOTALL)
    if cert_match:
        if cert_block:
            result = result.replace(cert_match.group(0), cert_block)
        else:
            result = result.replace(cert_match.group(0), "")
    
    return result

def _compile_latex_to_pdf(latex_content: str, output_dir: str) -> Optional[str]:
    """Compile LaTeX to PDF using pdflatex"""
    try:
        # Write LaTeX file
        tex_file = os.path.join(output_dir, "generated_resume.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Compile with pdflatex (run twice for references)
        pdf_file = os.path.join(output_dir, "generated_resume.pdf")
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                print(f"pdflatex error: {result.stderr}")
                return None
        
        if os.path.exists(pdf_file):
            return pdf_file
        return None
    except subprocess.TimeoutExpired:
        print("pdflatex timeout")
        return None
    except FileNotFoundError:
        print("pdflatex not found. Please install LaTeX distribution.")
        return None
    except Exception as e:
        print(f"Compilation error: {str(e)}")
        return None

def _generate_ats_latex(parsed_data: Dict) -> str:
    """Generate one-page ATS-compliant LaTeX resume using base template"""
    # Load base template
    template = _load_template()
    
    # Map parsed data to template variables (using optimized version)
    template_data = _map_parsed_to_template_optimized(parsed_data)
    
    # Render template with data
    latex_content = _render_template(template, template_data)
    
    return latex_content

class SearchRequest(BaseModel):
    query: str
    session_id: str


class ClarifyRequest(BaseModel):
    session_id: str
    answer: str


router = APIRouter(prefix="/api", tags=["assistant-v2"])


def _llm_chat_message(user_query: str) -> Optional[str]:
    """Génère un message conversationnel via Ollama quand dispo."""
    try:
        analysis = llm_assistant.analyze_query(user_query)
        if isinstance(analysis, dict) and analysis.get("response"):
            return analysis["response"]
        if isinstance(analysis, str):
            return analysis
    except Exception:
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
    session = career_assistant.get_session(session_id)
    if not session or not session.get("last_results"):
        raise HTTPException(status_code=404, detail="No results stored for this session")
    return session["last_results"]


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
        matched_skills = sorted(list(set(cv_skills) & set(job_skills)))
        missing_skills = [s for s in job_skills if s not in cv_skills]
        skills_match = len(matched_skills) / len(job_skills) if job_skills else 0.0

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


# --- ATS CV Optimizer Endpoint ---
@router.post("/ats_cv")
async def ats_cv_optimizer(
    cv_file: Optional[UploadFile] = File(None, description="CV (PDF, DOCX, TXT)"),
    target_role: str = Form("", description="Rôle cible (optionnel)"),
    session_id: str = Form("", description="Session ID")
):
    """
    Parse CV using ResumeParser.app and format as ATS-compliant text.
    """
    if not cv_file:
        return {"success": False, "error": "Missing CV file."}

    try:
        # Parse CV using ResumeParser.app
        api_response = resume_parser_api.parse_cv_with_resumeparser(cv_file)
        
        if not api_response.get("success"):
            return {"success": False, "error": api_response.get("error", "Failed to parse CV")}
        
        # Extract parsed data
        parsed_data = api_response.get("data", {}).get("parsed", {})
        
        # Generate ATS-compliant LaTeX using base template
        ats_latex = _generate_ats_latex(parsed_data)
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Compile LaTeX to PDF
            pdf_path = _compile_latex_to_pdf(ats_latex, temp_dir)
            
            # Read PDF if compilation succeeded
            pdf_base64 = ""
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
            
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
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            if session_id:
                career_assistant.update_session_results(session_id, response)

            return response
    except Exception as e:
        return {"success": False, "error": str(e)}



def _map_parsed_to_template_optimized(parsed_data: Dict) -> Dict:
    """Map ResumeParser.app JSON structure to template variables, optimized for one page"""
    contact = parsed_data.get("contact", {})
    
    # Build compact location string
    location_parts = []
    if contact.get("location_city"):
        location_parts.append(contact["location_city"])
    if contact.get("location_state"):
        location_parts.append(contact["location_state"])
    # Omit country if it's obvious (like "USA" for US addresses)
    if contact.get("location_country") and contact.get("location_country").lower() not in ['usa', 'united states', 'us']:
        location_parts.append(contact["location_country"])
    location = ", ".join(location_parts) if location_parts else ""
    
    # Map experience - prioritize recent and relevant
    experience_list = []
    employment_history = parsed_data.get("employment_history", [])
    
    # Sort by recency (assuming dates are available)
    sorted_experience = sorted(
        employment_history,
        key=lambda x: x.get('end_date', 'Present') if x.get('end_date', 'Present') != 'Present' else '9999-12-31',
        reverse=True
    )
    
    for job in sorted_experience[:3]:  # Only keep 3 most recent jobs
        exp_item = {
            "position": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "start_date": job.get("start_date", ""),
            "end_date": job.get("end_date", "Present"),
            "description": []
        }
        
        # Collect responsibilities, prioritize bullet points
        responsibilities = job.get("responsibilities", [])
        bullet_points = []
        
        for resp in responsibilities:
            if isinstance(resp, str):
                bullet_points.append(resp)
            elif isinstance(resp, dict):
                # Handle nested roles
                if "responsibilities" in resp:
                    for r in resp.get("responsibilities", []):
                        if isinstance(r, str):
                            bullet_points.append(r)
        
        # Take only the most important 3-4 bullet points
        exp_item["description"] = bullet_points[:4]
        
        if exp_item["description"] or exp_item["position"]:
            experience_list.append(exp_item)
    
    # Map education - only highest degree
    education_list = []
    education_data = parsed_data.get("education", [])
    
    # Sort by education level (simplified)
    education_priority = {
        'phd': 1, 'doctorate': 1,
        'master': 2, 'masters': 2, 'msc': 2, 'ma': 2,
        'bachelor': 3, 'bachelors': 3, 'bs': 3, 'ba': 3,
        'associate': 4, 'diploma': 5, 'certificate': 6
    }
    
    sorted_education = sorted(
        education_data,
        key=lambda x: education_priority.get(x.get('degree', '').lower().split()[0], 99)
    )
    
    for edu in sorted_education[:2]:  # Only keep top 2 degrees
        edu_item = {
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution_name", ""),
            "details": ""
        }
        
        # Build compact details
        details_parts = []
        if edu.get("institution_country"):
            country = edu["institution_country"]
            # Abbreviate common countries
            if country.lower() == 'united states':
                country = 'USA'
            details_parts.append(country)
        
        # Format dates compactly
        if edu.get("start_date") or edu.get("end_date"):
            start = edu.get('start_date', '')[:4]  # Just year
            end = edu.get('end_date', '')[:4] if edu.get('end_date') else 'Present'
            if start or end:
                edu_date = f"{start} - {end}".strip(" -")
                if edu_date:
                    details_parts.append(edu_date)
        
        edu_item["details"] = " | ".join(details_parts)
        education_list.append(edu_item)
    
    # Process skills - categorize and prioritize
    raw_skills = parsed_data.get("skills", [])
    # Remove duplicates and prioritize technical/hard skills
    unique_skills = []
    seen = set()
    for skill in raw_skills:
        if skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    # Limit to 15 most relevant skills
    prioritized_skills = unique_skills[:15]
    
    # Process certifications
    certs = parsed_data.get("courses", [])[:5]  # Limit to 5
    
    return {
        "name": parsed_data.get("name", ""),
        "title": parsed_data.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": location,
        "summary": parsed_data.get("brief", "")[:300],  # Limit summary length
        "skills": prioritized_skills,
        "experience": experience_list,
        "education": education_list,
        "languages": parsed_data.get("languages", [])[:3],  # Limit to 3 languages
        "certifications": certs
    }