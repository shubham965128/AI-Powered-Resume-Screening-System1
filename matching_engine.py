"""
Matching Engine Module
Implements NLP preprocessing, TF-IDF vectorization, Cosine Similarity,
and Skill Gap Analysis for candidate ranking.
"""

import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from resume_extractor import extract_skills

# Standard English stopwords to avoid external runtime download dependencies
STOPWORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
])


def clean_text(text):
    """
    Cleans text by converting to lowercase, removing special characters/numbers,
    and filtering common stopwords for TF-IDF processing.
    """
    text = text.lower()
    # Preserve key symbols like c++, c#
    text = text.replace("c++", "cplusplus").replace("c#", "csharp").replace(".net", "dotnet")
    # Remove non-alphanumeric except spaces
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    # Tokenize and remove stopwords
    tokens = [word for word in text.split() if word not in STOPWORDS and len(word) > 1]
    return " ".join(tokens)


def compute_tfidf_similarity(job_description, resumes_text):
    """
    Computes cosine similarity between Job Description and each resume
    using Scikit-learn's TfidfVectorizer.
    
    Returns a list of similarity percentages (0 - 100).
    """
    cleaned_jd = clean_text(job_description)
    cleaned_resumes = [clean_text(r) for r in resumes_text]
    
    # Combined corpus
    corpus = [cleaned_jd] + cleaned_resumes
    
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True
    )
    
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    jd_vector = tfidf_matrix[0:1]
    resume_vectors = tfidf_matrix[1:]
    
    # Cosine similarities
    similarities = cosine_similarity(jd_vector, resume_vectors)[0]
    
    # Scale to percentage
    return [round(float(sim) * 100, 2) for sim in similarities]


def analyze_candidate_match(candidate, jd_text, jd_skills, tfidf_score, skill_weight=0.6, tfidf_weight=0.4):
    """
    Computes detailed skill overlap, missing skills, and composite score for a candidate.
    """
    candidate_skills_set = set(s.lower() for s in candidate["skills"])
    jd_skills_set = set(s.lower() for s in jd_skills)
    
    if jd_skills_set:
        matched_set = candidate_skills_set.intersection(jd_skills_set)
        missing_set = jd_skills_set.difference(candidate_skills_set)
        skill_score = (len(matched_set) / len(jd_skills_set)) * 100
    else:
        # If no specific skills detected in JD, fallback fully to TF-IDF score
        matched_set = set()
        missing_set = set()
        skill_score = tfidf_score
        skill_weight = 0.0
        tfidf_weight = 1.0

    # Composite Match Score
    composite_score = round((skill_weight * skill_score) + (tfidf_weight * tfidf_score), 2)
    
    # Status Category
    if composite_score >= 70:
        status = "Shortlisted"
        status_color = "green"
    elif composite_score >= 50:
        status = "Under Review"
        status_color = "orange"
    else:
        status = "Low Match"
        status_color = "red"
        
    return {
        "candidate_name": candidate["name"],
        "email": candidate["email"],
        "phone": candidate["phone"],
        "education": candidate["education"],
        "filename": candidate["filename"],
        "total_candidate_skills": len(candidate["skills"]),
        "matched_skills": sorted([s.title() for s in matched_set]),
        "missing_skills": sorted([s.title() for s in missing_set]),
        "matched_skills_count": len(matched_set),
        "missing_skills_count": len(missing_set),
        "skill_match_percentage": round(skill_score, 2),
        "tfidf_similarity": tfidf_score,
        "composite_score": composite_score,
        "status": status,
        "status_color": status_color,
        "all_candidate_skills": candidate["skills"],
        "skills_categorized": candidate["skills_categorized"],
        "raw_text": candidate["raw_text"]
    }


RANKING_COLUMNS = [
    "Rank", "Candidate Name", "Composite Score (%)", "Skill Match (%)",
    "TF-IDF Match (%)", "Status", "Matched Skills", "Missing Skills",
    "Education", "Email", "Filename"
]


def rank_candidates(candidates, job_description, skill_weight=0.6, tfidf_weight=0.4):
    """
    Master function:
    1. Extracts required skills from Job Description
    2. Runs TF-IDF vectorization & Cosine Similarity across all candidates
    3. Computes composite scores & gap analysis
    4. Returns ranked Pandas DataFrame and list of candidate detail records.
    """
    if not candidates or not job_description.strip():
        return pd.DataFrame(columns=RANKING_COLUMNS), []
        
    # Extract skills present in JD
    jd_skills_data = extract_skills(job_description)
    jd_skills = jd_skills_data["all_skills"]
    
    # Compute TF-IDF Cosine Similarity
    resumes_text = [c["raw_text"] for c in candidates]
    tfidf_scores = compute_tfidf_similarity(job_description, resumes_text)
    
    # Analyze each candidate
    analyzed_records = []
    for cand, tfidf in zip(candidates, tfidf_scores):
        record = analyze_candidate_match(
            cand,
            job_description,
            jd_skills,
            tfidf,
            skill_weight=skill_weight,
            tfidf_weight=tfidf_weight
        )
        analyzed_records.append(record)
        
    # Sort descending by composite_score
    analyzed_records.sort(key=lambda x: x["composite_score"], reverse=True)
    
    # Build clean DataFrame for Streamlit table display
    df_data = []
    for rank, rec in enumerate(analyzed_records, start=1):
        df_data.append({
            "Rank": rank,
            "Candidate Name": rec["candidate_name"],
            "Composite Score (%)": rec["composite_score"],
            "Skill Match (%)": rec["skill_match_percentage"],
            "TF-IDF Match (%)": rec["tfidf_similarity"],
            "Status": rec["status"],
            "Matched Skills": ", ".join(rec["matched_skills"]) if rec["matched_skills"] else "None",
            "Missing Skills": ", ".join(rec["missing_skills"]) if rec["missing_skills"] else "None",
            "Education": rec["education"],
            "Email": rec["email"],
            "Filename": rec["filename"]
        })
        
    df = pd.DataFrame(df_data)
    return df, analyzed_records
