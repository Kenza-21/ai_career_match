import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import string
from typing import List, Tuple
import os

class JobMatcher:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.vectorizer = None
        self.job_vectors = None
        self._preprocess_data()
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for vectorization"""
        if pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _combine_job_features(self, row) -> str:
        """Combine job features with weights for better matching"""
        title_weight = 3  # Weight title more heavily
        skills_weight = 2  # Weight skills more heavily
        description_weight = 1
        
        title = ' '.join([self._preprocess_text(row['job_title'])] * title_weight)
        skills = ' '.join([self._preprocess_text(row['required_skills'])] * skills_weight)
        description = ' '.join([self._preprocess_text(row['description'])] * description_weight)
        category = self._preprocess_text(row['category'])
        
        combined = f"{title} {skills} {description} {category}"
        return combined
    
    def _preprocess_data(self):
        """Preprocess the dataset and create TF-IDF vectors"""
        print("📊 Preprocessing job data...")
        
        # Combine features for each job
        self.df['combined_features'] = self.df.apply(self._combine_job_features, axis=1)
        
        # Initialize and fit TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=['le', 'la', 'les', 'de', 'des', 'du', 'et', 'en', 'au', 'aux', 'à', 'dans', 'pour'],
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        
        # Create TF-IDF vectors
        self.job_vectors = self.vectorizer.fit_transform(self.df['combined_features'])
        print(f"✅ Vectorized {len(self.df)} jobs with {len(self.vectorizer.get_feature_names_out())} features")
    
    def search_jobs(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """Search for jobs matching the query"""
        if not query or query.strip() == "":
            return []
        
        # Preprocess query
        processed_query = self._preprocess_text(query)
        
        # Vectorize query
        query_vector = self.vectorizer.transform([processed_query])
        
        # Compute cosine similarity
        similarities = cosine_similarity(query_vector, self.job_vectors).flatten()
        
        # Get top k matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Only include matches with some similarity
                results.append((idx, similarities[idx]))
        
        return results
    
    def get_job_by_index(self, index: int) -> dict:
        """Get job data by index"""
        return self.df.iloc[index].to_dict()
    
    def get_all_jobs(self) -> List[dict]:
        """Get all jobs"""
        return self.df.to_dict('records')
    
    def get_jobs_by_category(self, category: str) -> List[dict]:
        """Get jobs by category"""
        category_jobs = self.df[self.df['category'].str.lower() == category.lower()]
        return category_jobs.to_dict('records')
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        return self.df['category'].unique().tolist()

    def has_job_title(self, query: str) -> bool:
        """Check if a query matches a known job title in the dataset"""
        if not query or query.strip() == "":
            return False
        q = self._preprocess_text(query)
        titles = self.df['job_title'].fillna("").apply(self._preprocess_text)
        return titles.str.contains(q, regex=False).any()

    def semantic_match_title(self, query: str, threshold: float = 0.6) -> bool:
        """
        Lightweight semantic-ish match: uses TF-IDF on job titles only,
        returns True if cosine similarity exceeds threshold.
        """
        if not query or query.strip() == "":
            return False
        titles = self.df['job_title'].fillna("").apply(self._preprocess_text).tolist()
        # Reuse vectorizer on titles only (small corpus)
        vectorizer = TfidfVectorizer(stop_words=None, ngram_range=(1, 2))
        title_vectors = vectorizer.fit_transform(titles)
        q_vec = vectorizer.transform([self._preprocess_text(query)])
        sims = cosine_similarity(q_vec, title_vectors).flatten()
        return float(sims.max()) >= threshold