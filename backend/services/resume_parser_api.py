import requests
import base64
from typing import Dict, Optional
from fastapi import UploadFile, HTTPException
import io

class ResumeParserAPI:
    """Service to parse CVs using ResumeParser.app external API"""
    
    API_KEY = "02b26c9f3f302d61667637f5159fdf2b"
    API_URL = "https://resumeparser.app/resume/parse"
    
    @staticmethod
    def parse_cv_with_resumeparser(cv_file: UploadFile) -> Dict:
        """
        Parse CV using ResumeParser.app API
        
        Args:
            cv_file: Uploaded CV file (PDF, DOCX, TXT)
            
        Returns:
            Dict with parsed CV data from API
        """
        try:
            # Read file content
            file_content = cv_file.file.read()
            cv_file.file.seek(0)
            
            # Try method 1: Multipart form data (most common for file uploads)
            try:
                files = {
                    "file": (cv_file.filename, file_content, cv_file.content_type or "application/octet-stream")
                }
                headers = {
                    "Authorization": f"Bearer {ResumeParserAPI.API_KEY}"
                }
                
                response = requests.post(
                    ResumeParserAPI.API_URL,
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    api_data = response.json()
                    return ResumeParserAPI._format_api_response(api_data)
            except Exception as e1:
                print(f"Method 1 (multipart) failed: {e1}")
            
            # Try method 2: Base64 in JSON with Bearer token
            try:
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                headers = {
                    "Authorization": f"Bearer {ResumeParserAPI.API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "file": file_base64,
                    "filename": cv_file.filename
                }
                
                response = requests.post(
                    ResumeParserAPI.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    api_data = response.json()
                    return ResumeParserAPI._format_api_response(api_data)
            except Exception as e2:
                print(f"Method 2 (base64 + bearer) failed: {e2}")
            
            # Try method 3: Base64 in JSON with key in payload
            try:
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                payload = {
                    "file": file_base64,
                    "filename": cv_file.filename,
                    "key": ResumeParserAPI.API_KEY
                }
                
                response = requests.post(
                    ResumeParserAPI.API_URL,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    api_data = response.json()
                    return ResumeParserAPI._format_api_response(api_data)
                else:
                    error_msg = response.json().get("error", f"API error: {response.status_code}")
                    return {"success": False, "error": error_msg}
            except Exception as e3:
                print(f"Method 3 (base64 + key) failed: {e3}")
                return {
                    "success": False,
                    "error": f"All API methods failed. Last error: {str(e3)}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error calling ResumeParser API: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing CV: {str(e)}"
            }
    
    @staticmethod
    def _format_api_response(api_data: Dict) -> Dict:
        """Format ResumeParser.app API response into standardized structure"""
        # ResumeParser.app returns data in "parsed" key
        parsed = api_data.get("parsed", {})
        
        # Build raw text from structured data
        text_parts = []
        if parsed.get("name"):
            text_parts.append(parsed["name"])
        if parsed.get("title"):
            text_parts.append(parsed["title"])
        if parsed.get("brief"):
            text_parts.append(parsed["brief"])
        
        # Add employment history
        for job in parsed.get("employment_history", []):
            if job.get("title"):
                text_parts.append(f"{job.get('title')} at {job.get('company', '')}")
            for resp in job.get("responsibilities", []):
                if isinstance(resp, str):
                    text_parts.append(resp)
        
        # Add education
        for edu in parsed.get("education", []):
            if edu.get("degree"):
                text_parts.append(f"{edu.get('degree')} from {edu.get('institution_name', '')}")
        
        # Add skills
        if parsed.get("skills"):
            text_parts.append(", ".join(parsed["skills"]))
        
        raw_text = "\n".join(text_parts)
        
        return {
            "success": True,
            "data": api_data,
            "parsed": parsed,
            "raw_text": raw_text,
            "skills": parsed.get("skills", []),
            "experience": parsed.get("employment_history", []),
            "education": parsed.get("education", []),
            "contact": parsed.get("contact", {}),
            "summary": parsed.get("brief", ""),
            "job_titles": [job.get("title", "") for job in parsed.get("employment_history", []) if job.get("title")]
        }
    
    @staticmethod
    def get_cv_text_from_api_response(api_response: Dict) -> str:
        """Extract plain text from API response for backward compatibility"""
        if not api_response.get("success"):
            return ""
        return api_response.get("raw_text", "")
    
    @staticmethod
    def get_cv_skills_from_api_response(api_response: Dict) -> list:
        """Extract skills list from API response"""
        if not api_response.get("success"):
            return []
        return api_response.get("skills", [])

# Global instance
resume_parser_api = ResumeParserAPI()

