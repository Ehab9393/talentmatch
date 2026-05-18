"""TalentMatch Flask REST API."""
import os
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps

import jwt
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    get_conn, init_db, seed_db,
    job_row_to_dict, user_row_to_dict
)
from search_engine import (
    job_matches_query, candidate_matches_query,
    recommend_jobs_for_candidate, recommend_candidates_for_job
)

# ── App setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("TM_SECRET", "dev-secret-change-in-prod")
CORS(app, resources={r"/api/*": {"origins": "*"}})

JWT_EXPIRY_HOURS = 24 * 7  # 1 week


# ── DB bootstrap ─────────────────────────────────────────────────────────────

def bootstrap_db():
    """Initialise and seed the database. Called at startup, not on import."""
    init_db()
    seed_db()


# Auto-bootstrap unless running under pytest (conftest sets this flag)
if not os.environ.get("TM_TESTING"):
    with app.app_context():
        bootstrap_db()


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError:
        return None


def require_auth(f):
    """Decorator: injects g.user or returns 401."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401
        token = auth_header.split(" ", 1)[1]
        user_id = decode_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401
        conn = get_conn()
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "User not found"}), 401
        conn2 = get_conn()
        g.user = user_row_to_dict(row, conn2)
        conn2.close()
        return f(*args, **kwargs)
    return wrapper


def require_employer(f):
    @wraps(f)
    @require_auth
    def wrapper(*args, **kwargs):
        if g.user["type"] != "employer":
            return jsonify({"error": "Employer account required"}), 403
        return f(*args, **kwargs)
    return wrapper


def require_candidate(f):
    @wraps(f)
    @require_auth
    def wrapper(*args, **kwargs):
        if g.user["type"] != "candidate":
            return jsonify({"error": "Candidate account required"}), 403
        return f(*args, **kwargs)
    return wrapper


# ── Utilities ─────────────────────────────────────────────────────────────────

def err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


def ok(data: dict | list, code: int = 200):
    return jsonify(data), code


def _get_all_jobs(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM jobs ORDER BY posted_at DESC").fetchall()
    return [job_row_to_dict(r, conn) for r in rows]


def _get_all_candidates(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM users WHERE type='candidate'").fetchall()
    return [user_row_to_dict(r, conn) for r in rows]


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""
    mobile = (d.get("mobile") or "").strip()
    user_type = d.get("type") or "candidate"
    company = (d.get("company") or "").strip()
    company_logo = d.get("companyLogo") or "default"
    company_description = d.get("companyDescription") or ""

    if not name:
        return err("Full name is required")
    if not email:
        return err("Email is required")
    if len(password) < 6:
        return err("Password must be at least 6 characters")
    if not mobile:
        return err("Mobile number is required")
    if user_type == "employer" and not company:
        return err("Company name is required for employer accounts")
    if user_type not in ("candidate", "employer"):
        return err("Invalid account type")

    conn = get_conn()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            return err("An account with this email already exists")

        uid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        hashed = generate_password_hash(password)

        conn.execute("""INSERT INTO users
            (id,type,name,email,password,mobile,company,company_logo,company_description,
             bio,location,preferred_location,education_level,field_of_study,
             years_of_experience,preferred_work_mode,is_member,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)""",
            (uid, user_type, name, email, hashed, mobile,
             company, company_logo, company_description,
             "", "", "", "", "", 0, "no preference", now))
        conn.commit()

        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        user = user_row_to_dict(row, conn)
        token = create_token(uid)
        return ok({"token": token, "user": user}, 201)
    finally:
        conn.close()


@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    email = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""

    if not email or not password:
        return err("Email and password are required")

    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            return err("Invalid email or password", 401)
        user_with_pass = dict(row)
        if not check_password_hash(user_with_pass["password"], password):
            return err("Invalid email or password", 401)

        user = user_row_to_dict(row, conn)
        token = create_token(user["id"])
        return ok({"token": token, "user": user})
    finally:
        conn.close()


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def get_me():
    return ok(g.user)


@app.route("/api/auth/me", methods=["PUT"])
@require_auth
def update_me():
    d = request.get_json(silent=True) or {}
    uid = g.user["id"]

    allowed_fields = {
        "name", "mobile", "bio", "location", "preferred_location",
        "education_level", "field_of_study", "years_of_experience",
        "preferred_work_mode", "company", "company_logo", "company_description"
    }

    # Accept both snake_case and camelCase keys from frontend
    camel_to_snake = {
        "preferredLocation": "preferred_location",
        "educationLevel": "education_level",
        "fieldOfStudy": "field_of_study",
        "yearsOfExperience": "years_of_experience",
        "preferredWorkMode": "preferred_work_mode",
        "companyLogo": "company_logo",
        "companyDescription": "company_description",
    }
    normalized = {}
    for k, v in d.items():
        snake = camel_to_snake.get(k, k)
        if snake in allowed_fields:
            normalized[snake] = v

    conn = get_conn()
    try:
        if normalized:
            set_clause = ", ".join(f"{k}=?" for k in normalized)
            conn.execute(f"UPDATE users SET {set_clause} WHERE id=?",
                         list(normalized.values()) + [uid])

        skills = d.get("skills")
        if skills is not None:
            conn.execute("DELETE FROM user_skills WHERE user_id=?", (uid,))
            for skill in skills:
                conn.execute("INSERT OR IGNORE INTO user_skills(user_id,skill) VALUES (?,?)",
                             (uid, str(skill).strip()))

        work_exp = d.get("workExperience")
        if work_exp is not None:
            conn.execute("DELETE FROM work_experience WHERE user_id=?", (uid,))
            for wx in work_exp:
                conn.execute("""INSERT INTO work_experience(user_id,title,company,duration,description)
                    VALUES (?,?,?,?,?)""",
                    (uid, wx.get("title",""), wx.get("company",""),
                     wx.get("duration",""), wx.get("description","")))

        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        return ok(user_row_to_dict(row, conn))
    finally:
        conn.close()


# ── Job routes ────────────────────────────────────────────────────────────────

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    query = request.args.get("q", "").strip()
    job_type = request.args.getlist("jobType")
    work_mode = request.args.getlist("workMode")
    job_function = request.args.getlist("jobFunction")
    experience_level = request.args.getlist("experienceLevel")
    min_salary = request.args.get("minSalary", "")
    max_salary = request.args.get("maxSalary", "")
    location = request.args.get("location", "").strip()
    experience = request.args.get("experience", "")
    sort_by = request.args.get("sort", "popular")

    conn = get_conn()
    try:
        jobs = _get_all_jobs(conn)

        if query:
            jobs = [j for j in jobs if job_matches_query(j, query)]
        if job_type:
            jobs = [j for j in jobs if j["jobType"] in job_type]
        if work_mode:
            jobs = [j for j in jobs if j["workMode"] in work_mode]
        if job_function:
            jobs = [j for j in jobs if j["jobFunction"] in job_function]
        if experience_level:
            jobs = [j for j in jobs if j["jobLevel"] in experience_level]
        if min_salary and min_salary.isdigit():
            jobs = [j for j in jobs if j["maxSalary"] >= int(min_salary)]
        if max_salary and max_salary.isdigit():
            jobs = [j for j in jobs if j["minSalary"] <= int(max_salary)]
        if location:
            loc = location.lower()
            jobs = [j for j in jobs if
                    loc in (j.get("city") or "").lower() or
                    loc in (j.get("country") or "").lower() or
                    loc in (j.get("location") or "").lower()]
        if experience:
            try:
                exp = int(experience)
                if exp > 0:
                    jobs = [j for j in jobs if int(j.get("requiredExperience") or 0) <= exp]
            except ValueError:
                pass

        if sort_by == "salary-high":
            jobs.sort(key=lambda x: x["maxSalary"], reverse=True)
        elif sort_by == "salary-low":
            jobs.sort(key=lambda x: x["minSalary"])
        elif sort_by == "recent":
            jobs.sort(key=lambda x: x.get("postedAt", ""), reverse=True)
        else:
            jobs.sort(key=lambda x: x.get("applicants", 0), reverse=True)

        return ok(jobs)
    finally:
        conn.close()


@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job(job_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return err("Job not found", 404)
        return ok(job_row_to_dict(row, conn))
    finally:
        conn.close()


@app.route("/api/jobs", methods=["POST"])
@require_employer
def create_job():
    d = request.get_json(silent=True) or {}
    title = (d.get("title") or "").strip()
    if not title:
        return err("Job title is required")

    uid = g.user["id"]
    jid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = get_conn()
    try:
        employer = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        company = employer["company"] or g.user.get("name", "")
        company_logo = employer["company_logo"] or "default"

        country = (d.get("country") or "").strip()
        city = (d.get("city") or "").strip()
        location = d.get("location") or (f"{city}, {country}".strip(", ") if city or country else "")

        conn.execute("""INSERT INTO jobs
            (id,employer_id,title,company,company_logo,location,city,country,
             job_type,work_mode,job_level,job_role,job_function,
             min_salary,max_salary,currency,required_experience,required_education,
             vacancies,description,applicants,rating,posted_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,0,?)""",
            (jid, uid, title, company, company_logo,
             location, city, country,
             d.get("jobType", "full-time"), d.get("workMode", "on-site"),
             d.get("jobLevel", "mid"), d.get("jobRole", ""),
             d.get("jobFunction", ""),
             int(d.get("minSalary", 0) or 0), int(d.get("maxSalary", 0) or 0),
             d.get("currency", "AUD"),
             int(d.get("requiredExperience", 0) or 0),
             d.get("requiredEducation", ""),
             int(d.get("vacancies", 1) or 1),
             d.get("description", ""), now))

        for skill in (d.get("requiredSkills") or []):
            conn.execute("INSERT OR IGNORE INTO job_skills(job_id,skill) VALUES (?,?)",
                         (jid, str(skill).strip()))
        for tag in (d.get("tags") or []):
            conn.execute("INSERT OR IGNORE INTO job_tags(job_id,tag) VALUES (?,?)",
                         (jid, str(tag).strip()))

        conn.commit()
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        return ok(job_row_to_dict(row, conn), 201)
    finally:
        conn.close()


@app.route("/api/jobs/<job_id>", methods=["DELETE"])
@require_employer
def delete_job(job_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return err("Job not found", 404)
        if row["employer_id"] != g.user["id"]:
            return err("You can only delete your own job listings", 403)
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()
        return ok({"message": "Job deleted"})
    finally:
        conn.close()


@app.route("/api/jobs/<job_id>/apply", methods=["POST"])
@require_candidate
def apply_to_job(job_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return err("Job not found", 404)

        existing = conn.execute(
            "SELECT id FROM applications WHERE job_id=? AND user_id=?",
            (job_id, g.user["id"])).fetchone()
        if existing:
            return err("You have already applied for this job", 409)

        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""INSERT INTO applications(job_id,user_id,status,applied_at)
            VALUES (?,?,?,?)""", (job_id, g.user["id"], "Pending", now))
        conn.execute("UPDATE jobs SET applicants = applicants + 1 WHERE id=?", (job_id,))
        conn.commit()
        return ok({"message": "Application submitted", "status": "Pending"}, 201)
    finally:
        conn.close()


@app.route("/api/jobs/<job_id>/applications", methods=["GET"])
@require_employer
def get_job_applications(job_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return err("Job not found", 404)
        if row["employer_id"] != g.user["id"]:
            return err("Access denied", 403)

        apps = conn.execute("""
            SELECT a.id, a.status, a.applied_at, u.*
            FROM applications a JOIN users u ON a.user_id=u.id
            WHERE a.job_id=?
            ORDER BY a.applied_at DESC
        """, (job_id,)).fetchall()

        result = []
        for a in apps:
            candidate = user_row_to_dict(a, conn)
            candidate["applicationId"] = a["a.id"] if "a.id" in a.keys() else None
            # Re-query cleanly
            u_row = conn.execute("SELECT * FROM users WHERE id=?", (a["id"],)).fetchone()
            app_row = conn.execute(
                "SELECT * FROM applications WHERE job_id=? AND user_id=?",
                (job_id, a["id"])).fetchone()
            c = user_row_to_dict(u_row, conn)
            c["applicationStatus"] = app_row["status"]
            c["appliedAt"] = app_row["applied_at"]
            result.append(c)
        return ok(result)
    finally:
        conn.close()


@app.route("/api/jobs/<job_id>/saved", methods=["POST"])
@require_auth
def toggle_saved(job_id):
    uid = g.user["id"]
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT 1 FROM saved_jobs WHERE user_id=? AND job_id=?",
            (uid, job_id)).fetchone()
        if existing:
            conn.execute("DELETE FROM saved_jobs WHERE user_id=? AND job_id=?", (uid, job_id))
            saved = False
        else:
            row = conn.execute("SELECT id FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return err("Job not found", 404)
            conn.execute("INSERT INTO saved_jobs(user_id,job_id) VALUES (?,?)", (uid, job_id))
            saved = True
        conn.commit()
        return ok({"saved": saved})
    finally:
        conn.close()


# ── Saved jobs ────────────────────────────────────────────────────────────────

@app.route("/api/saved", methods=["GET"])
@require_auth
def get_saved():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT job_id FROM saved_jobs WHERE user_id=?", (g.user["id"],)).fetchall()
        return ok([r["job_id"] for r in rows])
    finally:
        conn.close()


# ── Candidate routes ──────────────────────────────────────────────────────────

@app.route("/api/candidates", methods=["GET"])
@require_auth
def get_candidates():
    query = request.args.get("q", "").strip()
    skills_filter = request.args.getlist("skills")
    work_mode = request.args.getlist("workMode")
    min_experience = request.args.get("minExperience", "")
    education = request.args.get("education", "").strip()
    location = request.args.get("location", "").strip()

    conn = get_conn()
    try:
        candidates = _get_all_candidates(conn)

        if query:
            candidates = [c for c in candidates if candidate_matches_query(c, query)]
        if skills_filter:
            candidates = [c for c in candidates if any(
                s.lower() in [sk.lower() for sk in c.get("skills", [])]
                for s in skills_filter)]
        if work_mode:
            candidates = [c for c in candidates if c.get("preferredWorkMode") in work_mode]
        if min_experience:
            try:
                me = int(min_experience)
                candidates = [c for c in candidates
                              if int(c.get("yearsOfExperience") or 0) >= me]
            except ValueError:
                pass
        if education:
            edu = education.lower()
            candidates = [c for c in candidates
                          if edu in (c.get("educationLevel") or "").lower()]
        if location:
            loc = location.lower()
            candidates = [c for c in candidates if
                          loc in (c.get("location") or "").lower() or
                          loc in (c.get("preferredLocation") or "").lower()]

        return ok(candidates)
    finally:
        conn.close()


@app.route("/api/candidates/<uid>", methods=["GET"])
@require_auth
def get_candidate(uid):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id=? AND type='candidate'", (uid,)).fetchone()
        if not row:
            return err("Candidate not found", 404)
        return ok(user_row_to_dict(row, conn))
    finally:
        conn.close()


# ── Recommendations ───────────────────────────────────────────────────────────

@app.route("/api/recommendations/jobs", methods=["GET"])
@require_candidate
def recommend_jobs():
    limit = None if g.user.get("isMember") else 10
    conn = get_conn()
    try:
        all_jobs = _get_all_jobs(conn)
        results = recommend_jobs_for_candidate(g.user, all_jobs, limit)
        return ok(results)
    finally:
        conn.close()


@app.route("/api/recommendations/candidates", methods=["GET"])
@require_employer
def recommend_candidates():
    job_id = request.args.get("jobId")
    limit = None if g.user.get("isMember") else 10

    conn = get_conn()
    try:
        if job_id:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row or row["employer_id"] != g.user["id"]:
                return err("Job not found or access denied", 404)
            job = job_row_to_dict(row, conn)
        else:
            row = conn.execute(
                "SELECT * FROM jobs WHERE employer_id=? ORDER BY posted_at DESC LIMIT 1",
                (g.user["id"],)).fetchone()
            if not row:
                return ok([])
            job = job_row_to_dict(row, conn)

        all_candidates = _get_all_candidates(conn)
        results = recommend_candidates_for_job(job, all_candidates, limit)
        return ok(results)
    finally:
        conn.close()


# ── Membership ────────────────────────────────────────────────────────────────

@app.route("/api/membership", methods=["POST"])
@require_auth
def toggle_membership():
    uid = g.user["id"]
    new_status = not g.user.get("isMember", False)

    conn = get_conn()
    try:
        conn.execute("UPDATE users SET is_member=? WHERE id=?",
                     (1 if new_status else 0, uid))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        return ok({"user": user_row_to_dict(row, conn), "isMember": new_status})
    finally:
        conn.close()


# ── My data ───────────────────────────────────────────────────────────────────

@app.route("/api/my/applications", methods=["GET"])
@require_candidate
def my_applications():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT a.status, a.applied_at, j.*
            FROM applications a JOIN jobs j ON a.job_id=j.id
            WHERE a.user_id=?
            ORDER BY a.applied_at DESC
        """, (g.user["id"],)).fetchall()

        result = []
        for r in rows:
            j_row = conn.execute("SELECT * FROM jobs WHERE id=?", (r["id"],)).fetchone()
            a_row = conn.execute(
                "SELECT status, applied_at FROM applications WHERE job_id=? AND user_id=?",
                (r["id"], g.user["id"])).fetchone()
            item = {"job": job_row_to_dict(j_row, conn),
                    "status": a_row["status"],
                    "appliedAt": a_row["applied_at"]}
            result.append(item)
        return ok(result)
    finally:
        conn.close()


@app.route("/api/my/jobs", methods=["GET"])
@require_employer
def my_jobs():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE employer_id=? ORDER BY posted_at DESC",
            (g.user["id"],)).fetchall()
        return ok([job_row_to_dict(r, conn) for r in rows])
    finally:
        conn.close()


# ── Health check ──────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return ok({"status": "ok", "service": "TalentMatch API"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
