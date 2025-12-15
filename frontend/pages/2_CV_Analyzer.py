"""
CV Analyzer Page
Page for analyzing CV against job descriptions
"""
import streamlit as st
from services.api_client import api_client
from utils.session_manager import SessionManager
from components.layout import render_header, render_footer
from components.cv_analysis import render_cv_analysis_results


def render_cv_upload_form():
    """Render CV upload and analysis form"""
    with st.form("cv_form", clear_on_submit=False):
        st.subheader("📄 Uploader votre CV")
        
        uploaded_cv = st.file_uploader(
            "Fichier CV (PDF/DOCX/TXT)",
            type=["pdf", "docx", "txt"],
            help="Téléchargez votre CV au format PDF, DOCX ou TXT"
        )
        
        st.markdown("**OU**")
        
        cv_text_input = st.text_area(
            "Collez votre CV (texte)",
            height=150,
            help="Si vous n'avez pas de fichier, collez le texte de votre CV ici",
            placeholder="Collez le contenu de votre CV ici..."
        )
        
        st.divider()
        
        st.subheader("🎯 Description de l'offre")
        jd_text = st.text_area(
            "Description de l'offre d'emploi",
            height=150,
            help="Collez la description complète de l'offre d'emploi",
            placeholder="Collez la description de l'offre ici..."
        )
        
        submitted = st.form_submit_button("🔍 Analyser", use_container_width=True)
        
        if submitted:
            if (not uploaded_cv and not cv_text_input.strip()) or not jd_text.strip():
                st.warning("⚠️ Veuillez fournir un CV (fichier ou texte) et une description d'offre.")
            else:
                try:
                    session_id = SessionManager.get_session_id()
                    result = api_client.analyze_cv(
                        cv_file=uploaded_cv,
                        cv_text=cv_text_input,
                        job_description=jd_text,
                        session_id=session_id
                    )
                    SessionManager.set_last_response(result)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erreur d'appel API: {exc}")


def render_analysis_results():
    """Render CV analysis results if available"""
    last_response = SessionManager.get_last_response()
    
    if last_response and isinstance(last_response, dict):
        if last_response.get("success") or "score" in last_response:
            st.divider()
            st.subheader("📊 Résultats de l'analyse")
            render_cv_analysis_results(last_response)


def main():
    """Main page function"""
    render_header("Analyse CV vs Offre", "📄")
    
    st.markdown(
        """
        Analysez la correspondance entre votre CV et une offre d'emploi.
        Obtenez un score de matching, identifiez les compétences communes et manquantes.
        """
    )
    
    st.divider()
    
    # CV upload form
    render_cv_upload_form()
    
    # Display results
    render_analysis_results()
    
    render_footer()


if __name__ == "__main__":
    main()

