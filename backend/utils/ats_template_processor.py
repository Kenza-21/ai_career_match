
from typing import Dict, List, Any

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
    
    # Map projects
    projects_list = []
    raw_projects = parsed_data.get("projects", [])
    for proj in raw_projects:
        if isinstance(proj, dict):
            project_item = {
                "title": proj.get("title", ""),
                "description": proj.get("description", ""),
                "technologies": proj.get("technologies", ""),
                "achievements": proj.get("achievements", [])
            }
            projects_list.append(project_item)
        elif isinstance(proj, str):
            projects_list.append({"title": "", "description": proj})
    
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
        "certifications": parsed_data.get("courses", []),
        "projects": projects_list  # ADD THIS LINE
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
    
    # Process projects - limit for one-page CV
    projects_list = []
    raw_projects = parsed_data.get("projects", [])
    for proj in raw_projects[:2]:  # Only 2 most important projects
        if isinstance(proj, dict):
            project_item = {
                "title": proj.get("title", ""),
                "description": proj.get("description", "")[:150] if proj.get("description") else "",  # Truncate
                "technologies": proj.get("technologies", "")
            }
            projects_list.append(project_item)
    
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
        "certifications": certs,
        "projects": projects_list  # ADD THIS LINE
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
    
    # Process ALL projects
    projects_list = []
    raw_projects = parsed_data.get("projects", [])
    for proj in raw_projects:
        if isinstance(proj, dict):
            project_item = {
                "title": proj.get("title", ""),
                "description": proj.get("description", ""),
                "technologies": proj.get("technologies", ""),
                "achievements": proj.get("achievements", [])
            }
            projects_list.append(project_item)
        elif isinstance(proj, str):
            projects_list.append({"title": "", "description": proj})
    
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
        "certifications": certs,  # ALL certifications
        "projects": projects_list  # ADD THIS LINE - ALL projects
    }