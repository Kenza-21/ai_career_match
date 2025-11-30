from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class JobBase(BaseModel):
    job_title: str
    category: str
    description: str
    required_skills: str
    recommended_courses: str
    avg_salary_mad: str
    demand_level: str

class Job(JobBase):
    job_id: int
    
    class Config:
        from_attributes = True
        extra = "ignore"  # ← IMPORTANT: Ignore les champs supplémentaires

class JobMatch(Job):
    match_score: float
    linkedin_url: str

class JobSearchResponse(BaseModel):
    query: str
    top_k: int
    results: List[JobMatch]

class SearchLinkResponse(BaseModel):
    job_title: str
    linkedin_url: str
    indeed_url: str
    google_url: str
    marocannonces_url: str  #
    rekrute_url: str   
    
class AssistantResponse(BaseModel):
    analysis: Dict
    summary: Dict
    search_query_used: str
    jobs: List[JobMatch]
    suggestions: List[str]    