import os

def create_pdf(filepath, title, sections):
    """
    Generates a valid, well-formed PDF document with multiple text sections
    using standard PDF 1.4 syntax, without requiring third-party PDF compilation libraries.
    """
    stream_content = []
    
    # Starting vertical position
    y = 750
    line_height = 14
    margin_left = 50
    
    # Title
    stream_content.append("BT")
    stream_content.append("/F2 16 Tf")
    stream_content.append(f"{margin_left} {y} Td")
    stream_content.append(f"({escape_pdf(title)}) Tj")
    stream_content.append("ET")
    y -= 25
    
    for heading, items in sections:
        if y < 60:
            break
            
        # Section Heading
        stream_content.append("BT")
        stream_content.append("/F2 12 Tf")
        stream_content.append(f"{margin_left} {y} Td")
        stream_content.append(f"({escape_pdf(heading)}) Tj")
        stream_content.append("ET")
        y -= 18
        
        # Section Items
        stream_content.append("BT")
        stream_content.append("/F1 10 Tf")
        stream_content.append(f"{margin_left + 10} {y} Td")
        
        first = True
        for line in items:
            if not first:
                stream_content.append(f"0 -{line_height} Td")
            first = False
            stream_content.append(f"({escape_pdf(line)}) Tj")
            y -= line_height
            
        stream_content.append("ET")
        y -= 12

    stream_bytes = "\n".join(stream_content).encode('latin-1', 'replace')
    stream_len = len(stream_bytes)
    
    # PDF Objects
    objects = []
    
    # 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    # 3: Page
    objects.append(
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj"
    )
    # 4: Contents Stream
    objects.append(
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n"
        + "\n".join(stream_content)
        + "\nendstream\nendobj"
    )
    # 5: Regular Font (Helvetica)
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    # 6: Bold Font (Helvetica-Bold)
    objects.append("6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj")
    
    # Build complete PDF with XRef table
    header = "%PDF-1.4\n"
    body = ""
    offsets = [0]
    
    curr_offset = len(header)
    for obj in objects:
        offsets.append(curr_offset)
        obj_str = obj + "\n"
        body += obj_str
        curr_offset += len(obj_str.encode('latin-1'))
        
    xref_offset = curr_offset
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n"
        
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write((header + body + xref + trailer).encode('latin-1', 'replace'))

def escape_pdf(text):
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

def generate_sample_resumes(output_dir="sample_resumes"):
    resumes = [
        {
            "filename": "Aarav_Sharma_AI_ML_Engineer.pdf",
            "title": "Aarav Sharma - Machine Learning Engineer",
            "sections": [
                ("Contact Information", [
                    "Email: aarav.sharma@email.com",
                    "Phone: +91 98765 43210",
                    "LinkedIn: linkedin.com/in/aarav-sharma-ml",
                    "Location: Bangalore, India"
                ]),
                ("Education", [
                    "B.Tech in Computer Science and Engineering - IIT Madras (CGPA: 8.9/10)",
                    "Year of Graduation: 2024",
                    "Relevant Coursework: Machine Learning, Deep Learning, NLP, Data Structures & Algorithms"
                ]),
                ("Technical Skills", [
                    "Languages: Python, C++, SQL, R",
                    "Machine Learning & AI: Scikit-learn, TensorFlow, PyTorch, Hugging Face, NLP, Computer Vision",
                    "Data Science & Analytics: Pandas, NumPy, Matplotlib, Seaborn, Feature Engineering",
                    "Tools & Cloud: Git, Docker, AWS, MLflow, Linux, Streamlit, Jupyter"
                ]),
                ("Experience & Projects", [
                    "AI Resume Screening Engine: Built TF-IDF and BERT semantic search engine for matching candidate profiles.",
                    "Customer Sentiment Analysis System: End-to-end NLP classification pipeline using Transformers.",
                    "Predictive Maintenance Model: Developed Scikit-learn Random Forest regression model on IoT data."
                ])
            ]
        },
        {
            "filename": "Priya_Patel_FullStack_Developer.pdf",
            "title": "Priya Patel - Full Stack Web Developer",
            "sections": [
                ("Contact Information", [
                    "Email: priya.patel@gmail.com",
                    "Phone: +91 98123 45678",
                    "GitHub: github.com/priyapatel-dev",
                    "Location: Pune, India"
                ]),
                ("Education", [
                    "B.E. in Information Technology - Pune Institute of Computer Technology (CGPA: 8.7/10)",
                    "Year of Graduation: 2023",
                    "Key Courses: Web Development, Database Management Systems, Computer Networks"
                ]),
                ("Technical Skills", [
                    "Languages: JavaScript, TypeScript, Python, HTML5, CSS3, SQL",
                    "Frontend: React, Redux, Next.js, Tailwind CSS, Bootstrap",
                    "Backend: Node.js, Express, Django, FastAPI, REST APIs",
                    "Databases & DevOps: MongoDB, PostgreSQL, Redis, Docker, Git, AWS S3, CI/CD"
                ]),
                ("Experience & Projects", [
                    "E-Commerce SaaS Application: Full stack application with React, Node.js, Stripe and PostgreSQL.",
                    "College Placement Portal: Built interactive student dashboard with real-time job application tracking.",
                    "RESTful Microservices: Architected scalable authentication and profile APIs using FastAPI."
                ])
            ]
        },
        {
            "filename": "Rohan_Verma_DevOps_Cloud.pdf",
            "title": "Rohan Verma - Cloud & DevOps Engineer",
            "sections": [
                ("Contact Information", [
                    "Email: rohan.verma@techmail.com",
                    "Phone: +91 97654 32109",
                    "Location: Hyderabad, India"
                ]),
                ("Education", [
                    "B.Tech in Computer Science - NIT Warangal (CGPA: 8.4/10)",
                    "Year of Graduation: 2024",
                    "Certification: AWS Certified Solutions Architect Associate"
                ]),
                ("Technical Skills", [
                    "Cloud Platforms: Amazon Web Services (AWS), Microsoft Azure, Google Cloud Platform (GCP)",
                    "DevOps & Containers: Docker, Kubernetes, Terraform, Ansible, Jenkins, GitHub Actions",
                    "Scripting & OS: Python, Bash, Shell Scripting, Linux (Ubuntu, CentOS)",
                    "Monitoring & Security: Prometheus, Grafana, ELK Stack, Nginx, Git, CI/CD"
                ]),
                ("Experience & Projects", [
                    "Kubernetes Cluster Deployment: Managed multi-node microservices deployment with automated scaling.",
                    "Infrastructure as Code (IaC): Provisioned multi-region AWS cloud VPC using Terraform.",
                    "Automated CI/CD Pipeline: Built GitHub Actions pipeline reducing deployment time by 45%."
                ])
            ]
        },
        {
            "filename": "Sneha_Reddy_Junior_Developer.pdf",
            "title": "Sneha Reddy - Associate Software Engineer",
            "sections": [
                ("Contact Information", [
                    "Email: sneha.reddy@student.ac.in",
                    "Phone: +91 99887 66554",
                    "Location: Bangalore, India"
                ]),
                ("Education", [
                    "B.Sc in Computer Science - St. Joseph's College (CGPA: 7.9/10)",
                    "Year of Graduation: 2024"
                ]),
                ("Technical Skills", [
                    "Languages: Python, C, Java, Basic SQL",
                    "Web Basics: HTML, CSS, JavaScript, Flask",
                    "Core Fundamentals: Object Oriented Programming (OOP), Data Structures, Git, MS Excel"
                ]),
                ("Experience & Projects", [
                    "Library Management System: Developed database-backed inventory system using Python and SQLite.",
                    "Personal Portfolio Website: Responsive website using HTML, CSS, and JavaScript.",
                    "Data Analysis Internship: Cleaned and summarized survey responses using Pandas and Excel."
                ])
            ]
        }
    ]
    
    created_files = []
    for r in resumes:
        path = os.path.join(output_dir, r["filename"])
        create_pdf(path, r["title"], r["sections"])
        created_files.append(path)
        print(f"Created: {path}")
        
    return created_files

if __name__ == "__main__":
    generate_sample_resumes()
