"""
Smart Assistant Page
AI-powered career coach chatbot with chat interface
"""
import streamlit as st
from datetime import datetime
from services.api_client import api_client
from components.layout import render_header, render_footer
from components.job_results import render_job_listings

import re
# Initialize conversation history in session state
if "smart_assistant_messages" not in st.session_state:
    st.session_state.smart_assistant_messages = []


def render_chat_bubble(message: str, is_user: bool, timestamp: str = None, is_coach: bool = True):
    """Render a chat bubble for user or assistant messages"""
    bubble_class = "user-bubble" if is_user else "assistant-bubble"
    
    # CHANGEMENT ICI : Différencier le coach de l'assistant normal
    if is_coach and not is_user:
        icon = "🧠"  # Icône coach (cerveau)
        sender = "Coach Karim"
        bubble_color = "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"  # Bleu coach
    elif not is_user:
        icon = "🤖"
        sender = "Assistant"
        bubble_color = "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)"
    else:
        icon = "👤"
        sender = "Vous"
        bubble_color = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    
    # Create HTML for chat bubble
    cleaned_message = message.replace('\n', '<br>')
    
    # CHANGEMENT ICI : Si c'est une liste numérotée, la formater proprement
    if re.search(r'\d+\.\s+', message) and '\n' in message:
        lines = message.split('\n')
        formatted_lines = []
        for line in lines:
            if re.match(r'\d+\.\s+', line):
                formatted_lines.append(f'<strong>{line}</strong><br>')
            elif line.strip():
                formatted_lines.append(f'{line}<br>')
        cleaned_message = ''.join(formatted_lines)
    
    # Create HTML for chat bubble
    bubble_html = f"""
    <div class="chat-container">
        <div class="{bubble_class}" style="background: {bubble_color if is_coach and not is_user else ''};">
            <div class="bubble-header">
                <span class="bubble-icon">{icon}</span>
                <span class="bubble-sender">{sender}</span>
                {f'<span class="bubble-timestamp">{timestamp}</span>' if timestamp else ''}
            </div>
            <div class="bubble-content">
                {cleaned_message}
            </div>
        </div>
    </div>
    """
    st.markdown(bubble_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

def render_job_links_bubble(search_urls: list):
    """Render job links in a special bubble"""
    if not search_urls:
        return
    
    links_html = '''
    <div class="chat-container">
        <div class="assistant-bubble" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
            <div class="bubble-header">
                <span class="bubble-icon">🔗</span>
                <span class="bubble-sender">Liens d'emploi</span>
            </div>
            <div class="bubble-content">
                <ul style="margin: 0; padding-left: 20px;">
    '''
    
    for url_item in search_urls:
        job_title = url_item.get("job_title", "Offre d'emploi")
        stagiaires_url = url_item.get("stagiaires_url") or url_item.get("linkedin_url")
        rekrute_url = url_item.get("rekrute_url")
        
        if stagiaires_url:
            links_html += f'<li><strong>{job_title}</strong>: <a href="{stagiaires_url}" target="_blank" style="color: #1f77b4; font-weight: 500;">Voir sur Stagiaires.ma</a></li>'
        if rekrute_url:
            links_html += f'<li><strong>{job_title}</strong>: <a href="{rekrute_url}" target="_blank" style="color: #1f77b4; font-weight: 500;">Voir sur ReKrute</a></li>'
    
    links_html += '</ul></div></div></div>'
    st.markdown(links_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_chat_css():
    """Inject CSS for chat bubbles"""
    css = """
    <style>
    .chat-container {
        margin: 10px 0;
        display: flex;
        flex-direction: column;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin-left: auto;
        max-width: 75%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        animation: slideInRight 0.3s ease-out;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .assistant-bubble {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2c3e50;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin-right: auto;
        max-width: 75%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        animation: slideInLeft 0.3s ease-out;
        border-left: 4px solid #4facfe;
    }
    
    .coach-bubble {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
        color: white !important;
        border-left: 4px solid #ff9a9e !important;
        box-shadow: 0 6px 16px rgba(79, 172, 254, 0.3) !important;
    }
    
    .bubble-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-size: 0.85em;
        opacity: 0.9;
    }
    
    .bubble-icon {
        font-size: 1.1em;
    }
    
    .bubble-sender {
        font-weight: 600;
    }
    
    .bubble-timestamp {
        font-size: 0.75em;
        opacity: 0.7;
        margin-left: auto;
    }
    
    .bubble-content {
        line-height: 1.6;
        word-wrap: break-word;
        font-size: 0.95em;
    }
    
    .bubble-content ul {
        margin: 8px 0;
    }
    
    .bubble-content a {
        text-decoration: none;
        font-weight: 500;
        color: #1f77b4 !important;
    }
    
    .bubble-content a:hover {
        text-decoration: underline;
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 15px 0;
        border-top: 1px solid #e0e0e0;
        margin-top: 20px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
        font-size: 1em;
        transition: all 0.3s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4facfe;
        box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.2);
    }
    
    .stButton > button {
        border-radius: 25px;
        padding: 10px 30px;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
    }
    
    .stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Coaching style indicators */
    .coach-indicator {
        display: inline-block;
        background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 100%);
        color: white;
        font-size: 0.75em;
        padding: 2px 8px;
        border-radius: 12px;
        margin-left: 8px;
        font-weight: bold;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .user-bubble, .assistant-bubble {
            max-width: 85%;
        }
        
        .bubble-content {
            font-size: 0.9em;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def add_message_to_history(content: str, is_user: bool, metadata: dict = None, is_coach: bool = True):
    """Add a message to conversation history"""
    timestamp = datetime.now().strftime("%H:%M")
    message = {
        "content": content,
        "is_user": is_user,
        "timestamp": timestamp,
        "metadata": metadata or {},
        "is_coach": is_coach if not is_user else False
    }
    st.session_state.smart_assistant_messages.append(message)


def render_chat_interface():
    """Render the main chat interface"""
    render_chat_css()
    
    # Display conversation history
    if st.session_state.smart_assistant_messages:
        st.markdown("### 💬 Conversation avec le Coach ")
        st.markdown('<div class="coach-indicator">🧠 Coach IA</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        for msg in st.session_state.smart_assistant_messages:
            render_chat_bubble(
                msg["content"],
                msg["is_user"],
                msg.get("timestamp"),
                is_coach=msg.get("is_coach", True)
            )
            
            # Render job links if present
            if not msg["is_user"] and msg.get("metadata", {}).get("search_urls"):
                render_job_links_bubble(msg["metadata"]["search_urls"])
            
            # Render jobs if present
            if not msg["is_user"] and msg.get("metadata", {}).get("jobs"):
                jobs = msg["metadata"]["jobs"]
                if jobs:
                    # Normalize job format for rendering
                    normalized_jobs = []
                    for job in jobs:
                        normalized_job = {
                            "job_title": job.get("job_title", "Titre inconnu"),
                            "match_score": job.get("match_score", 0),
                            "description": job.get("description") or job.get("description_preview", ""),
                            "category": job.get("category", ""),
                            "demand_level": job.get("demand_level", ""),
                            "salary_range": job.get("salary_range") or job.get("avg_salary_mad", ""),
                            "required_skills": job.get("required_skills", ""),
                            "all_search_urls": job.get("all_search_urls", {}),
                            "stagiaires_url": job.get("stagiaires_url", ""),
                            "rekrute_url": job.get("rekrute_url", "")
                        }
                        # If no all_search_urls but we have individual URLs, create it
                        if not normalized_job["all_search_urls"]:
                            normalized_job["all_search_urls"] = {
                                "stagiaires_url": normalized_job.get("stagiaires_url", ""),
                                "rekrute_url": normalized_job.get("rekrute_url", "")
                            }
                        normalized_jobs.append(normalized_job)
                    
                    with st.expander(f"💼 Voir {len(normalized_jobs)} offres d'emploi (conseillées par Karim)", expanded=False):
                        st.info("📊 Ces offres correspondent à votre recherche et aux conseils du coach")
                        render_job_listings(normalized_jobs)
    else:
        # CHANGEMENT ICI : Message d'accueil du coach
        st.markdown("### 🧠 Coach Karim - Prêt à vous aider")
        st.markdown("---")
        
        st.info("""
        Bonjour ! Je suis Karim, votre coach de carrière tech marocain. 
        
        Avec 15 ans d'expérience dans le recrutement au Maroc, je suis là pour vous aider à :
        - Trouver votre voie dans la tech marocaine
        - Comparer des options de carrière
        - Obtenir des conseils pratiques sur le marché local
        - Trouver les meilleures opportunités d'emploi
        
        Parlez-moi naturellement, comme à un mentor :
        - "Je suis perdu, je veux travailler en tech"
        - "Dev frontend vs backend au Maroc ?"
        - "Quelles opportunités en data science à Casablanca ?"
        - "Comment me reconvertir dans le développement ?"
        """)

def handle_smart_assistant_request(message: str, clarification: str = None):
    """Handle smart assistant API request and update conversation"""
    try:
        with st.spinner("🧠 Karim réfléchit à votre situation..."):
            response = api_client.smart_assistant_search(message, clarification)
            
            # Add user message to history
            add_message_to_history(message, is_user=True)
            
            # Extract assistant response
            assistant_response = response.get("assistant_response", "Désolé, je n'ai pas pu générer de réponse.")
            
            # Vérifier si c'est une réponse de coaching
            is_coach_response = response.get("is_coaching", True)
            
            # Prepare metadata
            metadata = {
                "jobs": response.get("jobs", []),
                "search_urls": response.get("search_urls", []),
                "intent": response.get("intent", ""),
                "needs_clarification": response.get("needs_clarification", False),
                "clarification_questions": response.get("clarification_questions", []),
                "is_coach": is_coach_response
            }
            
            # Add coach response to history
            add_message_to_history(
                assistant_response, 
                is_user=False, 
                metadata=metadata,
                is_coach=is_coach_response
            )
            
            # Handle clarification if needed
            if response.get("needs_clarification") and response.get("clarification_questions"):
                clarification_msg = "Pour mieux vous aider, Karim vous demande :\n\n"
                for i, question in enumerate(response.get("clarification_questions", []), 1):
                    clarification_msg += f"{i}.{question}\n"
                add_message_to_history(
                    clarification_msg, 
                    is_user=False, 
                    metadata={"is_clarification": True},
                    is_coach=True
                )
            
            return response
    except Exception as e:
        error_msg = f"❌ Désolé, une erreur technique est survenue. Karim revient bientôt !\n\n*(Détail : {str(e)})*"
        add_message_to_history(error_msg, is_user=False, is_coach=True)
        st.error("Une erreur est survenue avec le coach")
        return None


def render_chat_input():
    """Render chat input form"""
    st.markdown("---")
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    # Check if we're waiting for clarification
    last_message = st.session_state.smart_assistant_messages[-1] if st.session_state.smart_assistant_messages else None
    needs_clarification = last_message and last_message.get("metadata", {}).get("needs_clarification", False)
    
    if needs_clarification:
        placeholder = "Répondez aux questions de Karim ci-dessus..."
        input_key = "clarification_input"
    else:
        placeholder = "Parlez à Karim, votre coach (ex: 'Je suis perdu', 'Dev vs Data', 'Offres React Casablanca'...)"
        input_key = "message_input"
    
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder=placeholder,
                key=input_key,
                label_visibility="collapsed"
            )
        
        with col2:
            submit_button = st.form_submit_button("📤 Envoyer", use_container_width=True)
        
        if submit_button and user_input:
            # Get original message if this is a clarification
            if needs_clarification:
                # Find the last user message before the clarification request
                original_message = ""
                for msg in reversed(st.session_state.smart_assistant_messages):
                    if msg["is_user"]:
                        original_message = msg["content"]
                        break
                
                if original_message:
                    handle_smart_assistant_request(original_message, clarification=user_input)
                else:
                    # Fallback: use the clarification as the main message
                    handle_smart_assistant_request(user_input)
            else:
                handle_smart_assistant_request(user_input)
            
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main page function"""
    # CHANGEMENT ICI : Nouveau titre et description du coach
    render_header("Coach Karim - Assistant Intelligent", "🧠")
    
    st.markdown(
    """
    ### Coach de Carrière Tech Marocain
        
    Karim est votre coach personnel spécialisé dans le marché tech marocain. 
    Avec 15 ans d'expérience dans le recrutement, il vous guide comme un vrai mentor.
    
    ✨ Ce que Karim fait différemment :
    - 🧠 Pense comme un coach humain, pas comme un bot
    - 🇲🇦 Connaît le marché marocain (salaires, entreprises, tendances)
    - 💬 Réponses naturelles avec empathie et franchise
    - 🎯 Analyse votre vraie situation derrière les mots
    - ⚖️ Compare objectivement les options de carrière
    
    🎯 Scénarios où Karim excelle :
    1. "Je suis perdu dans ma carrière tech" → Orientation personnalisée
    2. "Dev frontend vs backend au Maroc ?" → Comparaison détaillée
    3. "Conseils pour débuter en data science" → Guide pratique étape par étape
    4. "Quelles entreprises recrutent à Casablanca ?" → Insights marché local
    5. "Comment me reconvertir ?" → Stratégie de transition
    
    💡 Astuce : Parlez-lui naturellement, comme à un mentor expérimenté !
    """
)
    
    st.divider()
    
    # Render chat interface
    render_chat_interface()
    
    # Render chat input
    render_chat_input()
    
    # Clear conversation button
    if st.session_state.smart_assistant_messages:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("💭 Conversation avec Karim - Votre coach personnel")
        with col2:
            if st.button("🗑️ Nouvelle discussion", use_container_width=True):
                st.session_state.smart_assistant_messages = []
                st.rerun()
    
    render_footer()


if __name__ == "__main__":
    main()