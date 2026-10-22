"""
Resume Extractor Module
Handles PDF ingestion and automated extraction of:
- Candidate Name
- Contact Information (Email, Phone, Links)
- Education Credentials (Degree, Major, Institution, CGPA/Year)
- Technical and Professional Skills (categorized)
"""

import re
import os
import pypdf

# Predefined comprehensive skill taxonomy categorized by domain
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "c++", "c#", "c", "javascript", "typescript",
        "go", "golang", "rust", "r", "php", "ruby", "kotlin", "swift",
        "scala", "dart", "bash", "shell", "sql"
    ],
    "Machine Learning & AI": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "scikit-learn", "sklearn", "tensorflow", "keras",
        "pytorch", "hugging face", "transformers", "llm", "large language models",
        "opencv", "nltk", "spacy", "xgboost", "lightgbm", "random forest",
        "decision trees", "neural networks", "bert", "feature engineering"
    ],
    "Data Science & Analytics": [
        "pandas", "numpy", "matplotlib", "seaborn", "tableau", "power bi",
        "data analysis", "data analytics", "data mining", "statistics",
        "jupyter", "spark", "hadoop", "excel", "etl"
    ],
    "Web & Frameworks": [
        "react", "react.js", "angular", "vue", "vue.js", "next.js",
        "node.js", "nodejs", "express", "express.js", "django", "fastapi",
        "flask", "spring boot", "html", "html5", "css", "css3", "tailwind",
        "tailwind css", "bootstrap", "rest api", "restful", "rest apis", "graphql"
    ],
    "Databases": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
        "cassandra", "oracle", "dynamodb", "firebase"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "docker", "kubernetes", "terraform", "ansible", "jenkins",
        "github actions", "ci/cd", "git", "github", "linux", "unix",
        "prometheus", "grafana", "nginx", "microservices"
    ],
    "Soft Skills & Management": [
        "agile", "scrum", "communication", "leadership", "problem solving",
        "critical thinking", "collaboration", "time management"
    ]
}

# Inverted mapping: skill -> category
SKILL_TO_CATEGORY = {}
for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        SKILL_TO_CATEGORY[skill.lower()] = category

# Flattened list of skills sorted by length descending (so multi-word skills like "machine learning" match before "learning")
ALL_SKILLS_SORTED = sorted(SKILL_TO_CATEGORY.keys(), key=lambda x: len(x), reverse=True)

# Degree patterns
DEGREE_PATTERNS = [
    r"\b(B\.?Tech|B\.?E\.?|Bachelor of Technology|Bachelor of Engineering)\b",
    r"\b(M\.?Tech|M\.?E\.?|Master of Technology|Master of Engineering)\b",
    r"\b(B\.?Sc\.?|BCA|Bachelor of Computer Applications|Bachelor of Science)\b",
    r"\b(M\.?Sc\.?|MCA|Master of Computer Applications|Master of Science)\b",
    r"\b(MBA|Master of Business Administration)\b",
    r"\b(Ph\.?D|Doctor of Philosophy)\b"
]


def extract_text_from_pdf(pdf_source):
    """
    Extracts plain text from a PDF file path or a file-like object (e.g., Streamlit UploadedFile).
    """
    text = ""
    try:
        reader = pypdf.PdfReader(pdf_source)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text.strip()


def extract_email(text):
    """Extract candidate email using regex."""
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else "Not Found"


def extract_phone(text):
    """Extract candidate phone number using regex."""
    phone_pattern = r"(?:(?:\+|00)\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{3,5}"
    matches = re.findall(phone_pattern, text)
    for m in matches:
        cleaned = re.sub(r"[^\d+]", "", m)
        if 10 <= len(cleaned) <= 14:
            return m.strip()
    return "Not Found"


def extract_name(text, filename=""):
    """
    Attempts to extract candidate name:
    1. First checking if the filename has a formatted name (e.g., Aarav_Sharma_AI_ML.pdf)
    2. Then inspecting the top lines of the resume text.
    """
    # Try from filename first if descriptive
    if filename:
        clean_name = os.path.splitext(os.path.basename(filename))[0]
        # If separated by underscores, take first 2 parts if they look like names
        parts = clean_name.split("_")
        if len(parts) >= 2 and all(p.isalpha() for p in parts[:2]):
            return f"{parts[0]} {parts[1]}"
            
    # Try from top lines of text
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:
        # Ignore common headings
        if any(h in line.lower() for h in ["resume", "curriculum", "vitae", "profile", "contact", "page"]):
            continue
        # Split on hyphen or pipe if present (e.g., "Aarav Sharma - ML Engineer")
        if "-" in line:
            candidate = line.split("-")[0].strip()
            if 2 <= len(candidate.split()) <= 4:
                return candidate
        elif "|" in line:
            candidate = line.split("|")[0].strip()
            if 2 <= len(candidate.split()) <= 4:
                return candidate
        elif 2 <= len(line.split()) <= 4 and not re.search(r"[@\d:]", line):
            return line

    return "Candidate"


def extract_education(text):
    """
    Extracts degrees, institutions, and graduation year/CGPA if present.
    """
    education_records = []
    lines = text.split("\n")
    
    # Check degree matches
    for line in lines:
        for pat in DEGREE_PATTERNS:
            match = re.search(pat, line, re.IGNORECASE)
            if match:
                clean_line = line.strip()
                if clean_line not in education_records and len(clean_line) < 120:
                    education_records.append(clean_line)
                break
                
    # Search for CGPA / Percentage
    cgpa_match = re.search(r"\b(CGPA[:\s]+[0-9\.]+(?:\s*/\s*10)?|[0-9\.]+\s*CGPA)\b", text, re.IGNORECASE)
    cgpa = cgpa_match.group(0).strip() if cgpa_match else None
    
    # Search for Year of Graduation
    year_match = re.search(r"\b(?:Graduation|Passing|Batch|Year)[:\s]+(20\d\d)\b", text, re.IGNORECASE)
    year = year_match.group(1).strip() if year_match else None
    
    summary = []
    if education_records:
        summary.extend(education_records[:2])
    else:
        summary.append("Degree information mentioned in resume")
        
    if cgpa and not any(cgpa.lower() in rec.lower() for rec in education_records):
        summary.append(cgpa)
    if year and not any(year in rec for rec in education_records):
        summary.append(f"Class of {year}")
        
    return " | ".join(summary)


def extract_skills(text):
    """
    Extracts skills using case-insensitive regex pattern matching from the predefined taxonomy.
    Avoids false positives for short 1-letter or 2-letter tokens using word boundary checks.
    """
    text_lower = " " + text.lower() + " "
    # Replace common punctuation with spaces to allow clean boundary detection
    text_clean = re.sub(r"[,/\\|()\n\r]", " ", text_lower)
    
    found_skills = set()
    
    for skill in ALL_SKILLS_SORTED:
        # Regex boundary check
        pattern = r"(?<![a-zA-Z0-9_#+])" + re.escape(skill) + r"(?![a-zA-Z0-9_#+])"
        if re.search(pattern, text_clean):
            found_skills.add(skill)
            
    # Group found skills by category
    categorized = {}
    for skill in found_skills:
        cat = SKILL_TO_CATEGORY.get(skill, "Other")
        categorized.setdefault(cat, []).append(skill.title())
        
    # Standardize skill capitalization
    formatted_skills = sorted([s.title() for s in found_skills])
    
    return {
        "all_skills": formatted_skills,
        "categorized": categorized,
        "count": len(formatted_skills)
    }


def parse_resume(pdf_source, filename=""):
    """
    Master function: Parses a resume PDF and returns an enriched dictionary.
    """
    raw_text = extract_text_from_pdf(pdf_source)
    if not raw_text:
        return None
        
    name = extract_name(raw_text, filename)
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    education = extract_education(raw_text)
    skills_data = extract_skills(raw_text)
    
    return {
        "filename": filename or "Resume.pdf",
        "name": name,
        "email": email,
        "phone": phone,
        "education": education,
        "skills": skills_data["all_skills"],
        "skills_categorized": skills_data["categorized"],
        "skills_count": skills_data["count"],
        "raw_text": raw_text
    }
