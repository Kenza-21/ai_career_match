"""
Resume Builder Page
Page for creating and generating professional resumes
"""
import streamlit as st
from services.api_client import api_client
from utils.session_manager import SessionManager
from components.layout import render_header, render_footer

def render_personal_section():
    """Render personal information form"""
    with st.expander("👤 Personal Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", key="resume_name")
            email = st.text_input("Email *", key="resume_email")
            location = st.text_input("Location", key="resume_location")
            linkedin = st.text_input("LinkedIn URL", key="resume_linkedin")
        with col2:
            title = st.text_input("Professional Title", key="resume_title")
            phone = st.text_input("Phone Number *", key="resume_phone")
            website = st.text_input("Portfolio Website", key="resume_website")
            github = st.text_input("GitHub URL", key="resume_github")
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "website": website,
        "title": title
    }

def render_education_section():
    """Render education form"""
    with st.expander("🎓 Education"):
        if 'education_count' not in st.session_state:
            st.session_state.education_count = 1
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ Add Education"):
                st.session_state.education_count += 1
                st.rerun()
        
        education_entries = []
        for i in range(st.session_state.education_count):
            st.markdown(f"**Education {i+1}**")
            cols = st.columns(2)
            with cols[0]:
                university = st.text_input(f"University", key=f"edu_uni_{i}")
                location = st.text_input("Location", key=f"edu_loc_{i}")
                start_date = st.text_input("Start Date", key=f"edu_start_{i}")
            with cols[1]:
                degree = st.text_input(f"Degree", key=f"edu_degree_{i}")
                gpa = st.text_input("GPA", key=f"edu_gpa_{i}")
                end_date = st.text_input("End Date", key=f"edu_end_{i}")
            coursework = st.text_area("Relevant Coursework", key=f"edu_course_{i}")
            
            education_entries.append({
                "university": university,
                "degree": degree,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "gpa": gpa,
                "coursework": coursework
            })
    
    return education_entries

def render_experience_section():
    """Render work experience form"""
    with st.expander("💼 Work Experience"):
        if 'experience_count' not in st.session_state:
            st.session_state.experience_count = 1
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ Add Experience"):
                st.session_state.experience_count += 1
                st.rerun()
        
        experience_entries = []
        for i in range(st.session_state.experience_count):
            st.markdown(f"**Experience {i+1}**")
            job_title = st.text_input("Job Title", key=f"exp_title_{i}")
            cols = st.columns(2)
            with cols[0]:
                company = st.text_input("Company", key=f"exp_company_{i}")
                start_date = st.text_input("Start Date", key=f"exp_start_{i}")
            with cols[1]:
                location = st.text_input("Location", key=f"exp_loc_{i}")
                end_date = st.text_input("End Date", key=f"exp_end_{i}")
            responsibilities = st.text_area("Responsibilities (one per line)", 
                                          height=100, key=f"exp_resp_{i}")
            
            experience_entries.append({
                "job_title": job_title,
                "company": company,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "responsibilities": responsibilities.splitlines() if responsibilities else []
            })
    
    return experience_entries

def render_projects_section():
    """Render projects form"""
    with st.expander("🛠️ Projects"):
        if 'projects_count' not in st.session_state:
            st.session_state.projects_count = 1
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ Add Project"):
                st.session_state.projects_count += 1
                st.rerun()
        
        project_entries = []
        for i in range(st.session_state.projects_count):
            st.markdown(f"**Project {i+1}**")
            title = st.text_input("Project Title", key=f"proj_title_{i}")
            cols = st.columns(2)
            with cols[0]:
                tech_stack = st.text_input("Tech Stack", key=f"proj_tech_{i}")
                deployment = st.text_input("Deployment Link", key=f"proj_deploy_{i}")
            with cols[1]:
                link = st.text_input("GitHub Link", key=f"proj_link_{i}")
            description = st.text_area("Description", height=80, key=f"proj_desc_{i}")
            
            project_entries.append({
                "title": title,
                "tech_stack": tech_stack,
                "deployment": deployment,
                "link": link,
                "description": description
            })
    
    return project_entries

def render_skills_section():
    """Render skills form"""
    with st.expander("🧠 Skills"):
        hard_skills = st.text_area("Technical Skills (comma or line separated)",
                                 help="Python, JavaScript, React, AWS, SQL")
        soft_skills = st.text_area("Soft Skills (comma or line separated)",
                                 help="Leadership, Communication, Problem-solving")
    
    return {
        "technical": [h.strip() for h in hard_skills.replace("\n", ",").split(",") if h.strip()],
        "soft": [s.strip() for s in soft_skills.replace("\n", ",").split(",") if s.strip()]
    }

def render_summary_section():
    """Render professional summary"""
    with st.expander("📝 Professional Summary"):
        summary = st.text_area("Write a brief professional summary",
                             height=150,
                             help="A concise overview of your experience, skills, and career goals")
    
    return summary

def main():
    """Main resume builder page"""
    render_header("Professional Resume Builder", "📄")
    
    st.markdown("""
    Create a professional, ATS-friendly resume. Fill in the sections below and generate 
    a perfectly formatted Word document.
    
    **Required fields are marked with ***
    """)
    
    # Collect all data
    st.divider()
    personal = render_personal_section()
    st.divider()
    summary = render_summary_section()
    st.divider()
    education = render_education_section()
    st.divider()
    experience = render_experience_section()
    st.divider()
    projects = render_projects_section()
    st.divider()
    skills = render_skills_section()
    
    # Certifications section (optional)
    with st.expander("📜 Certifications (Optional)"):
        if 'cert_count' not in st.session_state:
            st.session_state.cert_count = 0
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("➕ Add Certification"):
                st.session_state.cert_count += 1
                st.rerun()
        
        certifications = []
        for i in range(st.session_state.cert_count):
            st.markdown(f"**Certification {i+1}**")
            title = st.text_input("Title", key=f"cert_title_{i}")
            cols = st.columns(2)
            with cols[0]:
                issuer = st.text_input("Issued By", key=f"cert_issuer_{i}")
            with cols[1]:
                link = st.text_input("Certificate Link", key=f"cert_link_{i}")
            certifications.append({
                "title": title,
                "issuer": issuer,
                "link": link
            })
    
    # Achievements & Hobbies section (optional)
    with st.expander("🏆 Achievements & Hobbies (Optional)"):
        achievements = st.text_area("Achievements (comma or line separated)")
        hobbies = st.text_area("Hobbies (comma or line separated)")
    
    extras = {
        "achievements": [a.strip() for a in achievements.replace("\n", ",").split(",") if a.strip()],
        "hobbies": [h.strip() for h in hobbies.replace("\n", ",").split(",") if h.strip()]
    }
    
    # Generate button
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ Generate Resume", type="primary", use_container_width=True):
            # Validate required fields
            if not personal.get('name') or not personal.get('email') or not personal.get('phone'):
                st.error("Please fill in all required fields (Name, Email, Phone)")
                return
            
            # Structure the data
            resume_data = {
                "personal": personal,
                "summary": summary,
                "education": education,
                "experience": experience,
                "projects": projects,
                "skills": skills,
                "certifications": certifications,
                "achievements_hobbies": extras
            }
            
            try:
                with st.spinner("Generating your professional resume..."):
                    # Call the API
                    doc_bytes = api_client.generate_resume(resume_data)
                    
                    # Offer download
                    st.success("✅ Resume generated successfully!")
                    
                    st.download_button(
                        label="📥 Download Resume (.docx)",
                        data=doc_bytes.getvalue(),
                        file_name="resume.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    
                    # Show preview button
                    if st.button("👁️ Preview Data Structure", use_container_width=True):
                        st.json(resume_data)
                        
            except Exception as e:
                st.error(f"Error generating resume: {str(e)}")
                st.info("Make sure your backend server is running and has the resume generator endpoint.")
    
    render_footer()

if __name__ == "__main__":
    main()