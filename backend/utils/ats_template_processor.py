"""
ATS Template Processor
Functions for processing and rendering ATS-compliant LaTeX templates
"""
import re
from typing import Dict, List
from utils.latex_utils import escape_latex


def map_parsed_to_template(parsed_data: Dict) -> Dict:
    """Map ResumeParser.app JSON structure to template variables"""
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
    
    # Map experience
    experience_list = []
    for job in parsed_data.get("employment_history", []):
        exp_item = {
            "position": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "start_date": job.get("start_date", ""),
            "end_date": job.get("end_date", "Present"),
            "description": []
        }
        
        # Collect all responsibilities
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
        
        if exp_item["description"]:
            experience_list.append(exp_item)
    
    # Map education
    education_list = []
    for edu in parsed_data.get("education", []):
        edu_item = {
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution_name", ""),
            "details": ""
        }
        # Build details from available fields
        details_parts = []
        if edu.get("institution_country"):
            details_parts.append(edu["institution_country"])
        if edu.get("start_date") or edu.get("end_date"):
            edu_date = f"{edu.get('start_date', '')} - {edu.get('end_date', '')}".strip(" -")
            if edu_date:
                details_parts.append(edu_date)
        edu_item["details"] = " | ".join(details_parts)
        education_list.append(edu_item)
    
    return {
        "name": parsed_data.get("name", ""),
        "title": parsed_data.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": location,
        "summary": parsed_data.get("brief", ""),
        "skills": parsed_data.get("skills", []),
        "experience": experience_list,
        "education": education_list,
        "languages": parsed_data.get("languages", []),
        "certifications": parsed_data.get("courses", [])
    }


def map_parsed_to_template_optimized(parsed_data: Dict) -> Dict:
    """Map ResumeParser.app JSON structure to template variables, optimized for one page"""
    contact = parsed_data.get("contact", {})
    
    # Build compact location string
    location_parts = []
    if contact.get("location_city"):
        location_parts.append(contact["location_city"])
    if contact.get("location_state"):
        location_parts.append(contact["location_state"])
    # Omit country if it's obvious (like "USA" for US addresses)
    if contact.get("location_country") and contact.get("location_country").lower() not in ['usa', 'united states', 'us']:
        location_parts.append(contact["location_country"])
    location = ", ".join(location_parts) if location_parts else ""
    
    # Map experience - prioritize recent and relevant
    experience_list = []
    employment_history = parsed_data.get("employment_history", [])
    
    # Sort by recency (assuming dates are available)
    sorted_experience = sorted(
        employment_history,
        key=lambda x: x.get('end_date', 'Present') if x.get('end_date', 'Present') != 'Present' else '9999-12-31',
        reverse=True
    )
    
    for job in sorted_experience[:3]:  # Only keep 3 most recent jobs
        exp_item = {
            "position": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "start_date": job.get("start_date", ""),
            "end_date": job.get("end_date", "Present"),
            "description": []
        }
        
        # Collect responsibilities, prioritize bullet points
        responsibilities = job.get("responsibilities", [])
        bullet_points = []
        
        for resp in responsibilities:
            if isinstance(resp, str):
                bullet_points.append(resp)
            elif isinstance(resp, dict):
                # Handle nested roles
                if "responsibilities" in resp:
                    for r in resp.get("responsibilities", []):
                        if isinstance(r, str):
                            bullet_points.append(r)
        
        # Take only the most important 3-4 bullet points
        exp_item["description"] = bullet_points[:4]
        
        if exp_item["description"] or exp_item["position"]:
            experience_list.append(exp_item)
    
    # Map education - only highest degree
    education_list = []
    education_data = parsed_data.get("education", [])
    
    # Sort by education level (simplified)
    education_priority = {
        'phd': 1, 'doctorate': 1,
        'master': 2, 'masters': 2, 'msc': 2, 'ma': 2,
        'bachelor': 3, 'bachelors': 3, 'bs': 3, 'ba': 3,
        'associate': 4, 'diploma': 5, 'certificate': 6
    }
    
    sorted_education = sorted(
        education_data,
        key=lambda x: education_priority.get(x.get('degree', '').lower().split()[0], 99)
    )
    
    for edu in sorted_education[:2]:  # Only keep top 2 degrees
        edu_item = {
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution_name", ""),
            "details": ""
        }
        
        # Build compact details
        details_parts = []
        if edu.get("institution_country"):
            country = edu["institution_country"]
            # Abbreviate common countries
            if country.lower() == 'united states':
                country = 'USA'
            details_parts.append(country)
        
        # Format dates compactly
        if edu.get("start_date") or edu.get("end_date"):
            start = edu.get('start_date', '')[:4]  # Just year
            end = edu.get('end_date', '')[:4] if edu.get('end_date') else 'Present'
            if start or end:
                edu_date = f"{start} - {end}".strip(" -")
                if edu_date:
                    details_parts.append(edu_date)
        
        edu_item["details"] = " | ".join(details_parts)
        education_list.append(edu_item)
    
    # Process skills - categorize and prioritize
    raw_skills = parsed_data.get("skills", [])
    # Remove duplicates and prioritize technical/hard skills
    unique_skills = []
    seen = set()
    for skill in raw_skills:
        if skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    # Limit to 15 most relevant skills
    prioritized_skills = unique_skills[:15]
    
    # Process certifications
    certs = parsed_data.get("courses", [])[:5]  # Limit to 5
    
    return {
        "name": parsed_data.get("name", ""),
        "title": parsed_data.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": location,
        "summary": parsed_data.get("brief", "")[:300],  # Limit summary length
        "skills": prioritized_skills,
        "experience": experience_list,
        "education": education_list,
        "languages": parsed_data.get("languages", [])[:3],  # Limit to 3 languages
        "certifications": certs
    }


def map_parsed_to_template_full(parsed_data: Dict) -> Dict:
    """Map ResumeParser.app JSON structure to template variables - PRESERVES ALL CONTENT"""
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
    
    # Map ALL experience - no truncation
    experience_list = []
    employment_history = parsed_data.get("employment_history", [])
    
    # Sort by recency
    sorted_experience = sorted(
        employment_history,
        key=lambda x: x.get('end_date', 'Present') if x.get('end_date', 'Present') != 'Present' else '9999-12-31',
        reverse=True
    )
    
    for job in sorted_experience:  # ALL jobs, no limit
        exp_item = {
            "position": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "start_date": job.get("start_date", ""),
            "end_date": job.get("end_date", "Present"),
            "description": []
        }
        
        # Collect ALL responsibilities - no truncation
        responsibilities = job.get("responsibilities", [])
        bullet_points = []
        
        for resp in responsibilities:
            if isinstance(resp, str):
                bullet_points.append(resp)
            elif isinstance(resp, dict):
                # Handle nested roles
                if "responsibilities" in resp:
                    for r in resp.get("responsibilities", []):
                        if isinstance(r, str):
                            bullet_points.append(r)
        
        # ALL bullet points - no limit
        exp_item["description"] = bullet_points
        
        if exp_item["description"] or exp_item["position"]:
            experience_list.append(exp_item)
    
    # Map ALL education - no truncation
    education_list = []
    education_data = parsed_data.get("education", [])
    
    # Sort by education level
    education_priority = {
        'phd': 1, 'doctorate': 1,
        'master': 2, 'masters': 2, 'msc': 2, 'ma': 2,
        'bachelor': 3, 'bachelors': 3, 'bs': 3, 'ba': 3,
        'associate': 4, 'diploma': 5, 'certificate': 6
    }
    
    sorted_education = sorted(
        education_data,
        key=lambda x: education_priority.get(x.get('degree', '').lower().split()[0], 99)
    )
    
    for edu in sorted_education:  # ALL education entries
        edu_item = {
            "degree": edu.get("degree", ""),
            "institution": edu.get("institution_name", ""),
            "details": ""
        }
        
        # Build details
        details_parts = []
        if edu.get("institution_country"):
            details_parts.append(edu["institution_country"])
        
        # Format dates
        if edu.get("start_date") or edu.get("end_date"):
            start = edu.get('start_date', '')
            end = edu.get('end_date', '') if edu.get('end_date') else 'Present'
            if start or end:
                edu_date = f"{start} - {end}".strip(" -")
                if edu_date:
                    details_parts.append(edu_date)
        
        edu_item["details"] = " | ".join(details_parts)
        education_list.append(edu_item)
    
    # Process ALL skills - remove duplicates only
    raw_skills = parsed_data.get("skills", [])
    unique_skills = []
    seen = set()
    for skill in raw_skills:
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)
    
    # Process ALL certifications
    certs = parsed_data.get("courses", [])
    
    return {
        "name": parsed_data.get("name", ""),
        "title": parsed_data.get("title", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": location,
        "summary": parsed_data.get("brief", ""),  # NO truncation
        "skills": unique_skills,  # ALL skills
        "experience": experience_list,  # ALL experience
        "education": education_list,  # ALL education
        "languages": parsed_data.get("languages", []),  # ALL languages
        "certifications": certs  # ALL certifications
    }


def render_template(template: str, data: Dict) -> str:
    """Replace template placeholders with actual data for new template format"""
    result = template
    
    # Simple replacements
    result = result.replace("{{ name }}", escape_latex(data.get("name", "")))
    result = result.replace("{{ location }}", escape_latex(data.get("location", "")))
    result = result.replace("{{ email }}", escape_latex(data.get("email", "")))
    result = result.replace("{{ phone }}", escape_latex(data.get("phone", "")))
    result = result.replace("{{ summary }}", escape_latex(data.get("summary", "")))
    
    # Education loop - handle empty case
    education_block = ""
    education_items = data.get("education", [])
    
    for edu in education_items[:2]:  # Max 2 education items for space
        degree = escape_latex(edu.get('degree', ''))
        institution = escape_latex(edu.get('institution', ''))
        details = escape_latex(edu.get('details', ''))
        
        if degree or institution:
            education_block += f"\\cventry{{{degree}}}{{{institution}}}{{{details}}}\n"
            if edu != education_items[-1] and len(education_items) > 1:
                education_block += "\\vspace{2pt}\n"
    
    # Replace education loop block
    edu_pattern = r'\{%\s*for\s+edu\s+in\s+education\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    edu_match = re.search(edu_pattern, result, re.DOTALL)
    if edu_match:
        if education_block:
            result = result.replace(edu_match.group(0), education_block)
        else:
            result = result.replace(edu_match.group(0), "")
    
    # Experience loop
    experience_block = ""
    experience_items = data.get("experience", [])
    
    for exp in experience_items[:2]:  # Max 2 experiences for one page
        position = escape_latex(exp.get('position', ''))
        company = escape_latex(exp.get('company', ''))
        location = escape_latex(exp.get('location', ''))
        start_date = escape_latex(exp.get('start_date', ''))
        end_date = escape_latex(exp.get('end_date', 'Present'))
        
        if position and company:
            experience_block += f"\\cventry{{{position}}}{{{start_date} - {end_date}}}{{{company}}}{{{location}}}\n"
            experience_block += "\\begin{itemize}\n"
            
            # Add bullet points (max 3 per experience)
            for item in exp.get("description", [])[:3]:
                if item:
                    escaped_item = escape_latex(item)
                    if len(escaped_item) > 120:  # Truncate long items
                        escaped_item = escaped_item[:117] + "..."
                    experience_block += f"    \\item {escaped_item}\n"
            
            experience_block += "\\end{itemize}\n"
            if exp != experience_items[-1] and len(experience_items) > 1:
                experience_block += "\\vspace{3pt}\n"
    
    # Replace experience loop block
    exp_pattern = r'\{%\s*for\s+exp\s+in\s+experience\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    exp_match = re.search(exp_pattern, result, re.DOTALL)
    if exp_match:
        if experience_block:
            result = result.replace(exp_match.group(0), experience_block)
        else:
            result = result.replace(exp_match.group(0), "")
    
    # Skills - format as pipe-separated list
    skills = data.get("skills", [])
    if len(skills) > 15:  # Limit skills for space
        skills = skills[:15]
    
    skills_text = ""
    for i, skill in enumerate(skills):
        if skill:
            skills_text += escape_latex(skill)
            if i < len(skills) - 1:
                skills_text += " | "
    
    # Replace skills block
    skills_pattern = r'\{%\s*for\s+skill\s+in\s+skills\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    skills_match = re.search(skills_pattern, result, re.DOTALL)
    if skills_match:
        if skills_text:
            # Find the {{ skill }} placeholder in the loop
            inner_text = skills_match.group(1)
            if "{{ skill }}" in inner_text:
                # Replace the entire loop with the formatted skills text
                result = result.replace(skills_match.group(0), f"\\noindent\n{skills_text}")
            else:
                # Direct replacement
                result = result.replace(skills_match.group(0), skills_text)
        else:
            result = result.replace(skills_match.group(0), "")
    
    # Languages - format as pipe-separated list
    languages = data.get("languages", [])
    if len(languages) > 3:  # Limit languages
        languages = languages[:3]
    
    languages_text = ""
    for i, lang in enumerate(languages):
        if lang:
            languages_text += escape_latex(lang)
            if i < len(languages) - 1:
                languages_text += " | "
    
    # Replace languages block
    lang_pattern = r'\{%\s*for\s+lang\s+in\s+languages\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    lang_match = re.search(lang_pattern, result, re.DOTALL)
    if lang_match:
        if languages_text:
            inner_text = lang_match.group(1)
            if "{{ lang }}" in inner_text:
                result = result.replace(lang_match.group(0), f"\\noindent\n{languages_text}")
            else:
                result = result.replace(lang_match.group(0), languages_text)
        else:
            result = result.replace(lang_match.group(0), "")
    
    # Certifications loop
    cert_block = ""
    certifications = data.get("certifications", [])
    
    for cert in certifications[:3]:  # Max 3 certifications
        if cert:
            escaped_cert = escape_latex(cert)
            if len(escaped_cert) > 80:  # Truncate long certifications
                escaped_cert = escaped_cert[:77] + "..."
            cert_block += f"    \\item {escaped_cert}\n"
    
    # Replace certifications loop block
    cert_pattern = r'\{%\s*for\s+cert\s+in\s+certifications\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    cert_match = re.search(cert_pattern, result, re.DOTALL)
    if cert_match:
        if cert_block:
            result = result.replace(cert_match.group(0), cert_block)
        else:
            result = result.replace(cert_match.group(0), "")
    
    return result


def render_template_full(template: str, data: Dict) -> str:
    """Replace template placeholders with actual data - PRESERVES ALL CONTENT, NO TRUNCATION"""
    result = template
    
    # Simple replacements
    result = result.replace("{{ name }}", escape_latex(data.get("name", "")))
    result = result.replace("{{ location }}", escape_latex(data.get("location", "")))
    result = result.replace("{{ email }}", escape_latex(data.get("email", "")))
    result = result.replace("{{ phone }}", escape_latex(data.get("phone", "")))
    result = result.replace("{{ summary }}", escape_latex(data.get("summary", "")))
    
    # Education loop - ALL education items
    education_block = ""
    education_items = data.get("education", [])
    
    for edu in education_items:  # ALL education items
        degree = escape_latex(edu.get('degree', ''))
        institution = escape_latex(edu.get('institution', ''))
        details = escape_latex(edu.get('details', ''))
        
        if degree or institution:
            education_block += f"\\cventry{{{degree}}}{{{institution}}}{{{details}}}\n"
            if edu != education_items[-1] and len(education_items) > 1:
                education_block += "\\vspace{1pt}\n"
    
    # Replace education loop block
    edu_pattern = r'\{%\s*for\s+edu\s+in\s+education\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    edu_match = re.search(edu_pattern, result, re.DOTALL)
    if edu_match:
        if education_block:
            result = result.replace(edu_match.group(0), education_block)
        else:
            result = result.replace(edu_match.group(0), "")
    
    # Experience loop - ALL experiences, ALL bullet points
    experience_block = ""
    experience_items = data.get("experience", [])
    
    for exp in experience_items:  # ALL experiences
        position = escape_latex(exp.get('position', ''))
        company = escape_latex(exp.get('company', ''))
        location = escape_latex(exp.get('location', ''))
        start_date = escape_latex(exp.get('start_date', ''))
        end_date = escape_latex(exp.get('end_date', 'Present'))
        
        if position and company:
            experience_block += f"\\cventry{{{position}}}{{{start_date} - {end_date}}}{{{company}}}{{{location}}}\n"
            experience_block += "\\begin{itemize}[leftmargin=*,itemsep=0pt,parsep=0pt,topsep=1pt]\n"
            
            # Add ALL bullet points - NO truncation
            for item in exp.get("description", []):
                if item:
                    escaped_item = escape_latex(item)
                    # NO truncation - preserve full content
                    experience_block += f"    \\item {escaped_item}\n"
            
            experience_block += "\\end{itemize}\n"
            if exp != experience_items[-1] and len(experience_items) > 1:
                experience_block += "\\vspace{2pt}\n"
    
    # Replace experience loop block
    exp_pattern = r'\{%\s*for\s+exp\s+in\s+experience\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    exp_match = re.search(exp_pattern, result, re.DOTALL)
    if exp_match:
        if experience_block:
            result = result.replace(exp_match.group(0), experience_block)
        else:
            result = result.replace(exp_match.group(0), "")
    
    # Skills - format as pipe-separated list - ALL skills
    skills = data.get("skills", [])
    # NO limit on skills
    
    skills_text = ""
    for i, skill in enumerate(skills):
        if skill:
            skills_text += escape_latex(skill)
            if i < len(skills) - 1:
                skills_text += " | "
    
    # Replace skills block
    skills_pattern = r'\{%\s*for\s+skill\s+in\s+skills\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    skills_match = re.search(skills_pattern, result, re.DOTALL)
    if skills_match:
        if skills_text:
            inner_text = skills_match.group(1)
            if "{{ skill }}" in inner_text:
                result = result.replace(skills_match.group(0), f"\\noindent\n{skills_text}")
            else:
                result = result.replace(skills_match.group(0), skills_text)
        else:
            result = result.replace(skills_match.group(0), "")
    
    # Languages - format as pipe-separated list - ALL languages
    languages = data.get("languages", [])
    # NO limit on languages
    
    languages_text = ""
    for i, lang in enumerate(languages):
        if lang:
            languages_text += escape_latex(lang)
            if i < len(languages) - 1:
                languages_text += " | "
    
    # Replace languages block
    lang_pattern = r'\{%\s*for\s+lang\s+in\s+languages\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    lang_match = re.search(lang_pattern, result, re.DOTALL)
    if lang_match:
        if languages_text:
            inner_text = lang_match.group(1)
            if "{{ lang }}" in inner_text:
                result = result.replace(lang_match.group(0), f"\\noindent\n{languages_text}")
            else:
                result = result.replace(lang_match.group(0), languages_text)
        else:
            result = result.replace(lang_match.group(0), "")
    
    # Certifications loop - ALL certifications
    cert_block = ""
    certifications = data.get("certifications", [])
    
    for cert in certifications:  # ALL certifications
        if cert:
            escaped_cert = escape_latex(cert)
            # NO truncation - preserve full content
            cert_block += f"    \\item {escaped_cert}\n"
    
    # Replace certifications loop block
    cert_pattern = r'\{%\s*for\s+cert\s+in\s+certifications\s*%\}(.*?)\{%\s*endfor\s*%\}' 
    cert_match = re.search(cert_pattern, result, re.DOTALL)
    if cert_match:
        if cert_block:
            result = result.replace(cert_match.group(0), cert_block)
        else:
            result = result.replace(cert_match.group(0), "")
    
    return result

