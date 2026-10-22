"""
Automated Verification Script for AI Resume Screening System
Tests:
1. PDF file generation
2. Resume Parsing (Email, Phone, Education, Skills)
3. Matching Engine (TF-IDF, Cosine Similarity, Skill Gap)
4. Candidate Ranking Leaderboard
"""

import os
import glob
from sample_generator import generate_sample_resumes
from resume_extractor import parse_resume
from matching_engine import rank_candidates

def run_tests():
    print("=" * 60)
    print("RUNNING AI RESUME SCREENING TEST SUITE")
    print("=" * 60)
    
    # 1. Test Sample Resumes Generation
    pdf_files = generate_sample_resumes("sample_resumes")
    assert len(pdf_files) == 4, f"Expected 4 PDFs, got {len(pdf_files)}"
    print("[PASS] 1. Sample PDF Generation verified (4 PDFs created)")
    
    # 2. Test Parsing on all resumes
    parsed_resumes = []
    for f in pdf_files:
        data = parse_resume(f, os.path.basename(f))
        assert data is not None, f"Failed to parse {f}"
        assert data["email"] != "Not Found", f"Email not extracted in {f}"
        assert data["phone"] != "Not Found", f"Phone not extracted in {f}"
        assert len(data["skills"]) > 0, f"No skills extracted in {f}"
        parsed_resumes.append(data)
        print(f"  - Parsed {data['name']}: {data['email']} | Skills: {len(data['skills'])}")
    print("[PASS] 2. Information & Skill Extraction verified")
    
    # 3. Test Machine Learning Matching for AI/ML Job Description
    ml_jd = (
        "Seeking an AI / Machine Learning Engineer with strong Python skills, "
        "Scikit-learn, TensorFlow, PyTorch, Deep Learning, NLP, Docker, and AWS."
    )
    df_rank, records = rank_candidates(parsed_resumes, ml_jd)
    assert not df_rank.empty, "Ranking DataFrame is empty"
    assert records[0]["candidate_name"] == "Aarav Sharma", f"Expected Aarav Sharma to rank #1 for ML role, got {records[0]['candidate_name']}"
    assert records[0]["skill_match_percentage"] == 100.0, "Expected 100% skill match for Aarav Sharma"
    print(f"[PASS] 3. ML Job Match Ranking verified (Top: {records[0]['candidate_name']} with {records[0]['composite_score']}%)")
    
    # 4. Test Web Developer Job Description
    web_jd = (
        "Seeking a Full Stack Web Developer skilled in React, Node.js, Express, "
        "JavaScript, TypeScript, HTML, CSS, MongoDB, and PostgreSQL."
    )
    df_web, records_web = rank_candidates(parsed_resumes, web_jd)
    assert records_web[0]["candidate_name"] == "Priya Patel", f"Expected Priya Patel to rank #1 for Web role, got {records_web[0]['candidate_name']}"
    print(f"[PASS] 4. Web Developer Match Ranking verified (Top: {records_web[0]['candidate_name']} with {records_web[0]['composite_score']}%)")
    
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! The system is ready to run and demo.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
