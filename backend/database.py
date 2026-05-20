"""SQLite database layer for TalentMatch."""
import sqlite3
import os
import json
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get("TM_DB_PATH", os.path.join(os.path.dirname(__file__), "talentmatch.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn=None):
    close = conn is None
    if conn is None:
        conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          TEXT PRIMARY KEY,
        type        TEXT NOT NULL CHECK(type IN ('candidate','employer')),
        name        TEXT NOT NULL,
        email       TEXT NOT NULL UNIQUE,
        password    TEXT NOT NULL,
        mobile      TEXT,
        company     TEXT,
        company_logo        TEXT DEFAULT 'default',
        company_description TEXT DEFAULT '',
        bio         TEXT DEFAULT '',
        location    TEXT DEFAULT '',
        preferred_location  TEXT DEFAULT '',
        education_level     TEXT DEFAULT '',
        field_of_study      TEXT DEFAULT '',
        years_of_experience INTEGER DEFAULT 0,
        preferred_work_mode TEXT DEFAULT 'no preference',
        is_member   INTEGER DEFAULT 0,
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_skills (
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        skill   TEXT NOT NULL,
        PRIMARY KEY (user_id, skill)
    );

    CREATE TABLE IF NOT EXISTS work_experience (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title       TEXT NOT NULL,
        company     TEXT NOT NULL,
        duration    TEXT DEFAULT '',
        description TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id                  TEXT PRIMARY KEY,
        employer_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title               TEXT NOT NULL,
        company             TEXT NOT NULL,
        company_logo        TEXT DEFAULT 'default',
        location            TEXT DEFAULT '',
        city                TEXT DEFAULT '',
        country             TEXT DEFAULT '',
        job_type            TEXT DEFAULT 'full-time',
        work_mode           TEXT DEFAULT 'on-site',
        job_level           TEXT DEFAULT 'mid',
        job_role            TEXT DEFAULT '',
        job_function        TEXT DEFAULT '',
        min_salary          INTEGER DEFAULT 0,
        max_salary          INTEGER DEFAULT 0,
        currency            TEXT DEFAULT 'USD',
        required_experience INTEGER DEFAULT 0,
        required_education  TEXT DEFAULT '',
        vacancies           INTEGER DEFAULT 1,
        description         TEXT DEFAULT '',
        applicants          INTEGER DEFAULT 0,
        rating              REAL DEFAULT 0,
        posted_at           TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS job_skills (
        job_id  TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        skill   TEXT NOT NULL,
        PRIMARY KEY (job_id, skill)
    );

    CREATE TABLE IF NOT EXISTS job_tags (
        job_id  TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        tag     TEXT NOT NULL,
        PRIMARY KEY (job_id, tag)
    );

    CREATE TABLE IF NOT EXISTS applications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id      TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status      TEXT DEFAULT 'Pending',
        applied_at  TEXT NOT NULL,
        UNIQUE(job_id, user_id)
    );

    CREATE TABLE IF NOT EXISTS saved_jobs (
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        job_id  TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        PRIMARY KEY (user_id, job_id)
    );
    """)
    conn.commit()
    if close:
        conn.close()


def _uid():
    import uuid
    return str(uuid.uuid4())


def seed_db(conn=None):
    """Populate with sample users and jobs (idempotent)."""
    close = conn is None
    if conn is None:
        conn = get_conn()
    c = conn.cursor()

    # Skip if already seeded
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        if close:
            conn.close()
        return

    now = datetime.now(timezone.utc).isoformat()

    # ── Candidates ───────────────────────────────────────────────────
    candidates = [
        {
            "id": "u1", "type": "candidate", "name": "Alice Johnson",
            "email": "alice@example.com", "password": generate_password_hash("password123"),
            "mobile": "0412345678", "location": "Sydney, Australia",
            "preferred_location": "Sydney", "education_level": "Bachelor's Degree",
            "field_of_study": "Computer Science", "years_of_experience": 3,
            "preferred_work_mode": "hybrid", "bio": "Passionate frontend developer.",
            "skills": ["JavaScript", "React", "CSS", "HTML", "TypeScript"],
            "work_experience": [
                {"title": "Frontend Developer", "company": "StartupXYZ",
                 "duration": "2021-2023", "description": "Built React apps."}
            ]
        },
        {
            "id": "u2", "type": "candidate", "name": "Bob Smith",
            "email": "bob@example.com", "password": generate_password_hash("password123"),
            "mobile": "0423456789", "location": "Melbourne, Australia",
            "preferred_location": "Melbourne", "education_level": "Master's Degree",
            "field_of_study": "Data Science", "years_of_experience": 5,
            "preferred_work_mode": "remote", "bio": "Data scientist specialising in ML.",
            "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Pandas"],
            "work_experience": [
                {"title": "Data Analyst", "company": "Analytics Co",
                 "duration": "2018-2021", "description": "Built predictive models."},
                {"title": "ML Engineer", "company": "TechCorp",
                 "duration": "2021-2023", "description": "Deep learning pipelines."}
            ]
        },
        {
            "id": "u3", "type": "candidate", "name": "Carol Williams",
            "email": "carol@example.com", "password": generate_password_hash("password123"),
            "mobile": "0434567890", "location": "Brisbane, Australia",
            "preferred_location": "Brisbane", "education_level": "Bachelor's Degree",
            "field_of_study": "Cybersecurity", "years_of_experience": 2,
            "preferred_work_mode": "on-site", "bio": "Cybersecurity enthusiast.",
            "skills": ["Network Security", "Penetration Testing", "Python", "Linux", "SIEM"],
            "work_experience": [
                {"title": "Security Analyst", "company": "SecureTech",
                 "duration": "2022-2023", "description": "Monitored network threats."}
            ]
        },
        {
            "id": "u4", "type": "candidate", "name": "David Chen",
            "email": "david@example.com", "password": generate_password_hash("password123"),
            "mobile": "0445678901", "location": "Melbourne, Australia",
            "preferred_location": "Melbourne", "education_level": "Bachelor's Degree",
            "field_of_study": "Software Engineering", "years_of_experience": 4,
            "preferred_work_mode": "remote", "bio": "Full-stack developer with experience in modern web technologies.",
            "skills": ["JavaScript", "React", "Node.js", "Python", "PostgreSQL"],
            "work_experience": [
                {"title": "Full Stack Developer", "company": "WebSolutions",
                 "duration": "2020-2024", "description": "Built full-stack web applications using React and Node.js."}
            ]
        },
        {
            "id": "u5", "type": "candidate", "name": "Emma Rodriguez",
            "email": "emma@example.com", "password": generate_password_hash("password123"),
            "mobile": "0456789012", "location": "Sydney, Australia",
            "preferred_location": "Sydney", "education_level": "Bachelor's Degree",
            "field_of_study": "Interaction Design", "years_of_experience": 3,
            "preferred_work_mode": "hybrid", "bio": "UX/UI designer passionate about creating intuitive user experiences.",
            "skills": ["Figma", "Adobe XD", "Prototyping", "User Research", "CSS"],
            "work_experience": [
                {"title": "UI/UX Designer", "company": "DesignStudio",
                 "duration": "2021-2024", "description": "Designed user interfaces for mobile and web applications."}
            ]
        },
        {
            "id": "u6", "type": "candidate", "name": "Frank Taylor",
            "email": "frank@example.com", "password": generate_password_hash("password123"),
            "mobile": "0467890123", "location": "Brisbane, Australia",
            "preferred_location": "Brisbane", "education_level": "Bachelor's Degree",
            "field_of_study": "Information Technology", "years_of_experience": 6,
            "preferred_work_mode": "on-site", "bio": "Experienced DevOps engineer specialising in cloud infrastructure.",
            "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD"],
            "work_experience": [
                {"title": "DevOps Engineer", "company": "CloudTech",
                 "duration": "2018-2024", "description": "Managed cloud infrastructure and CI/CD pipelines on AWS."}
            ]
        },
    ]

    # ── Employers ────────────────────────────────────────────────────
    employers = [
        {
            "id": "e1", "type": "employer", "name": "Google Recruiter",
            "email": "recruiter@google.com", "password": generate_password_hash("password123"),
            "mobile": "0400000001", "company": "Google", "company_logo": "google",
            "company_description": "Organise the world's information."
        },
        {
            "id": "e2", "type": "employer", "name": "Microsoft HR",
            "email": "hr@microsoft.com", "password": generate_password_hash("password123"),
            "mobile": "0400000002", "company": "Microsoft", "company_logo": "microsoft",
            "company_description": "Empower every person on the planet."
        },
        {
            "id": "e3", "type": "employer", "name": "Amazon Talent",
            "email": "talent@amazon.com", "password": generate_password_hash("password123"),
            "mobile": "0400000003", "company": "Amazon", "company_logo": "amazon",
            "company_description": "Work hard. Have fun. Make history."
        },
    ]

    for u in candidates + employers:
        c.execute("""INSERT INTO users
            (id,type,name,email,password,mobile,company,company_logo,company_description,
             bio,location,preferred_location,education_level,field_of_study,
             years_of_experience,preferred_work_mode,is_member,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)""",
            (u["id"], u["type"], u["name"], u["email"], u["password"],
             u.get("mobile",""), u.get("company",""), u.get("company_logo","default"),
             u.get("company_description",""), u.get("bio",""), u.get("location",""),
             u.get("preferred_location",""), u.get("education_level",""),
             u.get("field_of_study",""), u.get("years_of_experience",0),
             u.get("preferred_work_mode","no preference"), now))

        for skill in u.get("skills", []):
            c.execute("INSERT OR IGNORE INTO user_skills(user_id,skill) VALUES (?,?)",
                      (u["id"], skill))

        for wx in u.get("work_experience", []):
            c.execute("""INSERT INTO work_experience(user_id,title,company,duration,description)
                VALUES (?,?,?,?,?)""",
                (u["id"], wx["title"], wx["company"],
                 wx.get("duration",""), wx.get("description","")))

    # ── Jobs ─────────────────────────────────────────────────────────
    jobs = [
        {
            "id": "j1", "employer_id": "e1", "title": "Senior Frontend Developer",
            "company": "Google", "company_logo": "google",
            "location": "Sydney, Australia", "city": "Sydney", "country": "Australia",
            "job_type": "full-time", "work_mode": "hybrid", "job_level": "senior",
            "job_role": "Software Engineer", "job_function": "Engineering",
            "min_salary": 120000, "max_salary": 160000, "currency": "AUD",
            "required_experience": 5, "required_education": "Bachelor's Degree",
            "vacancies": 2, "applicants": 45, "rating": 4.8,
            "description": "<p>Build world-class web apps with React and TypeScript.</p>",
            "skills": ["JavaScript", "React", "TypeScript", "CSS", "GraphQL"],
            "tags": ["react", "frontend", "javascript"]
        },
        {
            "id": "j2", "employer_id": "e2", "title": "Machine Learning Engineer",
            "company": "Microsoft", "company_logo": "microsoft",
            "location": "Melbourne, Australia", "city": "Melbourne", "country": "Australia",
            "job_type": "full-time", "work_mode": "remote", "job_level": "mid",
            "job_role": "ML Engineer", "job_function": "Data & Analytics",
            "min_salary": 110000, "max_salary": 150000, "currency": "AUD",
            "required_experience": 3, "required_education": "Master's Degree",
            "vacancies": 1, "applicants": 32, "rating": 4.7,
            "description": "<p>Design and deploy ML models at scale.</p>",
            "skills": ["Python", "TensorFlow", "PyTorch", "SQL", "Azure ML"],
            "tags": ["ml", "python", "data science"]
        },
        {
            "id": "j3", "employer_id": "e3", "title": "Backend Developer",
            "company": "Amazon", "company_logo": "amazon",
            "location": "Sydney, Australia", "city": "Sydney", "country": "Australia",
            "job_type": "full-time", "work_mode": "on-site", "job_level": "mid",
            "job_role": "Software Engineer", "job_function": "Engineering",
            "min_salary": 100000, "max_salary": 140000, "currency": "AUD",
            "required_experience": 3, "required_education": "Bachelor's Degree",
            "vacancies": 3, "applicants": 27, "rating": 4.5,
            "description": "<p>Build scalable microservices with Python and AWS.</p>",
            "skills": ["Python", "AWS", "Docker", "REST APIs", "PostgreSQL"],
            "tags": ["backend", "python", "aws"]
        },
        {
            "id": "j4", "employer_id": "e1", "title": "UI/UX Designer",
            "company": "Google", "company_logo": "google",
            "location": "Remote", "city": "", "country": "Australia",
            "job_type": "full-time", "work_mode": "remote", "job_level": "mid",
            "job_role": "Designer", "job_function": "Design",
            "min_salary": 90000, "max_salary": 120000, "currency": "AUD",
            "required_experience": 2, "required_education": "Bachelor's Degree",
            "vacancies": 1, "applicants": 38, "rating": 4.9,
            "description": "<p>Design intuitive user experiences for Google products.</p>",
            "skills": ["Figma", "Adobe XD", "Prototyping", "User Research", "CSS"],
            "tags": ["design", "ui", "ux"]
        },
        {
            "id": "j5", "employer_id": "e2", "title": "DevOps Engineer",
            "company": "Microsoft", "company_logo": "microsoft",
            "location": "Brisbane, Australia", "city": "Brisbane", "country": "Australia",
            "job_type": "full-time", "work_mode": "hybrid", "job_level": "senior",
            "job_role": "DevOps Engineer", "job_function": "Engineering",
            "min_salary": 115000, "max_salary": 155000, "currency": "AUD",
            "required_experience": 5, "required_education": "Bachelor's Degree",
            "vacancies": 2, "applicants": 19, "rating": 4.6,
            "description": "<p>Manage CI/CD pipelines and cloud infrastructure.</p>",
            "skills": ["Azure", "Kubernetes", "Docker", "Terraform", "CI/CD"],
            "tags": ["devops", "cloud", "kubernetes"]
        },
        {
            "id": "j6", "employer_id": "e3", "title": "Data Analyst",
            "company": "Amazon", "company_logo": "amazon",
            "location": "Sydney, Australia", "city": "Sydney", "country": "Australia",
            "job_type": "full-time", "work_mode": "on-site", "job_level": "entry",
            "job_role": "Data Analyst", "job_function": "Data & Analytics",
            "min_salary": 70000, "max_salary": 95000, "currency": "AUD",
            "required_experience": 1, "required_education": "Bachelor's Degree",
            "vacancies": 2, "applicants": 55, "rating": 4.4,
            "description": "<p>Analyse customer data to drive business decisions.</p>",
            "skills": ["SQL", "Python", "Tableau", "Excel", "Statistics"],
            "tags": ["data", "analytics", "sql"]
        },
        {
            "id": "j7", "employer_id": "e1", "title": "Product Manager",
            "company": "Google", "company_logo": "google",
            "location": "Melbourne, Australia", "city": "Melbourne", "country": "Australia",
            "job_type": "full-time", "work_mode": "hybrid", "job_level": "senior",
            "job_role": "Product Manager", "job_function": "Product",
            "min_salary": 130000, "max_salary": 180000, "currency": "AUD",
            "required_experience": 6, "required_education": "Master's Degree",
            "vacancies": 1, "applicants": 61, "rating": 4.7,
            "description": "<p>Lead product strategy for Google Cloud services.</p>",
            "skills": ["Product Strategy", "Agile", "Data Analysis", "Roadmapping", "Leadership"],
            "tags": ["product", "management", "strategy"]
        },
        {
            "id": "j8", "employer_id": "e2", "title": "React Developer",
            "company": "Microsoft", "company_logo": "microsoft",
            "location": "Remote", "city": "", "country": "Australia",
            "job_type": "contract", "work_mode": "remote", "job_level": "mid",
            "job_role": "Software Engineer", "job_function": "Engineering",
            "min_salary": 80000, "max_salary": 110000, "currency": "AUD",
            "required_experience": 2, "required_education": "Bachelor's Degree",
            "vacancies": 3, "applicants": 24, "rating": 4.5,
            "description": "<p>Build React components for Microsoft 365 products.</p>",
            "skills": ["React", "JavaScript", "TypeScript", "Redux", "REST APIs"],
            "tags": ["react", "frontend", "contract"]
        },
        {
            "id": "j9", "employer_id": "e3", "title": "Marketing Specialist",
            "company": "Amazon", "company_logo": "amazon",
            "location": "Sydney, Australia", "city": "Sydney", "country": "Australia",
            "job_type": "full-time", "work_mode": "on-site", "job_level": "mid",
            "job_role": "Marketing Specialist", "job_function": "Marketing",
            "min_salary": 75000, "max_salary": 100000, "currency": "AUD",
            "required_experience": 3, "required_education": "Bachelor's Degree",
            "vacancies": 1, "applicants": 42, "rating": 4.3,
            "description": "<p>Drive growth campaigns for Amazon Marketplace.</p>",
            "skills": ["Digital Marketing", "SEO", "Google Ads", "Analytics", "Content Strategy"],
            "tags": ["marketing", "seo", "digital"]
        },
        {
            "id": "j10", "employer_id": "e1", "title": "Junior Software Developer",
            "company": "Google", "company_logo": "google",
            "location": "Brisbane, Australia", "city": "Brisbane", "country": "Australia",
            "job_type": "full-time", "work_mode": "on-site", "job_level": "entry",
            "job_role": "Software Engineer", "job_function": "Engineering",
            "min_salary": 65000, "max_salary": 85000, "currency": "AUD",
            "required_experience": 0, "required_education": "Bachelor's Degree",
            "vacancies": 5, "applicants": 88, "rating": 4.6,
            "description": "<p>Entry-level role for fresh graduates. Build Google services.</p>",
            "skills": ["Java", "Python", "Data Structures", "Algorithms", "Git"],
            "tags": ["entry-level", "graduate", "software"]
        },
        {
            "id": "j11", "employer_id": "e2", "title": "Cybersecurity Analyst",
            "company": "Microsoft", "company_logo": "microsoft",
            "location": "Sydney, Australia", "city": "Sydney", "country": "Australia",
            "job_type": "full-time", "work_mode": "hybrid", "job_level": "mid",
            "job_role": "Security Analyst", "job_function": "Cybersecurity",
            "min_salary": 95000, "max_salary": 130000, "currency": "AUD",
            "required_experience": 2, "required_education": "Bachelor's Degree",
            "vacancies": 2, "applicants": 15, "rating": 4.7,
            "description": "<p>Monitor and defend Microsoft infrastructure against cyber threats.</p>",
            "skills": ["Network Security", "SIEM", "Incident Response", "Python", "Forensics"],
            "tags": ["cybersecurity", "security", "infosec"]
        },
        {
            "id": "j12", "employer_id": "e3", "title": "IT Support Engineer",
            "company": "Amazon", "company_logo": "amazon",
            "location": "Melbourne, Australia", "city": "Melbourne", "country": "Australia",
            "job_type": "full-time", "work_mode": "on-site", "job_level": "entry",
            "job_role": "IT Support", "job_function": "Information Technology",
            "min_salary": 60000, "max_salary": 80000, "currency": "AUD",
            "required_experience": 1, "required_education": "Bachelor's Degree",
            "vacancies": 3, "applicants": 22, "rating": 4.2,
            "description": "<p>Provide technical support and maintain IT infrastructure.</p>",
            "skills": ["Windows", "Linux", "Networking", "Troubleshooting", "Active Directory"],
            "tags": ["it", "support", "helpdesk"]
        },
        {
            "id": "j13", "employer_id": "e1", "title": "Network Security Engineer",
            "company": "Google", "company_logo": "google",
            "location": "Sydney, Australia", "city": "Sydney", "country": "Australia",
            "job_type": "full-time", "work_mode": "on-site", "job_level": "senior",
            "job_role": "Network Engineer", "job_function": "Cybersecurity",
            "min_salary": 110000, "max_salary": 150000, "currency": "AUD",
            "required_experience": 5, "required_education": "Bachelor's Degree",
            "vacancies": 1, "applicants": 11, "rating": 4.8,
            "description": "<p>Design and secure Google's global network infrastructure.</p>",
            "skills": ["Network Security", "Firewalls", "VPN", "IDS/IPS", "Python"],
            "tags": ["network", "security", "infrastructure"]
        },
        {
            "id": "j14", "employer_id": "e2", "title": "Information Security Manager",
            "company": "Microsoft", "company_logo": "microsoft",
            "location": "Melbourne, Australia", "city": "Melbourne", "country": "Australia",
            "job_type": "full-time", "work_mode": "hybrid", "job_level": "manager",
            "job_role": "Security Manager", "job_function": "Cybersecurity",
            "min_salary": 140000, "max_salary": 185000, "currency": "AUD",
            "required_experience": 8, "required_education": "Master's Degree",
            "vacancies": 1, "applicants": 8, "rating": 4.9,
            "description": "<p>Lead the information security programme across Microsoft ANZ.</p>",
            "skills": ["ISO 27001", "Risk Management", "GDPR", "Leadership", "Security Auditing"],
            "tags": ["infosec", "management", "compliance"]
        },
    ]

    for j in jobs:
        posted_at = datetime.now(timezone.utc).isoformat()
        c.execute("""INSERT INTO jobs
            (id,employer_id,title,company,company_logo,location,city,country,
             job_type,work_mode,job_level,job_role,job_function,
             min_salary,max_salary,currency,required_experience,required_education,
             vacancies,description,applicants,rating,posted_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (j["id"], j["employer_id"], j["title"], j["company"], j["company_logo"],
             j["location"], j["city"], j["country"], j["job_type"], j["work_mode"],
             j["job_level"], j["job_role"], j["job_function"],
             j["min_salary"], j["max_salary"], j["currency"],
             j["required_experience"], j["required_education"],
             j["vacancies"], j["description"], j["applicants"], j["rating"], posted_at))

        for skill in j.get("skills", []):
            c.execute("INSERT OR IGNORE INTO job_skills(job_id,skill) VALUES (?,?)",
                      (j["id"], skill))
        for tag in j.get("tags", []):
            c.execute("INSERT OR IGNORE INTO job_tags(job_id,tag) VALUES (?,?)",
                      (j["id"], tag))

    conn.commit()
    if close:
        conn.close()


# ── Row → dict helpers ───────────────────────────────────────────────────────

def job_row_to_dict(row, conn):
    d = dict(row)
    jid = d["id"]
    d["requiredSkills"] = [r[0] for r in conn.execute(
        "SELECT skill FROM job_skills WHERE job_id=?", (jid,))]
    d["tags"] = [r[0] for r in conn.execute(
        "SELECT tag FROM job_tags WHERE job_id=?", (jid,))]
    # camelCase aliases for frontend compatibility
    d["jobType"] = d.pop("job_type", "")
    d["workMode"] = d.pop("work_mode", "")
    d["jobLevel"] = d.pop("job_level", "")
    d["jobRole"] = d.pop("job_role", "")
    d["jobFunction"] = d.pop("job_function", "")
    d["minSalary"] = d.pop("min_salary", 0)
    d["maxSalary"] = d.pop("max_salary", 0)
    d["companyLogo"] = d.pop("company_logo", "")
    d["requiredExperience"] = d.pop("required_experience", 0)
    d["requiredEducation"] = d.pop("required_education", "")
    d["postedAt"] = d.pop("posted_at", "")
    d["employerId"] = d.pop("employer_id", "")
    return d


def user_row_to_dict(row, conn, include_password=False):
    d = dict(row)
    uid = d["id"]
    d["skills"] = [r[0] for r in conn.execute(
        "SELECT skill FROM user_skills WHERE user_id=?", (uid,))]
    d["workExperience"] = [
        {"id": r["id"], "title": r["title"], "company": r["company"],
         "duration": r["duration"], "description": r["description"]}
        for r in conn.execute(
            "SELECT * FROM work_experience WHERE user_id=? ORDER BY id", (uid,))
    ]
    # camelCase aliases
    d["isMember"] = bool(d.pop("is_member", 0))
    d["companyLogo"] = d.pop("company_logo", "")
    d["companyDescription"] = d.pop("company_description", "")
    d["preferredLocation"] = d.pop("preferred_location", "")
    d["educationLevel"] = d.pop("education_level", "")
    d["fieldOfStudy"] = d.pop("field_of_study", "")
    d["yearsOfExperience"] = d.pop("years_of_experience", 0)
    d["preferredWorkMode"] = d.pop("preferred_work_mode", "no preference")
    d["createdAt"] = d.pop("created_at", "")
    if not include_password:
        d.pop("password", None)
    return d
