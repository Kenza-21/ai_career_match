import re
from datetime import datetime
from typing import Dict, List, Set, Optional
from services.matcher import JobMatcher
from utils.link_generator import LinkGenerator

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
        # État de session léger pour les flux de clarification
        self.sessions: Dict[str, Dict] = {}
    
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
        
        # Préparer les requêtes de secours
        fallback_queries = []
        if analysis['lieu']:
            fallback_queries.append(f"{user_message} {analysis['lieu']}")
        if analysis['competences']:
            fallback_queries.extend([f"{skill} emploi maroc" for skill in analysis['competences']])
        analysis['fallback_queries'] = fallback_queries

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

    # --- NOUVELLE LOGIQUE ---
    def is_ambiguous(self, user_message: str) -> bool:
        """Heuristique simple pour détecter les requêtes vagues"""
        tokens = re.findall(r"\w+", user_message.lower())
        if len(tokens) < 4:
            return True
        vague_markers = {"help", "aide", "projet", "project", "issue", "problème", "error", "besoin", "conseil"}
        if any(t in vague_markers for t in tokens):
            return True
        # Absence de mots clés métier
        skill_markers = {"developpeur", "developer", "data", "analyste", "designer", "marketing", "devops", "backend", "frontend"}
        return not any(t in skill_markers for t in tokens)

    def generate_search_queries(self, user_message: str, intent: Optional[str] = None) -> List[Dict]:
        """Construit au moins 5 requêtes distinctes et classées, avec liens"""
        analysis = self.analyze_query(user_message)
        base = analysis['search_query'] or user_message

        queries: List[Dict] = []
        seen: Set[str] = set()

        def add(q: str):
            q_norm = q.strip()
            if q_norm and q_norm not in seen:
                seen.add(q_norm)
                queries.append(self._with_links(q_norm, analysis.get("lieu")))

        # Requête principale et brute
        add(base)
        add(user_message)

        # Boost pour python/backend si présent dans le texte
        tokens = {t for t in re.findall(r"\w+", user_message.lower())}
        if "python" in tokens and "backend" in tokens:
            add("developpeur backend python maroc")
            add("python backend developer maroc")
            add(f"{base} python backend")

        if analysis['lieu']:
            add(f"{base} {analysis['lieu']}")
        if "remote" in analysis["intentions"]:
            add(f"{base} télétravail")
        for skill in analysis["competences"]:
            add(f"offre {skill} {analysis['lieu'] or 'maroc'}")
            add(f"{skill} junior emploi")

        # Templates génériques
        add(f"{base} recrutement maroc")
        add(f"poste {base} 2025")
        add(f"emploi {base} casablanca")

        # Assurer un minimum de 5 requêtes
        fallback_templates = [
            f"{base} salaire",
            f"{base} CDI",
            f"{base} stage",
            f"{base} offre d'emploi",
            f"{base} opportunités"
        ]
        for extra in fallback_templates:
            if len(queries) >= 5:
                break
            add(extra)

        # Garder une taille raisonnable et ordonnée
        return queries[:8]

    def _with_links(self, query: str, location: Optional[str] = "Morocco") -> Dict:
        loc = location or "Morocco"
        return {
            "query": query,
            "google_link": LinkGenerator.generate_google_url(query, loc),
            "indeed_link": LinkGenerator.generate_indeed_url(query, loc)
        }

    def build_job_results(self, job_matcher: JobMatcher, search_queries: List[Dict], top_k: int = 5) -> List[Dict]:
        """Lance les recherches, fusionne et classe les résultats par score max, en filtrant les résultats hors-sujet"""
        if not job_matcher:
            return []

        aggregated: Dict[int, Dict] = {}
        for entry in search_queries:
            query = entry["query"]
            matches = job_matcher.search_jobs(query, top_k)
            for idx, score in matches:
                job_data = job_matcher.get_job_by_index(idx)
                job_id = int(job_data.get("job_id", idx))
                if job_id not in aggregated or score > aggregated[job_id]["score"]:
                    aggregated[job_id] = {"score": score, "job": job_data, "source_query": query}

        ranked = sorted(aggregated.values(), key=lambda x: x["score"], reverse=True)

        # Filtrer les résultats pour correspondre davantage au texte de la requête principale
        primary_query = search_queries[0]["query"] if search_queries else ""
        primary_tokens = {t for t in re.findall(r"\w+", primary_query.lower()) if len(t) > 2}

        def is_relevant(job_dict: Dict) -> bool:
            title = job_dict.get("job_title", "").lower()
            skills = job_dict.get("required_skills", "").lower()
            desc = job_dict.get("description", "").lower()
            # Au moins un token du user query doit apparaître dans le titre ou les compétences
            return any(tok in title or tok in skills or tok in desc for tok in primary_tokens)

        filtered_ranked = [item for item in ranked if is_relevant(item["job"])]

        # Si tout est filtré, conserver les top_k originaux pour ne pas retourner 0
        ranked = filtered_ranked if filtered_ranked else ranked
        ranked = ranked[: top_k]

        results: List[Dict] = []
        for item in ranked:
            job = item["job"]
            urls = LinkGenerator.generate_all_urls(job.get("job_title", search_queries[0] if search_queries else ""))
            results.append({
                "job_id": job.get("job_id"),
                "job_title": job.get("job_title", ""),
                "category": job.get("category", ""),
                "description": job.get("description", ""),
                "required_skills": job.get("required_skills", ""),
                "recommended_courses": job.get("recommended_courses", ""),
                "avg_salary_mad": job.get("avg_salary_mad", ""),
                "demand_level": job.get("demand_level", "Medium"),
                "match_score": round(item["score"], 4),
                "linkedin_url": urls.get("linkedin_url"),
                "all_search_urls": urls,
                "source_query": item["source_query"],
            })
        return results

    def build_clarification_question(self, user_message: str) -> str:
        """Crée une question de clarification, phrasing varié"""
        variants = [
            "Juste pour mieux cibler, quel métier ou domaine tu vises ?",
            "Tu pensais à quel rôle exactement (ex: backend, data, design) ?",
            "Dis-m'en un peu plus : quel type de poste veux-tu que je cherche ?",
            "Super ! Quelle famille de métiers t'intéresse (tech, marketing, ops) ?",
            "Top, vers quel job devrais-je orienter la recherche ?"
        ]
        # Choisir une variante pseudo-aléatoire en fonction du hash du message
        idx = abs(hash(user_message)) % len(variants)
        return variants[idx]

    def save_session(self, session_id: str, original_query: str, question: str):
        self.sessions[session_id] = {
            "original_query": original_query,
            "clarify_question": question,
            "last_results": None,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_session(self, session_id: str) -> Dict | None:
        return self.sessions.get(session_id)

    def update_session_results(self, session_id: str, results: Dict):
        if session_id in self.sessions:
            self.sessions[session_id]["last_results"] = results
    
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