"""
Assistant Page
Basic pattern-based assistant for job search
"""
import streamlit as st
from services.api_client import api_client
from components.layout import render_header, render_footer
from components.job_results import render_job_listings


def render_assistant_form():
    """Render assistant input form"""
    with st.form("assistant_form", clear_on_submit=False):
        message = st.text_input(
            "Votre demande",
            placeholder="ex: développeur backend télétravail",
            help="Décrivez le type d'emploi que vous recherchez"
        )
        submitted = st.form_submit_button("🔍 Rechercher", use_container_width=True)
        
        if submitted and message:
            try:
                with st.spinner("Recherche en cours..."):
                    response = api_client.assistant_search(message)
                    st.session_state.assistant_response = response
                    st.rerun()
            except Exception as exc:
                st.error(f"Erreur: {exc}")


def render_assistant_results(response: dict):
    """Render assistant search results"""
    if not response:
        return
    
    # Display assistant message
    if response.get("summary"):
        st.info(f"💬 {response.get('summary')}")
    
    # Display jobs
    jobs = response.get("jobs", [])
    if jobs:
        render_job_listings(jobs)
    else:
        st.info("Aucune offre trouvée pour cette recherche.")
    
    # Display debug info if available
    if response.get("debug_info"):
        with st.expander("ℹ️ Informations de debug"):
            st.json(response.get("debug_info"))


def main():
    """Main page function"""
    render_header("Assistant de Recherche", "🔍")
    
    st.markdown(
        """
        **Assistant de Recherche d'Emploi**
        
        Utilisez des requêtes en langage naturel pour rechercher des offres d'emploi.
        L'assistant analyse votre demande et trouve les meilleures correspondances.
        """
    )
    
    st.divider()
    
    # Assistant form
    render_assistant_form()
    
    # Display results
    if "assistant_response" in st.session_state:
        st.divider()
        render_assistant_results(st.session_state.assistant_response)
    
    render_footer()


if __name__ == "__main__":
    main()

