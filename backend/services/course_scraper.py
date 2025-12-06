import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict
import re

class CourseScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_coursera(self, skill: str) -> List[Dict]:
        """Scrape les cours Coursera en temps réel"""
        try:
            search_url = f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            courses = []
            
            # Sélecteurs pour les cours Coursera
            course_cards = soup.select('[data-testid*="search-result"], .cds-CommonCard')[:5]
            
            for card in course_cards[:3]:  # Limiter à 3 cours
                try:
                    # Nom du cours
                    name_elem = card.select_one('[data-testid*="title"], .cds-CommonCard-title')
                    name = name_elem.get_text(strip=True) if name_elem else f"Cours {skill} - Coursera"
                    
                    # URL
                    link_elem = card.find('a', href=True)
                    if link_elem and link_elem.get('href'):
                        url = "https://www.coursera.org" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                    else:
                        url = search_url
                    
                    # Niveau (approximatif)
                    level = "Beginner"
                    card_text = card.get_text().lower()
                    if 'intermediate' in card_text:
                        level = "Intermediate"
                    elif 'advanced' in card_text:
                        level = "Advanced"
                    
                    courses.append({
                        "platform": "Coursera",
                        "name": name,
                        "url": url,
                        "duration": "4-8 weeks",  # Estimation
                        "level": level,
                        "skill": skill,
                        "source": "live_scraping"
                    })
                except Exception as e:
                    continue
            
            return courses
            
        except Exception as e:
            print(f"❌ Erreur scraping Coursera pour {skill}: {e}")
            return []

    def search_udemy(self, skill: str) -> List[Dict]:
        """Scrape les cours Udemy en temps réel"""
        try:
            search_url = f"https://www.udemy.com/courses/search/?q={skill.replace(' ', '%20')}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            courses = []
            course_cards = soup.select('[data-purpose*="course-card"], .course-card')[:5]
            
            for card in course_cards[:3]:
                try:
                    name_elem = card.select_one('[data-purpose*="course-title"], .course-card-title')
                    name = name_elem.get_text(strip=True) if name_elem else f"Cours {skill} - Udemy"
                    
                    link_elem = card.find('a', href=True)
                    if link_elem and link_elem.get('href'):
                        url = "https://www.udemy.com" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                    else:
                        url = search_url
                    
                    # Durée estimée
                    duration_elem = card.select_one('[data-purpose*="course-duration"], .course-duration')
                    duration = duration_elem.get_text(strip=True) if duration_elem else "10+ hours"
                    
                    courses.append({
                        "platform": "Udemy",
                        "name": name,
                        "url": url,
                        "duration": duration,
                        "level": "Beginner",  # Udemy a souvent des cours débutants
                        "skill": skill,
                        "source": "live_scraping"
                    })
                except Exception as e:
                    continue
            
            return courses
                
        except Exception as e:
            print(f"❌ Erreur scraping Udemy pour {skill}: {e}")
            return []

    def search_edx(self, skill: str) -> List[Dict]:
        """Scrape les cours edX en temps réel"""
        try:
            search_url = f"https://www.edx.org/search?q={skill.replace(' ', '%20')}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            courses = []
            course_cards = soup.select('[data-course-id], .course-card')[:5]
            
            for card in course_cards[:3]:
                try:
                    name_elem = card.select_one('h3, .course-title, [class*="title"]')
                    name = name_elem.get_text(strip=True) if name_elem else f"Cours {skill} - edX"
                    
                    link_elem = card.find('a', href=True)
                    if link_elem and link_elem.get('href'):
                        url = "https://www.edx.org" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                    else:
                        url = search_url
                    
                    courses.append({
                        "platform": "edX",
                        "name": name,
                        "url": url,
                        "duration": "6-8 weeks",
                        "level": "Beginner",
                        "skill": skill,
                        "source": "live_scraping"
                    })
                except Exception as e:
                    continue
            
            return courses
                
        except Exception as e:
            print(f"❌ Erreur scraping edX pour {skill}: {e}")
            return []

    def search_google_digital_garage(self, skill: str) -> List[Dict]:
        """Scrape les cours Google Digital Garage (gratuits)"""
        try:
            # Google Digital Garage pour les compétences digitales
            digital_skills = ["marketing digital", "seo", "analytics", "e-commerce", "réseaux sociaux", "digital marketing"]
            
            if skill.lower() in digital_skills:
                search_url = "https://learndigital.withgoogle.com/digitalgarage/courses"
                response = self.session.get(search_url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                courses = []
                course_cards = soup.select('[class*="course-card"], .course-item')[:3]
                
                for card in course_cards:
                    try:
                        name_elem = card.select_one('h3, [class*="title"]')
                        name = name_elem.get_text(strip=True) if name_elem else f"Fundamentals of {skill}"
                        
                        link_elem = card.find('a', href=True)
                        if link_elem and link_elem.get('href'):
                            url = "https://learndigital.withgoogle.com" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                        else:
                            url = search_url
                        
                        courses.append({
                            "platform": "Google Digital Garage",
                            "name": name,
                            "url": url,
                            "duration": "Self-paced",
                            "level": "Beginner",
                            "skill": skill,
                            "source": "live_scraping",
                            "free": True
                        })
                    except:
                        continue
                
                return courses
                
        except Exception as e:
            print(f"❌ Erreur scraping Google Digital Garage: {e}")
        
        return []

    def search_courses(self, skill: str, max_courses: int = 5) -> List[Dict]:
        """Recherche des cours en temps réel sur toutes les plateformes"""
        print(f"🔍 Recherche de cours en temps réel pour: {skill}")
        
        all_courses = []
        
        try:
            # Recherche sur différentes plateformes
            platforms = [
                self.search_coursera(skill),
                self.search_udemy(skill),
                self.search_edx(skill),
                self.search_google_digital_garage(skill)
            ]
            
            for platform_courses in platforms:
                all_courses.extend(platform_courses)
            
            # Éviter les doublons basés sur le nom
            unique_courses = []
            seen_names = set()
            
            for course in all_courses:
                if course['name'] not in seen_names:
                    seen_names.add(course['name'])
                    unique_courses.append(course)
            
            # Limiter le nombre de résultats
            result = unique_courses[:max_courses]
            
            print(f"✅ Trouvé {len(result)} cours en temps réel pour {skill}")
            return result
            
        except Exception as e:
            print(f"❌ Erreur générale dans la recherche de cours: {e}")
            return []

# Instance globale
course_scraper = CourseScraper()