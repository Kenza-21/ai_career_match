"""
Job Results Display Components
Reusable components for displaying job search results
"""
import streamlit as st
from typing import List, Dict


def render_search_queries(queries: List[Dict]):
    """Render generated search queries with links"""
    if not queries:
        return
    
    st.subheader("🔍 Requêtes générées")
    for query_item in queries:
        query_text = query_item.get('query', '')
        google_link = query_item.get('google_link', '')
        indeed_link = query_item.get('indeed_link', '')
        
        st.write(f"**{query_text}**")
        if google_link or indeed_link:
            links = []
            if google_link:
                links.append(f"[Google]({google_link})")
            if indeed_link:
                links.append(f"[Indeed]({indeed_link})")
            st.caption(" | ".join(links))


def render_job_summary(summary: Dict):
    """Render job search summary"""
    if not summary:
        return
    
    st.subheader("📊 Résumé")
    if isinstance(summary, dict):
        for key, value in summary.items():
            st.write(f"**{key}**: {value}")
    else:
        st.write(summary)


def render_job_listings(jobs: List[Dict]):
    """Render list of job listings"""
    if not jobs:
        st.info("Aucune offre trouvée.")
        return
    
    st.subheader("💼 Offres trouvées")
    
    for job in jobs:
        with st.container():
            job_title = job.get('job_title', 'Titre inconnu')
            match_score = job.get('match_score', 0)
            description = job.get('description', '')
            urls = job.get('all_search_urls') or {}
            
            # Job title and score
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{job_title}**")
            with col2:
                st.metric("Score", f"{match_score:.2f}")
            
            # Description preview
            if description:
                st.caption(description[:200] + ("..." if len(description) > 200 else ""))
            
            # External links - Stagiaires.ma is primary
            if urls:
                link_cols = st.columns(4)
                # Primary link: Stagiaires.ma (direct to job posting)
                stagiaires_url = urls.get('stagiaires_url') or urls.get('linkedin_url')
                if stagiaires_url:
                    link_cols[0].markdown(f"🔗 [Voir sur Stagiaires.ma]({stagiaires_url})", help="Lien direct vers l'offre d'emploi")
                if urls.get('rekrute_url'):
                    link_cols[1].markdown(f"[ReKrute]({urls['rekrute_url']})")
                if urls.get('google_url'):
                    link_cols[2].markdown(f"[Google]({urls['google_url']})")
                if urls.get('indeed_url'):
                    link_cols[3].markdown(f"[Indeed]({urls['indeed_url']})")
            
            st.divider()

