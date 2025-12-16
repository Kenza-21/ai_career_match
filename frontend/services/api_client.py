"""
API Client Service
Centralized service for all backend API communications
"""
import os
import requests
from typing import Dict, Optional, List
from io import BytesIO


class APIClient:
    """Centralized API client for backend communication"""
    
    def __init__(self):
        self.base_url = os.getenv("ASSISTANT_API_URL", "http://localhost:8000")
        self.timeout = 600
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict:
        """Make HTTP request to backend API"""
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=json_data, timeout=timeout)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, data=data, files=files, timeout=timeout)
                else:
                    response = requests.post(url, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    # Search API methods
    def search_jobs(self, query: str, session_id: str) -> Dict:
        """Search for jobs using natural language query"""
        return self._make_request(
            "POST",
            "/api/search",
            json_data={"query": query, "session_id": session_id}
        )
    
    def clarify_search(self, answer: str, session_id: str) -> Dict:
        """Clarify ambiguous search query"""
        return self._make_request(
            "POST",
            "/api/clarify",
            json_data={"session_id": session_id, "answer": answer}
        )
    
    def get_last_results(self, session_id: str) -> Dict:
        """Get last search results for a session"""
        url = f"{self.base_url}/api/results?session_id={session_id}"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    # CV Analyzer API methods
    def analyze_cv(
        self,
        cv_file: Optional[BytesIO] = None,
        cv_text: str = "",
        job_description: str = "",
        session_id: str = ""
    ) -> Dict:
        """Analyze CV against job description"""
        files = {}
        data = {
            "cv_text": cv_text,
            "job_description": job_description,
            "session_id": session_id
        }
        
        if cv_file:
            files["cv_file"] = (cv_file.name, cv_file.getvalue(), cv_file.type)
        
        return self._make_request(
            "POST",
            "/api/cv_analyser",
            data=data,
            files=files if files else None
        )
    
    # ATS Optimizer API methods
    def optimize_ats_cv(
        self,
        cv_file: BytesIO,
        target_role: str = "",
        session_id: str = ""
    ) -> Dict:
        """Optimize CV for ATS systems"""
        files = {"cv_file": (cv_file.name, cv_file.getvalue(), cv_file.type)}
        data = {
            "target_role": target_role,
            "session_id": session_id
        }
        
        return self._make_request(
            "POST",
            "/api/ats_cv",
            data=data,
            files=files
        )
    
    def evaluate_ats_resume(
        self,
        cv_file: Optional[BytesIO] = None,
        cv_text: str = "",
        session_id: str = ""
    ) -> Dict:
        """Evaluate resume using Google Gemini ATS evaluator"""
        files = {}
        data = {
            "cv_text": cv_text,
            "session_id": session_id
        }
        
        if cv_file:
            files["cv_file"] = (cv_file.name, cv_file.getvalue(), cv_file.type)
        
        return self._make_request(
            "POST",
            "/api/ats_evaluate",
            data=data,
            files=files if files else None
        )
    
    # Job routes API methods
    def get_all_jobs(self) -> List[Dict]:
        """Get all available jobs"""
        return self._make_request("GET", "/jobs/all")
    
    def search_jobs_by_query(self, query: str, top_k: int = 5) -> Dict:
        """Search jobs by query string"""
        url = f"{self.base_url}/jobs/search?query={query}&top_k={top_k}"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def get_job_categories(self) -> Dict:
        """Get all job categories"""
        return self._make_request("GET", "/jobs/categories")
    
    def get_jobs_by_category(self, category: str) -> Dict:
        """Get jobs by category"""
        return self._make_request("GET", f"/jobs/category/{category}")
    
    # Assistant API methods
    def assistant_search(self, message: str) -> Dict:
        """Basic Assistant - Pattern-based job search"""
        url = f"{self.base_url}/api/assistant"
        try:
            response = requests.post(url, params={"message": message}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    # Smart Assistant API methods
    def smart_assistant_search(
        self, 
        message: str, 
        clarification: Optional[str] = None
    ) -> Dict:
        """Smart Assistant - LLM-powered job search with clarification"""
        params = {"message": message}
        if clarification:
            params["clarification"] = clarification
        
        url = f"{self.base_url}/api/smart-assistant"
        try:
            response = requests.post(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")


   # Add to APIClient class in api_client.py

    def generate_resume(self, resume_data: Dict) -> BytesIO:
        """Generate resume from structured data"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate-resume",
                json=resume_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate resume: {str(e)}")
# Singleton instance
api_client = APIClient()

