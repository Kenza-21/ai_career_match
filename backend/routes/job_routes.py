from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional,Dict
import os
from services.assistant import career_assistant

from models.job import Job, JobMatch, JobSearchResponse, SearchLinkResponse
from services.matcher import JobMatcher
from utils.link_generator import LinkGenerator
from services.llm_assistant import career_assistant
# Initialize the job matcher
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(current_dir, "data", "jobs_morocco.csv")

try:
    job_matcher = JobMatcher(csv_path)
    print("✅ Job matcher initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing job matcher: {e}")
    job_matcher = None

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/all", response_model=List[Job])
async def get_all_jobs():
    """Get all available jobs"""
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")
    
    try:
        print("🔍 Debug: Getting all jobs...")
        jobs_data = job_matcher.get_all_jobs()
        print(f"✅ Debug: Got {len(jobs_data)} raw jobs")
        
        # Debug: Vérifier le premier élément
        if jobs_data:
            first_job = jobs_data[0]
            print(f"🔍 First job keys: {list(first_job.keys())}")
            print(f"🔍 First job values: {first_job}")
        
        # Convertir en objets Pydantic avec gestion d'erreur
        jobs = []
        for i, job_dict in enumerate(jobs_data):
            try:
                # Nettoyer les données si nécessaire
                cleaned_job = {
                    'job_id': int(job_dict.get('job_id', 0)),
                    'job_title': str(job_dict.get('job_title', '')),
                    'category': str(job_dict.get('category', '')),
                    'description': str(job_dict.get('description', '')),
                    'required_skills': str(job_dict.get('required_skills', '')),
                    'recommended_courses': str(job_dict.get('recommended_courses', '')),
                    'avg_salary_mad': str(job_dict.get('avg_salary_mad', '')),
                    'demand_level': str(job_dict.get('demand_level', ''))
                }
                job_obj = Job(**cleaned_job)
                jobs.append(job_obj)
            except Exception as e:
                print(f"❌ Error processing job {i}: {e}")
                print(f"🔍 Problematic job data: {job_dict}")
                continue
        
        print(f"✅ Successfully processed {len(jobs)} jobs")
        return jobs
        
    except Exception as e:
        print(f"❌ Error in /jobs/all: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/search", response_model=JobSearchResponse)
async def search_jobs(
    query: str = Query(..., description="Job search query"),
    top_k: int = Query(5, description="Number of top matches to return", ge=1, le=20)
):
    """Search for jobs matching the query"""
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")
    
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        print(f"🔍 Searching for: '{query}' with top_k={top_k}")
        
        # Search for matching jobs
        matches = job_matcher.search_jobs(query, top_k)
        print(f"✅ Found {len(matches)} matches")
        
        # Prepare results
        results = []
        for idx, score in matches:
            try:
                job_data = job_matcher.get_job_by_index(idx)
                print(f"🔍 Processing job {idx}: {job_data.get('job_title', 'Unknown')}")
                
                # Debug: print all available keys
                print(f"🔍 Available keys: {list(job_data.keys())}")
                
                # Generate LinkedIn URL
                linkedin_url = LinkGenerator.generate_linkedin_url(job_data.get('job_title', query))
                
                # Create job match result with safe field access
                job_match = JobMatch(
                    job_id=job_data.get('job_id', idx + 1),
                    job_title=job_data.get('job_title', f'Poste {idx + 1}'),
                    category=job_data.get('category', 'Général'),
                    description=job_data.get('description', f'Poste correspondant à la recherche: {query}'),
                    required_skills=job_data.get('required_skills', 'Compétences variées'),
                    recommended_courses=job_data.get('recommended_courses', 'Formations adaptées au poste'),
                    avg_salary_mad=job_data.get('avg_salary_mad', '5000-10000'),
                    demand_level=job_data.get('demand_level', 'Medium'),
                    match_score=round(score, 4),
                    linkedin_url=linkedin_url
                )
                results.append(job_match)
                
            except Exception as job_error:
                print(f"⚠️ Error processing job {idx}: {job_error}")
                continue
        
        print(f"✅ Returning {len(results)} results")
        return JobSearchResponse(
            query=query,
            top_k=top_k,
            results=results
        )
        
    except Exception as e:
        print(f"❌ Error in search_jobs: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/{job_title}/search-link", response_model=SearchLinkResponse)
async def get_job_search_link(job_title: str):
    """Generate external job search links for a specific job title"""
    urls = LinkGenerator.generate_all_urls(job_title)
    
    return SearchLinkResponse(
        job_title=job_title,
        linkedin_url=urls["linkedin_url"],
        indeed_url=urls["indeed_url"],
        google_url=urls["google_url"],
        marocannonces_url=urls["marocannonces_url"],  # 
        rekrute_url=urls["rekrute_url"] 
    )

@router.get("/categories")
async def get_categories():
    """Get all available job categories"""
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")
    
    categories = job_matcher.get_categories()
    return {"categories": categories}

@router.get("/category/{category_name}")
async def get_jobs_by_category(category_name: str):
    """Get jobs by category"""
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")
    
    jobs = job_matcher.get_jobs_by_category(category_name)
    return {"category": category_name, "jobs": jobs, "count": len(jobs)}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    status = "healthy" if job_matcher else "unhealthy"
    jobs_loaded = len(job_matcher.df) if job_matcher else 0
    
    return {
        "status": status,
        "jobs_loaded": jobs_loaded,
        "matcher_initialized": job_matcher is not None
    }
    
@router.post("/assistant", response_model=Dict)
async def career_assistant_endpoint(
    message: str = Query(..., description="Message en langage naturel pour l'assistant")
):
    """Assistant conversationnel pour la recherche d'emploi"""
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")
    
    try:
        # Analyser le message avec l'assistant
        analysis = career_assistant.analyze_query(message)
        
        # Utiliser la requête optimisée pour la recherche
        search_query = analysis['search_query'] or message
        matches = job_matcher.search_jobs(search_query, top_k=10)
        
        # Préparer les résultats
        jobs_results = []
        for idx, score in matches:
            job_data = job_matcher.get_job_by_index(idx)
            
            # Générer toutes les URLs
            all_urls = LinkGenerator.generate_all_urls(job_data.get('job_title', search_query))
            
            job_match = JobMatch(
                job_id=job_data.get('job_id', idx + 1),
                job_title=job_data.get('job_title', f'Poste {idx + 1}'),
                category=job_data.get('category', 'Général'),
                description=job_data.get('description', 'Description non disponible'),
                required_skills=job_data.get('required_skills', 'Compétences variées'),
                recommended_courses=job_data.get('recommended_courses', ''),
                avg_salary_mad=job_data.get('avg_salary_mad', 'Non spécifié'),
                demand_level=job_data.get('demand_level', 'Medium'),
                match_score=round(score, 4),
                linkedin_url=all_urls["linkedin_url"]  # Utiliser LinkedIn comme avant
            )
            jobs_results.append(job_match)
        
        # Convertir en dictionnaires pour ajouter les URLs supplémentaires
        jobs_with_all_urls = []
        for i, job in enumerate(jobs_results):
            job_dict = job.dict()
            # Ajouter toutes les URLs pour ce job
            job_data = job_matcher.get_job_by_index(matches[i][0])
            all_urls = LinkGenerator.generate_all_urls(job_data.get('job_title', search_query))
            job_dict["all_search_urls"] = all_urls  # ← AJOUTER TOUTES LES URLs
            jobs_with_all_urls.append(job_dict)
        
        # Générer la réponse complète de l'assistant
        assistant_response = career_assistant.generate_response(message, jobs_with_all_urls)
        
        return assistant_response
        
    except Exception as e:
        print(f"❌ Error in assistant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")
    
    
@router.post("/smart-assistant")
async def smart_career_assistant(
    message: str = Query(..., description="Message à l'assistant"),
    clarification: Optional[str] = Query(None)
):
    """Assistant IA intelligent pour la recherche d'emploi"""
    try:
        print(f"🤖 Assistant reçoit: {message}")
        
        # Analyse avec le LLM
        analysis = career_assistant.analyze_query(message)
        
        # VÉRIFIER SI C'EST UN STRING JSON ET LE PARSER
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except:
                analysis = {"intent": "clair", "response": analysis}
        
        # Si besoin de clarification
        if analysis.get('needs_clarification') and not clarification:
            return {
                "assistant_response": analysis.get('response', ''),
                "needs_clarification": True,
                "clarification_questions": analysis.get('clarification_questions', []),
                "intent": analysis.get('intent', 'vague')
            }
        
        # DÉTERMINER LA REQUÊTE DE RECHERCHE
        if clarification:
            search_query = f"{message} {clarification}"
        else:
            search_query = analysis.get('search_query', message)
        
        # Si recherche vague ou vide
        if not search_query or search_query.strip() == "":
            return {
                "assistant_response": analysis.get('response', ''),
                "needs_clarification": True,
                "clarification_questions": ["Quel domaine tech précis ?", "Quel type de poste ?"],
                "intent": "vague"
            }
        
        # 🔍 RECHERCHE AVEC LE MOTEUR EXISTANT
        matches = job_matcher.search_jobs(search_query, top_k=5)
        
        # Préparer les résultats SANS SCORE
        results = []
        for idx, _ in matches:  # On ignore le score ici
            job_data = job_matcher.get_job_by_index(idx)
            
            results.append({
                "job_title": job_data.get('job_title', 'Titre inconnu'),
                "category": job_data.get('category', 'Non catégorisé'),
                "description_preview": job_data.get('description', '')[:100] + "...",
                "demand_level": job_data.get('demand_level', 'Medium'),
                "salary_range": job_data.get('avg_salary_mad', 'Non spécifié')
            })
        
        # Générer les liens de recherche
        search_urls = []
        if results:
            # Générer des liens pour les 3 premiers jobs
            for job in results[:3]:
                job_title = job['job_title']
                urls = LinkGenerator.generate_all_urls(job_title)
                search_urls.append({
                    "job_title": job_title,
                    "linkedin_url": urls.get("linkedin_url"),
                    "rekrute_url": urls.get("rekrute_url")
                })
        
        # Construire la réponse finale
        response_message = f"J'ai trouvé {len(results)} offres correspondant à votre recherche."
        if results:
            top_jobs = ", ".join([r['job_title'] for r in results[:3]])
            response_message += f" Par exemple : {top_jobs}."
        
        return {
            "assistant_response": response_message,
            "intent": analysis.get('intent', 'clair'),
            "search_query_used": search_query,
            "total_matches": len(results),
            "jobs": results,  # Renommé de "results" à "jobs" pour clarté
            "search_urls": search_urls,  # Liens de recherche externes
            "next_step": "Pour une analyse détaillée de compatibilité, uploadez votre CV via /cv/analyze-upload",
            "needs_clarification": False
        }
        
    except Exception as e:
        print(f"❌ Erreur assistant: {e}")
        return {
            "error": str(e),
            "assistant_response": "Désolé, une erreur est survenue.",
            "needs_clarification": False
        }