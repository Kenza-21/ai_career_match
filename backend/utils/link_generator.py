from urllib.parse import quote, quote_plus
from typing import Optional

class LinkGenerator:
    @staticmethod
    def generate_linkedin_url(job_title: str, location: str = "Morocco") -> str:
        """Generate LinkedIn job search URL that avoids login/registration page"""
        # Use LinkedIn job search with Morocco filter to get direct job listings
        # Format: https://www.linkedin.com/jobs/search/?keywords=job_title&location=Morocco
        encoded_title = quote_plus(job_title)
        encoded_location = quote_plus(location)
        return f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}&location={encoded_location}"
    
    @staticmethod
    def generate_stagiaires_url(job_title: str, job_id: Optional[str] = None) -> str:
        """
        Generate Stagiaires.ma job search URL
        Format: https://www.stagiaires.ma/candidat/offres/?query=<job_title>
        Example: data scientist → https://www.stagiaires.ma/candidat/offres/?query=data%20scientist
        """
        encoded_title = quote(job_title)
        return f"https://www.stagiaires.ma/candidat/offres/?query={encoded_title}"
    
    @staticmethod
    def generate_indeed_url(job_title: str, location: str = "Morocco") -> str:
        """Generate Indeed job search URL"""
        encoded_title = quote(job_title)
        encoded_location = quote(location)
        
        return f"https://ma.indeed.com/jobs?q={encoded_title}&l={encoded_location}"

    @staticmethod
    def generate_google_url(job_title: str, location: str = "Morocco") -> str:
        """Generate Google Jobs search URL"""
        encoded_query = quote(f"{job_title} jobs in {location}")
        return f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
    
    @staticmethod
    def generate_rekrute_url(job_title: str, location: str = "") -> str:
        """
        Generate Rekrute.com job search URL
        Format: https://www.rekrute.com/offres.html?st=d&keywordNew=1&jobLocation=RK&tagSearchKey=&keyword=<job_title>
        Example: data scientist → https://www.rekrute.com/offres.html?st=d&keywordNew=1&jobLocation=RK&tagSearchKey=&keyword=data+scientist
        """
        # Use quote_plus to encode spaces as + (as required by Rekrute format)
        encoded_title = quote_plus(job_title)
        return f"https://www.rekrute.com/offres.html?st=d&keywordNew=1&jobLocation=RK&tagSearchKey=&keyword={encoded_title}"
    
    
    
    @staticmethod
    def generate_all_urls(job_title: str, location: str = "Morocco", job_id: Optional[str] = None) -> dict:
        """Generate primary search URLs for a job title"""
        # Primary link is Stagiaires.ma
        stagiaires_url = LinkGenerator.generate_stagiaires_url(job_title, job_id)
        # LinkedIn link (proper format, avoids login page)
        linkedin_url = LinkGenerator.generate_linkedin_url(job_title, location)
        return {
            "stagiaires_url": stagiaires_url,  # Primary link - Stagiaires.ma search
            "linkedin_url": linkedin_url,  # LinkedIn job search (direct to listings)
            "indeed_url": LinkGenerator.generate_indeed_url(job_title, location),
            "google_url": LinkGenerator.generate_google_url(job_title, location),
            "rekrute_url": LinkGenerator.generate_rekrute_url(job_title)
        }