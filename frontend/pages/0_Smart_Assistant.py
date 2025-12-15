"""
Smart Assistant Page
AI-powered career coach chatbot with chat interface
"""
import streamlit as st
from datetime import datetime
from services.api_client import api_client
from components.layout import render_header, render_footer
from components.job_results import render_job_listings


# Initialize conversation history in session state
if "smart_assistant_messages" not in st.session_state:
    st.session_state.smart_assistant_messages = []


def render_chat_bubble(message: str, is_user: bool, timestamp: str = None):
    """Render a chat bubble for user or assistant messages"""
    bubble_class = "user-bubble" if is_user else "assistant-bubble"
    icon = "👤" if is_user else "🤖"
    
    # Create HTML for chat bubble
    bubble_html = f"""
    <div class="chat-container">
        <div class="{bubble_class}">
            <div class="bubble-header">
                <span class="bubble-icon">{icon}</span>
                <span class="bubble-sender">{'Vous' if is_user else 'Coach'}</span>
                {f'<span class="bubble-timestamp">{timestamp}</span>' if timestamp else ''}
            </div>
            <div class="bubble-content">
                {message}
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
    
    links_html = '<div class="chat-container"><div class="assistant-bubble"><div class="bubble-header"><span class="bubble-icon">🔗</span><span class="bubble-sender">Liens d\'emploi</span></div><div class="bubble-content"><ul style="margin: 0; padding-left: 20px;">'
    
    for url_item in search_urls:
        job_title = url_item.get("job_title", "Offre d'emploi")
        stagiaires_url = url_item.get("stagiaires_url") or url_item.get("linkedin_url")
        rekrute_url = url_item.get("rekrute_url")
        
        if stagiaires_url:
            links_html += f'<li><strong>{job_title}</strong>: <a href="{stagiaires_url}" target="_blank" style="color: #1f77b4;">Voir sur Stagiaires.ma</a></li>'
        if rekrute_url:
            links_html += f'<li><strong>{job_title}</strong>: <a href="{rekrute_url}" target="_blank" style="color: #1f77b4;">Voir sur ReKrute</a></li>'
    
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
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        animation: slideInRight 0.3s ease-out;
    }
    
    .assistant-bubble {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2c3e50;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin-right: auto;
        max-width: 75%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        animation: slideInLeft 0.3s ease-out;
        border-left: 3px solid #667eea;
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
        line-height: 1.5;
        word-wrap: break-word;
    }
    
    .bubble-content ul {
        margin: 8px 0;
    }
    
    .bubble-content a {
        text-decoration: none;
        font-weight: 500;
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
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
        font-size: 1em;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stButton > button {
        border-radius: 25px;
        padding: 10px 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .user-bubble, .assistant-bubble {
            max-width: 85%;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def add_message_to_history(content: str, is_user: bool, metadata: dict = None):
    """Add a message to conversation history"""
    timestamp = datetime.now().strftime("%H:%M")
    message = {
        "content": content,
        "is_user": is_user,
        "timestamp": timestamp,
        "metadata": metadata or {}
    }
    st.session_state.smart_assistant_messages.append(message)


def render_chat_interface():
    """Render the main chat interface"""
    render_chat_css()
    
    # Display conversation history
    if st.session_state.smart_assistant_messages:
        st.markdown("### 💬 Conversation")
        st.markdown("---")
        
        for msg in st.session_state.smart_assistant_messages:
            render_chat_bubble(
                msg["content"],
                msg["is_user"],
                msg.get("timestamp")
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
                    
                    with st.expander(f"💼 Voir {len(normalized_jobs)} offres d'emploi", expanded=False):
                        render_job_listings(normalized_jobs)
    else:
        st.info("👋 Bonjour ! Je suis votre coach de carrière. Posez-moi une question ou décrivez ce que vous recherchez.")


def handle_smart_assistant_request(message: str, clarification: str = None):
    """Handle smart assistant API request and update conversation"""
    try:
        with st.spinner("🤖 Le coach réfléchit..."):
            response = api_client.smart_assistant_search(message, clarification)
            
            # Add user message to history
            add_message_to_history(message, is_user=True)
            
            # Extract assistant response
            assistant_response = response.get("assistant_response", "Désolé, je n'ai pas pu générer de réponse.")
            
            # Prepare metadata
            metadata = {
                "jobs": response.get("jobs", []),
                "search_urls": response.get("search_urls", []),
                "intent": response.get("intent", ""),
                "needs_clarification": response.get("needs_clarification", False),
                "clarification_questions": response.get("clarification_questions", [])
            }
            
            # Add assistant response to history
            add_message_to_history(assistant_response, is_user=False, metadata=metadata)
            
            # Handle clarification if needed
            if response.get("needs_clarification") and response.get("clarification_questions"):
                clarification_msg = "**Questions de clarification:**\n\n"
                for i, question in enumerate(response.get("clarification_questions", []), 1):
                    clarification_msg += f"{i}. {question}\n"
                add_message_to_history(clarification_msg, is_user=False, metadata={"is_clarification": True})
            
            return response
    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        add_message_to_history(error_msg, is_user=False)
        st.error(error_msg)
        return None


def render_chat_input():
    """Render chat input form"""
    st.markdown("---")
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    # Check if we're waiting for clarification
    last_message = st.session_state.smart_assistant_messages[-1] if st.session_state.smart_assistant_messages else None
    needs_clarification = last_message and last_message.get("metadata", {}).get("needs_clarification", False)
    
    if needs_clarification:
        placeholder = "Répondez aux questions ci-dessus..."
        input_key = "clarification_input"
    else:
        placeholder = "Posez votre question ou décrivez ce que vous recherchez..."
        input_key = "message_input"
    
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",  # Add a non-empty label
                placeholder=placeholder,
                key=input_key,
                label_visibility="collapsed"  # Hide the label visually but keep it for accessibility
            )
        
        with col2:
            submit_button = st.form_submit_button("📤", use_container_width=True)
        
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
    render_header("Assistant Intelligent", "🤖")
    
    st.markdown(
        """
        **Coach de Carrière Intelligent**
        
        Votre coach personnel pour la recherche d'emploi ! Cet assistant utilise l'IA
        pour vous guider, vous conseiller, et vous aider à prendre les meilleures décisions.
        
        **Fonctionnalités:**
        - 💬 Réponses en langage naturel et conversationnel
        - 🎯 Guidance personnalisée quand vous êtes perdu
        - ⚖️ Comparaison détaillée d'offres d'emploi
        - 💡 Conseils basés sur le marché tech marocain
        - 🔍 Recherche intelligente avec contexte
        """
    )
    
    st.divider()
    
    # Render chat interface
    render_chat_interface()
    
    # Render chat input
    render_chat_input()
    
    # Clear conversation button
    if st.session_state.smart_assistant_messages:
        if st.button("🗑️ Effacer la conversation", use_container_width=True):
            st.session_state.smart_assistant_messages = []
            st.rerun()
    
    render_footer()


if __name__ == "__main__":
    main()
