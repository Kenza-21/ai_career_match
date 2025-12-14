"""
DEPRECATED: This module is deprecated. All CV parsing is now handled by ResumeParser.app API.

See services/resume_parser_api.py for the new implementation.

This file is kept for backward compatibility only and should not be used for new code.
"""

from typing import Dict
from fastapi import HTTPException

class CVParser:
    """
    DEPRECATED: Use services.resume_parser_api.ResumeParserAPI instead.
    
    This class is kept for backward compatibility but all parsing methods
    have been disabled. All CV parsing must go through ResumeParser.app API.
    """
    
    @staticmethod
    def extract_text_from_cv(file) -> str:
        """DEPRECATED: Use ResumeParser.app API instead"""
        raise HTTPException(
            status_code=501,
            detail="Local CV parsing is disabled. Please use ResumeParser.app API via services.resume_parser_api"
        )
    
    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        """DEPRECATED"""
        raise HTTPException(status_code=501, detail="Local PDF parsing is disabled")
    
    @staticmethod
    def _extract_from_docx(content: bytes) -> str:
        """DEPRECATED"""
        raise HTTPException(status_code=501, detail="Local DOCX parsing is disabled")
    
    @staticmethod
    def _extract_from_txt(content: bytes) -> str:
        """DEPRECATED"""
        raise HTTPException(status_code=501, detail="Local TXT parsing is disabled")
    
    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """DEPRECATED"""
        return text
    
    @staticmethod
    def parse_cv_sections(cv_text: str) -> Dict[str, str]:
        """
        DEPRECATED: This method returns empty sections.
        Use ResumeParser.app API response structure instead.
        """
        return {
            "experience": "",
            "education": "",
            "skills": "",
            "projects": "",
            "summary": "",
            "contact": "",
            "languages": "",
            "certifications": ""
        }
