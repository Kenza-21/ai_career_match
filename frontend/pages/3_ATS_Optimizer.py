"""
ATS Optimizer Page
Page for optimizing CV for ATS (Applicant Tracking Systems)
"""
import streamlit as st
from services.api_client import api_client
from utils.session_manager import SessionManager
from components.layout import render_header, render_footer
from components.ats_optimizer import render_ats_results


def render_ats_form():
    """Render ATS optimization form"""
    with st.form("ats_form", clear_on_submit=False):
        st.subheader("📄 Uploader votre CV")
        
        ats_cv_file = st.file_uploader(
            "CV à optimiser (PDF/DOCX/TXT)",
            type=["pdf", "docx", "txt"],
            help="Téléchargez votre CV pour générer une version optimisée ATS",
            key="ats_cv_file"
        )
        
        st.divider()
        
        target_role = st.text_input(
            "Rôle cible (optionnel)",
            help="Spécifiez le rôle cible pour une optimisation personnalisée",
            key="ats_target_role",
            placeholder="ex: Développeur Full Stack"
        )
        
        submitted = st.form_submit_button("✨ Optimiser", use_container_width=True)
        
        if submitted:
            if not ats_cv_file:
                st.warning("⚠️ Veuillez fournir un CV (fichier) pour l'optimiser.")
            else:
                try:
                    session_id = SessionManager.get_session_id()
                    result = api_client.optimize_ats_cv(
                        cv_file=ats_cv_file,
                        target_role=target_role,
                        session_id=session_id
                    )
                    SessionManager.set_last_response(result)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erreur d'appel API: {exc}")


def render_optimization_results():
    """Render ATS optimization results if available"""
    last_response = SessionManager.get_last_response()
    
    if last_response and isinstance(last_response, dict):
        if last_response.get("success") or "ats_latex" in last_response:
            st.divider()
            st.subheader("✨ Résultats de l'optimisation")
            render_ats_results(last_response)


def main():
    """Main page function"""
    render_header("Optimisation ATS du CV", "✨")
    
    st.markdown(
        """
        Optimisez votre CV pour les systèmes ATS (Applicant Tracking Systems).
        Générez une version LaTeX professionnelle et ATS-compliant de votre CV.
        """
    )
    
    st.info(
        "💡 **Conseil**: Les CV optimisés ATS sont formatés pour être facilement "
        "lus par les systèmes de recrutement automatisés, augmentant vos chances "
        "de passer les filtres initiaux."
    )
    
    st.divider()
    
    # ATS optimization form
    render_ats_form()
    
    # Display results
    render_optimization_results()
    
    render_footer()


if __name__ == "__main__":
    main()

