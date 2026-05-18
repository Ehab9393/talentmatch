"""Search and recommendation engine for TalentMatch."""

SYNONYMS = {
    "programmer": ["developer", "software engineer", "coder", "engineer"],
    "coder": ["developer", "programmer", "software engineer"],
    "developer": ["programmer", "software engineer", "coder", "engineer"],
    "software engineer": ["developer", "programmer", "coder", "engineer"],
    "ui designer": ["ux designer", "product designer", "visual designer", "ui/ux", "designer"],
    "ux designer": ["ui designer", "product designer", "ui/ux", "designer"],
    "data scientist": ["data analyst", "ml engineer", "machine learning", "analytics"],
    "data analyst": ["data scientist", "analytics", "business analyst"],
    "frontend": ["front-end", "front end", "ui developer", "react developer", "javascript developer"],
    "backend": ["back-end", "back end", "server-side", "api developer"],
    "fullstack": ["full-stack", "full stack", "frontend", "backend"],
    "devops": ["cloud engineer", "infrastructure engineer", "sre", "platform engineer"],
    "marketing": ["digital marketing", "growth", "seo", "content marketing"],
    "manager": ["lead", "head", "director", "vp"],
    "intern": ["internship", "graduate", "entry level", "fresher"],
    "it": ["information technology", "tech", "technical", "software", "computing",
           "computer science", "engineer", "developer"],
    "information technology": ["it", "tech", "software", "computer science", "engineering"],
    "tech": ["it", "technology", "software", "engineering", "developer"],
    "cybersecurity": ["cyber security", "security", "information security", "infosec",
                      "network security", "penetration testing", "ethical hacking"],
    "cyber security": ["cybersecurity", "security", "infosec", "information security"],
    "infosec": ["cybersecurity", "cyber security", "information security", "security"],
    "security": ["cybersecurity", "infosec", "information security", "network security"],
    "network": ["networking", "network engineer", "network security", "infrastructure"],
    "cloud": ["aws", "gcp", "azure", "devops", "infrastructure", "cloud engineer"],
    "mobile": ["ios", "android", "react native", "flutter", "app developer"],
    "ai": ["artificial intelligence", "machine learning", "deep learning", "ml", "data science"],
    "machine learning": ["ai", "artificial intelligence", "deep learning", "data science", "ml engineer"],
}

EDU_ORDER = [
    "high school", "diploma", "associate", "bachelor", "bachelor's",
    "bachelor's degree", "postgraduate", "master", "master's", "master's degree",
    "phd", "doctorate"
]


# ── Fuzzy helpers ────────────────────────────────────────────────────────────

def levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def fuzzy_word_match(word: str, target: str, threshold: float = 0.72) -> bool:
    if target in word or word in target:
        return True
    if len(word) < 3 or len(target) < 3:
        return word == target
    max_len = max(len(word), len(target))
    return (1 - levenshtein(word, target) / max_len) >= threshold


def expand_query(query: str) -> list[str]:
    q = query.lower().strip()
    terms = {q}
    q_words = q.split()

    for key, syns in SYNONYMS.items():
        key_words = key.split()
        q_matches_key = q == key or all(kw in q_words for kw in key_words)
        key_matches_q = key == q or all(qw in key_words for qw in q_words)

        if q_matches_key or key_matches_q:
            terms.update(syns)
            terms.add(key)

        for s in syns:
            s_words = s.split()
            if q == s or all(sw in q_words for sw in s_words):
                terms.add(key)
                terms.update(syns)

    return list(terms)


# ── Job / Candidate matching ─────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", text or "")


def job_matches_query(job: dict, query: str) -> bool:
    if not query or not query.strip():
        return True
    q = query.lower().strip()
    expanded = expand_query(q)

    searchable = " ".join([
        job.get("title", ""), job.get("company", ""),
        _strip_html(job.get("description", "")),
        " ".join(job.get("tags", [])),
        " ".join(job.get("requiredSkills", [])),
        job.get("jobRole", ""), job.get("jobFunction", ""),
        job.get("location", ""), job.get("city", ""), job.get("country", "")
    ]).lower()

    if any(t in searchable for t in expanded):
        return True

    q_words = q.split()
    text_words = [w for w in searchable.split() if len(w) >= 3]
    return all(any(fuzzy_word_match(qw, tw) for tw in text_words) for qw in q_words)


def candidate_matches_query(candidate: dict, query: str) -> bool:
    if not query or not query.strip():
        return True
    q = query.lower().strip()
    expanded = expand_query(q)

    wx_text = " ".join(
        f"{w.get('title','')} {w.get('company','')} {w.get('description','')}"
        for w in candidate.get("workExperience", [])
    )
    searchable = " ".join([
        candidate.get("name", ""), candidate.get("bio", ""),
        " ".join(candidate.get("skills", [])),
        candidate.get("fieldOfStudy", ""), candidate.get("educationLevel", ""),
        candidate.get("location", ""), candidate.get("preferredLocation", ""),
        wx_text
    ]).lower()

    if any(t in searchable for t in expanded):
        return True

    q_words = q.split()
    text_words = [w for w in searchable.split() if len(w) >= 3]
    return all(any(fuzzy_word_match(qw, tw) for tw in text_words) for qw in q_words)


# ── Recommendation scoring ────────────────────────────────────────────────────

def edu_index(level: str) -> int:
    l = (level or "").lower()
    for i, e in enumerate(EDU_ORDER):
        if e in l:
            return i
    return -1


def skill_similarity(candidate_skills: list[str], required_skills: list[str]) -> float:
    if not required_skills:
        return 1.0
    cs = [s.lower() for s in candidate_skills]
    matched = sum(
        1 for rs in required_skills
        if any(fuzzy_word_match(rs.lower(), c) for c in cs)
    )
    return matched / len(required_skills)


def score_job_for_candidate(candidate: dict, job: dict) -> float:
    score = 0.0

    # Skills — 40%
    skill_score = skill_similarity(
        candidate.get("skills", []), job.get("requiredSkills", []))
    score += skill_score * 40

    # Experience — 20%
    years = int(candidate.get("yearsOfExperience") or 0)
    req_exp = int(job.get("requiredExperience") or 0)
    if years >= req_exp:
        score += 20
    elif req_exp > 0:
        score += max(0, (years / req_exp)) * 20

    # Work mode — 20%
    c_mode = (candidate.get("preferredWorkMode") or "no preference").lower()
    j_mode = (job.get("workMode") or "").lower()
    if c_mode == "no preference" or c_mode == j_mode:
        score += 20
    elif "hybrid" in (c_mode, j_mode):
        score += 10

    # Location — 10%
    c_loc = (candidate.get("preferredLocation") or candidate.get("location") or "").lower()
    j_city = (job.get("city") or "").lower()
    j_country = (job.get("country") or "").lower()
    if j_mode == "remote":
        score += 10
    elif c_loc and (c_loc in j_city or c_loc in j_country or j_city in c_loc):
        score += 10
    elif c_loc and j_country and c_loc in j_country:
        score += 5

    # Education — 10%
    c_edu = edu_index(candidate.get("educationLevel", ""))
    j_edu = edu_index(job.get("requiredEducation", ""))
    if c_edu >= j_edu:
        score += 10
    elif c_edu >= 0 and j_edu > 0:
        score += max(0, (c_edu / j_edu)) * 10

    return round(score)


def score_candidate_for_job(candidate: dict, job: dict) -> float:
    score = 0.0

    skill_score = skill_similarity(
        candidate.get("skills", []), job.get("requiredSkills", []))
    score += skill_score * 40

    years = int(candidate.get("yearsOfExperience") or 0)
    req_exp = int(job.get("requiredExperience") or 0)
    if years >= req_exp:
        score += 20
    elif req_exp > 0:
        score += max(0, (years / req_exp)) * 20

    c_mode = (candidate.get("preferredWorkMode") or "no preference").lower()
    j_mode = (job.get("workMode") or "").lower()
    if c_mode == "no preference" or c_mode == j_mode:
        score += 20
    elif "hybrid" in (c_mode, j_mode):
        score += 10

    c_loc = (candidate.get("preferredLocation") or candidate.get("location") or "").lower()
    j_city = (job.get("city") or "").lower()
    j_country = (job.get("country") or "").lower()
    if j_mode == "remote":
        score += 10
    elif c_loc and (c_loc in j_city or j_city in c_loc):
        score += 10
    elif c_loc and j_country and (c_loc in j_country or j_country in c_loc):
        score += 5

    c_edu = edu_index(candidate.get("educationLevel", ""))
    j_edu = edu_index(job.get("requiredEducation", ""))
    if c_edu >= j_edu:
        score += 10
    elif c_edu >= 0 and j_edu > 0:
        score += max(0, (c_edu / j_edu)) * 10

    return round(score)


def recommend_jobs_for_candidate(candidate: dict, all_jobs: list[dict],
                                  limit: int | None = None) -> list[dict]:
    scored = []
    for job in all_jobs:
        s = score_job_for_candidate(candidate, job)
        scored.append({**job, "matchScore": s})
    scored.sort(key=lambda x: x["matchScore"], reverse=True)
    if limit:
        scored = scored[:limit]
    return scored


def recommend_candidates_for_job(job: dict, all_candidates: list[dict],
                                  limit: int | None = None) -> list[dict]:
    scored = []
    for c in all_candidates:
        s = score_candidate_for_job(c, job)
        scored.append({**c, "matchScore": s})
    scored.sort(key=lambda x: x["matchScore"], reverse=True)
    if limit:
        scored = scored[:limit]
    return scored
