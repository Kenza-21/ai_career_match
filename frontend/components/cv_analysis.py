"""
CV Analysis Display Components
Professional coaching assistant-like interface for CV analysis results
"""
import streamlit as st
from typing import Dict, List


def render_cv_analysis_results(result: Dict):
    """Render CV analysis results in a professional coaching assistant style"""
    if not result:
        st.warning("Aucun résultat d'analyse disponible.")
        return
    
    # Check if this is the new format (from /cv/analyze-upload) or old format (from /cv_analyser)
    has_new_format = "match_score" in result or "score_analysis" in result
    has_old_format = "score" in result and "success" in result
    
    if has_old_format and not result.get("success"):
        st.error(result.get("error", "Erreur d'analyse"))
        return
    
    # Render header with score
    render_score_header(result, has_new_format)
    
    st.divider()
    
    # Render skills comparison
    render_skills_comparison(result, has_new_format)
    
    st.divider()
    
    # Render skill gaps analysis
    render_skill_gaps(result, has_new_format)
    
    st.divider()
    
    # Render course recommendations
    render_course_recommendations(result, has_new_format)
    
    # Render additional recommendations if available
    if has_new_format:
        if result.get("key_phrases"):
            st.divider()
            render_key_phrases(result.get("key_phrases"))
        
        if result.get("ats_recommendations"):
            st.divider()
            render_ats_recommendations(result.get("ats_recommendations"))
        
        if result.get("overall_assessment"):
            st.divider()
            render_overall_assessment(result)


def render_score_header(result: Dict, new_format: bool):
    """Render the score header with visual indicators"""
    if new_format:
        score = result.get("match_score", 0)
        score_pct = int(score * 100) if score <= 1 else int(score)
        assessment = result.get("overall_assessment", "")
        confidence = result.get("confidence_level", "")
    else:
        score_pct = result.get("score", 0)
        assessment = ""
        confidence = ""
    
    # Color coding based on score
    if score_pct >= 70:
        color = "🟢"
        bg_color = "#d4edda"
    elif score_pct >= 50:
        color = "🟡"
        bg_color = "#fff3cd"
    elif score_pct >= 30:
        color = "🟠"
        bg_color = "#ffeaa7"
    else:
        color = "🔴"
        bg_color = "#f8d7da"
    
    st.markdown(
        f"""
        <div style="background: {bg_color}; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #2c3e50;">
                {color} Score de Matching: <strong>{score_pct}%</strong>
            </h2>
            {f'<p style="margin: 10px 0 0 0; font-size: 1.1em;">{assessment}</p>' if assessment else ''}
            {f'<p style="margin: 5px 0 0 0; color: #666;">Niveau de confiance: {confidence}</p>' if confidence else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_skills_comparison(result: Dict, new_format: bool):
    """Render skills comparison in a clear, visual way"""
    st.subheader("📊 Analyse des Compétences")
    
    if new_format:
        cv_skills = result.get("cv_skills", [])
        job_skills = result.get("job_skills", [])
        summary = result.get("summary", {})
        common_skills = summary.get("common_skills", [])
        coverage = summary.get("coverage", "0%")
    else:
        cv_skills = result.get("cv_keywords", [])
        job_skills = result.get("job_keywords", [])
        common_skills = result.get("matched_skills", [])
        # Use coverage_percentage if available, otherwise calculate
        if result.get("coverage_percentage") is not None:
            coverage = f"{result.get('coverage_percentage')}%"
        elif result.get("coverage"):
            coverage = result.get("coverage")
        else:
            coverage = f"{len(common_skills) / len(job_skills) * 100:.1f}%" if job_skills else "0%"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Compétences CV", len(cv_skills))
        if cv_skills:
            with st.expander("Voir toutes les compétences CV", expanded=False):
                for skill in cv_skills[:30]:
                    st.write(f"• {skill}")
    
    with col2:
        st.metric("Compétences demandées", len(job_skills))
        if job_skills:
            with st.expander("Voir toutes les compétences demandées", expanded=False):
                for skill in job_skills[:30]:
                    st.write(f"• {skill}")
    
    with col3:
        st.metric("Compétences communes", len(common_skills))
        st.caption(f"Couverture: {coverage}")
        if common_skills:
            with st.expander("Voir les compétences communes", expanded=False):
                for skill in common_skills[:20]:
                    st.success(f"✅ {skill}")


def render_skill_gaps(result: Dict, new_format: bool):
    """Render skill gaps with severity indicators"""
    st.subheader("🎯 Compétences Manquantes")
    
    if new_format:
        skill_gaps = result.get("skill_gaps", [])
        missing_skills = result.get("missing_skills", [])
    else:
        missing_skills = result.get("missing_skills", [])
        skill_gaps = [{"skill_name": skill, "gap_severity": "medium", "importance": "Moyenne"} 
                     for skill in missing_skills]
    
    if not skill_gaps and not missing_skills:
        st.success("🎉 Excellent ! Toutes les compétences requises sont présentes dans votre CV.")
        return
    
    # Group by severity
    high_priority = [gap for gap in skill_gaps if gap.get("gap_severity") == "high" or gap.get("importance") == "Essentielle"]
    medium_priority = [gap for gap in skill_gaps if gap.get("gap_severity") == "medium" or gap.get("importance") == "Importante"]
    low_priority = [gap for gap in skill_gaps if gap.get("gap_severity") == "low" or gap.get("importance") == "Secondaire"]
    
    if high_priority:
        st.warning(f"🔴 **Priorité Haute** ({len(high_priority)} compétences)")
        for gap in high_priority:
            skill_name = gap.get("skill_name", "")
            suggestion = gap.get("suggestion", f"Formation recommandée en {skill_name}")
            st.write(f"• **{skill_name}**: {suggestion}")
    
    if medium_priority:
        st.info(f"🟡 **Priorité Moyenne** ({len(medium_priority)} compétences)")
        for gap in medium_priority:
            skill_name = gap.get("skill_name", "")
            suggestion = gap.get("suggestion", f"Formation recommandée en {skill_name}")
            st.write(f"• **{skill_name}**: {suggestion}")
    
    if low_priority:
        st.caption(f"🟢 **Priorité Basse** ({len(low_priority)} compétences)")
        for gap in low_priority:
            skill_name = gap.get("skill_name", "")
            st.write(f"• {skill_name}")


def render_course_recommendations(result: Dict, new_format: bool):
    """Render course recommendations with links, explanations, and priority levels"""
    st.subheader("📚 Recommandations de Formation")
    
    if new_format:
        recommendations = result.get("training_recommendations", [])
    else:
        recommendations = []
    
    if not recommendations:
        st.info("💡 Aucune recommandation de formation disponible pour le moment.")
        return
    
    st.markdown("""
    <div style="background: #f0f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <p style="margin: 0; color: #2c3e50;">
            💡 <strong>Conseil du Coach:</strong> Les formations ci-dessous sont sélectionnées spécifiquement 
            pour combler les compétences manquantes identifiées dans votre CV. Chaque cours inclut une explication 
            de sa pertinence pour votre profil.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Group by priority
    high_priority_courses = [r for r in recommendations if r.get("priority", "").lower() == "high"]
    medium_priority_courses = [r for r in recommendations if r.get("priority", "").lower() == "medium"]
    other_courses = [r for r in recommendations if r.get("priority", "").lower() not in ["high", "medium"]]
    
    all_courses = high_priority_courses + medium_priority_courses + other_courses
    
    for idx, course in enumerate(all_courses[:8], 1):  # Show max 8 courses
        skill = course.get("skill", "Compétence")
        platform = course.get("platform", "Plateforme")
        course_name = course.get("course_name", "Cours")
        url = course.get("url", "#")
        duration = course.get("duration", "Variable")
        level = course.get("level", "N/A")
        difficulty = course.get("difficulty", "N/A")
        explanation = course.get("explanation", "Formation recommandée pour développer cette compétence.")
        priority = course.get("priority", "Medium")
        topics = course.get("topics", [])
        
        # Priority badge
        priority_colors = {
            "High": ("🔴", "#dc3545", "Haute"),
            "Medium": ("🟡", "#ffc107", "Moyenne"),
            "Low": ("🟢", "#28a745", "Basse")
        }
        priority_icon, priority_color, priority_text = priority_colors.get(priority, ("⚪", "#6c757d", priority))
        
        # Difficulty badge
        difficulty_colors = {
            "Easy": ("🟢", "Facile"),
            "Medium": ("🟡", "Moyen"),
            "Hard": ("🔴", "Difficile")
        }
        difficulty_icon, difficulty_text = difficulty_colors.get(difficulty, ("⚪", difficulty))
        
        with st.container():
            st.markdown(
                f"""
                <div style="border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 15px; 
                            background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <h3 style="margin: 0; color: #2c3e50;">{idx}. {course_name}</h3>
                        <div style="text-align: right;">
                            <span style="background: {priority_color}; color: white; padding: 4px 8px; border-radius: 4px; 
                                        font-size: 0.8em; margin-left: 5px;">
                                {priority_icon} {priority_text}
                            </span>
                        </div>
                    </div>
                    <p style="margin: 5px 0; color: #666;">
                        <strong>Plateforme:</strong> {platform} | 
                        <strong>Durée:</strong> {duration} | 
                        <strong>Niveau:</strong> {level} | 
                        <strong>Difficulté:</strong> {difficulty_icon} {difficulty_text}
                    </p>
                    <p style="margin: 10px 0; color: #2c3e50; line-height: 1.6;">
                        <strong>💡 Pourquoi ce cours ?</strong><br>
                        {explanation}
                    </p>
                    {f'<p style="margin: 10px 0; color: #555;"><strong>📖 Sujets couverts:</strong> {", ".join(topics[:5])}</p>' if topics else ''}
                    <a href="{url}" target="_blank" style="display: inline-block; background: #667eea; color: white; 
                        padding: 10px 20px; border-radius: 5px; text-decoration: none; margin-top: 10px; font-weight: bold;">
                        🔗 Accéder au cours →
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_key_phrases(key_phrases: List[Dict]):
    """Render key phrases recommendations"""
    st.subheader("✍️ Suggestions de Phrases Clés")
    
    for phrase_data in key_phrases[:5]:
        skill = phrase_data.get("skill", "")
        suggested_phrases = phrase_data.get("suggested_phrases", [])
        recommended_sections = phrase_data.get("recommended_sections", [])
        
        with st.expander(f"💼 Phrases pour: {skill}", expanded=False):
            st.write("**Phrases suggérées:**")
            for phrase in suggested_phrases:
                st.write(f"• {phrase}")
            if recommended_sections:
                st.write(f"**Sections recommandées:** {', '.join(recommended_sections)}")


def render_ats_recommendations(ats_recommendations: List[Dict]):
    """Render ATS optimization recommendations"""
    st.subheader("🔍 Recommandations d'Optimisation ATS")
    
    for rec in ats_recommendations[:5]:
        category = rec.get("category", "")
        issue = rec.get("issue", "")
        solution = rec.get("solution", "")
        priority = rec.get("priority", "")
        action_items = rec.get("action_items", [])
        
        priority_icon = "🔴" if priority == "Élevée" else "🟡" if priority == "Moyenne" else "🟢"
        
        with st.expander(f"{priority_icon} {category}", expanded=False):
            st.write(f"**Problème:** {issue}")
            st.write(f"**Solution:** {solution}")
            if action_items:
                st.write("**Actions à entreprendre:**")
                for action in action_items:
                    st.write(f"• {action}")


def render_overall_assessment(result: Dict):
    """Render overall assessment"""
    assessment = result.get("overall_assessment", "")
    confidence = result.get("confidence_level", "")
    
    if assessment:
        st.subheader("📋 Évaluation Globale")
        st.info(assessment)
        if confidence:
            st.caption(f"Niveau de confiance: {confidence}")
