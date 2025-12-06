import ollama
import json
from typing import Dict, List
import re

class CareerAssistantLLM:
    def __init__(self):
        self.model = "phi3"  # Modèle gratuit et performant
        self.system_prompt = """Tu es CareerMatch Pro, un assistant IA spécialisé dans le matching de carrières tech au Maroc.

TON RÔLE :
1. Analyser les requêtes utilisateurs pour comprendre leur intention réelle
2. Qualifier les demandes vagues ou incomplètes  
3. Reformuler pour le moteur de recherche
4. Conseiller quand l'utilisateur est perdu

TON COMPORTEMENT :
- Sois DIRECT et CONCIS
- Pose MAXIMUM 3 questions à la fois
- Reste DANS LE DOMAINE des carrières tech
- Ne donne JAMAIS de liens (c'est le service qui s'en charge)
- Identifie ce qui relève de ta compétence vs le service automatique

FORMAT DE RÉPONSE :
{
  "intent": "vague|clair|conseil|insuffisant",
  "response": "ta réponse à l'utilisateur",
  "search_query": "query pour le moteur (si pertinent)",
  "needs_clarification": true/false,
  "clarification_questions": ["q1", "q2", "q3"]
}"""
    
    def analyze_query(self, user_message: str) -> Dict:
        """Analyse la requête utilisateur et détermine l'action"""
        
        # Vérifier si Ollama est disponible
        if not self._check_ollama():
            return self._fallback_analysis(user_message)
        
        try:
            # Préparer le prompt
            prompt = f"""
            Requête utilisateur: "{user_message}"
            
            Analyse cette requête selon les 4 cas :
            1. CAS VAGUE : Phrases courtes, mots indécis, demandes multiples
            2. CAS CLAIR : Requête précise avec spécifications techniques
            3. CAS CONSEIL : Questions d'orientation, compétences, stratégie
            4. CAS INSUFFISANT : Mention "pas de résultats", frustration
            
            Réponds au format JSON précis.
            """
            
            # Appeler Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraire et parser la réponse
            content = response['message']['content']
            
            # Essayer d'extraire le JSON
            try:
                # Chercher du JSON dans la réponse
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = self._parse_response(content)
            except:
                result = self._parse_response(content)
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur LLM: {e}")
            return self._fallback_analysis(user_message)
    
    def _check_ollama(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            models = ollama.list()
            return len(models['models']) > 0
        except:
            return False
    
    def _fallback_analysis(self, user_message: str) -> Dict:
        """Analyse de fallback si Ollama n'est pas disponible"""
        
        user_message_lower = user_message.lower()
        
        # Règles simples pour détection
        vague_keywords = ["stage", "travail", "emploi", "job", "quelque chose", "je sais pas", "truc"]
        clear_keywords = ["développeur", "developer", "data", "analyste", "marketing", "design"]
        advice_keywords = ["conseil", "orientation", "apprendre", "choisir", "différence", "vs"]
        
        # Détection de cas
        if any(word in user_message_lower for word in vague_keywords) and len(user_message.split()) < 8:
            return {
                "intent": "vague",
                "response": "Je vois que votre demande est large. Pour vous aider précisément :\n1. Quel domaine tech vous intéresse ? (dev web, data, mobile...)\n2. Quel type de contrat ? (stage, alternance, CDI)\n3. Quel est votre niveau d'expérience ?",
                "needs_clarification": True,
                "clarification_questions": [
                    "Quel domaine tech vous intéresse ?",
                    "Quel type de contrat recherchez-vous ?",
                    "Quel est votre niveau d'expérience ?"
                ]
            }
        
        elif any(word in user_message_lower for word in advice_keywords):
            return {
                "intent": "conseil",
                "response": "C'est une question d'orientation intéressante. Pouvez-vous préciser :\n1. Votre background actuel ?\n2. Vos centres d'intérêt dans la tech ?\n3. Vos objectifs de carrière à moyen terme ?",
                "needs_clarification": True
            }
        
        else:
            # Considérer comme demande claire
            return {
                "intent": "clair",
                "response": "Requête analysée. Je recherche les meilleures correspondances pour vous...",
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