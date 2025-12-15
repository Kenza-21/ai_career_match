"""
ATS Evaluator Display Components
Reusable components for displaying ATS evaluation results
"""
import streamlit as st
from typing import Dict


def render_ats_evaluation_results(result: Dict):
    """Render ATS evaluation results from Google Gemini"""
    if not result.get("success"):
        st.error(result.get("error", "Erreur d'évaluation ATS"))
        if result.get("error_details"):
            with st.expander("Détails de l'erreur"):
                st.code(result.get("error_details"), language="text")
        return
    
    evaluation = result.get("evaluation", {})
    ats_score = result.get("ats_score", 0)
    
    # Score header with color coding
    if ats_score >= 80:
        color = "🟢"
        bg_color = "#d4edda"
        status = "Excellent"
    elif ats_score >= 60:
        color = "🟡"
        bg_color = "#fff3cd"
        status = "Bon"
    elif ats_score >= 40:
        color = "🟠"
        bg_color = "#ffeaa7"
        status = "Moyen"
    else:
        color = "🔴"
        bg_color = "#f8d7da"
        status = "À améliorer"
    
    st.markdown(
        f"""
        <div style="background: {bg_color}; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #2c3e50;">
                {color} Score ATS: <strong>{ats_score}/100</strong>
            </h2>
            <p style="margin: 10px 0 0 0; font-size: 1.1em;">Statut: {status}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.divider()
    
    # Categories
    categories = [
        "Contact Information",
        "Spelling & Grammar",
        "Personal Pronoun Usage",
        "Skills & Keyword Targeting",
        "Complex or Long Sentences",
        "Generic or Weak Phrases",
        "Passive Voice Usage",
        "Quantified Achievements",
        "Required Resume Sections",
        "AI-generated Language",
        "Repeated Action Verbs",
        "Visual Formatting or Readability",
        "Personal Information / Bias Triggers",
        "Other Strengths and Weaknesses"
    ]
    
    # Group categories into tabs or sections
    for category in categories:
        category_data = evaluation.get(category, {})
        positives = category_data.get("Positives", [])
        negatives = category_data.get("Negatives", [])
        
        # Skip if no feedback
        if not positives and not negatives:
            continue
        
        with st.expander(f"📋 {category}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if positives:
                    st.success("✅ **Points Positifs**")
                    for item in positives:
                        st.write(f"• {item}")
                else:
                    st.info("Aucun point positif identifié")
            
            with col2:
                if negatives:
                    st.error("❌ **Points à Améliorer**")
                    for item in negatives:
                        st.write(f"• {item}")
                else:
                    st.success("Aucun point négatif identifié")
    
    # Metadata
    metadata = result.get("metadata", {})
    if metadata:
        with st.expander("ℹ️ Informations sur l'analyse", expanded=False):
            st.write(f"**Modèle**: {metadata.get('model', 'N/A')}")
            st.write(f"**Source**: {metadata.get('source', 'N/A')}")
            st.write(f"**Longueur du CV**: {metadata.get('resume_length', 0)} caractères")
            if metadata.get('timestamp'):
                st.write(f"**Date**: {metadata.get('timestamp')}")


def render_category_summary(evaluation: Dict):
    """Render a summary view of all categories"""
    categories = [
        "Contact Information",
        "Spelling & Grammar",
        "Personal Pronoun Usage",
        "Skills & Keyword Targeting",
        "Complex or Long Sentences",
        "Generic or Weak Phrases",
        "Passive Voice Usage",
        "Quantified Achievements",
        "Required Resume Sections",
        "AI-generated Language",
        "Repeated Action Verbs",
        "Visual Formatting or Readability",
        "Personal Information / Bias Triggers",
        "Other Strengths and Weaknesses"
    ]
    
    st.subheader("📊 Résumé par Catégorie")
    
    summary_data = []
    for category in categories:
        category_data = evaluation.get(category, {})
        positives_count = len(category_data.get("Positives", []))
        negatives_count = len(category_data.get("Negatives", []))
        
        if positives_count > 0 or negatives_count > 0:
            summary_data.append({
                "Catégorie": category,
                "✅ Positifs": positives_count,
                "❌ Négatifs": negatives_count,
                "Statut": "✅" if negatives_count == 0 else "⚠️" if negatives_count <= 2 else "❌"
            })
    
    if summary_data:
        st.dataframe(summary_data, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée disponible pour le résumé")
