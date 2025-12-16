"""
Smart Assistant Routes
AI-powered assistant with LLM-based query analysis and clarification flow
Acts as a career coach chatbot with natural language responses
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query
import json
import httpx
from routes.job_routes import job_matcher
from services.llm_assistant import CareerAssistant, get_coach_response
from utils.link_generator import LinkGenerator

router = APIRouter(prefix="/api", tags=["smart-assistant"])

# Créer une instance du nouveau coach
career_coach = CareerAssistant()


@router.post("/smart-assistant")
async def smart_career_assistant(
    message: str = Query(..., description="Message à l'assistant"),
    clarification: Optional[str] = Query(None, description="Réponse à une question de clarification")
):
    """
    Smart Assistant - AI-powered job search assistant with LLM analysis.
    """
    try:
        print(f"🤖 Smart Assistant receives: {message}")
        if clarification:
            print(f"📝 With clarification: {clarification}")

        # CRITICAL: When clarification is provided, forward to normal Assistant API
        # This ensures we always get job links and never return "no results found"
        if clarification:
            # Combine original message with clarification
            combined_query = f"{message} {clarification}".strip()
            print(f"🔄 Forwarding clarification to normal Assistant: {combined_query}")
            
            # Call normal assistant endpoint internally via HTTP
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://localhost:8000/api/assistant",
                        params={"message": combined_query},
                        timeout=30.0
                    )
                    response.raise_for_status()
                    assistant_response = response.json()
                
                # ✅ CORRECTION : Utiliser career_coach (l'instance existante)
                jobs = assistant_response.get("jobs", [])
                
                if jobs:
                    # Utiliser le coach avec contexte d'offres
                    coaching_response = career_coach.respond_with_jobs_context(
                        f"L'utilisateur cherche: {combined_query}",
                        job_data=jobs[:5]  # Use top 5 jobs for context
                    )
                else:
                    # Utiliser le coach pour une réponse naturelle
                    coach_result = career_coach.coach_thinking(f"L'utilisateur cherche: {combined_query}")
                    coaching_response = coach_result.get("response", "Je vais vous aider à trouver les meilleures opportunités.")
                
                # Extract job links from assistant response
                search_urls = []
                for job in jobs:
                    job_title = job.get('job_title', '')
                    job_id = str(job.get('job_id', ''))
                    if job_title:
                        urls = LinkGenerator.generate_all_urls(job_title, job_id=job_id)
                        search_urls.append({
                            "job_title": job_title,
                            "stagiaires_url": urls.get("stagiaires_url", urls.get("linkedin_url")),
                            "rekrute_url": urls.get("rekrute_url")
                        })
                
                # Return Smart Assistant response with coaching and job links
                return {
                    "assistant_response": coaching_response,
                    "coaching_advice": "",
                    "intent": "search",
                    "search_query_used": combined_query,
                    "total_matches": len(jobs),
                    "jobs": jobs,
                    "search_urls": search_urls,
                    "needs_clarification": False,
                    "is_coaching": True
                }
            except Exception as e:
                print(f"⚠️ Error calling normal assistant: {e}")
                # Fallback: continue with smart assistant logic

        # ✅ CORRECTION : Utiliser career_coach pour analyser la requête
        coach_result = career_coach.coach_thinking(message)
        
        # Vérifier si c'est une demande de coaching pur (orientation, comparaison, guidance)
        intent = coach_result.get("intent", "search")
        
        if intent in ["orientation", "comparison", "guidance", "coaching"]:
            # Pour les réponses de coaching pur, retourner directement
            return {
                "assistant_response": coach_result.get("response", ""),
                "coaching_advice": "",
                "needs_clarification": coach_result.get("needs_clarification", False),
                "clarification_questions": coach_result.get("next_questions", []),
                "intent": intent,
                "is_coaching": True,
                "jobs": [],
                "search_urls": []
            }
        
        # Si le coach demande des clarifications
        if coach_result.get("needs_clarification"):
            return {
                "assistant_response": coach_result.get("response", ""),
                "needs_clarification": True,
                "clarification_questions": coach_result.get("next_questions", []),
                "intent": intent,
                "is_coaching": True,
                "jobs": [],
                "search_urls": []
            }

        # Si c'est une recherche, forward au normal assistant
        search_query = message  # Utiliser le message original
        
        print(f"🔄 Forwarding search to normal Assistant: {search_query}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/assistant",
                    params={"message": search_query},
                    timeout=30.0
                )
                response.raise_for_status()
                assistant_response = response.json()
            jobs = assistant_response.get("jobs", [])
            
            # ✅ CORRECTION : Générer une réponse de coaching avec contexte
            if jobs:
                coaching_response = career_coach.respond_with_jobs_context(
                    message,
                    job_data=jobs[:5]
                )
            else:
                # Même sans offres, fournir un conseil de coach
                coaching_response = coach_result.get("response", 
                    "D'après mon analyse du marché, voici ce que je peux vous conseiller...")
            
            # Extract job links
            search_urls = []
            for job in jobs:
                job_title = job.get('job_title', '')
                job_id = str(job.get('job_id', ''))
                if job_title:
                    urls = LinkGenerator.generate_all_urls(job_title, job_id=job_id)
                    search_urls.append({
                        "job_title": job_title,
                        "stagiaires_url": urls.get("stagiaires_url", urls.get("linkedin_url")),
                        "rekrute_url": urls.get("rekrute_url")
                    })
            
            return {
                "assistant_response": coaching_response,
                "coaching_advice": "",
                "intent": intent,
                "search_query_used": search_query,
                "total_matches": len(jobs),
                "jobs": jobs,
                "search_urls": search_urls,
                "needs_clarification": False,
                "is_coaching": True
            }
        except Exception as e:
            print(f"⚠️ Error calling normal assistant: {e}")
            # Fallback to direct search if assistant fails
            matches = job_matcher.search_jobs(search_query, top_k=8)
            results = []
            for idx, _ in matches:
                job_data = job_matcher.get_job_by_index(idx)
                results.append({
                    "job_title": job_data.get('job_title', 'Titre inconnu'),
                    "category": job_data.get('category', 'Non catégorisé'),
                    "description_preview": job_data.get('description', '')[:100] + "...",
                    "demand_level": job_data.get('demand_level', 'Medium'),
                    "salary_range": job_data.get('avg_salary_mad', 'Non spécifié'),
                    "required_skills": job_data.get('required_skills', ''),
                    "job_id": job_data.get('job_id', idx + 1)
                })
            
            # Utiliser le coach avec les résultats
            coaching_response = career_coach.respond_with_jobs_context(
                message,
                job_data=results
            )
            
            search_urls = []
            for job in results:
                job_title = job['job_title']
                job_id = str(job.get('job_id', ''))
                urls = LinkGenerator.generate_all_urls(job_title, job_id=job_id)
                search_urls.append({
                    "job_title": job_title,
                    "stagiaires_url": urls.get("stagiaires_url", urls.get("linkedin_url")),
                    "rekrute_url": urls.get("rekrute_url")
                })
            
            return {
                "assistant_response": coaching_response,
                "coaching_advice": "",
                "intent": intent,
                "search_query_used": search_query,
                "total_matches": len(results),
                "jobs": results,
                "search_urls": search_urls,
                "needs_clarification": False,
                "is_coaching": True
            }
        
    except Exception as e:
        print(f"❌ Smart Assistant error: {e}")
        import traceback
        print(traceback.format_exc())
        # ✅ CORRECTION : Utiliser le fallback du coach
        fallback_result = career_coach._fallback_coach_response(message)
        return {
            "error": str(e),
            "assistant_response": fallback_result.get("response", "Désolé, une erreur est survenue. Laissez-moi vous aider autrement."),
            "needs_clarification": fallback_result.get("needs_clarification", False),
            "clarification_questions": fallback_result.get("next_questions", []),
            "is_coaching": True,
            "jobs": [],
            "search_urls": []
        }