# AI-Powered Resume Screening & Ranking System

An AI-driven platform tailored for **campus placements, recruitment drives, and project viva demonstrations**. Built using **Python, NLP, Scikit-learn, Streamlit, and Pandas**.

---

## 🌟 Key Features

1. **Automated PDF Parsing**: Extracts text from multiple candidate resume PDFs concurrently using `pypdf`.
2. **NLP-Powered Entity Extraction**: Automatically detects:
   - Candidate Name
   - Email address and Phone number
   - Education credentials (Degrees, Institutions, Year of Passing, CGPA)
   - Technical skills categorized into 6 domains (ML/AI, Web Development, Programming, Cloud/DevOps, Databases, Soft Skills).
3. **Scikit-learn TF-IDF & Cosine Similarity**:
   - Vectorizes resumes and job descriptions using unigrams & bigrams.
   - Measures semantic alignment length-invariantly using Cosine Similarity.
4. **Skill Gap Analysis**: Compares candidate competencies against required skills, highlighting matched skills and missing qualifications.
5. **Interactive Streamlit Dashboard**:
   - **Leaderboard**: Ranked candidate table with score bars, status badges, and CSV export.
   - **Candidate Deep Dive**: Detailed candidate profile, matched vs missing skills, and comparison charts.
   - **Batch Analytics**: Candidate score distribution and most commonly missing skills across applicants.
   - **Invigilator / Viva Defense Guide**: Built-in architecture diagram, mathematical formulas (TF-IDF, Cosine Similarity), and answers to top 7 viva questions.
6. **Built-in Sample Resumes**: Comes with 4 pre-built realistic candidate PDFs (*Aarav Sharma - ML*, *Priya Patel - Full Stack*, *Rohan Verma - DevOps*, *Sneha Reddy - Junior Intern*) for immediate 1-click demonstration.

---

## 🚀 Quick Start (Running the Code)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Sample Resumes (If needed)
```bash
python sample_generator.py
```

### 3. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
The application will open in your web browser at:
`http://localhost:8501`

---

## 🎯 How to Demonstrate to the Invigilator

1. **Launch the App**: Run `streamlit run app.py`.
2. **Select a Job Role**: In the left sidebar, choose a role like **"AI / Machine Learning Engineer"** or **"Full Stack Web Developer"**.
3. **Load Candidates**: Click the **"🚀 Load Demo Resumes"** button (or upload your own PDF resumes).
4. **Show the Leaderboard**:
   - Show how candidates are automatically ranked.
   - For an ML job, show that *Aarav Sharma* ranks #1 with top match score, while web and devops candidates rank lower.
   - Switch the job role to **"Full Stack Web Developer"** to show that *Priya Patel* immediately rises to #1!
5. **Show Candidate Deep Dive**:
   - Click the **"🔍 Candidate Deep Dive"** tab.
   - Point out the extracted Name, Email, Phone, and Education (e.g., IIT Madras, CGPA).
   - Show the green **Matched Skills** vs red **Missing Skills**.
6. **Show Batch Analytics**:
   - Click the **"📈 Batch Analytics"** tab to display the score distribution and talent gap charts.
7. **Open Viva Defense Guide**:
   - Click the **"🎓 Invigilator & Viva Defense Guide"** tab.
   - Show the system architecture diagram, TF-IDF mathematical formula, and Cosine similarity equations.

---

## 📁 Project Structure

```
├── app.py                 # Main Streamlit web dashboard
├── resume_extractor.py    # PDF parsing & NLP entity/skill extraction
├── matching_engine.py     # TF-IDF, Cosine similarity & candidate ranking
├── sample_generator.py    # Generates realistic sample candidate PDF resumes
├── requirements.txt       # Python package dependencies
├── sample_resumes/        # Pre-generated candidate resumes
└── README.md              # Project documentation
```

---

## 📐 Mathematical Formulation

### 1. TF-IDF (Term Frequency - Inverse Document Frequency)
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \log\left(\frac{1 + |D|}{1 + \text{df}(t)}\right) + 1$$

### 2. Cosine Similarity
$$\text{Similarity}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$

### 3. Composite Score
$$\text{Score} = (0.60 \times \text{Skill Match \%}) + (0.40 \times \text{TF-IDF Match \%})$$
