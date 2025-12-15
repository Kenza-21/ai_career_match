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
from services.llm_assistant import career_assistant as llm_assistant
from utils.link_generator import LinkGenerator

router = APIRouter(prefix="/api", tags=["smart-assistant"])


@router.post("/smart-assistant")
async def smart_career_assistant(
    message: str = Query(..., description="Message à l'assistant"),
    clarification: Optional[str] = Query(None, description="Réponse à une question de clarification")
):
    """
    Smart Assistant - AI-powered job search assistant with LLM analysis.
    
    Acts as a career coach chatbot that:
    - Uses Ollama LLM to generate natural, human-like coaching responses
    - Forwards clarifications to normal Assistant API to get job links
    - Never returns "no results found" - always forwards to normal assistant
    - Provides advice, trends, and comparisons between jobs
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
                
                # Generate coaching response using Ollama with the job context
                jobs = assistant_response.get("jobs", [])
                coaching_response = ""
                
                if jobs:
                    # Use Ollama to generate a natural coaching response about the found jobs
                    coaching_response = llm_assistant.generate_coaching_response(
                        f"L'utilisateur cherche: {combined_query}",
                        job_data=jobs[:5]  # Use top 5 jobs for context
                    )
                else:
                    # Even if no jobs, provide coaching advice
                    coaching_response = llm_assistant.generate_coaching_response(
                        f"L'utilisateur cherche: {combined_query}",
                        job_data=None
                    )
                
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
                    "assistant_response": coaching_response or assistant_response.get("summary", "J'ai trouvé des opportunités pour vous."),
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

        # Detect if user is lost/needs guidance or wants comparison
        lost_markers = {"help", "aide", "lost", "perdu", "conseil", "orient", "guidance"}
        comparison_markers = {"compare", "comparer", "vs", "versus", "différence", "mieux"}
        is_lost = any(token in lost_markers for token in message.lower().split())
        is_comparison = any(token in comparison_markers for token in message.lower().split())

        # Use LLM for coaching responses (natural language)
        analysis = llm_assistant.analyze_query(message)
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except:
                analysis = {"intent": "coaching", "response": analysis}

        # Handle coaching responses (lost, guidance, comparison) - return immediately
        intent = analysis.get('intent', 'search')
        if intent in ['coaching', 'comparison']:
            # For coaching/comparison, return the natural language response from Ollama
            coaching_response = analysis.get('response', '')
            coaching_advice = analysis.get('coaching_advice', '')
            
            return {
                "assistant_response": coaching_response,
                "coaching_advice": coaching_advice,
                "needs_clarification": analysis.get('needs_clarification', False),
                "clarification_questions": analysis.get('clarification_questions', []),
                "intent": intent,
                "is_coaching": True,
                "jobs": [],
                "search_urls": []
            }
        
        # Handle clarification if requested by LLM
        if analysis.get('needs_clarification'):
            return {
                "assistant_response": analysis.get('response', ''),
                "needs_clarification": True,
                "clarification_questions": analysis.get('clarification_questions', []),
                "intent": analysis.get('intent', 'vague'),
                "is_coaching": True,
                "jobs": [],
                "search_urls": []
            }

        # Determine search query
        search_query = analysis.get('search_query', message)

        # If search is vague or empty, ask for clarification
        if not search_query or len(search_query.strip()) < 3:
            return {
                "assistant_response": analysis.get('response', 'Pourriez-vous préciser votre recherche ?'),
                "needs_clarification": True,
                "clarification_questions": ["Quel domaine tech précis ?", "Quel type de poste ?"],
                "intent": "vague",
                "is_coaching": True,
                "jobs": [],
                "search_urls": []
            }

        # CRITICAL: Forward to normal Assistant API instead of searching directly
        # This ensures we get job links and proper formatting
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
            
            # Generate coaching response using Ollama with job context
            if jobs:
                coaching_response = llm_assistant.generate_coaching_response(
                    message,
                    job_data=jobs[:5]
                )
            else:
                # Even with no jobs, provide helpful coaching
                coaching_response = llm_assistant.generate_coaching_response(
                    message,
                    job_data=None
                )
            
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
                "assistant_response": coaching_response or assistant_response.get("summary", "J'ai analysé le marché pour vous."),
                "coaching_advice": analysis.get('coaching_advice', ''),
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
            
            coaching_response = llm_assistant.generate_coaching_response(
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
                "coaching_advice": analysis.get('coaching_advice', ''),
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
        return {
            "error": str(e),
            "assistant_response": "Désolé, une erreur est survenue. Laissez-moi vous aider autrement.",
            "needs_clarification": False,
            "is_coaching": True,
            "jobs": [],
            "search_urls": []
        }

