import requests

def test_cv_analysis():
    # Test avec des données d'exemple
    cv_text = """
    INGÉNIEUR LOGICIEL
    Marie Martin
    Email: marie.martin@email.com
    
    EXPÉRIENCE
    Développeuse Python - Startup (2021-2023)
    - Développement d'APIs avec Django
    - Base de données PostgreSQL
    - Tests unitaires
    
    COMPÉTENCES
    Python, Django, SQL, Git
    """
    
    job_description = """
    Développeur Full Stack
    Compétences: Python, JavaScript, React, Node.js, MongoDB
    Expérience en cloud AWS appréciée
    """
    
    response = requests.post(
        "http://localhost:8000/cv/analyze",
        data={
            "cv_text": cv_text,
            "job_description": job_description
        }
    )
    
    print("Status:", response.status_code)
    print("Result:", response.json())

if __name__ == "__main__":
    test_cv_analysis()