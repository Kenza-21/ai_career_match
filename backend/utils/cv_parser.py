import PyPDF2
import docx2txt
from fastapi import UploadFile, HTTPException
import re
from typing import Dict
import io

class CVParser:
    @staticmethod
    def extract_text_from_cv(file: UploadFile) -> str:
        """Extrait le texte d'un CV PDF, DOCX ou TXT"""
        try:
            # Lire le contenu du fichier
            content = file.file.read()
            
            # Réinitialiser pour pouvoir relire
            file.file.seek(0)
            
            if file.filename.lower().endswith(".pdf"):
                return CVParser._extract_from_pdf(content)
            elif file.filename.lower().endswith(".docx"):
                return CVParser._extract_from_docx(content)
            elif file.filename.lower().endswith(".txt"):
                return CVParser._extract_from_txt(content)
            else:
                raise HTTPException(status_code=400, detail="Format non supporté. Utilisez PDF, DOCX ou TXT.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur d'extraction: {str(e)}")
    
    @staticmethod
    def _extract_from_pdf(content: bytes) -> str:
        """Extrait le texte d'un PDF"""
        try:
            # Créer un objet fichier en mémoire
            pdf_file = io.BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Nettoyer le texte
            text = CVParser._clean_extracted_text(text)
            return text
            
        except Exception as e:
            raise Exception(f"Erreur lecture PDF: {str(e)}")
    
    @staticmethod
    def _extract_from_docx(content: bytes) -> str:
        """Extrait le texte d'un DOCX"""
        try:
            # Créer un objet fichier en mémoire
            docx_file = io.BytesIO(content)
            text = docx2txt.process(docx_file)
            return CVParser._clean_extracted_text(text)
        except Exception as e:
            raise Exception(f"Erreur lecture DOCX: {str(e)}")
    
    @staticmethod
    def _extract_from_txt(content: bytes) -> str:
        """Extrait le texte d'un TXT"""
        try:
            text = content.decode('utf-8')
            return CVParser._clean_extracted_text(text)
        except Exception as e:
            raise Exception(f"Erreur lecture TXT: {str(e)}")
    
    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """Nettoie le texte extrait"""
        # Supprimer les caractères non imprimables
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def parse_cv_sections(cv_text: str) -> Dict[str, str]:
        """Parse le CV et extrait les sections automatiquement"""
        sections = {
            "experience": "",
            "education": "", 
            "skills": "",
            "projects": "",
            "summary": "",
            "contact": ""
        }
        
        # Patterns pour détecter les sections
        section_patterns = {
            "experience": r"(EXPÉRIENCE PROFESSIONNELLE|EXPERIENCE|WORK EXPERIENCE|EMPLOI|EMPLOIS|EXPERIENCES)(.*?)(?=EDUCATION|FORMATION|COMPÉTENCES|PROJETS|$)",
            "education": r"(EDUCATION|FORMATION|EDUCATION|DIPLÔMES|DIPLOMES|EDUCATION)(.*?)(?=COMPÉTENCES|EXPERIENCE|PROJETS|$)",
            "skills": r"(COMPÉTENCES|SKILLS|COMPETENCES|APTITUDES|COMPETENCES TECHNIQUES)(.*?)(?=EXPERIENCE|EDUCATION|PROJETS|$)",
            "projects": r"(PROJETS|PROJECTS|RÉALISATIONS|REALISATIONS|PORTFOLIO)(.*?)(?=EXPERIENCE|EDUCATION|COMPÉTENCES|$)",
            "summary": r"(PROFIL|SUMMARY|OBJECTIF|ABOUT|À PROPOS|PROFILE)(.*?)(?=EXPERIENCE|EDUCATION|COMPÉTENCES|$)",
            "contact": r"(CONTACT|COORDONNÉES|COORDONNEES|INFORMATION|INFORMATIONS)(.*?)(?=EXPERIENCE|EDUCATION|PROFILE|$)"
        }
        
        for section, pattern in section_patterns.items():
            match = re.search(pattern, cv_text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section] = match.group(2).strip()
        
        return sections