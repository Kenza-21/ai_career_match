import requests
import base64
import json  # ADD THIS IMPORT
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
            
            # DEBUG: Print file info
            print(f"\nDEBUG: Parsing file: {cv_file.filename}, size: {len(file_content)} bytes")
            
            # Try method 1: Multipart form data (most common for file uploads)
            try:
                files = {
                    "file": (cv_file.filename, file_content, cv_file.content_type or "application/octet-stream")
                }
                headers = {
                    "Authorization": f"Bearer {ResumeParserAPI.API_KEY}"
                }
                
                print("DEBUG: Trying Method 1 (multipart form)...")
                response = requests.post(
                    ResumeParserAPI.API_URL,
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                print(f"DEBUG: Method 1 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    api_data = response.json()
                    # DEBUG: Save and print full response
                    ResumeParserAPI._debug_api_response(api_data)
                    return ResumeParserAPI._format_api_response(api_data)
                else:
                    print(f"DEBUG: Method 1 failed with status {response.status_code}")
                    print(f"DEBUG: Response: {response.text[:500]}")
            except Exception as e1:
                print(f"DEBUG: Method 1 (multipart) failed: {e1}")
            
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
                
                print("\nDEBUG: Trying Method 2 (base64 + bearer)...")
                response = requests.post(
                    ResumeParserAPI.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"DEBUG: Method 2 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    api_data = response.json()
                    # DEBUG: Save and print full response
                    ResumeParserAPI._debug_api_response(api_data)
                    return ResumeParserAPI._format_api_response(api_data)
                else:
                    print(f"DEBUG: Method 2 failed with status {response.status_code}")
                    print(f"DEBUG: Response: {response.text[:500]}")
            except Exception as e2:
                print(f"DEBUG: Method 2 (base64 + bearer) failed: {e2}")
            
            # Try method 3: Base64 in JSON with key in payload
            try:
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                payload = {
                    "file": file_base64,
                    "filename": cv_file.filename,
                    "key": ResumeParserAPI.API_KEY
                }
                
                print("\nDEBUG: Trying Method 3 (base64 + key)...")
                response = requests.post(
                    ResumeParserAPI.API_URL,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                )
                
                print(f"DEBUG: Method 3 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    api_data = response.json()
                    # DEBUG: Save and print full response
                    ResumeParserAPI._debug_api_response(api_data)
                    return ResumeParserAPI._format_api_response(api_data)
                else:
                    error_msg = response.json().get("error", f"API error: {response.status_code}")
                    print(f"DEBUG: Method 3 failed: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "debug": {
                            "method": 3,
                            "status": response.status_code,
                            "response": response.text[:500]
                        }
                    }
            except Exception as e3:
                print(f"DEBUG: Method 3 (base64 + key) failed: {e3}")
                return {
                    "success": False,
                    "error": f"All API methods failed. Last error: {str(e3)}",
                    "debug": {
                        "method": 3,
                        "error": str(e3)
                    }
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error calling ResumeParser API: {str(e)}",
                "debug": {"network_error": True}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing CV: {str(e)}",
                "debug": {"general_error": True}
            }
    
    @staticmethod
    def _debug_api_response(api_data: Dict):
        """Save and print full API response for debugging"""
        print("\n" + "="*80)
        print("DEBUG: FULL RESUMEPARSER.APP API RESPONSE")
        print("="*80)
        
        # Save full response to file
        with open("debug_api_response.json", "w", encoding="utf-8") as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: Saved full response to debug_api_response.json")
        
        # Print structure
        parsed = api_data.get("parsed", {})
        print(f"\nDEBUG: Top-level keys in response: {list(api_data.keys())}")
        print(f"DEBUG: Keys in 'parsed' object: {list(parsed.keys())}")
        
        # Print counts
        print(f"\nDEBUG: Counts in parsed data:")
        print(f"  - employment_history: {len(parsed.get('employment_history', []))}")
        print(f"  - education: {len(parsed.get('education', []))}")
        print(f"  - skills: {len(parsed.get('skills', []))}")
        print(f"  - languages: {len(parsed.get('languages', []))}")
        print(f"  - certifications: {len(parsed.get('certifications', []))}")
        print(f"  - courses: {len(parsed.get('courses', []))}")
        
        # Look for projects or similar
        all_keys = list(parsed.keys())
        print(f"\nDEBUG: All keys in 'parsed': {all_keys}")
        
        # Check for any key that might contain projects
        project_like_keys = [k for k in all_keys if 'project' in k.lower() or 'portfolio' in k.lower()]
        if project_like_keys:
            print(f"DEBUG: Found project-like keys: {project_like_keys}")
        
        # Print first employment entry for inspection
        if parsed.get("employment_history"):
            print(f"\nDEBUG: First employment entry:")
            first_job = parsed["employment_history"][0]
            for key, value in first_job.items():
                if isinstance(value, list):
                    print(f"  {key}: list with {len(value)} items")
                    if value and isinstance(value[0], str):
                        print(f"    Sample: {value[:3]}")
                else:
                    print(f"  {key}: {str(value)[:100]}")
        
        print("="*80 + "\n")
    
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
        
        # Look for projects in various places
        projects = []
        
        # 1. Check for dedicated projects field
        if "projects" in parsed and isinstance(parsed["projects"], list):
            projects = parsed["projects"]
        elif "personal_projects" in parsed and isinstance(parsed["personal_projects"], list):
            projects = parsed["personal_projects"]
        elif "academic_projects" in parsed and isinstance(parsed["academic_projects"], list):
            projects = parsed["academic_projects"]
        
        # 2. Check employment history for project-like roles
        if not projects:
            for job in parsed.get("employment_history", []):
                job_title = job.get("title", "").lower()
                # Look for internship, project, research roles
                if any(keyword in job_title for keyword in ["project", "intern", "research", "thesis", "capstone","Projets académiques","Projets personnels"]):
                    project_data = {
                        "title": job.get("title", ""),
                        "description": f"At {job.get('company', 'Company')}: " + 
                                      ". ".join(job.get("responsibilities", [])),
                        "technologies": ", ".join(job.get("skills", [])) if job.get("skills") else ""
                    }
                    projects.append(project_data)
        
        # 3. If still no projects, create placeholder from skills
        if not projects and parsed.get("skills"):
            projects = [{
                "title": "Technical Projects Portfolio",
                "description": f"Applied skills in {', '.join(parsed['skills'][:5])} through various academic and personal projects.",
                "technologies": ", ".join(parsed["skills"][:10])
            }]
        
        print(f"DEBUG: Extracted {len(projects)} projects")
        
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
            "languages": parsed.get("languages", []),
            "certifications": parsed.get("certifications", []),
            "courses": parsed.get("courses", []),
            "projects": projects,  # ADD THIS
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