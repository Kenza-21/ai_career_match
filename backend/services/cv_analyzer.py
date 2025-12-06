import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CVAnalyzer:
    def __init__(self):
        print("🔧 Initialisation de CVAnalyzer...")
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['le', 'la', 'les', 'de', 'des', 'du', 'et', 'en', 'au', 'aux', 'à', 'dans', 'pour'],
            ngram_range=(1, 2)
        )
        
        # Compétences techniques étendues (sans NLTK)
        self.technical_skills = [
            # Langages
            "python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "swift", "kotlin", "typescript",
            # Frontend
            "react", "angular", "vue", "svelte", "html", "css", "sass", "bootstrap", "tailwind", "jquery",
            # Backend
            "node.js", "django", "flask", "spring", "laravel", "express", "fastapi", "ruby on rails",
            # Bases de données
            "sql", "mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite",
            # Cloud & DevOps
            "aws", "azure", "google cloud", "docker", "kubernetes", "jenkins", "terraform",
            # Data Science
            "machine learning", "deep learning", "data science", "ai", "nlp", "tensorflow", "pytorch",
            # Mobile
            "react native", "flutter", "android", "ios",
            # Outils
            "git", "github", "gitlab", "jira", "figma", "photoshop"
        ]
        print("✅ CVAnalyzer initialisé avec succès")

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extrait les compétences techniques d'un texte"""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.technical_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))

    def calculate_match_score(self, cv_text: str, job_description: str) -> float:
        """Calcule le score de matching entre CV et offre"""
        try:
            vectors = self.vectorizer.fit_transform([cv_text, job_description])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return round(similarity, 2)
        except Exception as e:
            print(f"❌ Erreur calcul similarité: {e}")
            return 0.0

    def identify_skill_gaps(self, cv_skills: List[str], job_skills: List[str]) -> List[Dict]:
        """Identifie les écarts de compétences"""
        missing_skills = [skill for skill in job_skills if skill not in cv_skills]
        
        skill_gaps = []
        for skill in missing_skills:
            # Déterminer la sévérité
            high_priority = ["python", "javascript", "react", "sql", "aws", "java"]
            gap_severity = "high" if skill in high_priority else "medium"
            
            skill_gaps.append({
                "skill_name": skill,
                "required_level": "Requis",
                "current_level": "Manquant",
                "gap_severity": gap_severity
            })
        
        return skill_gaps

    def get_training_recommendations(self, missing_skills: List[str]) -> List[Dict]:
        """Retourne des recommandations de formations (sans web scraping pour l'instant)"""
        recommendations = []
        
        # Base de formations statique (vous pourrez ajouter le scraping plus tard)
        courses_db = {
            "python": [
                {"platform": "Coursera", "name": "Python for Everybody", "url": "https://coursera.org/specializations/python", "duration": "3 months"},
                {"platform": "Udemy", "name": "Complete Python Bootcamp", "url": "https://udemy.com/python", "duration": "2 months"}
            ],
            "javascript": [
                {"platform": "Coursera", "name": "JavaScript Basics", "url": "https://coursera.org/learn/javascript", "duration": "1 month"},
                {"platform": "Udemy", "name": "Modern JavaScript", "url": "https://udemy.com/javascript", "duration": "2 months"}
            ],
            "react": [
                {"platform": "Coursera", "name": "Front-End with React", "url": "https://coursera.org/learn/react", "duration": "1 month"},
                {"platform": "Udemy", "name": "React Complete Guide", "url": "https://udemy.com/react", "duration": "3 months"}
            ],
            "sql": [
                {"platform": "Coursera", "name": "SQL for Data Science", "url": "https://coursera.org/learn/sql", "duration": "1 month"}
            ],
            "aws": [
                {"platform": "Coursera", "name": "AWS Fundamentals", "url": "https://coursera.org/learn/aws", "duration": "2 months"}
            ]
        }
        
        for skill in missing_skills[:3]:  # Max 3 compétences
            if skill in courses_db:
                for course in courses_db[skill][:2]:  # Max 2 cours par compétence
                    recommendations.append({
                        "skill": skill,
                        "platform": course["platform"],
                        "course_name": course["name"],
                        "url": course["url"],
                        "duration": course["duration"],
                        "level": "Beginner",
                        "source": "database"
                    })
        
        return recommendations

    def generate_key_phrases(self, job_skills: List[str], cv_skills: List[str]) -> List[Dict]:
        """Génère des phrases clés pour le CV"""
        key_phrases = []
        
        phrases_dict = {
            "python": "Développement d'applications Python robustes et maintenables",
            "javascript": "Création d'interfaces utilisateur dynamiques avec JavaScript",
            "react": "Développement de composants React réutilisables et performants",
            "sql": "Conception et optimisation de bases de données SQL",
            "machine learning": "Implémentation de modèles de machine learning",
            "aws": "Déploiement et gestion d'infrastructures cloud AWS",
            "docker": "Containerisation d'applications avec Docker",
            "git": "Gestion de versions collaborative avec Git"
        }
        
        for skill in job_skills[:5]:  # 5 premières compétences
            if skill not in cv_skills and skill in phrases_dict:
                key_phrases.append({
                    "skill": skill,
                    "current_situation": f"Compétence '{skill}' non mentionnée",
                    "suggested_phrase": phrases_dict[skill],
                    "section": "Expérience ou Compétences"
                })
        
        return key_phrases

    def generate_ats_recommendations(self, cv_text: str, job_description: str) -> List[Dict]:
        """Génère des recommandations pour l'optimisation ATS"""
        recommendations = []
        
        # Vérification mots-clés
        job_skills = self.extract_skills_from_text(job_description)
        cv_skills = self.extract_skills_from_text(cv_text)
        missing_keywords = [skill for skill in job_skills if skill not in cv_skills]
        
        if missing_keywords:
            recommendations.append({
                "type": "Mots-clés manquants",
                "issue": f"{len(missing_keywords)} compétences manquantes",
                "solution": f"Ajouter: {', '.join(missing_keywords[:3])}",
                "priority": "Haute"
            })
        
        # Vérification contact
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cv_text):
            recommendations.append({
                "type": "Contact",
                "issue": "Email manquant",
                "solution": "Ajouter une section contact avec email",
                "priority": "Haute"
            })
        
        return recommendations

    def analyze_cv_vs_job(self, cv_text: str, job_description: str) -> Dict:
        """Analyse complète CV vs Offre d'emploi"""
        print("🔍 Début de l'analyse CV...")
        
        # Extraction compétences
        cv_skills = self.extract_skills_from_text(cv_text)
        job_skills = self.extract_skills_from_text(job_description)
        
        print(f"✅ Compétences CV: {cv_skills}")
        print(f"✅ Compétences Offre: {job_skills}")
        
        # Calcul matching
        match_score = self.calculate_match_score(cv_text, job_description)
        
        # Analyse écarts
        skill_gaps = self.identify_skill_gaps(cv_skills, job_skills)
        missing_skills = [gap["skill_name"] for gap in skill_gaps]
        
        # Recommandations
        training_recommendations = self.get_training_recommendations(missing_skills)
        key_phrases = self.generate_key_phrases(job_skills, cv_skills)
        ats_recommendations = self.generate_ats_recommendations(cv_text, job_description)
        
        # Évaluation globale
        if match_score >= 0.7:
            assessment = "✅ Excellent matching - Candidature recommandée"
        elif match_score >= 0.5:
            assessment = "⚠️ Bon matching - Quelques compétences à développer"
        else:
            assessment = "❌ Matching faible - Formation recommandée"
        
        print(f"✅ Analyse terminée - Score: {match_score}")
        
        return {
            "match_score": match_score,
            "cv_skills": cv_skills,
            "job_skills": job_skills,
            "skill_gaps": skill_gaps,
            "missing_skills": missing_skills,
            "training_recommendations": training_recommendations,
            "key_phrases": key_phrases,
            "ats_recommendations": ats_recommendations,
            "overall_assessment": assessment
        }

# Instance globale
cv_analyzer = CVAnalyzer()