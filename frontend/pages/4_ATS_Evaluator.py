"""
ATS Evaluator Page
Page for evaluating CV using Google Gemini ATS evaluator
"""
import streamlit as st
from services.api_client import api_client
from utils.session_manager import SessionManager
from components.layout import render_header, render_footer
from components.ats_evaluator import render_ats_evaluation_results, render_category_summary


def render_evaluation_form():
    """Render ATS evaluation form"""
    with st.form("ats_evaluation_form", clear_on_submit=False):
        st.subheader("📄 Uploader votre CV")
        
        cv_file = st.file_uploader(
            "CV à évaluer (PDF/DOCX/TXT)",
            type=["pdf", "docx", "txt"],
            help="Téléchargez votre CV pour une évaluation ATS complète",
            key="ats_eval_cv_file"
        )
        
        st.markdown("**OU**")
        
        cv_text = st.text_area(
            "Collez votre CV (texte)",
            height=200,
            help="Si vous n'avez pas de fichier, collez le texte de votre CV ici",
            placeholder="Collez le contenu de votre CV ici...",
            key="ats_eval_cv_text"
        )
        
        submitted = st.form_submit_button("🔍 Évaluer avec Google Gemini", use_container_width=True)
        
        if submitted:
            if not cv_file and not cv_text.strip():
                st.warning("⚠️ Veuillez fournir un CV (fichier ou texte) pour l'évaluation.")
            else:
                try:
                    session_id = SessionManager.get_session_id()
                    with st.spinner("🔍 Analyse en cours avec Google Gemini..."):
                        result = api_client.evaluate_ats_resume(
                            cv_file=cv_file,
                            cv_text=cv_text,
                            session_id=session_id
                        )
                    SessionManager.set_last_response(result)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erreur d'appel API: {exc}")


def render_evaluation_results():
    """Render ATS evaluation results if available"""
    result = SessionManager.get_last_response()
    
    if result and result.get("success") and "evaluation" in result:
        st.divider()
        render_ats_evaluation_results(result)
        
        # Category summary
        evaluation = result.get("evaluation", {})
        if evaluation:
            st.divider()
            render_category_summary(evaluation)
    elif result and not result.get("success"):
        st.error(f"Erreur: {result.get('error', 'Erreur inconnue')}")


def main():
    """Main page function"""
    render_header("Évaluation ATS du CV", "🔍")
    
    st.markdown(
        """
        Évaluez votre CV avec l'IA Google Gemini pour identifier les points forts et les améliorations 
        à apporter pour optimiser votre passage dans les systèmes ATS (Applicant Tracking Systems).
        
        ### Analyse complète sur 14 catégories:
        
        - **Contact Information** - Informations de contact
        - **Spelling & Grammar** - Orthographe et grammaire
        - **Personal Pronoun Usage** - Utilisation des pronoms personnels
        - **Skills & Keyword Targeting** - Compétences et mots-clés
        - **Complex or Long Sentences** - Phrases complexes ou longues
        - **Generic or Weak Phrases** - Phrases génériques ou faibles
        - **Passive Voice Usage** - Utilisation de la voix passive
        - **Quantified Achievements** - Réalisations quantifiées
        - **Required Resume Sections** - Sections requises du CV
        - **AI-generated Language** - Détection de langage généré par IA
        - **Repeated Action Verbs** - Répétition des verbes d'action
        - **Visual Formatting or Readability** - Formatage et lisibilité
        - **Personal Information / Bias Triggers** - Informations personnelles / biais
        - **Other Strengths and Weaknesses** - Autres forces et faiblesses
        """
    )
    
    st.info(
        "💡 **Conseil**: L'évaluation utilise Google Gemini 2.5 Flash pour analyser votre CV de manière "
        "professionnelle et vous fournir des recommandations concrètes pour améliorer votre score ATS."
    )
    
    st.divider()
    
    # Evaluation form
    render_evaluation_form()
    
    # Display results
    render_evaluation_results()
    
    render_footer()


if __name__ == "__main__":
    main()
