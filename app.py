"""
AI-Powered Resume Screening System (Placements Edition)
Streamlit Application
"""

import os
import glob
import pandas as pd
import streamlit as st
import altair as alt

from resume_extractor import parse_resume, extract_skills
from matching_engine import rank_candidates, RANKING_COLUMNS
from sample_generator import generate_sample_resumes

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Screening System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern placement portal styling
st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    
    /* Section Headers */
    .sub-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #2b2d42;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    
    /* Skill Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 14px;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .badge-matched {
        background-color: #d1e7dd;
        color: #0f5132;
        border: 1px solid #badbcc;
    }
    .badge-missing {
        background-color: #f8d7da;
        color: #842029;
        border: 1px solid #f5c2c7;
    }
    .badge-extra {
        background-color: #e2e3e5;
        color: #41464b;
        border: 1px solid #d3d6d8;
    }
    .badge-category {
        background-color: #cfe2ff;
        color: #084298;
        border: 1px solid #b6d4fe;
    }
    
    /* Formula Box */
    .formula-box {
        background-color: #f8f9fa;
        border-left: 4px solid #4361ee;
        padding: 12px 18px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Preset Job Descriptions
# ---------------------------------------------------------
JOB_PRESETS = {
    "AI / Machine Learning Engineer": (
        "Role: AI / Machine Learning Engineer\n"
        "Requirements:\n"
        "- Strong proficiency in Python, Data Structures, and Algorithms.\n"
        "- Expertise in Scikit-learn, TensorFlow, PyTorch, and Deep Learning.\n"
        "- Hands-on experience with Natural Language Processing (NLP) or Computer Vision.\n"
        "- Experience with Pandas, NumPy, Feature Engineering, and model evaluation.\n"
        "- Familiarity with Docker, Git, and deploying ML models on AWS or GCP.\n"
        "- Degree: B.Tech / M.Tech in Computer Science, Data Science, or related field."
    ),
    "Full Stack Web Developer": (
        "Role: Full Stack Web Developer\n"
        "Requirements:\n"
        "- Strong fundamentals in JavaScript, TypeScript, HTML5, and CSS3.\n"
        "- Production experience with React, Next.js, and modern frontend state management.\n"
        "- Backend proficiency with Node.js, Express, FastAPI, or Django.\n"
        "- Experience designing RESTful APIs and working with PostgreSQL or MongoDB.\n"
        "- Working knowledge of Git, Docker, and CI/CD pipelines."
    ),
    "Cloud & DevOps Engineer": (
        "Role: Cloud & DevOps Engineer\n"
        "Requirements:\n"
        "- Extensive experience with AWS, Microsoft Azure, or GCP.\n"
        "- Strong containerization experience with Docker and Kubernetes.\n"
        "- Infrastructure as Code (IaC) using Terraform or Ansible.\n"
        "- Scripting skills in Python, Bash, and Linux administration.\n"
        "- CI/CD automation with GitHub Actions, Jenkins, and system monitoring with Prometheus/Grafana."
    ),
    "Data Analyst / BI Specialist": (
        "Role: Data Analyst\n"
        "Requirements:\n"
        "- Proficiency in Python and advanced SQL querying.\n"
        "- Expertise in Pandas, NumPy, Matplotlib, and Seaborn for statistical data analysis.\n"
        "- Experience building interactive business dashboards in Tableau or Power BI.\n"
        "- Solid grounding in Statistics, ETL processes, and Excel data modeling."
    ),
    "Custom Job Description": ""
}

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/resume.png", width=64)
    st.title("Screening Controls")
    
    st.subheader("1. Job Description")
    selected_preset = st.selectbox(
        "Select Job Role Preset:",
        options=list(JOB_PRESETS.keys()),
        index=0
    )
    
    if selected_preset == "Custom Job Description":
        jd_input = st.text_area(
            "Paste Job Description:",
            height=160,
            placeholder="Paste complete job description, requirements, and required skills here..."
        )
    else:
        jd_input = st.text_area(
            "Job Description (Editable):",
            value=JOB_PRESETS[selected_preset],
            height=160
        )
        
    st.markdown("---")
    st.subheader("2. Candidate Resumes (PDF)")
    
    # 1-Click Demo Resumes Loader
    col_demo, col_info = st.columns([1.8, 1])
    with col_demo:
        load_demo = st.button("🚀 Load Demo Resumes", help="Loads 4 sample resumes ready for invigilator testing.")
    with col_info:
        if st.button("🔄 Reset"):
            st.session_state["resumes"] = []
            st.rerun()
            
    uploaded_files = st.file_uploader(
        "Upload Resume PDFs:",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or multiple candidate resume PDFs."
    )
    
    st.markdown("---")
    st.subheader("3. Scoring Weights (Viva Tuning)")
    st.caption("Adjust weightage between direct Skill Match & TF-IDF Cosine Similarity:")
    skill_weight_pct = st.slider("Skill Match Weight (%)", min_value=0, max_value=100, value=60, step=5)
    tfidf_weight_pct = 100 - skill_weight_pct
    st.info(f"Weights: **{skill_weight_pct}% Skill Overlap** + **{tfidf_weight_pct}% TF-IDF Context**")
    
    min_shortlist_threshold = st.slider("Shortlist Cutoff Score (%)", min_value=30, max_value=90, value=65, step=5)

# Ensure sample resumes exist
if not os.path.exists("sample_resumes") or len(glob.glob("sample_resumes/*.pdf")) == 0:
    generate_sample_resumes("sample_resumes")

# State Management for parsed resumes
if "resumes" not in st.session_state:
    st.session_state["resumes"] = []

# If demo button clicked, load all sample PDFs
if load_demo:
    with st.spinner("Parsing sample candidate resumes..."):
        sample_files = glob.glob("sample_resumes/*.pdf")
        parsed = []
        for sf in sample_files:
            c = parse_resume(sf, os.path.basename(sf))
            if c:
                parsed.append(c)
        st.session_state["resumes"] = parsed
        st.success(f"Loaded {len(parsed)} candidate profiles!")

# If user uploaded files, parse them
if uploaded_files:
    with st.spinner("Extracting text and skills from uploaded resumes..."):
        parsed = []
        for uf in uploaded_files:
            c = parse_resume(uf, uf.name)
            if c:
                parsed.append(c)
        st.session_state["resumes"] = parsed

candidates = st.session_state.get("resumes", [])

# ---------------------------------------------------------
# Main UI
# ---------------------------------------------------------
st.markdown("## 🎯 AI-Powered Resume Screening System")
st.markdown(
    "**Campus Placement & Talent Screening Engine** &nbsp;|&nbsp; "
    "Powered by **NLP**, **Scikit-learn (TF-IDF & Cosine Similarity)**, and **Pandas**"
)

if not candidates:
    st.warning("👉 Please click **'🚀 Load Demo Resumes'** in the sidebar or upload candidate PDF resumes to begin screening.")
    
    # Quick teaser cards
    st.markdown("### System Capabilities for Placement Drives:")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        #### 📄 PDF Auto-Extraction
        - Extracts candidate Name, Email, and Phone number.
        - Automatically captures degree, institution, and graduation year/CGPA.
        - Identifies skills across 6 domains (ML, Web, Cloud, etc.).
        """)
    with c2:
        st.markdown("""
        #### 🧠 Machine Learning Engine
        - **Scikit-learn TF-IDF Vectorization** (Unigrams + Bigrams).
        - **Cosine Similarity** evaluates semantic relevance to JD.
        - **Skill Overlap Algorithm** identifies exact & missing qualifications.
        """)
    with c3:
        st.markdown("""
        #### 📊 Ranking & Analytics
        - Instant ranked candidate leaderboard.
        - Skill gap identification (Matched vs Missing).
        - One-click CSV export of placement screening results.
        - Viva defense notes with formulas and theory.
        """)
    st.stop()
    # Ensure execution stops cleanly even in bare mode
    df_rankings = pd.DataFrame(columns=RANKING_COLUMNS)
    candidate_records = []

if candidates:
    # ---------------------------------------------------------
    # Execute Ranking
    # ---------------------------------------------------------
    skill_weight = skill_weight_pct / 100.0
    tfidf_weight = tfidf_weight_pct / 100.0

    df_rankings, candidate_records = rank_candidates(
        candidates,
        jd_input,
        skill_weight=skill_weight,
        tfidf_weight=tfidf_weight
    )

# Apply threshold
for rec in candidate_records:
    if rec["composite_score"] >= min_shortlist_threshold:
        rec["status"] = "Shortlisted"
        rec["status_color"] = "green"
    elif rec["composite_score"] >= (min_shortlist_threshold - 20):
        rec["status"] = "Under Review"
        rec["status_color"] = "orange"
    else:
        rec["status"] = "Low Match"
        rec["status_color"] = "red"

# Update DF status
for i, rec in enumerate(candidate_records):
    df_rankings.loc[i, "Status"] = rec["status"]

# ---------------------------------------------------------
# Top Metric Cards
# ---------------------------------------------------------
total_candidates = len(candidate_records)
shortlisted_count = sum(1 for r in candidate_records if r["status"] == "Shortlisted")
avg_score = round(df_rankings["Composite Score (%)"].mean(), 2) if not df_rankings.empty else 0
top_score = df_rankings["Composite Score (%)"].max() if not df_rankings.empty else 0
top_candidate = candidate_records[0]["candidate_name"] if candidate_records else "N/A"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Resumes Screened", f"{total_candidates}")
m2.metric("Shortlisted Candidates", f"{shortlisted_count}", f"Cutoff: {min_shortlist_threshold}%")
m3.metric("Batch Average Score", f"{avg_score}%")
m4.metric("Top Ranked Applicant", f"{top_candidate}", f"{top_score}% Match")

st.markdown("---")

# ---------------------------------------------------------
# Tabs: Dashboard, Deep Dive, Analytics, Viva Guide
# ---------------------------------------------------------
tab_leaderboard, tab_deepdive, tab_analytics, tab_viva = st.tabs([
    "🏆 Candidate Leaderboard",
    "🔍 Candidate Deep Dive & Gap Analysis",
    "📈 Batch Analytics & Skill Trends",
    "🎓 Invigilator & Viva Defense Guide"
])

# =========================================================
# TAB 1: LEADERBOARD
# =========================================================
with tab_leaderboard:
    st.markdown("### 🏅 Candidate Screening & Ranking Leaderboard")
    st.caption("Candidates are ranked based on the weighted combination of Skill Overlap and TF-IDF Cosine Similarity.")
    
    # Format table for display
    display_df = df_rankings[[
        "Rank", "Candidate Name", "Composite Score (%)", "Skill Match (%)",
        "TF-IDF Match (%)", "Status", "Matched Skills", "Missing Skills", "Education", "Email"
    ]].copy()
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Composite Score (%)": st.column_config.ProgressColumn(
                "Composite Score",
                help="Weighted composite match score",
                format="%.1f%%",
                min_value=0,
                max_value=100
            ),
            "Skill Match (%)": st.column_config.NumberColumn(
                "Skill Match",
                format="%.1f%%"
            ),
            "TF-IDF Match (%)": st.column_config.NumberColumn(
                "TF-IDF Sim",
                format="%.1f%%"
            ),
            "Rank": st.column_config.NumberColumn("Rank", width="small")
        },
        hide_index=True
    )
    
    # Download Button
    csv = df_rankings.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Screening Results (CSV)",
        data=csv,
        file_name="placement_screening_results.csv",
        mime="text/csv"
    )

# =========================================================
# TAB 2: CANDIDATE DEEP DIVE
# =========================================================
with tab_deepdive:
    st.markdown("### 🔍 In-Depth Candidate Profile & Skill Gap Analysis")
    
    candidate_names = [r["candidate_name"] for r in candidate_records]
    if candidate_names:
        selected_name = st.selectbox("Select Candidate to Inspect:", options=candidate_names, index=0)
        cand = next(r for r in candidate_records if r["candidate_name"] == selected_name)
    else:
        st.info("Please load or upload candidate resumes to inspect detailed profiles.")
        cand = None

    if cand:
        # Candidate Header Card
        col_info_left, col_info_right = st.columns([2, 1])
        with col_info_left:
            st.markdown(f"#### **{cand['candidate_name']}**")
            st.markdown(f"📧 **Email:** `{cand['email']}` &nbsp;|&nbsp; 📞 **Phone:** `{cand['phone']}`")
            st.markdown(f"🎓 **Education:** {cand['education']}")
            st.markdown(f"📁 **Source File:** `{cand['filename']}`")
            
        with col_info_right:
            status_color = "#2ec4b6" if cand["status"] == "Shortlisted" else ("#ff9f1c" if cand["status"] == "Under Review" else "#e71d36")
            st.markdown(f"""
            <div style="background-color: #f8f9fa; border: 1px solid #ddd; padding: 12px; border-radius: 8px; text-align: center;">
                <span style="font-size: 0.9rem; color: #666;">Match Status</span><br/>
                <span style="font-size: 1.3rem; font-weight: bold; color: {status_color};">{cand['status']}</span>
                <div style="margin-top: 5px; font-size: 1.1rem; font-weight: 600;">
                    {cand['composite_score']}% Composite
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Skill Gap Comparison
        col_matched, col_missing, col_extra = st.columns(3)
        
        with col_matched:
            st.markdown(f"##### ✅ Matched Skills ({len(cand['matched_skills'])})")
            if cand["matched_skills"]:
                badges_html = "".join([f"<span class='badge badge-matched'>{s}</span>" for s in cand["matched_skills"]])
                st.markdown(badges_html, unsafe_allow_html=True)
            else:
                st.info("No matching skills found.")
                
        with col_missing:
            st.markdown(f"##### ❌ Missing Required Skills ({len(cand['missing_skills'])})")
            if cand["missing_skills"]:
                badges_html = "".join([f"<span class='badge badge-missing'>{s}</span>" for s in cand["missing_skills"]])
                st.markdown(badges_html, unsafe_allow_html=True)
            else:
                st.success("Candidate possesses all required skills!")
                
        with col_extra:
            extra_skills = [s for s in cand["all_candidate_skills"] if s not in cand["matched_skills"]]
            st.markdown(f"##### ➕ Additional Skills ({len(extra_skills)})")
            if extra_skills:
                badges_html = "".join([f"<span class='badge badge-extra'>{s}</span>" for s in extra_skills])
                st.markdown(badges_html, unsafe_allow_html=True)
            else:
                st.caption("No additional skills detected.")

        st.markdown("---")
        
        # Categorized Skills Breakdown
        st.markdown("##### 📂 Candidate Skills by Category")
        if cand["skills_categorized"]:
            cat_cols = st.columns(len(cand["skills_categorized"]))
            for idx, (cat_name, skills_list) in enumerate(cand["skills_categorized"].items()):
                with cat_cols[idx % len(cat_cols)]:
                    st.markdown(f"**{cat_name}**")
                    badges_html = "".join([f"<span class='badge badge-category'>{s}</span>" for s in skills_list])
                    st.markdown(badges_html, unsafe_allow_html=True)
                    
        st.markdown("---")
        
        # Candidate vs Batch Score Chart
        st.markdown("##### 📊 Performance vs. Batch Average")
        comparison_data = pd.DataFrame({
            "Metric": ["Skill Match", "TF-IDF Similarity", "Composite Score"],
            "Candidate": [cand["skill_match_percentage"], cand["tfidf_similarity"], cand["composite_score"]],
            "Batch Average": [
                round(df_rankings["Skill Match (%)"].mean(), 2) if not df_rankings.empty else 0,
                round(df_rankings["TF-IDF Match (%)"].mean(), 2) if not df_rankings.empty else 0,
                round(df_rankings["Composite Score (%)"].mean(), 2) if not df_rankings.empty else 0
            ]
        })
        
        melted = comparison_data.melt(id_vars="Metric", var_name="Source", value_name="Score (%)")
        chart = alt.Chart(melted).mark_bar().encode(
            x=alt.X("Metric:N", axis=alt.Axis(title=None)),
            y=alt.Y("Score (%):Q", axis=alt.Axis(title="Percentage (%)")),
            color=alt.Color("Source:N", scale=alt.Scale(range=["#4361ee", "#adb5bd"])),
            xOffset="Source:N"
        ).properties(height=260)
        
        st.altair_chart(chart, use_container_width=True)

# =========================================================
# TAB 3: BATCH ANALYTICS
# =========================================================
with tab_analytics:
    st.markdown("### 📈 Batch Analytics & Talent Insights")
    
    if not df_rankings.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("##### 📊 Candidate Score Distribution")
            score_chart = alt.Chart(df_rankings).mark_bar(color="#4361ee").encode(
                x=alt.X("Candidate Name:N", sort="-y", title="Candidate"),
                y=alt.Y("Composite Score (%):Q", title="Score (%)"),
                tooltip=["Candidate Name", "Composite Score (%)", "Skill Match (%)", "TF-IDF Match (%)"]
            ).properties(height=300)
            st.altair_chart(score_chart, use_container_width=True)
            
        with col_chart2:
            st.markdown("##### 📋 Placement Status Distribution")
            status_counts = df_rankings["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            donut_chart = alt.Chart(status_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Status", type="nominal", scale=alt.Scale(
                    domain=["Shortlisted", "Under Review", "Low Match"],
                    range=["#2ec4b6", "#ff9f1c", "#e71d36"]
                )),
                tooltip=["Status", "Count"]
            ).properties(height=300)
            st.altair_chart(donut_chart, use_container_width=True)
            
        st.markdown("---")
        
        # Missing Skills Gap Analysis Across the Batch
        st.markdown("##### ⚠️ Top Missing Skills Across All Applicants")
        all_missing = []
        for r in candidate_records:
            all_missing.extend(r["missing_skills"])
            
        if all_missing:
            missing_series = pd.Series(all_missing).value_counts().reset_index()
            missing_series.columns = ["Skill", "Candidates Lacking"]
            
            gap_chart = alt.Chart(missing_series.head(10)).mark_bar(color="#e71d36").encode(
                x=alt.X("Candidates Lacking:Q", title="Number of Candidates Missing This Skill"),
                y=alt.Y("Skill:N", sort="-x", title="Required Skill"),
                tooltip=["Skill", "Candidates Lacking"]
            ).properties(height=260)
            
            st.altair_chart(gap_chart, use_container_width=True)
        else:
            st.success("No missing skills recorded across applicants.")
    else:
        st.info("Please load or upload candidate resumes to view batch analytics.")

# =========================================================
# TAB 4: INVIGILATOR & VIVA DEFENSE GUIDE
# =========================================================
with tab_viva:
    st.markdown("### 🎓 Invigilator & Viva Defense Cheat Sheet")
    st.markdown(
        "Use this section to explain the mathematical underpinnings, NLP pipeline, and system architecture to your invigilator."
    )
    
    with st.expander("📌 1. System Architecture & Workflow", expanded=True):
        st.markdown("""
        ```mermaid
        graph TD
            A[Candidate Resumes in PDF] --> B[pypdf Text Extraction]
            B --> C[NLP Preprocessing & Cleaning]
            C --> D[Entity Extraction: Name, Email, Phone, Education]
            C --> E[Taxonomy-based Skill Extraction]
            
            F[Job Description] --> G[NLP Preprocessing]
            G --> H[JD Skill Extraction]
            
            C & G --> I[Scikit-learn TF-IDF Vectorizer]
            I --> J[Cosine Similarity Engine]
            
            E & H --> K[Skill Overlap & Jaccard Metric]
            
            J & K --> L[Weighted Composite Score Generator]
            L --> M[Candidate Ranking Leaderboard & Analytics]
        ```
        """)
        st.markdown("""
        **Pipeline Steps:**
        1. **Text Extraction**: `pypdf` streams binary PDF objects into normalized UTF-8 text.
        2. **Information Extraction**: Regular expressions and keyword boundaries parse candidate contact info and educational qualifications.
        3. **Skill Classification**: Multi-category taxonomy mapping skills into domain dictionaries.
        4. **Scikit-learn TF-IDF Vectorization**: Unigram and bigram representation with sublinear term frequency.
        5. **Cosine Similarity**: Vector dot-product in high-dimensional feature space.
        6. **Ranking & Dashboard**: Real-time Streamlit visualization and CSV export.
        """)
        
    with st.expander("📐 2. Mathematical Foundations (TF-IDF & Cosine Similarity)"):
        st.markdown("#### A. Term Frequency - Inverse Document Frequency (TF-IDF)")
        st.markdown(r"""
        $$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$
        - **Term Frequency $\text{TF}(t, d)$**: Measures how frequently term $t$ appears in document $d$. Sublinear scaling $\text{TF} = 1 + \log(\text{count})$ is used to prevent high-frequency words from dominating.
        - **Inverse Document Frequency $\text{IDF}(t, D)$**: Downweights words that appear across all resumes:
        $$\text{IDF}(t, D) = \log\left(\frac{1 + |D|}{1 + \text{df}(t)}\right) + 1$$
        """)
        
        st.markdown("#### B. Cosine Similarity Formula")
        st.markdown(r"""
        Measures the cosine of the angle between the Job Description vector $\vec{A}$ and Candidate Resume vector $\vec{B}$:
        $$\text{Cosine Similarity}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$
        - **Range**: $[0, 1]$ (or $0\%$ to $100\%$).
        - **Advantage over Euclidean distance**: Evaluates semantic orientation independent of resume document length.
        """)
        
        st.markdown("#### C. Composite Scoring Formula")
        st.markdown(r"""
        $$\text{Composite Score} = (w_{\text{skills}} \times \text{Skill Match \%}) + (w_{\text{tfidf}} \times \text{TF-IDF Similarity \%})$$
        - Default weights: $w_{\text{skills}} = 0.60$, $w_{\text{tfidf}} = 0.40$.
        """)

    with st.expander("💬 3. Top 7 Viva Questions & Model Answers"):
        st.markdown("""
        **Q1: Why did you use TF-IDF instead of simple keyword counting?**  
        *Answer:* Simple keyword counting suffers from word frequency bias (a resume repeating "Python" 20 times would artificially rank highest). TF-IDF penalizes common words and gives higher weight to rare, domain-specific technical terms.
        
        **Q2: Why use Cosine Similarity instead of Euclidean Distance?**  
        *Answer:* Euclidean distance is sensitive to document length (a 4-page resume would be positioned far from a 1-page job description even if they contain the same skills). Cosine similarity measures the angle between vectors, which is length-invariant.
        
        **Q3: How does the system handle multi-word skills like 'Machine Learning' or 'Deep Learning'?**  
        *Answer:* We use bi-gram tokenization `ngram_range=(1, 2)` in Scikit-learn's `TfidfVectorizer` and sort skill patterns by character length descending so multi-word tokens are matched before individual words.
        
        **Q4: How do you prevent single-letter skills like 'C' or 'R' from falsely matching in words like 'Computer'?**  
        *Answer:* We enforce negative lookahead and lookbehind word boundaries `(?<![a-zA-Z0-9_#+])` and `(?![a-zA-Z0-9_#+])` so 'C' only matches as an isolated programming language token.
        
        **Q5: What are the benefits for campus placement departments?**  
        *Answer:* It eliminates manual screening of hundreds of PDFs, prevents unconscious bias, produces an instant ranked shortlist, and highlights skill gaps for students to improve.
        
        **Q6: What is the time complexity of the matching engine?**  
        *Answer:* Feature extraction is $O(N \times L)$ where $N$ is resumes and $L$ is length. Cosine similarity against 1 job description vector is $O(N \times V)$ where $V$ is vocabulary size. It screens hundreds of resumes in seconds.
        
        **Q7: How can this system be extended in the future?**  
        *Answer:* By incorporating Transformer embeddings (BERT/Sentence-BERT), OCR for scanned image PDFs, and automated interview question generation based on missing skills.
        """)

st.markdown("---")
st.caption("AI-Powered Resume Screening System | Final Year / Placement Project Demonstration")
