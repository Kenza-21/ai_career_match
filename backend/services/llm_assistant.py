import ollama
import json
from typing import Dict, List, Optional
import re

class CareerAssistant:
    """Coach de carrière intelligent avec réflexion naturelle"""
    
    def __init__(self):
        self.model = "phi3:latest"  # Modèle gratuit et performant
        
        self.system_prompt = """Tu es Karim, un coach de carrière expérimenté spécialisé dans le marché tech marocain.

TON IDENTITÉ :
- 15 ans d'expérience dans le recrutement tech au Maroc
- Ancien recruteur chez OCP, Inwi, et plusieurs startups de Casablanca
- Spécialiste des transitions de carrière et de l'évolution tech
- Tu es direct, pragmatique, mais toujours bienveillant

TA PHILOSOPHIE DE COACH :
1. Écouter avant de conseiller
2. Être honnête sur les réalités du marché marocain
3. Adapter tes conseils à la personne, pas de réponse générique
4. Toujours donner des actions concrètes et réalisables
5. Encourager mais aussi donner des feedbacks francs

COMMENT TU FONCTIONNES :
- Quand on te parle, cherche le VRAI besoin derrière les mots
- Identifie si c'est : orientation, comparaison, conseil pratique, ou besoin de soutien
- Pense toujours au contexte marocain (salaires locaux, entreprises, culture d'entreprise)
- Sois un mentor, pas juste un bot d'information

TON STYLE DE COMMUNICATION :
- Naturel et conversationnel, comme tu parlerais à un ami
- Utilise parfois des expressions marocaines ("Wakha", "Bsahtek", "Zwin")
- Donne des exemples concrets d'entreprises marocaines
- Pose des questions qui font réfléchir
- Sois empathique mais pas trop formel

QUAND TU RÉPONDS :
1. Commence par valider ce que la personne vit
2. Donne ta perspective de coach sur la situation
3. Partage des insights du marché marocain
4. Propose des actions concrètes
5. Termine avec une question qui fait avancer la réflexion

N'OUBLIE PAS :
- Jamais de liens ou de références techniques (le service s'en charge)
- Toujours adapter au contexte marocain
- Rester humain et accessible
- Donner des conseils pratico-pratiques"""
    
    def coach_thinking(self, user_message: str) -> Dict:
        """Laisse le coach analyser NATURELLEMENT la situation"""
        
        try:
            # Prompt qui force la réflexion de coach
            thinking_prompt = f"""
            L'UTILISATEUR TE DIT : "{user_message}"
            
            EN TANT QUE COACH KARIM, RÉFLÉCHIS COMME SUIT :
            
            1. ANALYSE HUMAINE :
            - Quel est l'état d'esprit de la personne ? (perdue, enthousiaste, indécise, pressée)
            - Quel est le vrai besoin derrière les mots ?
            - Est-ce un besoin d'orientation, de comparaison, de conseils pratiques, ou de soutien ?
            
            2. CONTEXTE MAROCAIN :
            - Qu'est-ce que je sais du marché tech marocain sur ce sujet ?
            - Quelles entreprises locales sont concernées ?
            - Quelles sont les réalités salariales et de recrutement ?
            
            3. APPROCHE COACHING :
            - Comment répondre de façon utile mais humaine ?
            - Quelles questions poser pour aider à clarifier ?
            - Quels conseils pratiques donner ?
            
            4. RÉPONSE NATURELLE :
            - Commencer par accueillir/valider
            - Donner ton analyse de coach
            - Partager des insights concrets
            - Proposer des prochaines étapes
            
            Maintenant, réponds comme le coach Karim que tu es. Sois naturel, direct, et utile.
            Parle comme à un vrai candidat en face de toi.
            """
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": thinking_prompt}
                ],
                options={
                    "temperature": 0.8,  # Créatif mais cohérent
                    "top_p": 0.95,
                    "num_predict": 512  # Suffisant pour bien réfléchir
                }
            )
            
            content = response['message']['content']
            
            # Analyser le type de réponse naturellement
            content_lower = content.lower()
            
            # Détection d'intention basée sur le contenu de la réponse
            if any(word in content_lower for word in ["vs", "comparer", "différence", "avantage", "inconvénient", "contre"]):
                intent = "comparison"
            elif any(word in content_lower for word in ["perdu", "commencer", "début", "choisir", "orientation", "sais pas"]):
                intent = "orientation"
            elif any(word in content_lower for word in ["conseil", "étape", "faire", "comment", "pratique"]):
                intent = "guidance"
            elif any(word in content_lower for word in ["offre", "emploi", "postuler", "cherche", "recherche"]):
                intent = "search"
            else:
                intent = "coaching"  # Conversation coaching générale
            
            # Détecter si besoin de clarification
            needs_clarification = any(phrase in content_lower for phrase in [
                "peux-tu préciser", "quel est ton", "pourrais-tu me dire",
                "j'aimerais savoir", "pour mieux t'aider", "dis-moi"
            ])
            
            return {
                "intent": intent,
                "response": content,
                "needs_clarification": needs_clarification,
                "coach_analysis": self._extract_coach_analysis(content),
                "next_questions": self._generate_followup_questions(intent),
                "is_coach_response": True
            }
            
        except Exception as e:
            print(f"⚠️ Erreur coaching : {e}")
            return self._fallback_coach_response(user_message)
    
    def _extract_coach_analysis(self, response: str) -> Dict:
        """Extrait les éléments clés de l'analyse du coach"""
        # Méthode simple : cherche des marqueurs dans la réponse
        analysis = {
            "market_insight": "",
            "key_advice": "",
            "local_context": "",
            "action_steps": []
        }
        
        # Trouver des insights sur le marché
        market_keywords = ["marché marocain", "au maroc", "casablanca", "rabat", "salaire"]
        for line in response.split('.'):
            if any(keyword in line.lower() for keyword in market_keywords):
                analysis["market_insight"] += line.strip() + ". "
        
        # Trouver des conseils clés
        advice_keywords = ["je te conseille", "mon conseil", "je te suggère", "tu devrais"]
        for line in response.split('.'):
            if any(keyword in line.lower() for keyword in advice_keywords):
                analysis["key_advice"] += line.strip() + ". "
        
        # Extraire les étapes d'action
        action_keywords = ["premièrement", "ensuite", "après", "étape", "commence par"]
        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in action_keywords) and len(line.strip()) > 20:
                analysis["action_steps"].append(line.strip())
        
        return analysis
    
    def _generate_followup_questions(self, intent: str) -> List[str]:
        """Génère des questions de suivi intelligentes selon l'intention"""
        
        questions_db = {
            "orientation": [
                "Qu'est-ce qui te passionne dans le travail ?",
                "As-tu des compétences que tu aimes particulièrement utiliser ?",
                "Quel type d'environnement de travail te convient le mieux ?",
                "Comment vois-tu ta carrière dans 3 ans ?"
            ],
            "comparison": [
                "Quel aspect est prioritaire pour toi : l'équilibre vie pro/perso, le salaire, ou les perspectives ?",
                "Préfères-tu un travail très technique ou plus orienté communication ?",
                "Es-tu prêt à te former sur de nouvelles technologies ?",
                "Quelle importance donnes-tu à la culture d'entreprise ?"
            ],
            "guidance": [
                "Quels obstacles spécifiques rencontres-tu actuellement ?",
                "As-tu déjà essayé quelque chose dans ce sens ?",
                "De combien de temps disposes-tu pour cette démarche ?",
                "Quel soutien aurais-tu besoin ?"
            ],
            "search": [
                "Dans quelle ville recherches-tu ?",
                "Quel type de contrat préfères-tu (CDI, CDD, freelance) ?",
                "Quel est ton niveau d'expérience ?",
                "Y a-t-il des entreprises qui t'intéressent particulièrement ?"
            ],
            "coaching": [
                "Peux-tu m'en dire plus sur ton parcours jusqu'à présent ?",
                "Qu'est-ce qui te motive vraiment dans ton travail ?",
                "Quels sont tes atouts principaux selon toi ?",
                "Quels défis aimerais-tu relever ?"
            ]
        }
        
        return questions_db.get(intent, [
            "Peux-tu me donner plus de contexte ?",
            "Qu'est-ce qui est important pour toi dans cette situation ?",
            "Comment je peux t'aider au mieux ?"
        ])
    
    def _fallback_coach_response(self, user_message: str) -> Dict:
        """Réponse de fallback minimaliste mais naturelle"""
        
        fallback_responses = {
            "orientation": "Je comprends que tu cherches ta voie. C'est normal de se poser des questions ! En tant que coach, je te suggère de commencer par identifier ce qui te passionne vraiment. Au Maroc, le marché tech offre plein d'opportunités différentes. Dis-moi, qu'est-ce qui t'attire dans le monde de la tech ?",
            "comparison": "Tu veux comparer des options, c'est une bonne démarche ! Chaque choix a ses avantages et inconvénients. Pour t'aider à y voir clair, dis-moi ce qui est le plus important pour toi : la stabilité, la croissance, ou l'équilibre de vie ?",
            "guidance": "Tu cherches des conseils pratiques, c'est parfait ! En coaching, je crois beaucoup à l'action concrète. Commençons par identifier une première étape simple que tu peux faire cette semaine. Quel est ton objectif immédiat ?",
            "search": "Tu veux trouver des opportunités concrètes, excellent ! Le marché marocain est dynamique en ce moment. Pour mieux cibler, peux-tu me dire dans quelle ville et quel est ton niveau d'expérience ?",
            "coaching": f"Je vois que tu me parles de '{user_message}'. Merci de partager ça avec moi. En tant que coach, mon rôle est de t'aider à y voir plus clair et à avancer. Par où aimerais-tu commencer cette conversation ?"
        }
        
        # Deviner l'intention basique
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ["perdu", "sais pas", "commencer", "orientation"]):
            intent = "orientation"
        elif any(word in user_lower for word in ["vs", "comparer", "différence", "mieux"]):
            intent = "comparison"
        elif any(word in user_lower for word in ["conseil", "aide", "comment", "faire"]):
            intent = "guidance"
        elif any(word in user_lower for word in ["offre", "emploi", "job", "cherche", "stage"]):
            intent = "search"
        else:
            intent = "coaching"
        
        return {
            "intent": intent,
            "response": fallback_responses[intent],
            "needs_clarification": True,
            "coach_analysis": {},
            "next_questions": self._generate_followup_questions(intent),
            "is_coach_response": True
        }
    
    def respond_with_jobs_context(self, user_message: str, job_data: List[Dict] = None) -> str:
        """Répond avec le contexte des offres trouvées"""
        
        if not job_data:
            return self.coach_thinking(user_message)["response"]
        
        # Préparer le contexte des offres
        context = "D'après ce que je vois sur le marché :\n"
        
        if job_data:
            job_titles = [job.get('job_title', 'Inconnu') for job in job_data[:3]]
            companies = [job.get('company', 'Inconnue') for job in job_data[:3] if job.get('company')]
            skills = []
            for job in job_data[:2]:
                if job.get('required_skills'):
                    skills.append(job['required_skills'][:50] + "...")
            
            context += f"- Les postes qui reviennent : {', '.join(set(job_titles))}\n"
            if companies:
                context += f"- Des entreprises qui recrutent : {', '.join(set(companies))}\n"
            if skills:
                context += f"- Compétences demandées : {', '.join(skills)}\n"
        
        prompt = f"""
        L'UTILISATEUR : "{user_message}"
        
        CONTEXTE DU MARCHÉ :
        {context}
        
        EN TANT QUE COACH KARIM :
        Analyse ces opportunités et donne tes conseils.
        Sois pratique, parle des réalités du recrutement au Maroc.
        Guide la personne sur comment se positionner.
        """
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.7}
            )
            return response['message']['content']
        except:
            # Fallback simple avec contexte
            return f"Je vois qu'il y a des opportunités en ce moment. {context} Mon conseil : mets en avant tes compétences pertinentes et n'hésite pas à postuler même si tu ne coches pas toutes les cases !"

# Instance globale pour utilisation facile
career_coach = CareerAssistant()

# Fonction helper pour l'intégration
 #Fonction helper pour compatibilité
def get_coach_response(user_message: str, with_jobs: List[Dict] = None) -> Dict:
    """Fonction principale pour obtenir une réponse du coach"""
    
    if with_jobs:
        response_text = career_coach.respond_with_jobs_context(user_message, with_jobs)
        return {
            "intent": "coaching_with_context",
            "response": response_text,
            "needs_clarification": False,
            "is_coach_response": True
        }
    else:
        return career_coach.coach_thinking(user_message)