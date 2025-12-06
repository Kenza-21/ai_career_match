import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CVAnalyzer:
    def __init__(self):
        print("🔧 Initialisation de CVAnalyzer amélioré...")
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['le', 'la', 'les', 'de', 'des', 'du', 'et', 'en', 'au', 'aux', 'à', 'dans', 'pour'],
            ngram_range=(1, 2)
        )
        
        # Compétences techniques étendues
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
        
        # 🔥 NOUVEAU : Compétences par domaine pour mieux extraire de l'offre
        self.domain_keywords = {
            "data_science": ["python", "sql", "machine learning", "data analysis", "pandas", "numpy", "tensorflow", "pytorch", "data science"],
            "web_development": ["javascript", "react", "html", "css", "node.js", "typescript", "vue", "angular", "frontend", "backend"],
            "mobile": ["android", "ios", "flutter", "react native", "kotlin", "swift", "mobile"],
            "cloud_devops": ["aws", "azure", "docker", "kubernetes", "jenkins", "terraform", "cloud", "devops"],
            "backend": ["java", "spring", "python", "django", "flask", "sql", "mongodb", "api", "rest"]
        }
        
        print("✅ CVAnalyzer amélioré initialisé avec succès")

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extrait les compétences techniques d'un texte"""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.technical_skills:
            # Recherche avec word boundaries pour éviter les faux positifs
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))

    def extract_skills_from_job_description(self, job_description: str) -> List[str]:
        """🔥 NOUVEAU : Extrait mieux les compétences d'une description d'offre"""
        job_skills = []
        job_lower = job_description.lower()
        
        # 1. Rechercher les compétences techniques exactes
        for skill in self.technical_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, job_lower):
                job_skills.append(skill)
        
        # 2. Rechercher par domaines si peu de compétences trouvées
        if len(job_skills) < 3:
            for domain, keywords in self.domain_keywords.items():
                domain_matches = [kw for kw in keywords if kw in job_lower]
                if len(domain_matches) >= 2:  # Au moins 2 mots-clés du domaine
                    job_skills.extend(domain_matches)
        
        # 3. Rechercher des patterns communs dans les offres
        common_patterns = [
            r"expérience en (\w+)", r"connaissance en (\w+)", r"maîtrise de (\w+)",
            r"compétences en (\w+)", r"savoir (\w+)", r"expérience avec (\w+)"
        ]
        
        for pattern in common_patterns:
            matches = re.findall(pattern, job_lower)
            for match in matches:
                if isinstance(match, str) and match in self.technical_skills:
                    job_skills.append(match)
        
        # Dédoublonnage et limitation
        unique_skills = list(set(job_skills))
        return unique_skills[:15]  # Limiter à 15 compétences max

    def calculate_match_score_improved(self, cv_skills: List[str], job_skills: List[str], cv_text: str, job_text: str) -> Dict:
        """🔥 NOUVEAU : Calcule un score de matching amélioré avec détails"""
        
        if not job_skills:
            # Fallback : calculer avec TF-IDF sur le texte complet
            try:
                vectors = self.vectorizer.fit_transform([cv_text, job_text])
                tfidf_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                return {
                    "final_score": round(tfidf_score, 2),
                    "method": "tfidf_fallback",
                    "cv_skills_count": len(cv_skills),
                    "job_skills_count": 0,
                    "common_skills_count": 0,
                    "coverage_percentage": 0
                }
            except:
                return {
                    "final_score": 0.0,
                    "method": "no_skills_detected",
                    "cv_skills_count": len(cv_skills),
                    "job_skills_count": 0,
                    "common_skills_count": 0,
                    "coverage_percentage": 0
                }
        
        # Calcul basé sur les compétences
        common_skills = set(cv_skills) & set(job_skills)
        coverage = len(common_skills) / len(job_skills) if job_skills else 0
        
        # Pondération par importance
        important_skills = ["python", "javascript", "java", "sql", "react", "aws", "docker", "machine learning"]
        important_common = [skill for skill in common_skills if skill in important_skills]
        important_score = len(important_common) / len([s for s in job_skills if s in important_skills]) if any(s in important_skills for s in job_skills) else 0
        
        # Score final
        skill_based_score = coverage * 0.6 + important_score * 0.4
        
        # Combiner avec TF-IDF pour plus de robustesse
        try:
            vectors = self.vectorizer.fit_transform([cv_text, job_text])
            tfidf_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            final_score = skill_based_score * 0.7 + tfidf_score * 0.3
        except:
            final_score = skill_based_score
        
        return {
            "final_score": round(final_score, 2),
            "method": "skills_analysis",
            "cv_skills_count": len(cv_skills),
            "job_skills_count": len(job_skills),
            "common_skills_count": len(common_skills),
            "coverage_percentage": round(coverage * 100, 1),
            "important_matches": important_common
        }

    def identify_skill_gaps(self, cv_skills: List[str], job_skills: List[str]) -> List[Dict]:
        """Identifie les écarts de compétences avec plus de détails"""
        missing_skills = [skill for skill in job_skills if skill not in cv_skills]
        
        skill_gaps = []
        for skill in missing_skills:
            # Déterminer l'importance
            if skill in ["python", "javascript", "sql", "aws", "react", "java"]:
                gap_severity = "high"
                importance = "Essentielle"
            elif skill in ["docker", "kubernetes", "typescript", "node.js", "machine learning"]:
                gap_severity = "medium"
                importance = "Importante"
            else:
                gap_severity = "low"
                importance = "Secondaire"
            
            skill_gaps.append({
                "skill_name": skill,
                "required_level": "Demandée dans l'offre",
                "current_level": "Non présente dans le CV",
                "gap_severity": gap_severity,
                "importance": importance,
                "suggestion": f"Considérez une formation en {skill}"
            })
        
        return skill_gaps

    def get_training_recommendations(self, missing_skills: List[str]) -> List[Dict]:
        """Retourne des recommandations de formations améliorées"""
        recommendations = []
        
        # Base de formations enrichie
        courses_db = {
            "python": [
                {"platform": "Coursera", "name": "Python for Everybody", "url": "https://coursera.org/specializations/python", "duration": "3 months", "level": "Beginner"},
                {"platform": "Udemy", "name": "Complete Python Bootcamp", "url": "https://www.udemy.com/course/complete-python-bootcamp/", "duration": "22 hours", "level": "Beginner"}
            ],
            "javascript": [
                {"platform": "Coursera", "name": "JavaScript Basics", "url": "https://coursera.org/learn/javascript", "duration": "1 month", "level": "Beginner"},
                {"platform": "freeCodeCamp", "name": "JavaScript Algorithms", "url": "https://freecodecamp.org/learn/javascript-algorithms", "duration": "300 hours", "level": "Intermediate"}
            ],
            "react": [
                {"platform": "Coursera", "name": "Front-End with React", "url": "https://coursera.org/learn/react", "duration": "1 month", "level": "Intermediate"},
                {"platform": "Scrimba", "name": "Learn React", "url": "https://scrimba.com/learn/learnreact", "duration": "12 hours", "level": "Beginner"}
            ],
            "sql": [
                {"platform": "Coursera", "name": "SQL for Data Science", "url": "https://coursera.org/learn/sql-for-data-science", "duration": "1 month", "level": "Beginner"},
                {"platform": "Khan Academy", "name": "Intro to SQL", "url": "https://khanacademy.org/computing/computer-programming/sql", "duration": "15 hours", "level": "Beginner"}
            ],
            "aws": [
                {"platform": "Coursera", "name": "AWS Fundamentals", "url": "https://coursera.org/specializations/aws-fundamentals", "duration": "2 months", "level": "Beginner"},
                {"platform": "AWS Training", "name": "AWS Cloud Practitioner", "url": "https://aws.amazon.com/training/", "duration": "6 hours", "level": "Beginner"}
            ],
            "docker": [
                {"platform": "Udemy", "name": "Docker Mastery", "url": "https://www.udemy.com/course/docker-mastery/", "duration": "20 hours", "level": "Intermediate"},
                {"platform": "Docker Docs", "name": "Get Started with Docker", "url": "https://docs.docker.com/get-started/", "duration": "3 hours", "level": "Beginner"}
            ],
            "machine learning": [
                {"platform": "Coursera", "name": "Machine Learning by Andrew Ng", "url": "https://coursera.org/learn/machine-learning", "duration": "3 months", "level": "Intermediate"},
                {"platform": "fast.ai", "name": "Practical Deep Learning", "url": "https://course.fast.ai/", "duration": "2 months", "level": "Intermediate"}
            ]
        }
        
        for skill in missing_skills[:4]:  # Max 4 compétences
            if skill in courses_db:
                for course in courses_db[skill][:2]:  # Max 2 cours par compétence
                    recommendations.append({
                        "skill": skill,
                        "platform": course["platform"],
                        "course_name": course["name"],
                        "url": course["url"],
                        "duration": course["duration"],
                        "level": course["level"],
                        "source": "curated_database",
                        "priority": "high" if skill in ["python", "javascript", "sql"] else "medium"
                    })
        
        return recommendations

    def generate_key_phrases(self, job_skills: List[str], cv_skills: List[str]) -> List[Dict]:
        """Génère des phrases clés pour le CV avec plus de variété"""
        key_phrases = []
        
        phrases_dict = {
            "python": [
                "Développement d'applications Python robustes et maintenables",
                "Implémentation de solutions Python pour résoudre des problèmes complexes"
            ],
            "javascript": [
                "Création d'interfaces utilisateur dynamiques avec JavaScript moderne",
                "Développement d'applications web interactives avec JavaScript/TypeScript"
            ],
            "react": [
                "Développement de composants React réutilisables avec hooks et state management",
                "Création d'interfaces utilisateur performantes avec React et écosystème moderne"
            ],
            "sql": [
                "Conception et optimisation de bases de données relationnelles avec SQL",
                "Requêtage et modélisation de données avec SQL pour applications business"
            ],
            "aws": [
                "Déploiement et gestion d'infrastructures cloud scalables sur AWS",
                "Configuration de services AWS pour applications haute disponibilité"
            ],
            "docker": [
                "Containerisation d'applications avec Docker pour déploiement reproductible",
                "Création et gestion d'environnements Docker pour développement et production"
            ],
            "git": [
                "Gestion de versions collaborative avec Git et bonnes pratiques de branching",
                "Workflow Git pour développement collaboratif et intégration continue"
            ],
            "machine learning": [
                "Implémentation de modèles de machine learning pour résoudre des problèmes business",
                "Développement de pipelines data science avec preprocessing et modélisation"
            ]
        }
        
        for skill in job_skills[:6]:  # 6 premières compétences
            if skill not in cv_skills and skill in phrases_dict:
                phrases = phrases_dict[skill]
                key_phrases.append({
                    "skill": skill,
                    "current_situation": f"Compétence '{skill}' non mentionnée dans le CV",
                    "suggested_phrases": phrases,
                    "recommended_sections": ["Expérience professionnelle", "Compétences techniques", "Projets"],
                    "impact": "Améliorer la pertinence pour les systèmes ATS"
                })
        
        return key_phrases

    def generate_ats_recommendations(self, cv_text: str, job_description: str) -> List[Dict]:
        """Génère des recommandations détaillées pour l'optimisation ATS"""
        recommendations = []
        
        cv_skills = self.extract_skills_from_text(cv_text)
        job_skills = self.extract_skills_from_job_description(job_description)
        missing_keywords = [skill for skill in job_skills if skill not in cv_skills]
        
        # 1. Mots-clés manquants
        if missing_keywords:
            recommendations.append({
                "category": "Optimisation Mots-clés",
                "issue": f"{len(missing_keywords)} compétences demandées non présentes",
                "solution": f"Ajouter ces compétences clés: {', '.join(missing_keywords[:5])}",
                "priority": "Élevée",
                "action_items": [
                    "Inclure dans la section Compétences techniques",
                    "Mentionner dans les descriptions d'expérience",
                    "Ajouter dans le profil/summary"
                ]
            })
        
        # 2. Structure et format
        word_count = len(cv_text.split())
        if word_count > 800:
            recommendations.append({
                "category": "Structure du CV",
                "issue": f"CV trop long ({word_count} mots), risque de rejet ATS",
                "solution": "Réduire à 400-600 mots maximum",
                "priority": "Moyenne",
                "action_items": [
                    "Être concis dans les descriptions",
                    "Privilégier les phrases courtes",
                    "Supprimer les informations redondantes"
                ]
            })
        
        # 3. Contact et informations clés
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cv_text):
            recommendations.append({
                "category": "Informations de contact",
                "issue": "Email manquant dans le CV",
                "solution": "Ajouter une section contact avec email professionnel",
                "priority": "Élevée",
                "action_items": ["Ajouter email en haut du CV", "Inclure téléphone et LinkedIn si disponible"]
            })
        
        # 4. Chiffres et résultats
        number_count = len(re.findall(r'\b\d+\b', cv_text))
        if number_count < 3:
            recommendations.append({
                "category": "Quantification des résultats",
                "issue": "Peu de chiffres pour démontrer l'impact",
                "solution": "Ajouter des chiffres concrets (%, €, nombre de personnes, etc.)",
                "priority": "Moyenne",
                "action_items": [
                    "Quantifier les réalisations",
                    "Utiliser des pourcentages d'amélioration",
                    "Mentionner des chiffres business"
                ]
            })
        
        return recommendations

    def analyze_cv_vs_job(self, cv_text: str, job_description: str) -> Dict:
        """Analyse complète CV vs Offre d'emploi - VERSION AMÉLIORÉE"""
        print("🔍 Début de l'analyse CV améliorée...")
        
        # Extraction compétences
        cv_skills = self.extract_skills_from_text(cv_text)
        job_skills = self.extract_skills_from_job_description(job_description)  # 🔥 NOUVEAU
        
        print(f"✅ Compétences CV: {len(cv_skills)} trouvées")
        print(f"✅ Compétences Offre: {job_skills}")
        
        # 🔥 NOUVEAU : Calcul du matching amélioré
        score_analysis = self.calculate_match_score_improved(cv_skills, job_skills, cv_text, job_description)
        match_score = score_analysis["final_score"]
        
        # Analyse écarts
        skill_gaps = self.identify_skill_gaps(cv_skills, job_skills)
        missing_skills = [gap["skill_name"] for gap in skill_gaps]
        
        # Recommandations
        training_recommendations = self.get_training_recommendations(missing_skills)
        key_phrases = self.generate_key_phrases(job_skills, cv_skills)
        ats_recommendations = self.generate_ats_recommendations(cv_text, job_description)
        
        # Évaluation globale détaillée
        if match_score >= 0.7:
            assessment = "✅ Excellent matching - Candidature fortement recommandée"
            confidence = "Élevée"
        elif match_score >= 0.5:
            assessment = "⚠️ Bon matching - Quelques compétences à développer"
            confidence = "Moyenne"
        elif match_score >= 0.3:
            assessment = "⚠️ Matching moyen - Formation recommandée avant candidature"
            confidence = "Faible"
        else:
            assessment = "❌ Faible matching - Envisagez d'autres offres plus alignées"
            confidence = "Très faible"
        
        print(f"✅ Analyse terminée - Score: {match_score} - Méthode: {score_analysis['method']}")
        
        return {
            "match_score": match_score,
            "score_analysis": score_analysis,
            "cv_skills": cv_skills[:20],  # Limiter l'affichage
            "job_skills": job_skills,
            "skill_gaps": skill_gaps,
            "missing_skills": missing_skills,
            "training_recommendations": training_recommendations[:5],
            "key_phrases": key_phrases[:5],
            "ats_recommendations": ats_recommendations[:3],
            "overall_assessment": assessment,
            "confidence_level": confidence,
            "summary": {
                "cv_skills_count": len(cv_skills),
                "job_skills_count": len(job_skills),
                "common_skills": list(set(cv_skills) & set(job_skills))[:10],
                "coverage": f"{score_analysis.get('coverage_percentage', 0)}% des compétences demandées"
            }
        }

# Instance globale
cv_analyzer = CVAnalyzer()