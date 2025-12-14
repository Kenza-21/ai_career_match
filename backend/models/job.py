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
    rekrute_url: str   
    
class AssistantResponse(BaseModel):
    analysis: Dict
    summary: Dict
    search_query_used: str
    jobs: List[JobMatch]
    suggestions: List[str]    
    
    
class SkillGap(BaseModel):
    skill_name: str
    required_level: str
    current_level: str
    gap_severity: str  # "low", "medium", "high"

class TrainingRecommendation(BaseModel):
    skill: str
    platform: str
    course_name: str
    url: str
    duration: str
    level: str
    source: Optional[str] = "live_scraping"
    free: Optional[bool] = False

class CVImprovement(BaseModel):
    section: str
    current_situation: str
    suggested_text: str
    reason: str

class ATSRecommendation(BaseModel):
    type: str
    issue: str
    solution: str
    priority: str

class CVAnalysisRequest(BaseModel):
    cv_text: str
    job_description: str

class CVAnalysisResponse(BaseModel):
    match_score: float
    cv_skills: List[str]
    job_skills: List[str]
    skill_gaps: List[SkillGap]
    missing_skills: List[str]
    training_recommendations: List[TrainingRecommendation]
    key_phrases: List[Dict]
    ats_recommendations: List[ATSRecommendation]
    cv_sections: Optional[Dict] = None
    overall_assessment: str
    
    class Config:
        from_attributes = True    