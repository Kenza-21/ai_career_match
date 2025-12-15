"""
Job Search Page
Page for searching jobs using natural language queries
"""
import streamlit as st
from services.api_client import api_client
from utils.session_manager import SessionManager
from components.layout import render_header, render_footer
from components.job_results import render_search_queries, render_job_summary, render_job_listings


def render_clarification_flow(response: dict):
    """Render clarification question flow"""
    if not response or not response.get("clarify"):
        return False
    
    question = response.get("question", "")
    st.warning(f"❓ {question}")
    
    clar_answer = st.text_input("Précisez :", key="clarify_input")
    if st.button("Envoyer", key="clarify_submit"):
        try:
            session_id = SessionManager.get_session_id()
            new_response = api_client.clarify_search(clar_answer, session_id)
            SessionManager.set_last_response(new_response)
            st.rerun()
        except Exception as exc:
            st.error(f"Erreur: {exc}")
    
    return True


def render_search_form():
    """Render job search form"""
    with st.form("search_form", clear_on_submit=False):
        query = st.text_input(
            "Votre requête",
            placeholder="ex: développeur backend télétravail",
            help="Décrivez le type d'emploi que vous recherchez"
        )
        submitted = st.form_submit_button("🔍 Lancer la recherche", use_container_width=True)
        
        if submitted and query:
            try:
                session_id = SessionManager.get_session_id()
                response = api_client.search_jobs(query, session_id)
                SessionManager.set_last_response(response)
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur: {exc}")


def render_search_results(response: dict):
    """Render search results"""
    if not response or response.get("clarify"):
        return
    
    # Display assistant message if available
    if response.get("assistant_message"):
        st.info(f"💬 {response.get('assistant_message')}")
    
    # Display search queries
    search_queries = response.get("search_queries", [])
    if search_queries:
        render_search_queries(search_queries)
    
    # Display summary
    results = response.get("results", {})
    summary = results.get("summary", {})
    if summary:
        render_job_summary(summary)
    
    # Display job listings
    jobs = results.get("jobs", [])
    if jobs:
        render_job_listings(jobs)
    else:
        st.info("Aucune offre trouvée pour cette recherche.")


def main():
    """Main page function"""
    render_header("Recherche d'emploi", "🔍")
    
    st.markdown(
        """
        Recherchez des offres d'emploi en utilisant des requêtes en langage naturel.
        Notre assistant intelligent comprend votre demande et trouve les meilleures correspondances.
        """
    )
    
    st.divider()
    
    # Search form
    render_search_form()
    
    # Get last response
    last_response = SessionManager.get_last_response()
    
    # Clarification flow
    if last_response:
        if render_clarification_flow(last_response):
            return
    
    # Display results
    if last_response:
        render_search_results(last_response)
    
    render_footer()


if __name__ == "__main__":
    main()

