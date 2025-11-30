import re
from typing import Dict, List, Tuple
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CareerAssistant:
    def __init__(self):
        # Patterns pour comprendre l'intention utilisateur
        self.patterns = {
            'stage': [r'stage', r'stagi', r'intern', r'alternance', r'apprentissage'],
            'debutant': [r'débutant', r'junior', r'premier emploi', r'sans expérience'],
            'remote': [r'remote', r'télétravail', r'à distance', r'teletravail'],
            'ville': [r'à (\w+)', r'sur (\w+)', r'casablanca', r'rabat', r'marrakech', r'tanger'],
            'competences': [r'compétence en (\w+)', r'savoir (\w+)', r'connaissance en (\w+)']
        }
        
        # Mapping des intentions vers des requêtes de recherche
        self.intent_mapping = {
            'stage': 'stage alternance',
            'debutant': 'junior débutant',
            'remote': 'remote télétravail',
            'ville': ''  # Sera rempli dynamiquement
        }
    
    def analyze_query(self, user_message: str) -> Dict:
        """Analyse le message utilisateur et extrait les intentions"""
        user_message = user_message.lower()
        
        analysis = {
            'original_message': user_message,
            'intentions': [],
            'competences': [],
            'lieu': None,
            'type_contrat': 'CDI',  # Par défaut
            'experience_level': None,
            'search_query': ''
        }
        
        # Détection des intentions
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_message):
                    if intent not in analysis['intentions']:
                        analysis['intentions'].append(intent)
        
        # Extraction des compétences spécifiques
        competence_keywords = ['développeur', 'web', 'mobile', 'data', 'marketing', 'design', 'comptable', 'infirmier']
        for keyword in competence_keywords:
            if keyword in user_message:
                analysis['competences'].append(keyword)
        
        # Extraction du lieu
        ville_match = re.search(r'à (\w+)', user_message)
        if ville_match:
            analysis['lieu'] = ville_match.group(1)
        
        # Construction de la requête de recherche optimisée
        query_parts = []
        
        # Ajouter les compétences
        if analysis['competences']:
            query_parts.extend(analysis['competences'])
        
        # Ajouter les intentions spécifiques
        for intent in analysis['intentions']:
            if intent in self.intent_mapping and self.intent_mapping[intent]:
                query_parts.append(self.intent_mapping[intent])
        
        # Construire la requête finale
        analysis['search_query'] = ' '.join(query_parts) if query_parts else user_message
        
        return analysis
    
    def generate_response(self, user_message: str, search_results: List[Dict]) -> Dict:
        """Génère une réponse naturelle avec les résultats - VERSION CORRIGÉE"""
        analysis = self.analyze_query(user_message)
        
        # Convertir les objets JobMatch en dictionnaires pour l'analyse
        jobs_as_dicts = []
        for job in search_results:
            if hasattr(job, 'dict'):  # Si c'est un objet Pydantic
                job_dict = job.dict()
            else:  # Si c'est déjà un dictionnaire
                job_dict = job
            jobs_as_dicts.append(job_dict)
        
        # Statistiques des résultats
        total_jobs = len(jobs_as_dicts)
        high_match_jobs = [job for job in jobs_as_dicts if job.get('match_score', 0) > 0.7]
        
        # Construction de la réponse
        response = {
            "analysis": analysis,
            "summary": {
                "total_matches": total_jobs,
                "high_quality_matches": len(high_match_jobs),
                "detected_skills": analysis['competences'],
                "detected_intentions": analysis['intentions']
            },
            "search_query_used": analysis['search_query'],
            "jobs": search_results,  # Garder les objets originaux pour la réponse
            "suggestions": self._generate_suggestions(analysis, jobs_as_dicts)  # Utiliser les dicts pour l'analyse
        }
        
        return response
    
    def _generate_suggestions(self, analysis: Dict, jobs: List[Dict]) -> List[str]:
        """Génère des suggestions basées sur l'analyse"""
        suggestions = []
        
        if not jobs:
            suggestions.append("Aucun emploi trouvé. Essayez d'élargir vos critères de recherche.")
            return suggestions
        
        # Suggestion basée sur le nombre de résultats
        if len(jobs) < 3:
            suggestions.append("Peu de résultats. Essayez avec des termes plus généraux comme 'développeur' ou 'marketing'.")
        
        # Suggestion basée sur les compétences détectées
        if analysis['competences']:
            suggestions.append(f"Compétences détectées: {', '.join(analysis['competences'])}")
        
        # Suggestion pour les stages
        if 'stage' in analysis['intentions'] and len([j for j in jobs if 'stage' in j.get('job_title', '').lower()]) == 0:
            suggestions.append("Pour plus de stages, visitez directement les sites des entreprises ou les plateformes spécialisées.")
        
        return suggestions

# Instance globale de l'assistant
career_assistant = CareerAssistant()