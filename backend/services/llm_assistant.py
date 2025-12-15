import ollama
import json
from typing import Dict, List, Optional
import re

class CareerAssistantLLM:
    def __init__(self):
        self.model = "phi3"  # Modèle gratuit et performant
        self.system_prompt = """Tu es un coach de carrière bienveillant et expérimenté spécialisé dans le marché tech marocain.

TON RÔLE :
Tu es un coach humain qui guide les candidats dans leur recherche d'emploi. Tu ne donnes pas juste des résultats, tu conseilles, tu orientes, et tu aides à prendre des décisions.

TON COMPORTEMENT :
- Parle comme un vrai coach : chaleureux, encourageant, et professionnel
- Utilise un langage naturel et conversationnel
- Donne des conseils pratiques basés sur le marché marocain
- Quand l'utilisateur demande des conseils sur un domaine (développement, data, etc.), fournis :
  * Les avantages et inconvénients du domaine
  * Les tendances actuelles du marché marocain
  * Les compétences clés et technologies en demande
  * Des mots-clés de recherche pertinents
  * Des conseils pratiques pour se positionner
- Pour les comparaisons de jobs, explique les avantages, inconvénients, et valeurs de chaque option
- Sois empathique et compréhensif
- Ne donne JAMAIS de liens (c'est le service qui s'en charge)

SCÉNARIOS SPÉCIFIQUES :
1. Guidance de carrière (développement, data, etc.) → Fournis :
   - Avantages du domaine (croissance, salaires, opportunités)
   - Inconvénients (compétition, exigences, évolution rapide)
   - Tendances actuelles au Maroc
   - Technologies et compétences en demande
   - Mots-clés de recherche pertinents
   - Conseils pour se positionner
2. "Je suis perdu" / "I'm lost" → Donne des conseils, tendances du marché, suggestions de parcours
3. Comparaison de jobs → Analyse détaillée : avantages, inconvénients, salaires, croissance, fit culturel
4. Questions d'orientation → Guide vers les meilleurs choix selon le profil

FORMAT DE RÉPONSE :
{
  "intent": "coaching|comparison|guidance|search",
  "response": "ta réponse naturelle et humaine à l'utilisateur (plusieurs phrases, conversationnelle, avec détails sur avantages/inconvénients, tendances, mots-clés)",
  "search_query": "query pour le moteur (si recherche nécessaire)",
  "needs_clarification": true/false,
  "clarification_questions": ["q1", "q2", "q3"],
  "coaching_advice": "conseils supplémentaires si pertinent"
}"""
    
    def analyze_query(self, user_message: str, context: Optional[Dict] = None) -> Dict:
        """Analyse la requête utilisateur et génère une réponse de coaching"""
        
        # Vérifier si Ollama est disponible
        if not self._check_ollama():
            return self._fallback_coaching_analysis(user_message)
        
        try:
            # Détecter le type de requête
            user_lower = user_message.lower()
            is_lost = any(word in user_lower for word in ["perdu", "lost", "help", "aide", "conseil", "guidance", "orient"])
            is_comparison = any(word in user_lower for word in ["compare", "comparer", "vs", "versus", "différence", "mieux"])
            
            # Préparer le prompt selon le contexte
            if is_lost:
                prompt = f"""
                L'utilisateur dit : "{user_message}"
                
                Il/elle est perdu(e) et a besoin d'aide. En tant que coach de carrière :
                1. Sois empathique et rassurant
                2. Donne des conseils pratiques sur les tendances du marché tech marocain
                3. Suggère des parcours ou domaines prometteurs
                4. Encourage et guide vers des prochaines étapes
                
                Réponds de manière naturelle et conversationnelle, comme un vrai coach.
                """
            elif is_comparison:
                prompt = f"""
                L'utilisateur demande : "{user_message}"
                
                Il/elle veut comparer des offres d'emploi. En tant que coach :
                1. Explique les avantages et inconvénients de chaque option
                2. Compare les salaires, la croissance, le fit culturel
                3. Donne ton avis professionnel sur quelle option pourrait être meilleure selon différents critères
                4. Sois équilibré et objectif
                
                Réponds de manière naturelle et détaillée.
                """
            else:
                # Détecter si c'est une demande de guidance sur un domaine spécifique
                domain_keywords = {
                    "développement": ["dev", "développeur", "developer", "programming", "code"],
                    "data": ["data", "data science", "analyste", "analyst", "big data"],
                    "marketing": ["marketing", "digital", "communication"],
                    "design": ["design", "designer", "ui", "ux", "graphique"]
                }
                
                detected_domain = None
                for domain, keywords in domain_keywords.items():
                    if any(kw in user_lower for kw in keywords):
                        detected_domain = domain
                        break
                
                if detected_domain:
                    prompt = f"""
                    L'utilisateur demande des conseils sur le domaine : "{detected_domain}" ou "{user_message}"
                    
                    En tant que coach de carrière spécialisé dans le marché tech marocain, fournis une réponse complète incluant :
                    1. **Avantages** : Pourquoi ce domaine est intéressant (croissance, salaires, opportunités au Maroc)
                    2. **Inconvénients** : Les défis (compétition, exigences techniques, évolution rapide)
                    3. **Tendances actuelles** : Ce qui est en demande en 2024-2025 au Maroc
                    4. **Compétences clés** : Technologies, outils, et compétences à maîtriser
                    5. **Mots-clés de recherche** : Suggestions de termes pour chercher des offres (ex: "développeur React", "data scientist Python")
                    6. **Conseils pratiques** : Comment se positionner, par où commencer, etc.
                    
                    Sois détaillé, pratique, et encourageant. Utilise un ton conversationnel et naturel.
                    """
                else:
                    prompt = f"""
                    L'utilisateur demande : "{user_message}"
                    
                    Analyse sa demande et réponds comme un coach de carrière :
                    - Si c'est une recherche d'emploi, guide-le vers les meilleures options
                    - Si c'est une question, réponds de manière naturelle et utile
                    - Sois conversationnel et humain
                    
                    Réponds au format JSON avec une réponse naturelle et conversationnelle.
                    """
            
            # Appeler Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.7,  # Plus créatif pour des réponses naturelles
                    "top_p": 0.9
                }
            )
            
            # Extraire et parser la réponse
            content = response['message']['content']
            
            # Essayer d'extraire le JSON
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Si pas de JSON, créer une structure avec la réponse textuelle
                    result = {
                        "intent": "coaching" if is_lost else "search",
                        "response": content,
                        "search_query": user_message if not is_lost else None,
                        "needs_clarification": False,
                        "coaching_advice": content if is_lost else None
                    }
            except:
                result = {
                    "intent": "coaching" if is_lost else "search",
                    "response": content,
                    "search_query": user_message if not is_lost else None,
                    "needs_clarification": False,
                    "coaching_advice": content if is_lost else None
                }
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur LLM: {e}")
            return self._fallback_coaching_analysis(user_message)
    
    def generate_coaching_response(self, user_message: str, job_data: Optional[List[Dict]] = None) -> str:
        """Génère une réponse de coaching conversationnelle avec contexte des offres"""
        if not self._check_ollama():
            return self._fallback_coaching_analysis(user_message).get("response", "")
        
        try:
            context = ""
            if job_data and len(job_data) > 0:
                # Construire un contexte riche avec les offres trouvées
                job_titles = [j.get('job_title', '') for j in job_data[:5]]
                categories = list(set([j.get('category', '') for j in job_data[:5] if j.get('category')]))
                skills_mentioned = []
                for job in job_data[:3]:
                    skills = job.get('required_skills', '')
                    if skills:
                        skills_mentioned.append(skills[:100])  # Limiter la longueur
                
                context = f"""
                
J'ai trouvé {len(job_data)} offres d'emploi pertinentes :
- Postes : {', '.join(job_titles[:5])}
- Catégories : {', '.join(categories) if categories else 'Divers'}
- Compétences demandées : {', '.join(skills_mentioned[:3]) if skills_mentioned else 'Variées'}

Analyse ces offres et donne des conseils pratiques à l'utilisateur sur :
1. Les opportunités disponibles et leur pertinence
2. Les compétences en demande dans ces offres
3. Des conseils pour se positionner et postuler
4. Des suggestions de mots-clés pour affiner la recherche si nécessaire
"""
            else:
                context = "\n\nAucune offre spécifique trouvée, mais fournis quand même des conseils utiles sur le domaine recherché."
            
            prompt = f"""
            L'utilisateur cherche : "{user_message}"
            {context}
            
            Réponds comme un coach de carrière bienveillant et expérimenté. Sois :
            - Naturel et conversationnel
            - Encourageant et positif
            - Pratique avec des conseils concrets
            - Informé sur le marché marocain
            - Utile pour guider l'utilisateur vers les meilleures opportunités
            
            Si des offres sont mentionnées, analyse-les brièvement et guide l'utilisateur.
            """
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.7, "top_p": 0.9}
            )
            
            return response['message']['content']
        except Exception as e:
            print(f"❌ Erreur génération coaching: {e}")
            return "Je comprends votre situation. Laissez-moi vous aider à trouver les meilleures opportunités."
    
    def _check_ollama(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            models = ollama.list()
            return len(models['models']) > 0
        except:
            return False
    
    def _fallback_coaching_analysis(self, user_message: str) -> Dict:
        """Analyse de fallback si Ollama n'est pas disponible"""
        
        user_message_lower = user_message.lower()
        
        # Règles simples pour détection
        vague_keywords = ["stage", "travail", "emploi", "job", "quelque chose", "je sais pas", "truc"]
        clear_keywords = ["développeur", "developer", "data", "analyste", "marketing", "design"]
        advice_keywords = ["conseil", "orientation", "apprendre", "choisir", "différence", "vs"]
        
        # Détection de cas avec coaching
        lost_keywords = ["perdu", "lost", "help", "aide", "conseil", "guidance"]
        if any(word in user_message_lower for word in lost_keywords):
            return {
                "intent": "coaching",
                "response": """Je comprends que vous vous sentez un peu perdu dans votre recherche. C'est tout à fait normal ! Laissez-moi vous aider.

**Tendances du marché tech marocain en 2024 :**
- Le développement web (React, Node.js) reste très demandé
- La data science et l'IA connaissent une forte croissance
- Le développement mobile (Flutter, React Native) est en expansion
- Les profils full-stack sont très recherchés

**Mes conseils pour vous :**
1. Identifiez vos compétences actuelles et celles que vous souhaitez développer
2. Explorez les offres dans les domaines qui vous intéressent
3. N'hésitez pas à postuler même si vous ne cochez pas toutes les cases

Quel domaine vous intéresse le plus ? Je peux vous guider vers des opportunités spécifiques.""",
                "needs_clarification": True,
                "clarification_questions": [
                    "Quel domaine tech vous intéresse le plus ?",
                    "Quel est votre niveau d'expérience actuel ?",
                    "Quels sont vos objectifs de carrière ?"
                ],
                "coaching_advice": "Focus sur les compétences en demande et la croissance personnelle"
            }
        
        elif any(word in user_message_lower for word in advice_keywords):
            return {
                "intent": "coaching",
                "response": "Excellente question ! En tant que coach, je peux vous aider à y voir plus clair. Pouvez-vous me donner plus de contexte sur votre situation actuelle ?",
                "needs_clarification": True,
                "coaching_advice": "Orientation personnalisée selon le profil"
            }
        
        elif any(word in user_message_lower for word in ["compare", "comparer", "vs", "versus"]):
            return {
                "intent": "comparison",
                "response": "Je peux vous aider à comparer des offres d'emploi. Pouvez-vous me donner les détails des deux postes que vous souhaitez comparer ? (titre, salaire, localisation, etc.)",
                "needs_clarification": True,
                "coaching_advice": "Comparaison détaillée des avantages et inconvénients"
            }
        
        else:
            # Considérer comme demande claire
            return {
                "intent": "search",
                "response": "Parfait ! Je vais rechercher les meilleures opportunités pour vous. Laissez-moi analyser le marché...",
                "search_query": user_message,
                "needs_clarification": False
            }
    
    def _parse_response(self, text: str) -> Dict:
        """Parse une réponse texte en structure"""
        lines = text.strip().split('\n')
        response = " ".join(lines[:3])
        
        return {
            "intent": "clair" if len(text.split()) > 5 else "vague",
            "response": response,
            "search_query": text,
            "needs_clarification": len(text.split()) < 10
        }
    
    def generate_clarified_query(self, original_query: str, answers: Dict) -> str:
        """Génère une requête clarifiée à partir des réponses"""
        clarified = original_query
        
        if answers.get('domain'):
            clarified += f" {answers['domain']}"
        if answers.get('contract_type'):
            clarified += f" {answers['contract_type']}"
        if answers.get('experience_level'):
            clarified += f" {answers['experience_level']}"
        if answers.get('location'):
            clarified += f" {answers['location']}"
        
        return clarified.strip()

# Instance globale
career_assistant = CareerAssistantLLM()