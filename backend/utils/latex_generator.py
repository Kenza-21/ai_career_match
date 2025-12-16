"""
LaTeX Generator for ATS CV
Modular functions for generating LaTeX code from CV data
"""
from typing import Dict, List, Optional
from utils.latex_utils import escape_latex, load_latex_template


def generate_latex_from_json(cv_data: Dict) -> str:
    """
    Main function to generate complete LaTeX document from CV JSON data.
    
    Args:
        cv_data: Dictionary containing CV information with keys:
            - name: str
            - title: str (optional)
            - email: str
            - phone: str
            - location: str
            - summary: str
            - experience: List[Dict]
            - education: List[Dict]
            - skills: List[str]
            - languages: List[str] (optional)
            - certifications: List[str] (optional)
            - projects: List[Dict] (optional)
    
    Returns:
        Complete LaTeX document as string
    """
    # Load base template
    template = load_latex_template()
    
    # Generate sections
    header = generate_header_section(
        name=cv_data.get("name", ""),
        title=cv_data.get("title", ""),
        email=cv_data.get("email", ""),
        phone=cv_data.get("phone", ""),
        location=cv_data.get("location", "")
    )
    print(f"DEBUG generate_latex_from_json:")
    print(f"  Keys in cv_data: {list(cv_data.keys())}")
    print(f"  Projects data exists: {'projects' in cv_data}")
    if 'projects' in cv_data:
        print(f"  Projects count: {len(cv_data['projects'])}")
        print(f"  Projects type: {type(cv_data['projects'])}")
        if cv_data['projects']:
            print(f"  First project: {cv_data['projects'][0]}")
    
    profile = generate_profile_section(cv_data.get("summary", ""))
    education = generate_education_section(cv_data.get("education", []))
    experience = generate_experience_section(cv_data.get("experience", []))
    skills = generate_skills_section(cv_data.get("skills", []))
    projects = generate_projects_section(cv_data.get("projects", []))
    certifications = generate_certifications_section(cv_data.get("certifications", []))
    languages = generate_languages_section(cv_data.get("languages", []))
    
    
      # Debug projects section generation
    projects_data = cv_data.get("projects", [])
    print(f"  DEBUG: Calling generate_projects_section with: {projects_data}")
    projects = generate_projects_section(projects_data)
    print(f"  DEBUG: Generated projects section: {projects[:200]}...")
    # Replace placeholders in template
    latex = template
    name_escaped = escape_latex(cv_data.get("name", ""))
    
    # Replace name in hyperref and throughout document
    latex = latex.replace("{{ name }}", name_escaped)
    
    # Replace section placeholders (using {{ SECTION_NAME }} format)
    latex = latex.replace("{{ HEADER }}", header)
    latex = latex.replace("{{ PROFILE }}", profile)
    latex = latex.replace("{{ EDUCATION }}", education)
    latex = latex.replace("{{ EXPERIENCE }}", experience)
    latex = latex.replace("{{ SKILLS }}", skills)
    latex = latex.replace("{{ PROJECTS }}", projects)
    latex = latex.replace("{{ CERTIFICATIONS }}", certifications)
    latex = latex.replace("{{ LANGUAGES }}", languages)
    
    return latex


def generate_header_section(
    name: str,
    title: str,
    email: str,
    phone: str,
    location: str
) -> str:
    """Generate header section with name and contact information"""
    header = ""
    name_escaped = escape_latex(name)
    header += f"{{\\Large \\textbf{{{name_escaped}}}}}\\\\\n"
    
    if title:
        title_escaped = escape_latex(title)
        header += f"    \\textit{{{title_escaped}}}\\\\\n"
    
    header += "    \\vspace{1pt}\n"
    header += "    \\small "
    
    contact_parts = []
    if location:
        contact_parts.append(escape_latex(location))
    if email:
        email_escaped = escape_latex(email)
        contact_parts.append(f"\\href{{mailto:{email_escaped}}}{{{email_escaped}}}")
    if phone:
        contact_parts.append(escape_latex(phone))
    
    header += " | ".join(contact_parts)
    header += "\n"
    header += "\\vspace{3pt}\n"
    
    return header




def generate_profile_section(summary: str) -> str:
    """Generate profile/summary section"""
    if not summary:
        return ""
    
    # REMOVED: \section*{Profil}
    profile = f"\\small {escape_latex(summary)}\n"
    profile += "\\vspace{2pt}\n"
    
    return profile


def generate_education_section(education_list: List[Dict]) -> str:
    """
    Generate education section from education list.
    
    Expected format for each education item:
    {
        "degree": str,
        "institution": str,
        "dates": str (optional),
        "location": str (optional),
        "details": List[str] (optional)
    }
    """
    if not education_list:
        return ""
    
    section = ""  # REMOVED: \section*{Formation}\n
    
    for i, edu in enumerate(education_list):
        degree = escape_latex(edu.get("degree", ""))
        institution = escape_latex(edu.get("institution", ""))
        dates = escape_latex(edu.get("dates", edu.get("start_date", "") + " - " + edu.get("end_date", "")))
        location = escape_latex(edu.get("location", edu.get("institution_country", "")))
        
        if degree or institution:
            section += f"\\cventry{{{degree}}}{{{dates}}}{{{institution}}}{{{location}}}\n"
            
            # Add details if available
            details = edu.get("details", [])
            if details:
                section += "\\begin{itemize}\n"
                for detail in details:
                    section += f"    \\item {escape_latex(str(detail))}\n"
                section += "\\end{itemize}\n"
            
            if i < len(education_list) - 1:
                section += "\\vspace{1pt}\n"
    
    return section


def generate_experience_section(experience_list: List[Dict]) -> str:
    """
    Generate professional experience section from experience list.
    
    Expected format for each experience item:
    {
        "position": str,
        "company": str,
        "start_date": str,
        "end_date": str,
        "location": str (optional),
        "description": List[str] - ALL bullet points preserved
    }
    """
    if not experience_list:
        return ""
    
    section = ""  # REMOVED: \section*{Expériences Professionnelles}\n
    
    for i, exp in enumerate(experience_list):
        position = escape_latex(exp.get("position", ""))
        company = escape_latex(exp.get("company", ""))
        start_date = escape_latex(exp.get("start_date", ""))
        end_date = escape_latex(exp.get("end_date", "Present"))
        location = escape_latex(exp.get("location", ""))
        
        if position and company:
            section += f"\\cventry{{{position}}}{{{start_date} - {end_date}}}{{{company}}}{{{location}}}\n"
            section += "\\begin{itemize}[leftmargin=*,itemsep=0pt,parsep=0pt,topsep=1pt]\n"
            
            # Add ALL bullet points - NO truncation
            descriptions = exp.get("description", [])
            for desc in descriptions:
                if desc:
                    section += f"    \\item {escape_latex(str(desc))}\n"
            
            section += "\\end{itemize}\n"
            
            if i < len(experience_list) - 1:
                section += "\\vspace{2pt}\n"
    
    return section


def generate_skills_section(skills_list: List[str]) -> str:
    """Generate technical skills section - ALL skills preserved"""
    if not skills_list:
        return ""
    
    # Remove duplicates while preserving order
    unique_skills = []
    seen = set()
    for skill in skills_list:
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    if not unique_skills:
        return ""
    
    section = ""  # REMOVED: \section*{Compétences Techniques}\n
    section += "\\small\n"
    section += "\\noindent\n"
    
    # Format as pipe-separated list
    skills_text = " | ".join([escape_latex(skill) for skill in unique_skills])
    section += skills_text + "\n"
    section += "\\vspace{2pt}\n"
    
    return section


def generate_projects_section(projects_list: List[Dict]) -> str:
    """
    Generate projects section from projects list - more flexible format.
    
    Accepts multiple formats:
    Format 1: {"title": "Project", "technologies": "React", "description": "..."}
    Format 2: {"project": "Project", "tech": "React", "desc": "..."}
    Format 3: {"name": "Project", "tools": "React", "details": "..."}
    Format 4: Just a string description
    """
    if not projects_list:
        return ""
    
    section = ""
    
    for i, project in enumerate(projects_list):
        # Try different possible keys for title
        title = ""
        possible_title_keys = ["title", "project", "name", "project_title", "project_name"]
        for key in possible_title_keys:
            if project.get(key):
                title = escape_latex(str(project[key]))
                break
        
        # Try different possible keys for technologies
        technologies = ""
        possible_tech_keys = ["technologies", "tech", "tools", "skills", "stack", "technology"]
        for key in possible_tech_keys:
            if project.get(key):
                tech_value = project[key]
                if isinstance(tech_value, list):
                    technologies = ", ".join([escape_latex(str(t)) for t in tech_value])
                else:
                    technologies = escape_latex(str(tech_value))
                break
        
        # Try different possible keys for description
        description = ""
        possible_desc_keys = ["description", "desc", "details", "summary", "overview"]
        for key in possible_desc_keys:
            if project.get(key):
                desc_value = project[key]
                if isinstance(desc_value, list):
                    description = " ".join([escape_latex(str(d)) for d in desc_value])
                else:
                    description = escape_latex(str(desc_value))
                break
        
        # If project is just a string, use it as description
        if not title and not description and isinstance(project, str):
            description = escape_latex(project)
        
        # If no title but we have description, create a simple bullet point
        if not title and description:
            section += f"• {description}"
            if i < len(projects_list) - 1:
                section += "\\\\\n"
            continue
        
        # If we have a title, format it properly
        if title:
            if technologies:
                section += f"\\textbf{{{title}}} - {technologies}\\\\\n"
            else:
                section += f"\\textbf{{{title}}}\\\\\n"
            
            if description:
                section += f"{description}\n"
            
            # Try different possible keys for achievements/bullet points
            achievements = []
            possible_achievement_keys = ["achievements", "responsibilities", "tasks", "highlights", "bullet_points", "points"]
            for key in possible_achievement_keys:
                if project.get(key):
                    achievements_value = project[key]
                    if isinstance(achievements_value, list):
                        achievements = [escape_latex(str(a)) for a in achievements_value]
                    elif isinstance(achievements_value, str):
                        # Split by common delimiters if it's a string
                        achievements = [escape_latex(a.strip()) for a in achievements_value.split(';') if a.strip()]
                    break
            
            # If no achievements but we have a list in the project dict, try to use list items
            if not achievements and isinstance(project, dict):
                # Look for any list values that aren't already used
                for key, value in project.items():
                    if isinstance(value, list) and key not in possible_title_keys + possible_tech_keys + possible_desc_keys + possible_achievement_keys:
                        if value and isinstance(value[0], str):
                            achievements = [escape_latex(str(v)) for v in value]
                            break
            
            if achievements:
                section += "\\begin{itemize}\n"
                for achievement in achievements:
                    if achievement:  # Skip empty achievements
                        section += f"    \\item {achievement}\n"
                section += "\\end{itemize}\n"
            
            if i < len(projects_list) - 1:
                section += "\\vspace{2pt}\n"
    
    return section

def generate_certifications_section(certifications_list: List[str]) -> str:
    """Generate certifications section - ALL certifications preserved"""
    if not certifications_list:
        return ""
    
    section = ""  # REMOVED: \section*{Certificats}\n
    section += "\\begin{itemize}\n"
    
    for cert in certifications_list:
        if cert:
            section += f"    \\item {escape_latex(str(cert))}\n"
    
    section += "\\end{itemize}\n"
    section += "\\vspace{2pt}\n"
    
    return section


def generate_languages_section(languages_list: List[str]) -> str:
    """Generate languages section - ALL languages preserved"""
    if not languages_list:
        return ""
    
    section = ""  # REMOVED: \section*{Langues}\n
    section += "\\small\n"
    section += "\\noindent\n"
    
    # Format as pipe-separated list
    languages_text = " | ".join([escape_latex(lang) for lang in languages_list])
    section += languages_text + "\n"
    
    return section


def format_cv_data_from_parser(parsed_data: Dict) -> Dict:
    """
    Format ResumeParser.app API response into standardized CV data structure
    for LaTeX generation. Preserves ALL content without truncation.
    
    Args:
        parsed_data: Raw parsed data from ResumeParser.app API
    
    Returns:
        Formatted CV data dictionary ready for LaTeX generation
    """
    contact = parsed_data.get("contact", {})
    
    # Build location string
    location_parts = []
    if contact.get("location_city"):
        location_parts.append(contact["location_city"])
    if contact.get("location_state"):
        location_parts.append(contact["location_state"])
    if contact.get("location_country"):
        location_parts.append(contact["location_country"])
    location = ", ".join(location_parts) if location_parts else ""
    
    # Format experience - ALL entries, ALL bullet points
    experience_list = []
    employment_history = parsed_data.get("employment_history", [])
    
    # Sort by recency (most recent first)
    sorted_experience = sorted(
        employment_history,
        key=lambda x: (
            x.get('end_date', 'Present') if x.get('end_date', 'Present') != 'Present' 
            else '9999-12-31'
        ),
        reverse=True
    )
    
    for job in sorted_experience:
        exp_item = {
            "position": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "start_date": job.get("start_date", ""),
            "end_date": job.get("end_date", "Present"),
            "description": []
        }
        
        # Collect ALL responsibilities - NO truncation
        responsibilities = job.get("responsibilities", [])
        for resp in responsibilities:
            if isinstance(resp, str):
                exp_item["description"].append(resp)
            elif isinstance(resp, dict):
                # Handle nested roles
                if "responsibilities" in resp:
                    for r in resp.get("responsibilities", []):
                        if isinstance(r, str):
                            exp_item["description"].append(r)
        
        if exp_item["position"] or exp_item["description"]:
            experience_list.append(exp_item)
    
    # Format education - ALL entries
    education_list = []
    education_data = parsed_data.get("education", [])
    
    # Sort by education level (highest first)
    education_priority = {
        'phd': 1, 'doctorate': 1, 'ph.d': 1,
        'master': 2, 'masters': 2, 'msc': 2, 'ma': 2, 'ms': 2, 'mba': 2,
        'bachelor': 3, 'bachelors': 3, 'bs': 3, 'ba': 3,
        'associate': 4, 'diploma': 5, 'certificate': 6
    }
    
    sorted_education = sorted(
        education_data,
        key=lambda x: education_priority.get(
            x.get('degree', '').lower().split()[0] if x.get('degree') else '', 
            99
        )
    )
    
    for edu in sorted_education:
        start_date = edu.get("start_date", "")
        end_date = edu.get("end_date", "")
        dates = f"{start_date} - {end_date}".strip(" -") if (start_date or end_date) else ""
        
        edu_item = {
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution_name", ""),
            "dates": dates,
            "location": edu.get("institution_country", ""),
            "details": []
        }
        
        # Add any additional details
        if edu.get("field_of_study"):
            edu_item["details"].append(f"Field: {edu.get('field_of_study')}")
        if edu.get("gpa"):
            edu_item["details"].append(f"GPA: {edu.get('gpa')}")
        
        education_list.append(edu_item)
    
    # Process skills - remove duplicates only
    raw_skills = parsed_data.get("skills", [])
    unique_skills = []
    seen = set()
    for skill in raw_skills:
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    # Process certifications - ALL preserved
    certifications = parsed_data.get("courses", [])
    if not certifications:
        certifications = parsed_data.get("certifications", [])
    
    # Process languages - ALL preserved
    languages = parsed_data.get("languages", [])
    
    # Process projects if available
    projects = parsed_data.get("projects", [])
    
    return {
        "name": parsed_data.get("name", ""),
        "title": parsed_data.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": location,
        "summary": parsed_data.get("brief", ""),  # NO truncation
        "experience": experience_list,  # ALL experience
        "education": education_list,  # ALL education
        "skills": unique_skills,  # ALL skills (deduplicated)
        "languages": languages,  # ALL languages
        "certifications": certifications,  # ALL certifications
        "projects": projects  # ALL projects
    }

