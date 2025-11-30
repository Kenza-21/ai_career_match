from urllib.parse import quote

class LinkGenerator:
    @staticmethod
    def generate_linkedin_url(job_title: str, location: str = "Morocco") -> str:
        """Generate LinkedIn job search URL for a specific job title and location"""
        encoded_title = quote(job_title)
        encoded_location = quote(location)
        
        return f"https://www.linkedin.com/jobs/search/?keywords={encoded_title}&location={encoded_location}"
    
    @staticmethod
    def generate_indeed_url(job_title: str, location: str = "Morocco") -> str:
        """Generate Indeed job search URL"""
        encoded_title = quote(job_title)
        encoded_location = quote(location)
        
        return f"https://ma.indeed.com/jobs?q={encoded_title}&l={encoded_location}"
    
    @staticmethod
    def generate_google_url(job_title: str, location: str = "Morocco") -> str:
        """Generate Google job search URL"""
        encoded_query = quote(f"{job_title} jobs in {location}")
        
        return f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
    
    @staticmethod
    def generate_marocannonces_url(job_title: str, location: str = "maroc") -> str:
        """Generate MarocAnnonces job search URL"""
        encoded_title = quote(job_title.lower().replace(' ', '-'))
        return f"https://www.marocannonces.com/categorie/309/Offres-emploi/{encoded_title}/"
    
    @staticmethod
    def generate_rekrute_url(job_title: str, location: str = "") -> str:
        """Generate Rekrute.com job search URL"""
        encoded_title = quote(job_title)
        return f"https://www.rekrute.com/offres.html?p={encoded_title}"
    
    
    
    @staticmethod
    def generate_all_urls(job_title: str, location: str = "Morocco") -> dict:
        """Generate all search URLs for a job title"""
        return {
            "linkedin_url": LinkGenerator.generate_linkedin_url(job_title, location),
            "indeed_url": LinkGenerator.generate_indeed_url(job_title, location),
            "google_url": LinkGenerator.generate_google_url(job_title, location),
            "marocannonces_url": LinkGenerator.generate_marocannonces_url(job_title),
            "rekrute_url": LinkGenerator.generate_rekrute_url(job_title)
        }