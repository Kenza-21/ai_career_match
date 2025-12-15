"""
Text Normalization and Skill Matching Module
Handles text normalization, synonym mapping, stemming, and semantic similarity
"""
import re
from typing import List, Dict, Set, Optional
from unicodedata import normalize
import string

try:
    from nltk.stem import SnowballStemmer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️ NLTK not available. Using basic stemming.")

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("⚠️ SentenceTransformers not available. Semantic matching disabled.")


class TextNormalizer:
    """Handles text normalization: lowercase, accent removal, punctuation, spaces"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text: lowercase, remove accents, punctuation, extra spaces
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents (é → e, à → a, etc.)
        text = normalize('NFD', text)
        text = text.encode('ascii', 'ignore').decode('utf-8')
        
        # Remove punctuation (keep spaces and alphanumeric)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing spaces
        text = text.strip()
        
        return text
    
    @staticmethod
    def normalize_skill(skill: str) -> str:
        """Normalize a single skill name"""
        return TextNormalizer.normalize_text(skill)


class SynonymMapper:
    """Maps synonyms and variants to standard skill names"""
    
    def __init__(self):
        # Extensible synonym mapping: variant -> standard form
        self.synonym_map: Dict[str, str] = {
            # SQL variants
            "sql server": "sql",
            "mssql": "sql",
            "mysql": "sql",
            "postgresql": "sql",
            "postgres": "sql",
            "oracle sql": "sql",
            "sqlite": "sql",
            "tsql": "sql",
            "plsql": "sql",
            
            # PyTorch variants
            "pytorch": "pytorch",
            "torch": "pytorch",
            "pytorch framework": "pytorch",
            
            # TensorFlow variants
            "tensorflow": "tensorflow",
            "tf": "tensorflow",
            "tensor flow": "tensorflow",
            
            # Deep Learning / Neural Networks
            "ann": "deep learning",
            "artificial neural network": "deep learning",
            "neural network": "deep learning",
            "neural networks": "deep learning",
            "neural net": "deep learning",
            "dnn": "deep learning",
            "deep neural network": "deep learning",
            "cnn": "deep learning",
            "convolutional neural network": "deep learning",
            "rnn": "deep learning",
            "recurrent neural network": "deep learning",
            "lstm": "deep learning",
            "long short term memory": "deep learning",
            
            # Machine Learning variants
            "ml": "machine learning",
            "machine learning": "machine learning",
            "statistical learning": "machine learning",
            "predictive modeling": "machine learning",
            
            # AI variants
            "artificial intelligence": "ai",
            "ai": "ai",
            "artificial intel": "ai",
            
            # Data Science variants
            "data science": "data science",
            "data scientist": "data science",
            "data analytics": "data science",
            "data analysis": "data science",
            "big data": "data science",
            
            # JavaScript variants
            "js": "javascript",
            "javascript": "javascript",
            "ecmascript": "javascript",
            "es6": "javascript",
            "es2015": "javascript",
            
            # Node.js variants
            "nodejs": "node.js",
            "node": "node.js",
            "node js": "node.js",
            
            # React variants
            "reactjs": "react",
            "react.js": "react",
            "react js": "react",
            
            # Vue variants
            "vuejs": "vue",
            "vue.js": "vue",
            "vue js": "vue",
            
            # Angular variants
            "angularjs": "angular",
            "angular.js": "angular",
            "angular js": "angular",
            
            # TypeScript variants
            "ts": "typescript",
            "typescript": "typescript",
            
            # Python variants
            "py": "python",
            "python3": "python",
            "python 3": "python",
            
            # Java variants
            "java": "java",
            "java se": "java",
            "java ee": "java",
            "j2ee": "java",
            
            # Docker variants
            "docker": "docker",
            "docker container": "docker",
            "containerization": "docker",
            
            # Kubernetes variants
            "k8s": "kubernetes",
            "kubernetes": "kubernetes",
            "kube": "kubernetes",
            
            # AWS variants
            "amazon web services": "aws",
            "amazon aws": "aws",
            "aws cloud": "aws",
            
            # Git variants
            "git": "git",
            "git version control": "git",
            "github": "git",
            "gitlab": "git",
            
            # REST API variants
            "rest": "rest api",
            "restful": "rest api",
            "rest api": "rest api",
            "restful api": "rest api",
            "api": "rest api",
            
            # HTML/CSS variants
            "html5": "html",
            "html": "html",
            "css3": "css",
            "css": "css",
            
            # MongoDB variants
            "mongo": "mongodb",
            "mongodb": "mongodb",
            "mongo db": "mongodb",
            
            # Redis variants
            "redis": "redis",
            "redis cache": "redis",
            
            # NLP variants
            "natural language processing": "nlp",
            "nlp": "nlp",
            "text processing": "nlp",
            
            # Frontend/Backend variants
            "front end": "frontend",
            "front-end": "frontend",
            "back end": "backend",
            "back-end": "backend",
            "full stack": "fullstack",
            "full-stack": "fullstack",
            "fullstack": "fullstack",
        }
        
        # Build reverse lookup for faster access
        self._build_reverse_map()
    
    def _build_reverse_map(self):
        """Build reverse lookup map for faster synonym resolution"""
        self.reverse_map: Dict[str, List[str]] = {}
        for variant, standard in self.synonym_map.items():
            if standard not in self.reverse_map:
                self.reverse_map[standard] = []
            self.reverse_map[standard].append(variant)
    
    def add_synonym(self, variant: str, standard: str):
        """
        Add a new synonym mapping (extensible)
        
        Args:
            variant: The variant/synonym form
            standard: The standard form to map to
        """
        normalized_variant = TextNormalizer.normalize_skill(variant)
        normalized_standard = TextNormalizer.normalize_skill(standard)
        self.synonym_map[normalized_variant] = normalized_standard
        
        # Update reverse map
        if normalized_standard not in self.reverse_map:
            self.reverse_map[normalized_standard] = []
        self.reverse_map[normalized_standard].append(normalized_variant)
    
    def normalize_skill(self, skill: str) -> str:
        """
        Normalize a skill name using synonym mapping
        
        Args:
            skill: Skill name to normalize
            
        Returns:
            Standardized skill name
        """
        normalized = TextNormalizer.normalize_skill(skill)
        
        # Check if we have a synonym mapping
        if normalized in self.synonym_map:
            return self.synonym_map[normalized]
        
        # Check for partial matches (e.g., "sql server" contains "sql")
        for variant, standard in self.synonym_map.items():
            if variant in normalized or normalized in variant:
                # Prefer longer matches
                if len(variant) > len(normalized) or normalized in variant:
                    return standard
        
        return normalized
    
    def get_all_variants(self, standard_skill: str) -> List[str]:
        """
        Get all known variants for a standard skill
        
        Args:
            standard_skill: Standard skill name
            
        Returns:
            List of all variants including the standard form
        """
        normalized = TextNormalizer.normalize_skill(standard_skill)
        variants = self.reverse_map.get(normalized, [])
        return [normalized] + variants


class SkillMatcher:
    """Intelligent skill matching with stemming and optional semantic similarity"""
    
    def __init__(self, use_semantic: bool = False):
        """
        Initialize skill matcher
        
        Args:
            use_semantic: Whether to use semantic embeddings for matching
        """
        self.normalizer = TextNormalizer()
        self.synonym_mapper = SynonymMapper()
        self.use_semantic = use_semantic and SEMANTIC_AVAILABLE
        
        # Initialize stemmer
        if NLTK_AVAILABLE:
            try:
                self.stemmer = SnowballStemmer('english')
                self.stop_words = set(stopwords.words('english'))
            except:
                self.stemmer = None
                self.stop_words = set()
        else:
            self.stemmer = None
            self.stop_words = set()
        
        # Initialize semantic model if available
        self.semantic_model = None
        if self.use_semantic:
            try:
                # Use a lightweight multilingual model
                self.semantic_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                print("✅ Semantic matching enabled with SentenceTransformer")
            except Exception as e:
                print(f"⚠️ Failed to load semantic model: {e}")
                self.use_semantic = False
    
    def _simple_stem(self, word: str) -> str:
        """Simple stemming fallback if NLTK not available"""
        if not word:
            return ""
        # Remove common suffixes
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 's']
        word_lower = word.lower()
        for suffix in suffixes:
            if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 2:
                return word_lower[:-len(suffix)]
        return word_lower
    
    def _tokenize_and_stem(self, text: str) -> List[str]:
        """
        Tokenize text and apply stemming
        
        Args:
            text: Text to tokenize and stem
            
        Returns:
            List of stemmed tokens
        """
        # Normalize first
        normalized = self.normalizer.normalize_text(text)
        
        if NLTK_AVAILABLE and self.stemmer:
            try:
                tokens = word_tokenize(normalized)
                # Remove stopwords and stem
                tokens = [self.stemmer.stem(token) 
                         for token in tokens 
                         if token not in self.stop_words and len(token) > 2]
                return tokens
            except:
                pass
        
        # Fallback: simple tokenization and stemming
        tokens = normalized.split()
        if self.stemmer:
            tokens = [self.stemmer.stem(token) for token in tokens if len(token) > 2]
        else:
            tokens = [self._simple_stem(token) for token in tokens if len(token) > 2]
        
        return tokens
    
    def _semantic_similarity(self, skill1: str, skill2: str) -> float:
        """
        Calculate semantic similarity between two skills using embeddings
        
        Args:
            skill1: First skill
            skill2: Second skill
            
        Returns:
            Similarity score between 0 and 1
        """
        if not self.use_semantic or not self.semantic_model:
            return 0.0
        
        try:
            embeddings = self.semantic_model.encode([skill1, skill2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:
            print(f"⚠️ Semantic similarity error: {e}")
            return 0.0
    
    def match_skills(self, skill1: str, skill2: str, semantic_threshold: float = 0.7) -> bool:
        """
        Check if two skills match using multiple strategies
        
        Args:
            skill1: First skill to compare
            skill2: Second skill to compare
            semantic_threshold: Minimum semantic similarity score (0-1)
            
        Returns:
            True if skills match, False otherwise
        """
        # Strategy 1: Exact match after normalization
        norm1 = self.normalizer.normalize_skill(skill1)
        norm2 = self.normalizer.normalize_skill(skill2)
        
        if norm1 == norm2:
            return True
        
        # Strategy 2: Synonym mapping
        syn1 = self.synonym_mapper.normalize_skill(skill1)
        syn2 = self.synonym_mapper.normalize_skill(skill2)
        
        if syn1 == syn2:
            return True
        
        # Strategy 3: Token-based matching with stemming
        tokens1 = set(self._tokenize_and_stem(skill1))
        tokens2 = set(self._tokenize_and_stem(skill2))
        
        # Check if significant overlap in tokens
        if tokens1 and tokens2:
            overlap = len(tokens1 & tokens2)
            total_unique = len(tokens1 | tokens2)
            token_similarity = overlap / total_unique if total_unique > 0 else 0
            
            if token_similarity > 0.5:  # More than 50% token overlap
                return True
        
        # Strategy 4: Semantic similarity (if enabled)
        if self.use_semantic:
            semantic_score = self._semantic_similarity(skill1, skill2)
            if semantic_score >= semantic_threshold:
                return True
        
        # Strategy 5: Substring matching (for cases like "machine learning" vs "ML")
        if norm1 in norm2 or norm2 in norm1:
            # Only if one is significantly longer (avoid false positives)
            if abs(len(norm1) - len(norm2)) > 2:
                return True
        
        return False
    
    def find_matching_skills(self, skill: str, skill_list: List[str], semantic_threshold: float = 0.7) -> List[str]:
        """
        Find all skills in a list that match a given skill
        
        Args:
            skill: Skill to match
            skill_list: List of skills to search
            semantic_threshold: Minimum semantic similarity score
            
        Returns:
            List of matching skills
        """
        matches = []
        for candidate in skill_list:
            if self.match_skills(skill, candidate, semantic_threshold):
                matches.append(candidate)
        return matches
    
    def normalize_skill_list(self, skills: List[str]) -> List[str]:
        """
        Normalize a list of skills (normalize + synonym mapping)
        
        Args:
            skills: List of skill names
            
        Returns:
            List of normalized skill names
        """
        normalized = []
        for skill in skills:
            norm_skill = self.synonym_mapper.normalize_skill(skill)
            if norm_skill and norm_skill not in normalized:
                normalized.append(norm_skill)
        return normalized


# Global instances
text_normalizer = TextNormalizer()
synonym_mapper = SynonymMapper()
skill_matcher = SkillMatcher(use_semantic=False)  # Semantic disabled by default (requires model download)
