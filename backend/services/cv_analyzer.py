import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_normalizer import TextNormalizer, SynonymMapper, SkillMatcher

class CVAnalyzer:
    def __init__(self, use_semantic_matching: bool = False):
        print("🔧 Initialisation de CVAnalyzer - Extraction stricte...")
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['le', 'la', 'les', 'de', 'des', 'du', 'et', 'en', 'au', 'aux', 'à', 'dans', 'pour'],
            ngram_range=(1, 2)
        )
        
        # Initialize text processing modules
        self.text_normalizer = TextNormalizer()
        self.synonym_mapper = SynonymMapper()
        self.skill_matcher = SkillMatcher(use_semantic=use_semantic_matching)
        
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
        
        print("✅ CVAnalyzer strict initialisé avec succès")

    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extrait STRICTEMENT les compétences techniques d'un texte
        Seulement ce qui est explicitement mentionné dans le texte
        """
        if not text:
            return []
        
        found_skills = []
        normalized_text = self.text_normalizer.normalize_text(text)
        
        # STRICT matching only - no semantic, no token overlap
        for skill in self.technical_skills:
            # Normalize skill for matching
            norm_skill = self.synonym_mapper.normalize_skill(skill)
            
            # Check for exact match with word boundaries
            pattern = r'\b' + re.escape(norm_skill) + r'\b'
            if re.search(pattern, normalized_text):
                found_skills.append(skill)
                continue
            
            # Check for synonym variants
            for variant, standard in self.synonym_mapper.synonym_map.items():
                if standard == norm_skill:
                    variant_pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(variant_pattern, normalized_text):
                        found_skills.append(skill)
                        break
        
        return list(set(found_skills))

    def extract_skills_from_job_description(self, job_description: str) -> List[str]:
        """
        Extrait STRICTEMENT les compétences d'une description d'offre
        Seulement ce qui est explicitement écrit dans le texte
        """
        if not job_description:
            return []
        
        job_skills = []
        normalized_jd = self.text_normalizer.normalize_text(job_description)
        
        # Sort skills by length (longest first) to match multi-word skills first
        sorted_skills = sorted(self.technical_skills, key=len, reverse=True)
        
        # STRICT matching only
        for skill in sorted_skills:
            norm_skill = self.synonym_mapper.normalize_skill(skill)
            
            # Skip if already found
            if skill in job_skills:
                continue
            
            # Exact word boundary matching
            if ' ' in norm_skill:
                # Multi-word skill: exact phrase match
                pattern = r'\b' + re.escape(norm_skill) + r'\b'
            else:
                # Single-word skill: word boundary
                pattern = r'\b' + re.escape(norm_skill) + r'\b'
            
            # Check if pattern matches in normalized text
            if re.search(pattern, normalized_jd, re.IGNORECASE):
                job_skills.append(skill)
                continue
            
            # Check for synonym variants
            for variant, standard in self.synonym_mapper.synonym_map.items():
                if standard == norm_skill:
                    variant_pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(variant_pattern, normalized_jd, re.IGNORECASE):
                        if skill not in job_skills:
                            job_skills.append(skill)
                        break
        
        # Remove duplicates
        seen = set()
        final_skills = []
        for skill in job_skills:
            norm_skill = self.synonym_mapper.normalize_skill(skill)
            if norm_skill not in seen:
                seen.add(norm_skill)
                final_skills.append(skill)
        
        return final_skills

    def calculate_strict_match_score(self, cv_skills: List[str], job_skills: List[str], cv_text: str, job_text: str) -> Dict:
        """
        Calcule un score de matching STRICT basé uniquement sur ce qui est explicitement mentionné
        """
        if not job_skills:
            # Fallback : calculer avec TF-IDF
            try:
                vectors = self.vectorizer.fit_transform([cv_text, job_text])
                tfidf_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                return {
                    "final_score": round(tfidf_score, 2),
                    "method": "tfidf_fallback",
                    "cv_skills_count": len(cv_skills),
                    "job_skills_count": 0,
                    "common_skills_count": 0,
                    "coverage_percentage": 0,
                    "strict_match": True
                }
            except:
                return {
                    "final_score": 0.0,
                    "method": "no_skills_detected",
                    "cv_skills_count": len(cv_skills),
                    "job_skills_count": 0,
                    "common_skills_count": 0,
                    "coverage_percentage": 0,
                    "strict_match": True
                }
        
        # STRICT comparison - only exact matches
        common_skills = []
        
        for job_skill in job_skills:
            norm_job = self.synonym_mapper.normalize_skill(job_skill)
            
            # Check for exact match in CV skills
            for cv_skill in cv_skills:
                norm_cv = self.synonym_mapper.normalize_skill(cv_skill)
                
                # EXACT match only
                if norm_cv == norm_job:
                    common_skills.append(job_skill)
                    break
                
                # Check synonym mapping
                if norm_cv in self.synonym_mapper.synonym_map.values() and norm_job in self.synonym_mapper.synonym_map.values():
                    # Both are standard forms, check if they map to same standard
                    cv_standard = self.synonym_mapper.get_standard_form(cv_skill)
                    job_standard = self.synonym_mapper.get_standard_form(job_skill)
                    if cv_standard and job_standard and cv_standard == job_standard:
                        common_skills.append(job_skill)
                        break
        
        coverage = len(common_skills) / len(job_skills) if job_skills else 0
        
        # Score final basé uniquement sur la couverture stricte
        skill_based_score = coverage
        
        # Combiner avec TF-IDF pour plus de robustesse
        try:
            vectors = self.vectorizer.fit_transform([cv_text, job_text])
            tfidf_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            final_score = skill_based_score * 0.8 + tfidf_score * 0.2  # Poids plus fort sur matching strict
        except:
            final_score = skill_based_score
        
        return {
            "final_score": round(final_score, 2),
            "method": "strict_skills_analysis",
            "cv_skills_count": len(cv_skills),
            "job_skills_count": len(job_skills),
            "common_skills_count": len(common_skills),
            "coverage_percentage": round(coverage * 100, 1),
            "common_skills": common_skills,
            "strict_match": True
        }

    def identify_strict_skill_gaps(self, cv_skills: List[str], job_skills: List[str]) -> List[Dict]:
        """
        Identifie STRICTEMENT les écarts de compétences
        Basé uniquement sur ce qui est explicitement dans le job et pas dans le CV
        """
        # Normalize all skills for strict comparison
        norm_cv_skills = {self.synonym_mapper.normalize_skill(s): s for s in cv_skills}
        norm_job_skills = {self.synonym_mapper.normalize_skill(s): s for s in job_skills}
        
        missing_skills = []
        
        for job_norm, job_orig in norm_job_skills.items():
            found = False
            
            # Check exact match
            if job_norm in norm_cv_skills:
                found = True
            else:
                # Check via standard forms
                job_standard = self.synonym_mapper.get_standard_form(job_orig)
                if job_standard:
                    for cv_norm, cv_orig in norm_cv_skills.items():
                        cv_standard = self.synonym_mapper.get_standard_form(cv_orig)
                        if cv_standard and cv_standard == job_standard:
                            found = True
                            break
            
            if not found:
                missing_skills.append(job_orig)
        
        skill_gaps = []
        for skill in missing_skills:
            skill_gaps.append({
                "skill_name": skill,
                "required_level": "Demandée dans l'offre",
                "current_level": "Non présente dans le CV",
                "gap_severity": "high" if skill in ["python", "javascript", "sql", "java"] else "medium",
                "strict_missing": True,
                "explicit_in_jd": True,
                "explicit_in_cv": False
            })
        
        return skill_gaps

    def analyze_cv_vs_job_strict(self, cv_text: str, job_description: str) -> Dict:
        """
        Analyse STRICTE CV vs Offre d'emploi
        Seulement ce qui est explicitement écrit dans les textes
        """
        print("🔍 Début de l'analyse STRICTE CV vs Offre...")
        
        # Extraction STRICTE des compétences
        cv_skills = self.extract_skills_from_text(cv_text)
        job_skills = self.extract_skills_from_job_description(job_description)
        
        print(f"✅ Compétences CV (strict): {len(cv_skills)} trouvées: {cv_skills}")
        print(f"✅ Compétences Offre (strict): {len(job_skills)} trouvées: {job_skills}")
        
        # Calcul du matching STRICT
        score_analysis = self.calculate_strict_match_score(cv_skills, job_skills, cv_text, job_description)
        match_score = score_analysis["final_score"]
        
        # Analyse écarts STRICTS
        skill_gaps = self.identify_strict_skill_gaps(cv_skills, job_skills)
        missing_skills = [gap["skill_name"] for gap in skill_gaps]
        
        # Évaluation globale basée sur matching strict
        if match_score >= 0.8:
            assessment = "✅ Excellent matching strict - Toutes compétences clés présentes"
            confidence = "Élevée (basée sur texte explicite)"
        elif match_score >= 0.6:
            assessment = "⚠️ Bon matching strict - La plupart des compétences présentes"
            confidence = "Moyenne (basée sur texte explicite)"
        elif match_score >= 0.4:
            assessment = "⚠️ Matching strict moyen - Compétences principales manquantes"
            confidence = "Faible (basée sur texte explicite)"
        else:
            assessment = "❌ Faible matching strict - Peu de compétences correspondantes"
            confidence = "Très faible (basée sur texte explicite)"
        
        print(f"✅ Analyse STRICTE terminée - Score: {match_score}")
        print(f"✅ Méthode: {score_analysis['method']}")
        print(f"✅ Compétences communes (strict): {score_analysis.get('common_skills', [])}")
        
        return {
            "match_score": match_score,
            "score_analysis": score_analysis,
            "cv_skills": cv_skills,
            "job_skills": job_skills,
            "skill_gaps": skill_gaps,
            "missing_skills": missing_skills,
            "strict_analysis": True,
            "overall_assessment": assessment,
            "confidence_level": confidence,
            "summary": {
                "cv_skills_count": len(cv_skills),
                "job_skills_count": len(job_skills),
                "common_skills": score_analysis.get('common_skills', []),
                "coverage": f"{score_analysis.get('coverage_percentage', 0)}% des compétences demandées (strict)",
                "coverage_percentage": score_analysis.get('coverage_percentage', 0),
                "methodology": "Extraction et comparaison STRICTE basée uniquement sur le texte explicite"
            }
        }

    def get_exact_matches_report(self, cv_text: str, job_description: str) -> Dict:
        """
        Génère un rapport détaillé des matches EXACTS entre CV et offre
        """
        cv_skills = self.extract_skills_from_text(cv_text)
        job_skills = self.extract_skills_from_job_description(job_description)
        
        exact_matches = []
        partial_matches = []
        no_matches = []
        
        for job_skill in job_skills:
            job_norm = self.synonym_mapper.normalize_skill(job_skill)
            found_exact = False
            found_partial = False
            
            for cv_skill in cv_skills:
                cv_norm = self.synonym_mapper.normalize_skill(cv_skill)
                
                # EXACT match
                if cv_norm == job_norm:
                    exact_matches.append({
                        "job_skill": job_skill,
                        "cv_skill": cv_skill,
                        "match_type": "exact",
                        "normalized_form": job_norm
                    })
                    found_exact = True
                    break
            
            if not found_exact:
                # Check for partial (synonym) match
                job_standard = self.synonym_mapper.get_standard_form(job_skill)
                if job_standard:
                    for cv_skill in cv_skills:
                        cv_standard = self.synonym_mapper.get_standard_form(cv_skill)
                        if cv_standard == job_standard:
                            partial_matches.append({
                                "job_skill": job_skill,
                                "cv_skill": cv_skill,
                                "match_type": "synonym",
                                "standard_form": job_standard
                            })
                            found_partial = True
                            break
            
            if not found_exact and not found_partial:
                no_matches.append({
                    "job_skill": job_skill,
                    "match_type": "none",
                    "normalized_form": job_norm
                })
        
        return {
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "no_matches": no_matches,
            "total_job_skills": len(job_skills),
            "total_cv_skills": len(cv_skills),
            "exact_match_count": len(exact_matches),
            "partial_match_count": len(partial_matches),
            "no_match_count": len(no_matches),
            "exact_match_percentage": round(len(exact_matches) / len(job_skills) * 100, 1) if job_skills else 0
        }

# Instance globale
cv_analyzer = CVAnalyzer()