import os
import uuid
from typing import Dict

import requests
from io import BytesIO
import streamlit as st

BASE_URL = os.getenv("ASSISTANT_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Assistant++", page_icon="🤖")
st.title("Assistant++ Search UI")

# Session handling
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "last_response" not in st.session_state:
    st.session_state.last_response = None


def call_search(query: str) -> Dict:
    resp = requests.post(f"{BASE_URL}/api/search", json={"query": query, "session_id": st.session_state.session_id}, timeout=15)
    resp.raise_for_status()
    return resp.json()


def call_clarify(answer: str) -> Dict:
    resp = requests.post(
        f"{BASE_URL}/api/clarify",
        json={"session_id": st.session_state.session_id, "answer": answer},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


with st.form("search_form"):
    query = st.text_input("Votre requête", placeholder="ex: développeur backend télétravail")
    submitted = st.form_submit_button("Lancer la recherche")

if submitted and query:
    try:
        st.session_state.last_response = call_search(query)
    except Exception as exc:  # pragma: no cover - UI feedback only
        st.error(f"Erreur: {exc}")

# Clarification flow
if st.session_state.last_response and st.session_state.last_response.get("clarify"):
    st.warning(st.session_state.last_response.get("question"))
    clar_answer = st.text_input("Précisez :", key="clarify_input")
    if st.button("Envoyer"):
        try:
            st.session_state.last_response = call_clarify(clar_answer)
        except Exception as exc:  # pragma: no cover - UI feedback only
            st.error(f"Erreur: {exc}")

# Display results
resp = st.session_state.last_response
if resp and not resp.get("clarify"):
    st.subheader("Requêtes générées")
    for q in resp.get("search_queries", []):
        st.write(f"- {q.get('query')}")
        st.caption(f"[Google]({q.get('google_link')}) | [Indeed]({q.get('indeed_link')})")

    st.subheader("Résumé")
    summary = resp.get("results", {}).get("summary", {})
    st.write(summary)

    st.subheader("Offres trouvées")
    for job in resp.get("results", {}).get("jobs", []):
        st.write(f"**{job.get('job_title', 'Titre inconnu')}** — score {job.get('match_score', 0)}")
        st.caption(job.get("description", "")[:180] + "...")
        urls = job.get("all_search_urls") or {}
        if urls:
            st.write(f"[LinkedIn]({urls.get('linkedin_url')}) | [ReKrute]({urls.get('rekrute_url')})")

# --- CV Analyser UI ---
st.divider()
st.header("Analyse CV vs Offre")
with st.form("cv_form"):
    uploaded_cv = st.file_uploader("Uploader votre CV (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
    cv_text_input = st.text_area("Ou collez votre CV (optionnel si fichier)", height=150)
    jd_text = st.text_area("Description de l'offre", height=150)
    submitted_cv = st.form_submit_button("Analyser")

if submitted_cv:
    if (not uploaded_cv and not cv_text_input.strip()) or not jd_text.strip():
        st.warning("Veuillez fournir un CV (fichier ou texte) et une description d'offre.")
    else:
        files = {}
        data = {
            "cv_text": cv_text_input,
            "job_description": jd_text,
            "session_id": st.session_state.session_id
        }
        if uploaded_cv:
            files["cv_file"] = (uploaded_cv.name, uploaded_cv.getvalue(), uploaded_cv.type)
        try:
            resp_cv = requests.post(f"{BASE_URL}/api/cv_analyser", data=data, files=files, timeout=20)
            resp_cv.raise_for_status()
            res_json = resp_cv.json()
            if res_json.get("success"):
                st.success(f"Score de matching : {res_json.get('score', 0)}%")
                st.write("Compétences trouvées (CV):", ", ".join(res_json.get("cv_keywords", [])))
                st.write("Compétences demandées (Offre):", ", ".join(res_json.get("job_keywords", [])))
                st.write("Compétences communes:", ", ".join(res_json.get("matched_skills", [])))
                st.write("Compétences manquantes:", ", ".join(res_json.get("missing_skills", [])))
            else:
                st.error(res_json.get("error", "Erreur d'analyse"))
        except Exception as exc:  # pragma: no cover
            st.error(f"Erreur d'appel API: {exc}")

# --- ATS CV Optimizer ---
st.divider()
st.header("Optimisation ATS du CV")
with st.form("ats_form"):
    ats_cv_file = st.file_uploader("Uploader votre CV (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ats_cv_file")
    target_role = st.text_input("Rôle cible (optionnel)", key="ats_target_role")
    submitted_ats = st.form_submit_button("Optimiser")

if submitted_ats:
    if not ats_cv_file:
        st.warning("Veuillez fournir un CV (fichier) pour l'optimiser.")
    else:
        files = {}
        data = {
            "target_role": target_role,
            "session_id": st.session_state.session_id
        }
        if ats_cv_file:
            files["cv_file"] = (ats_cv_file.name, ats_cv_file.getvalue(), ats_cv_file.type)
        try:
            resp_ats = requests.post(f"{BASE_URL}/api/ats_cv", data=data, files=files, timeout=20)
            resp_ats.raise_for_status()
            res_json = resp_ats.json()
            if res_json.get("success"):
                ats_latex = res_json.get("ats_latex") or res_json.get("ats_cv_text", "")
                st.success("CV optimisé (ATS-ready LaTeX) généré !")
                
                # Show PDF if available
                if res_json.get("pdf_available") and res_json.get("pdf_base64"):
                    import base64
                    pdf_bytes = base64.b64decode(res_json["pdf_base64"])
                    st.download_button(
                        "Télécharger le PDF ATS",
                        data=pdf_bytes,
                        file_name="cv_ats.pdf",
                        mime="application/pdf"
                    )
                    st.caption("PDF compilé et prêt à télécharger")
                
                st.info("Format: LaTeX (compilable avec pdflatex)")
                st.text_area("Code LaTeX", value=ats_latex, height=400, help="Copiez ce code dans un fichier .tex et compilez avec pdflatex")
                if res_json.get("download_url"):
                    st.markdown(f"[Télécharger le fichier]({res_json.get('download_url')})")
                st.download_button("Télécharger le fichier LaTeX (.tex)", data=ats_latex, file_name="cv_ats.tex", mime="text/x-tex")
                if not res_json.get("pdf_available"):
                    st.caption(" Pour compiler: `pdflatex cv_ats.tex` (nécessite LaTeX installé)")
            else:
                st.error(res_json.get("error", "Erreur d'analyse ATS"))
        except Exception as exc:  # pragma: no cover
            st.error(f"Erreur d'appel API: {exc}")

