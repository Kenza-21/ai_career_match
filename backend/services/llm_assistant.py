import google.generativeai as genai
import json
from typing import Dict, List, Optional
import re
import os

class CareerAssistant:
    """Coach de carrière intelligent avec réflexion naturelle utilisant Gemini"""
    
    def __init__(self):
        # NE LAISSEZ PAS VOTRE CLÉ API EN CLAIR DANS LE CODE !
        # Utilisez une variable d'environnement
        gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyC-ZRTAkgZ7uZ3BfBbLWbT9F7FHyyrbJlI")
        
        # IMPORTANT : Configurez avec la bonne version d'API
        genai.configure(
            api_key=gemini_api_key,
            # Spécifiez explicitement la version d'API si nécessaire
            # client_options={"api_version": "v1"}  # Essayez v1 si v1beta ne fonctionne pas
        )
        
        print(f"🔑 Clé API configurée")
        
        # Liste des modèles à essayer (par ordre de préférence)
        model_candidates = [
            "gemini-2.0-flash",        # Meilleur choix pour v1beta
            "gemini-2.0-flash-exp",    # Alternative
            "gemini-2.5-flash",        # Nouveaux modèles
            "gemini-2.0-flash-lite",   # Léger et rapide
            "gemini-pro-latest",       # Dernière version de gemini-pro
        ]
        
        self.model = None
        self.model_name = None
        
        # Testez chaque modèle
        for model_name in model_candidates:
            try:
                print(f"🔄 Tentative avec le modèle: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                self.model_name = model_name
                
                # Test rapide
                test_response = self.model.generate_content("Test")
                print(f"✅ Modèle chargé avec succès: {model_name}")
                break
                
            except Exception as e:
                print(f"❌ Modèle {model_name} échoué: {e}")
                continue
        
        if self.model is None:
            print("⚠️ Aucun modèle Gemini n'a fonctionné. Mode fallback activé.")
        
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
- Donner des conseils pratico-pratiques
    
RÈGLES DE CONVERSATION IMPORTANTES :
1. Quand l'utilisateur répond à tes questions de clarification, INTÈGRE ses réponses dans ton analyse
2. Ne répète pas "Je vois que tu me parles de..." - c'est mécanique
3. Montre que tu as écouté et compris ses précisions
4. Passe naturellement du questionnement aux conseils concrets
5. Si l'utilisateur donne assez d'infos (domaine + compétences + localisation), propose des pistes concrètes

EXEMPLE DE BONNE RÉPONSE :
"Super, tu m'as dit que tu aimes la data, que tu sais utiliser Python et ML, et que tu cherches un environnement stable à Casa. Excellent combo ! Au Maroc, les data scientists sont très recherchés, surtout à Casablanca. Parlons des opportunités concrètes..."""
    
    def _extract_coach_analysis(self, response: str) -> Dict:
        """Extrait les éléments clés de l'analyse du coach"""
        analysis = {
            "market_insight": "",
            "key_advice": "",
            "local_context": "",
            "action_steps": []
        }
        
        market_keywords = ["marché marocain", "au maroc", "casablanca", "rabat", "salaire"]
        for line in response.split('.'):
            if any(keyword in line.lower() for keyword in market_keywords):
                analysis["market_insight"] += line.strip() + ". "
        
        advice_keywords = ["je te conseille", "mon conseil", "je te suggère", "tu devrais"]
        for line in response.split('.'):
            if any(keyword in line.lower() for keyword in advice_keywords):
                analysis["key_advice"] += line.strip() + ". "
        
        action_keywords = ["premièrement", "ensuite", "après", "étape", "commence par"]
        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in action_keywords) and len(line.strip()) > 20:
                analysis["action_steps"].append(line.strip())
        
        return analysis
    
    def _generate_followup_questions(self, intent: str, user_message: str = "", coach_response: str = "") -> List[str]:
        """Génère des questions de suivi intelligentes basées sur la conversation"""
        
        user_lower = user_message.lower()
        
        # Questions contextuelles basées sur le contenu
        if "data" in user_lower or "python" in user_lower or "machine learning" in user_lower or "ia" in user_lower:
            if intent == "search":
                return [
                    "Dans quel secteur d'activité cherches-tu à travailler ? (fintech, e-commerce, santé, etc.)",
                    "Quel est ton niveau d'expérience en data science/ML ?",
                    "Recherches-tu un stage, alternance, ou CDI ?",
                    "As-tu un portfolio ou projets à montrer ?"
                ]
            elif intent == "orientation":
                return [
                    "Qu'est-ce qui t'attire particulièrement dans la data et l'IA ?",
                    "As-tu déjà travaillé sur des projets concrets en data/ML ?",
                    "Te vois-tu plutôt dans une startup dynamique ou une grande entreprise stable ?",
                    "Es-tu prêt à te former sur de nouvelles technologies ?"
                ]
            elif intent == "coaching":
                return [
                    "Quel type de problèmes en IA/data t'intéresse le plus ?",
                    "As-tu une spécialisation particulière en tête ?",
                    "Comment vois-tu ton évolution dans ce domaine ?",
                    "Quels sont tes objectifs à 1 an ?"
                ]
        
        # Questions par défaut selon l'intention
        questions_db = {
            "orientation": [
                "Qu'est-ce qui te passionne vraiment dans le travail ?",
                "Quels sont tes talents naturels que tu aimerais exploiter ?",
                "Te vois-tu plutôt en startup ou en grande entreprise ?",
                "Quel impact veux-tu avoir à travers ton travail ?"
            ],
            "comparison": [
                "Quel critère est le plus important pour toi dans ce choix ?",
                "Préfères-tu la stabilité ou les opportunités de croissance ?",
                "Quel équilibre vie pro/perso recherches-tu ?",
                "Quels compromis es-tu prêt à faire ?"
            ],
            "guidance": [
                "Quel est ton objectif principal à court terme ?",
                "Quels obstacles rencontres-tu actuellement ?",
                "De quelles ressources disposes-tu ? (temps, budget, réseau)",
                "Quelle serait une première petite victoire pour toi ?"
            ],
            "search": [
                "Dans quelle ville recherches-tu précisément ?",
                "Quel type de contrat préfères-tu ? (CDI, CDD, freelance, stage)",
                "Quel est ton niveau d'expérience dans ce domaine ?",
                "Y a-t-il des entreprises qui t'intéressent particulièrement ?"
            ],
            "coaching": [
                "Peux-tu me parler de ton parcours jusqu'à présent ?",
                "Qu'est-ce qui te motive profondément dans ton travail ?",
                "Quels sont tes trois plus grands atouts professionnels ?",
                "Quel défi professionnel aimerais-tu relever cette année ?"
            ]
        }
        
        return questions_db.get(intent, [
            "Peux-tu me donner un peu plus de contexte sur ta situation ?",
            "Qu'est-ce qui est le plus important pour toi dans cette démarche ?",
            "Comment puis-je t'aider au mieux à avancer ?"
        ])
    
    def coach_thinking(self, user_message: str) -> Dict:
        """Laisse le coach analyser NATURELLEMENT la situation avec Gemini"""
        
        # Vérifier si le modèle Gemini est disponible
        if self.model is None:
            print("⚠️ Utilisation du fallback car modèle Gemini non disponible")
            return self._fallback_coach_response(user_message)
        
        try:
            # Nettoyer le message
            user_message_clean = user_message.strip()
            user_lower = user_message_clean.lower()
            
            # Détection d'intention basée sur les mots-clés
            search_keywords = ["cherche", "recherche", "trouver", "postuler", "offre", "emploi", "job", "stage"]
            if any(keyword in user_lower for keyword in search_keywords):
                base_intent = "search"
            elif any(word in user_lower for word in ["perdu", "sais pas", "commencer", "début", "choisir"]):
                base_intent = "orientation"
            elif any(word in user_lower for word in ["conseil", "aide", "comment", "faire", "étapes"]):
                base_intent = "guidance"
            elif any(word in user_lower for word in ["vs", "comparer", "différence", "mieux"]):
                base_intent = "comparison"
            else:
                base_intent = "coaching"
            
            # Prompt adaptatif
            if base_intent == "search":
                thinking_prompt = f"""L'utilisateur cherche un emploi/opportunité. Message: "{user_message_clean}"

En tant que coach Karim, donne une réponse directe et pratique :
1. Analyse son besoin (domaine, compétences, localisation)
2. Partage 2-3 insights sur le marché marocain
3. Propose 1-2 actions concrètes
4. Pose 1 question pour préciser si besoin

Réponds naturellement comme à un candidat en face de toi."""
            
            elif base_intent == "orientation":
                thinking_prompt = f"""L'utilisateur cherche son orientation. Message: "{user_message_clean}"

En tant que coach Karim, aide-le à y voir plus clair :
1. Valide son état d'esprit
2. Pose 2-3 questions pour explorer ses intérêts
3. Donne un aperçu du marché tech marocain
4. Propose une première piste à explorer

Sois bienveillant et encourageant."""
            
            else:
                thinking_prompt = f"""Message de l'utilisateur: "{user_message_clean}"

En tant que coach Karim spécialisé dans le tech marocain :
1. Écoute et valide son message
2. Donne ton analyse de coach
3. Partage un insight concret sur le marché
4. Propose une prochaine étape
5. Pose une question pour avancer

Réponds de façon naturelle et conversationnelle."""
            
            # Configuration simple pour éviter les erreurs
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 400,
            }
            
            # Appel Gemini
            response = self.model.generate_content(
                contents=[
                    {"role": "user", "parts": [self.system_prompt]},
                    {"role": "user", "parts": [thinking_prompt]}
                ],
                generation_config=generation_config,
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            content = response.text
            
            # Analyser la réponse
            content_lower = content.lower()
            
            # Détecter si besoin de clarification
            needs_clarification = "?" in content or any(word in content_lower for word in 
                ["peux-tu", "pourrais-tu", "quel est", "quelle est", "dis-moi"])
            
            # Générer questions de suivi
            next_questions = self._generate_followup_questions(
                base_intent, 
                user_message_clean, 
                content
            )
            
            # Extraire analyse
            coach_analysis = self._extract_coach_analysis(content)
            
            return {
                "intent": base_intent,
                "response": content,
                "needs_clarification": needs_clarification,
                "coach_analysis": coach_analysis,
                "next_questions": next_questions,
                "is_coach_response": True,
                "model_used": self.model_name
            }
            
        except Exception as e:
            print(f"⚠️ Erreur Gemini: {e}")
            return self._fallback_coach_response(user_message)
    
    def _fallback_coach_response(self, user_message: str) -> Dict:
        """Réponse de fallback intelligente sans Gemini"""
        
        user_message_clean = user_message.strip().replace('"', '').replace("'", "")
        user_lower = user_message_clean.lower()
        
        # Logique contextuelle améliorée
        if "business" in user_lower or "startup" in user_lower or "propre" in user_lower:
            response = "Super ambition ! Créer son business dans le tech au Maroc, c'est le bon moment. À Casablanca, l'écosystème startup est dynamique avec des incubateurs comme SETT, Lean, et Foundawery. Parlons de ton projet : as-tu déjà une idée précise ou tu explores les possibilités ?"
            intent = "guidance"
            questions = [
                "As-tu une idée de business en tête ?",
                "Quel problème veux-tu résoudre avec la tech ?",
                "As-tu des compétences techniques ou commerciales ?",
                "Quel budget/temps peux-tu y consacrer ?"
            ]
            
        elif ("data" in user_lower or "python" in user_lower or "machine learning" in user_lower) and ("casa" in user_lower or "casablanca" in user_lower):
            response = "Excellent ! Tu as un profil data/ML et tu cherches à Casablanca. C'est très recherché ! Les entreprises comme OCP, Inwi, Marjane, et les fintechs recrutent activement. Veux-tu que je te montre des opportunités concrètes ?"
            intent = "search"
            questions = [
                "Dans quel secteur ? (fintech, e-commerce, santé, etc.)",
                "Quel niveau d'expérience ? (junior, intermédiaire, senior)",
                "Type de contrat ? (stage, alternance, CDI)",
                "Fourchette salariale attendue ?"
            ]
            
        elif "data" in user_lower or "python" in user_lower or "machine learning" in user_lower or "ia" in user_lower:
            response = "Je vois que tu t'intéresses à l'IA/Data. Excellent choix ! Le Maroc a un vrai besoin en compétences data. Le marché offre des salaires de 8k-25k MAD selon l'expérience. Veux-tu explorer les opportunités ou parler de ton orientation ?"
            intent = "coaching"
            questions = [
                "Qu'est-ce qui t'attire dans l'IA/Data ?",
                "As-tu déjà des compétences techniques ?",
                "Préfères-tu un emploi ou créer ton propre projet ?",
                "Quel est ton objectif à 1 an ?"
            ]
            
        elif any(word in user_lower for word in ["perdu", "orientation", "commencer", "sais pas"]):
            response = "Je comprends que tu cherches ta voie. C'est normal ! Le marché tech marocain offre plein d'opportunités : dev web/mobile, data science, cybersécurité, cloud, etc. Parlons de ce qui te passionne vraiment."
            intent = "orientation"
            questions = [
                "Qu'est-ce qui te passionne dans le tech ?",
                "Quels sont tes talents naturels ?",
                "Te vois-tu en startup ou grande entreprise ?",
                "Quel impact veux-tu avoir ?"
            ]
            
        else:
            response = f"Merci pour ton message. En tant que coach tech marocain, je peux t'aider sur : orientation carrière, recherche d'emploi, conseils business, ou développement de compétences. Sur quoi veux-tu qu'on travaille ensemble ?"
            intent = "coaching"
            questions = [
                "Peux-tu me parler de ta situation actuelle ?",
                "Quel est ton objectif principal ?",
                "De quel type d'aide as-tu le plus besoin ?",
                "Quelle serait une première victoire pour toi ?"
            ]
        
        return {
            "intent": intent,
            "response": response,
            "needs_clarification": True,
            "coach_analysis": {},
            "next_questions": questions,
            "is_coach_response": True,
            "is_fallback": True
        }
    
    def respond_with_jobs_context(self, user_message: str, job_data: List[Dict] = None) -> str:
        """Répond avec le contexte des offres trouvées"""
        
        if not job_data:
            return self.coach_thinking(user_message)["response"]
        
        # Fallback si pas de modèle
        if self.model is None:
            # Version simple avec contexte
            job_titles = [job.get('job_title', 'Inconnu') for job in job_data[:3]]
            companies = [job.get('company', '') for job in job_data[:3] if job.get('company')]
            
            context = f"Je vois {len(job_data)} opportunités pertinentes. Postes : {', '.join(job_titles[:3])}"
            if companies:
                context += f" chez {', '.join(filter(None, companies))}"
            
            return f"{context}. Mon conseil : personnalise ton CV pour chaque poste et mets en avant tes compétences en Python/ML !"
        
        # Sinon, utiliser Gemini
        context = "Opportunités trouvées :\n"
        for i, job in enumerate(job_data[:3], 1):
            title = job.get('job_title', 'Titre inconnu')
            company = job.get('company', '')
            context += f"{i}. {title}"
            if company:
                context += f" chez {company}"
            context += "\n"
        
        prompt = f"""L'utilisateur cherche : "{user_message}"

Voici des opportunités trouvées :
{context}

En tant que coach Karim, donne :
1. Une analyse de ces opportunités
2. Des conseils pour postuler
3. Des insights sur le marché marocain
4. La prochaine étape recommandée

Sois direct et pratique."""
        
        try:
            response = self.model.generate_content(
                contents=[
                    {"role": "user", "parts": [self.system_prompt]},
                    {"role": "user", "parts": [prompt]}
                ],
                generation_config={"temperature": 0.7, "max_output_tokens": 400}
            )
            return response.text
        except Exception as e:
            print(f"⚠️ Erreur Gemini avec jobs: {e}")
            return self._fallback_coach_response(user_message)["response"]

# Instance globale
career_coach = CareerAssistant()

def get_coach_response(user_message: str, with_jobs: List[Dict] = None) -> Dict:
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