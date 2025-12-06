import PyPDF2
import docx2txt
from fastapi import UploadFile, HTTPException
import re
import io
from typing import Dict

class CVParser:
    @staticmethod
    def extract_text_from_cv(file: UploadFile) -> str:
        """Extrait le texte d'un CV PDF, DOCX ou TXT"""
        try:
            # Lire le contenu du fichier
            content = file.file.read()
            
            # Réinitialiser pour pouvoir relire
            file.file.seek(0)
            
            # Vérifier l'extension
            filename_lower = file.filename.lower()
            
            if filename_lower.endswith(".pdf"):
                return CVParser._extract_from_pdf(content)
            elif filename_lower.endswith(".docx"):
                return CVParser._extract_from_docx(content)
            elif filename_lower.endswith(".txt"):
                return CVParser._extract_from_txt(content)
            else:
                raise HTTPException(status_code=400, 
                                  detail="Format non supporté. Utilisez PDF, DOCX ou TXT.")
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
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Nettoyer le texte
            text = CVParser._clean_extracted_text(text)
            
            if not text.strip():
                raise Exception("PDF vide ou non lisible")
                
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
            text = CVParser._clean_extracted_text(text)
            
            if not text.strip():
                raise Exception("DOCX vide ou non lisible")
                
            return text
        except Exception as e:
            raise Exception(f"Erreur lecture DOCX: {str(e)}")
    
    @staticmethod
    def _extract_from_txt(content: bytes) -> str:
        """Extrait le texte d'un TXT"""
        try:
            text = content.decode('utf-8', errors='ignore')
            text = CVParser._clean_extracted_text(text)
            
            if not text.strip():
                raise Exception("TXT vide")
                
            return text
        except Exception as e:
            raise Exception(f"Erreur lecture TXT: {str(e)}")
    
    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """Nettoie le texte extrait"""
        if not text:
            return ""
        
        # Remplacer les caractères problématiques
        replacements = {
            '�': '',  # Caractère inconnu
            '\x00': '',  # Null byte
            '\ufffd': '',  # Replacement character
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Supprimer les caractères non imprimables
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Normaliser les sauts de ligne
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
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
            "contact": "",
            "languages": "",
            "certifications": ""
        }
        
        # Normaliser le texte
        cv_text = cv_text.replace('\n', ' ').replace('\r', ' ')
        cv_text = re.sub(r'\s+', ' ', cv_text)
        
        # Patterns pour détecter les sections (français/anglais)
        section_patterns = {
            "experience": r"(EXPERIENCE|EXPÉRIENCE|WORK EXPERIENCE|EMPLOI|EMPLOIS|STAGE|STAGES|PROFESSIONAL EXPERIENCE)(.*?)(?=(EDUCATION|FORMATION|COMPÉTENCES|PROJETS|CERTIFICATIONS|$))",
            "education": r"(EDUCATION|FORMATION|ÉTUDES|DIPLÔMES|ACADÉMIQUE|ACADEMIC)(.*?)(?=(COMPÉTENCES|EXPERIENCE|PROJETS|CERTIFICATIONS|$))",
            "skills": r"(COMPÉTENCES|SKILLS|APTITUDES|TECHNICAL SKILLS|HARD SKILLS|COMPETENCES)(.*?)(?=(EXPERIENCE|EDUCATION|PROJETS|LANGUES|$))",
            "projects": r"(PROJETS|PROJECTS|RÉALISATIONS|PORTFOLIO)(.*?)(?=(EXPERIENCE|EDUCATION|COMPÉTENCES|$))",
            "languages": r"(LANGUES|LANGUAGES|LANGUE)(.*?)(?=(COMPÉTENCES|EXPERIENCE|FORMATION|$))",
            "certifications": r"(CERTIFICATIONS|CERTIFICATS|DIPLÔMES)(.*?)(?=(COMPÉTENCES|EXPERIENCE|FORMATION|$))",
            "summary": r"(PROFIL|SUMMARY|OBJECTIF|ABOUT|À PROPOS|PRÉSENTATION|PROFILE)(.*?)(?=(EXPERIENCE|EDUCATION|COMPÉTENCES|$))"
        }
        
        for section, pattern in section_patterns.items():
            match = re.search(pattern, cv_text, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section] = match.group(2).strip()
        
        # Contact: emails et téléphones (toujours chercher)
        email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,3}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}'
        
        emails = re.findall(email_pattern, cv_text)
        phones = re.findall(phone_pattern, cv_text)
        
        if emails or phones:
            sections["contact"] = f"Emails: {', '.join(emails[:3])} | Téléphones: {', '.join(phones[:2])}"
        else:
            # Chercher dans les premières lignes
            first_lines = cv_text[:500]
            emails = re.findall(email_pattern, first_lines)
            if emails:
                sections["contact"] = f"Email: {emails[0]}"
        
        return sections