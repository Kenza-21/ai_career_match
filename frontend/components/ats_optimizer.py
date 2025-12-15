"""
ATS Optimizer Display Components
Reusable components for displaying ATS optimization results
"""
import streamlit as st
import base64
from typing import Dict


def render_ats_results(result: Dict):
    """Render ATS optimization results"""
    if not result.get("success"):
        st.error(result.get("error", "Erreur d'optimisation ATS"))
        return
    
    st.success("✅ CV optimisé (ATS-ready LaTeX) généré !")
    
    ats_latex = result.get("ats_latex") or result.get("ats_cv_text", "")
    
    # PDF download if available
    if result.get("pdf_available") and result.get("pdf_base64"):
        pdf_bytes = base64.b64decode(result["pdf_base64"])
        st.download_button(
            "📥 Télécharger le PDF ATS",
            data=pdf_bytes,
            file_name="cv_ats.pdf",
            mime="application/pdf",
            key="download_pdf"
        )
        st.caption("PDF compilé et prêt à télécharger")
    
    st.info("📄 Format: LaTeX (compilable avec pdflatex)")
    
    # LaTeX code display
    st.subheader("Code LaTeX")
    st.text_area(
        "Code LaTeX",
        value=ats_latex,
        height=400,
        help="Copiez ce code dans un fichier .tex et compilez avec pdflatex",
        key="latex_code"
    )
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "📥 Télécharger le fichier LaTeX (.tex)",
            data=ats_latex,
            file_name="cv_ats.tex",
            mime="text/x-tex",
            key="download_tex"
        )
    
    with col2:
        if result.get("download_url"):
            st.markdown(f"[🔗 Télécharger via URL]({result.get('download_url')})")
    
    if not result.get("pdf_available"):
        st.caption("💡 Pour compiler: `pdflatex cv_ats.tex` (nécessite LaTeX installé)")

