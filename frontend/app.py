"""
Main Streamlit Application
Entry point with navigation and consistent layout
"""
import streamlit as st
from components.layout import render_footer


# Page configuration
st.set_page_config(
    page_title="Assistant++ - Career Match",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# Main page content
st.title("🤖 Assistant++ - Career Match")
st.markdown(
    """
    ## Bienvenue sur Assistant++
    
    Plateforme intelligente de recherche d'emploi et d'optimisation de CV 
    pour le marché marocain.
    
    ### Fonctionnalités disponibles:
    
    - **🔍 Assistant**: Recherche d'emploi avec analyse de patterns
    - **🤖 Assistant Intelligent**: Recherche d'emploi avec IA et clarification
    - **📄 Analyse CV**: Analysez la correspondance entre votre CV et une offre
    - **✨ Optimisation ATS**: Générez une version optimisée de votre CV pour les systèmes ATS
    - **🔍 Évaluation ATS**: Évaluez votre CV avec Google Gemini sur 14 catégories
    
    Utilisez le menu de navigation à gauche pour accéder aux différentes fonctionnalités.
    """
)

st.info(
    "💡 **Note**: Assurez-vous que le backend est en cours d'exécution sur "
    "`http://localhost:8000` pour que l'application fonctionne correctement."
)

render_footer()

