"""
Google Gemini ATS Resume Evaluator
Uses Google Gemini API to perform comprehensive ATS-style resume evaluation
"""
import json
import re
from typing import Dict, Optional
import google.generativeai as genai

# API Key

GEMINI_API_KEY = "wx"
# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class GeminiATSEvaluator:
    """ATS Resume Evaluator using Google Gemini"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def evaluate_resume(self, resume_text: str) -> Dict:
        """
        Evaluate resume using Google Gemini
        
        Args:
            resume_text: The resume text to analyze
            
        Returns:
            Dictionary with ATS evaluation results
        """
        if not resume_text or not resume_text.strip():
            return {
                "success": False,
                "error": "Resume text is empty"
            }
        
        try:
            # Build prompt using f-string to avoid format() issues with JSON braces
            prompt = f"""
        You are an expert ATS (Applicant Tracking System) resume reviewer. Analyze the resume below across these categories:

        1. Contact Information  
        2. Spelling & Grammar  
        3. Personal Pronoun Usage  
        4. Skills & Keyword Targeting  
        5. Complex or Long Sentences  
        6. Generic or Weak Phrases  
        7. Passive Voice Usage  
        8. Quantified Achievements  
        9. Required Resume Sections  
        10. AI-generated Language  
        11. Repeated Action Verbs  
        12. Visual Formatting or Readability  
        13. Personal Information / Bias Triggers  
        14. Other Strengths and Weaknesses  

        Return a **single valid JSON object**, and nothing else.

        The structure must follow this strict format:

        {{
        "ATS_Score": (Analyse thoroughly and allot an ATS score to the resume, integer from 0 to 100),
        "Contact Information": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Spelling & Grammar": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Personal Pronoun Usage": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Skills & Keyword Targeting": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Complex or Long Sentences": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Generic or Weak Phrases": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Passive Voice Usage": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Quantified Achievements": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Required Resume Sections": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "AI-generated Language": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Repeated Action Verbs": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Visual Formatting or Readability": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Personal Information / Bias Triggers": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }},
        "Other Strengths and Weaknesses": {{
            "Positives": ["..."],
            "Negatives": ["..."]
        }}
        }}

        Rules:
            -   You MUST return valid JSON that can be parsed directly by Python's json.loads()
            -   Use double quotes for all keys and string values
            -   Do NOT include trailing commas
            -   Do NOT skip either the "Positives" or "Negatives" key — include both, even if the value is an empty list ([])
            -   Do NOT break the format or insert partial structures like "Positives": [], }}
            -   Do NOT output markdown, comments, explanations, or headings
            -   The ONLY output should be a clean JSON object (no preamble, no explanation)
            -   Every "Positives" and "Negatives" list should contain detailed, constructive, and example-backed feedback
            -   Be thorough and professionally critical, but fair

        Resume Text:
        {resume_text}
        """
            
            # Generate response using Gemini
            print("🔍 Analyzing resume with Google Gemini...")
            response = self.model.generate_content(prompt)
            
            # Extract text from response
            raw_text = response.text.strip()
            
            # Find JSON block in response
            json_start = raw_text.find("{")
            json_end = raw_text.rfind("}") + 1
            
            if json_start == -1 or json_end == -1:
                print(f"⚠️ No JSON block detected in response")
                print(f"Response: {raw_text[:500]}")
                return {
                    "success": False,
                    "error": "No JSON block detected in AI response"
                }
            
            json_str = raw_text[json_start:json_end]
            
            # Parse JSON
            try:
                evaluation_result = json.loads(json_str)
            except json.JSONDecodeError as json_err:
                print(f"⚠️ JSON parsing error: {json_err}")
                print(f"JSON string: {json_str[:500]}")
                return {
                    "success": False,
                    "error": f"Failed to parse AI response as JSON: {str(json_err)}"
                }
            
            # Validate structure
            evaluation_result = self._validate_structure(evaluation_result)
            
            return {
                "success": True,
                "evaluation": evaluation_result,
                "ats_score": evaluation_result.get("ATS_Score", 0)
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error in Gemini ATS evaluation: {error_details}")
            return {
                "success": False,
                "error": str(e),
                "error_details": error_details
            }
    
    
    def _validate_structure(self, data: Dict) -> Dict:
        """Validate and ensure the response has the correct structure"""
        required_categories = [
            "Contact Information",
            "Spelling & Grammar",
            "Personal Pronoun Usage",
            "Skills & Keyword Targeting",
            "Complex or Long Sentences",
            "Generic or Weak Phrases",
            "Passive Voice Usage",
            "Quantified Achievements",
            "Required Resume Sections",
            "AI-generated Language",
            "Repeated Action Verbs",
            "Visual Formatting or Readability",
            "Personal Information / Bias Triggers",
            "Other Strengths and Weaknesses"
        ]
        
        # Ensure ATS_Score exists
        if "ATS_Score" not in data:
            data["ATS_Score"] = 0
        
        # Ensure all categories exist with Positives and Negatives
        for category in required_categories:
            if category not in data:
                data[category] = {"Positives": [], "Negatives": []}
            else:
                if "Positives" not in data[category]:
                    data[category]["Positives"] = []
                if "Negatives" not in data[category]:
                    data[category]["Negatives"] = []
        
        return data


# Global instance
gemini_ats_evaluator = GeminiATSEvaluator()
