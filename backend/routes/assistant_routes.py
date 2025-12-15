"""
Assistant Routes
Basic assistant for job search with pattern-based query analysis
"""
from typing import Dict
from fastapi import APIRouter, HTTPException, Query
from routes.job_routes import job_matcher
from services.assistant import career_assistant as simple_assistant
from utils.link_generator import LinkGenerator
from models.job import JobMatch

router = APIRouter(prefix="/api", tags=["assistant"])


@router.post("/assistant", response_model=Dict)
async def career_assistant_endpoint(
    message: str = Query(..., description="Message en langage naturel pour l'assistant")
):
    """
    Basic Assistant - Pattern-based job search assistant.
    
    Uses simple pattern matching to understand user queries and generate search results.
    Returns job matches with links to external platforms.
    """
    if not job_matcher:
        raise HTTPException(status_code=500, detail="Job matcher not initialized")
    
    try:
        # Analyze message with pattern-based assistant
        analysis = simple_assistant.analyze_query(message)
        
        # Try multiple queries in cascade
        all_matches = []
        tried_queries = []
        
        # 1. Main query
        search_query = analysis['search_query'] or message
        tried_queries.append(search_query)
        
        try:
            matches = job_matcher.search_jobs(search_query, top_k=10)
            all_matches.extend(matches)
            print(f"✅ Main query found: {len(matches)} results")
        except Exception as e:
            print(f"⚠️ Error with main query: {e}")
        
        # 2. Try fallbacks if not enough results
        if len(all_matches) < 5 and analysis.get('fallback_queries'):
            for fallback_query in analysis.get('fallback_queries', [])[:3]:
                tried_queries.append(fallback_query)
                try:
                    fallback_matches = job_matcher.search_jobs(fallback_query, top_k=5)
                    existing_indices = {idx for idx, _ in all_matches}
                    for idx, score in fallback_matches:
                        if idx not in existing_indices:
                            all_matches.append((idx, score))
                    print(f"✅ Fallback '{fallback_query}': {len(fallback_matches)} results")
                except Exception as e:
                    print(f"⚠️ Error with fallback '{fallback_query}': {e}")
        
        # 3. If still nothing, try very general search
        if len(all_matches) == 0:
            general_queries = ["technologie", "informatique", "digital"]
            for gen_query in general_queries:
                tried_queries.append(gen_query)
                try:
                    gen_matches = job_matcher.search_jobs(gen_query, top_k=3)
                    all_matches.extend(gen_matches)
                    if gen_matches:
                        print(f"✅ General search '{gen_query}': {len(gen_matches)} results")
                        break
                except Exception as e:
                    print(f"⚠️ Error with general search: {e}")
        
        # Sort by score and limit to at least 8 results
        all_matches.sort(key=lambda x: x[1], reverse=True)
        # Ensure minimum 8 results, but try to get more if available
        min_results = 8
        top_matches = all_matches[:max(min_results, len(all_matches))]
        
        # If we still don't have 8, try to get more with broader search
        if len(top_matches) < min_results:
            try:
                broader_matches = job_matcher.search_jobs(message, top_k=min_results * 2)
                existing_indices = {idx for idx, _ in top_matches}
                for idx, score in broader_matches:
                    if idx not in existing_indices and len(top_matches) < min_results:
                        top_matches.append((idx, score))
                top_matches.sort(key=lambda x: x[1], reverse=True)
            except Exception as e:
                print(f"⚠️ Error getting additional results: {e}")
        
        print(f"📊 Total queries tried: {tried_queries}")
        print(f"🎯 Final results: {len(top_matches)} jobs (minimum: {min_results})")
        
        # Prepare results
        jobs_results = []
        for idx, score in top_matches:
            try:
                job_data = job_matcher.get_job_by_index(idx)
                job_id = str(job_data.get('job_id', idx + 1))
                
                # Generate all URLs with Stagiaires.ma as primary
                all_urls = LinkGenerator.generate_all_urls(
                    job_data.get('job_title', search_query),
                    job_id=job_id
                )
                
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
                    linkedin_url=all_urls["linkedin_url"]
                )
                jobs_results.append(job_match)
                
            except Exception as job_error:
                print(f"⚠️ Error processing job {idx}: {job_error}")
                continue
        
        # Convert to dictionaries and add all URLs
        jobs_with_all_urls = []
        for i, job in enumerate(jobs_results):
            job_dict = job.dict()
            if i < len(top_matches):
                job_data = job_matcher.get_job_by_index(top_matches[i][0])
                job_id = str(job_data.get('job_id', top_matches[i][0] + 1))
                all_urls = LinkGenerator.generate_all_urls(
                    job_data.get('job_title', search_query),
                    job_id=job_id
                )
                job_dict["all_search_urls"] = all_urls
                # Add primary Stagiaires.ma URL
                job_dict["stagiaires_url"] = all_urls.get("stagiaires_url", all_urls.get("linkedin_url"))
            jobs_with_all_urls.append(job_dict)
        
        # Generate assistant response
        assistant_response = simple_assistant.generate_response(message, jobs_with_all_urls)
        
        # Add debug metadata
        assistant_response["debug_info"] = {
            "tried_queries": tried_queries,
            "total_candidates_found": len(all_matches),
            "returned_jobs": len(jobs_results)
        }
        
        return assistant_response
        
    except Exception as e:
        print(f"❌ Error in assistant: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")

