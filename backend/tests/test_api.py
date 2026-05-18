"""TalentMatch API test suite."""
import pytest
from tests.conftest import auth


# ── Health ────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"


# ── Auth — Register ───────────────────────────────────────────────────────────

class TestRegister:
    def test_register_candidate_success(self, client):
        res = client.post("/api/auth/register", json={
            "name": "Test Candidate",
            "email": "testcandidate@example.com",
            "password": "pass1234",
            "mobile": "0400000099",
            "type": "candidate"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert "token" in data
        assert data["user"]["type"] == "candidate"
        assert data["user"]["name"] == "Test Candidate"

    def test_register_employer_success(self, client):
        res = client.post("/api/auth/register", json={
            "name": "Test Employer",
            "email": "testemployer@example.com",
            "password": "pass1234",
            "mobile": "0400000088",
            "type": "employer",
            "company": "TestCorp"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["user"]["type"] == "employer"
        assert data["user"]["company"] == "TestCorp"

    def test_register_duplicate_email(self, client):
        res = client.post("/api/auth/register", json={
            "name": "Dupe", "email": "alice@example.com",
            "password": "pass1234", "mobile": "0400000077", "type": "candidate"
        })
        assert res.status_code == 400
        assert "already exists" in res.get_json()["error"].lower()

    def test_register_missing_name(self, client):
        res = client.post("/api/auth/register", json={
            "email": "noname@example.com", "password": "pass1234",
            "mobile": "0400000066", "type": "candidate"
        })
        assert res.status_code == 400

    def test_register_short_password(self, client):
        res = client.post("/api/auth/register", json={
            "name": "Short", "email": "short@example.com",
            "password": "abc", "mobile": "0400000055", "type": "candidate"
        })
        assert res.status_code == 400
        assert "6 characters" in res.get_json()["error"]

    def test_register_employer_without_company(self, client):
        res = client.post("/api/auth/register", json={
            "name": "No Company", "email": "nocompany@example.com",
            "password": "pass1234", "mobile": "0400000044", "type": "employer"
        })
        assert res.status_code == 400

    def test_register_password_not_returned(self, client):
        res = client.post("/api/auth/register", json={
            "name": "Secure User", "email": "secure@example.com",
            "password": "mysecretpass", "mobile": "0400000033", "type": "candidate"
        })
        assert res.status_code == 201
        assert "password" not in res.get_json()["user"]


# ── Auth — Login ──────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client):
        res = client.post("/api/auth/login",
                          json={"email": "alice@example.com", "password": "password123"})
        assert res.status_code == 200
        data = res.get_json()
        assert "token" in data
        assert data["user"]["email"] == "alice@example.com"

    def test_login_wrong_password(self, client):
        res = client.post("/api/auth/login",
                          json={"email": "alice@example.com", "password": "wrongpass"})
        assert res.status_code == 401

    def test_login_unknown_email(self, client):
        res = client.post("/api/auth/login",
                          json={"email": "nobody@example.com", "password": "password123"})
        assert res.status_code == 401

    def test_login_missing_fields(self, client):
        res = client.post("/api/auth/login", json={"email": "alice@example.com"})
        assert res.status_code == 400


# ── Auth — Me ─────────────────────────────────────────────────────────────────

class TestGetMe:
    def test_get_me_authenticated(self, client, candidate_token):
        res = client.get("/api/auth/me", headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["email"] == "alice@example.com"

    def test_get_me_no_token(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_get_me_invalid_token(self, client):
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert res.status_code == 401

    def test_update_profile(self, client, candidate_token):
        res = client.put("/api/auth/me",
                         json={"bio": "Updated bio", "skills": ["Python", "Flask"]},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        data = res.get_json()
        assert data["bio"] == "Updated bio"
        assert "Python" in data["skills"]

    def test_update_work_experience(self, client, candidate_token):
        res = client.put("/api/auth/me", json={
            "workExperience": [{"title": "Dev", "company": "Corp", "duration": "2022-2024"}]
        }, headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()["workExperience"]) == 1


# ── Jobs — List & search ──────────────────────────────────────────────────────

class TestJobSearch:
    def test_get_all_jobs(self, client):
        res = client.get("/api/jobs")
        assert res.status_code == 200
        jobs = res.get_json()
        assert len(jobs) >= 14

    def test_search_by_title(self, client):
        res = client.get("/api/jobs?q=cybersecurity")
        assert res.status_code == 200
        jobs = res.get_json()
        assert any("cybersecurity" in j["title"].lower() or
                   "security" in j["title"].lower() for j in jobs)

    def test_search_it_returns_results(self, client):
        res = client.get("/api/jobs?q=IT")
        assert res.status_code == 200
        assert len(res.get_json()) > 0

    def test_search_cybersecurity_synonym(self, client):
        res = client.get("/api/jobs?q=infosec")
        assert res.status_code == 200
        assert len(res.get_json()) > 0

    def test_filter_by_job_type(self, client):
        res = client.get("/api/jobs?jobType=full-time")
        assert res.status_code == 200
        assert all(j["jobType"] == "full-time" for j in res.get_json())

    def test_filter_by_work_mode(self, client):
        res = client.get("/api/jobs?workMode=remote")
        assert res.status_code == 200
        assert all(j["workMode"] == "remote" for j in res.get_json())

    def test_filter_by_location(self, client):
        res = client.get("/api/jobs?location=Sydney")
        assert res.status_code == 200
        jobs = res.get_json()
        assert all("sydney" in j["location"].lower() or
                   "sydney" in (j.get("city") or "").lower() for j in jobs)

    def test_filter_min_salary(self, client):
        res = client.get("/api/jobs?minSalary=120000")
        assert res.status_code == 200
        assert all(j["maxSalary"] >= 120000 for j in res.get_json())

    def test_sort_by_salary_high(self, client):
        res = client.get("/api/jobs?sort=salary-high")
        jobs = res.get_json()
        salaries = [j["maxSalary"] for j in jobs]
        assert salaries == sorted(salaries, reverse=True)

    def test_sort_by_salary_low(self, client):
        res = client.get("/api/jobs?sort=salary-low")
        jobs = res.get_json()
        salaries = [j["minSalary"] for j in jobs]
        assert salaries == sorted(salaries)

    def test_experience_zero_no_filter(self, client):
        """experience=0 should NOT filter out any jobs."""
        all_count = len(client.get("/api/jobs").get_json())
        filtered_count = len(client.get("/api/jobs?experience=0").get_json())
        assert filtered_count == all_count

    def test_get_single_job(self, client):
        res = client.get("/api/jobs/j1")
        assert res.status_code == 200
        assert res.get_json()["id"] == "j1"

    def test_get_nonexistent_job(self, client):
        res = client.get("/api/jobs/nonexistent")
        assert res.status_code == 404


# ── Jobs — Create & Delete ────────────────────────────────────────────────────

class TestJobCRUD:
    def test_create_job_as_employer(self, client, employer_token):
        res = client.post("/api/jobs", json={
            "title": "Test Engineer",
            "jobType": "full-time",
            "workMode": "remote",
            "country": "Australia",
            "requiredSkills": ["Python", "Pytest"]
        }, headers=auth(employer_token))
        assert res.status_code == 201
        data = res.get_json()
        assert data["title"] == "Test Engineer"
        assert "Python" in data["requiredSkills"]
        # Save ID for delete test
        TestJobCRUD._created_job_id = data["id"]

    def test_create_job_as_candidate_forbidden(self, client, candidate_token):
        res = client.post("/api/jobs", json={"title": "Sneaky Job"},
                          headers=auth(candidate_token))
        assert res.status_code == 403

    def test_create_job_missing_title(self, client, employer_token):
        res = client.post("/api/jobs", json={"jobType": "full-time"},
                          headers=auth(employer_token))
        assert res.status_code == 400

    def test_delete_own_job(self, client, employer_token):
        job_id = getattr(TestJobCRUD, "_created_job_id", None)
        if not job_id:
            pytest.skip("No created job ID available")
        res = client.delete(f"/api/jobs/{job_id}", headers=auth(employer_token))
        assert res.status_code == 200

    def test_delete_other_employers_job_forbidden(self, client, employer_token):
        # j2 belongs to e2 (hr@microsoft.com), not e1 (recruiter@google.com)
        res = client.delete("/api/jobs/j2", headers=auth(employer_token))
        assert res.status_code == 403


# ── Applications ──────────────────────────────────────────────────────────────

class TestApplications:
    def test_apply_to_job(self, client, candidate_token):
        res = client.post("/api/jobs/j3/apply", headers=auth(candidate_token))
        assert res.status_code in (201, 409)  # 409 if already applied in prior test

    def test_apply_twice_returns_conflict(self, client, candidate_token):
        client.post("/api/jobs/j4/apply", headers=auth(candidate_token))
        res = client.post("/api/jobs/j4/apply", headers=auth(candidate_token))
        assert res.status_code == 409

    def test_employer_cannot_apply(self, client, employer_token):
        res = client.post("/api/jobs/j1/apply", headers=auth(employer_token))
        assert res.status_code == 403

    def test_my_applications(self, client, candidate_token):
        res = client.get("/api/my/applications", headers=auth(candidate_token))
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_employer_views_own_job_applications(self, client, employer_token):
        res = client.get("/api/jobs/j1/applications", headers=auth(employer_token))
        assert res.status_code == 200

    def test_employer_cannot_view_others_applications(self, client, employer_token):
        res = client.get("/api/jobs/j2/applications", headers=auth(employer_token))
        assert res.status_code == 403


# ── Saved Jobs ────────────────────────────────────────────────────────────────

class TestSavedJobs:
    def test_toggle_save_job(self, client, candidate_token):
        res = client.post("/api/jobs/j5/saved", headers=auth(candidate_token))
        assert res.status_code == 200
        assert "saved" in res.get_json()

    def test_toggle_unsave_job(self, client, candidate_token):
        client.post("/api/jobs/j6/saved", headers=auth(candidate_token))
        res = client.post("/api/jobs/j6/saved", headers=auth(candidate_token))
        assert res.get_json()["saved"] is False

    def test_get_saved_jobs(self, client, candidate_token):
        res = client.get("/api/saved", headers=auth(candidate_token))
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_save_nonexistent_job(self, client, candidate_token):
        res = client.post("/api/jobs/j999/saved", headers=auth(candidate_token))
        assert res.status_code == 404


# ── Candidates ────────────────────────────────────────────────────────────────

class TestCandidates:
    def test_employer_can_browse_candidates(self, client, employer_token):
        res = client.get("/api/candidates", headers=auth(employer_token))
        assert res.status_code == 200
        candidates = res.get_json()
        assert len(candidates) >= 3
        assert all(c["type"] == "candidate" for c in candidates)

    def test_search_candidates_by_skill(self, client, employer_token):
        res = client.get("/api/candidates?q=python", headers=auth(employer_token))
        assert res.status_code == 200
        # Bob and Carol both have Python
        assert len(res.get_json()) >= 1

    def test_search_candidates_cybersecurity(self, client, employer_token):
        res = client.get("/api/candidates?q=cybersecurity", headers=auth(employer_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_get_candidate_by_id(self, client, employer_token):
        res = client.get("/api/candidates/u1", headers=auth(employer_token))
        assert res.status_code == 200
        assert res.get_json()["id"] == "u1"

    def test_candidate_profile_no_password(self, client, employer_token):
        res = client.get("/api/candidates/u1", headers=auth(employer_token))
        assert "password" not in res.get_json()


# ── Recommendations ───────────────────────────────────────────────────────────

class TestRecommendations:
    def test_job_recommendations_for_candidate(self, client, candidate_token):
        res = client.get("/api/recommendations/jobs", headers=auth(candidate_token))
        assert res.status_code == 200
        jobs = res.get_json()
        assert len(jobs) > 0
        assert all("matchScore" in j for j in jobs)
        # Free users get at most 10
        assert len(jobs) <= 10

    def test_candidate_recommendations_for_employer(self, client, employer_token):
        res = client.get("/api/recommendations/candidates?jobId=j1",
                         headers=auth(employer_token))
        assert res.status_code == 200
        candidates = res.get_json()
        assert all("matchScore" in c for c in candidates)

    def test_recommendations_scores_descending(self, client, candidate_token):
        res = client.get("/api/recommendations/jobs", headers=auth(candidate_token))
        scores = [j["matchScore"] for j in res.get_json()]
        assert scores == sorted(scores, reverse=True)

    def test_recommendations_require_auth(self, client):
        res = client.get("/api/recommendations/jobs")
        assert res.status_code == 401

    def test_employer_cannot_get_job_recommendations(self, client, employer_token):
        res = client.get("/api/recommendations/jobs", headers=auth(employer_token))
        assert res.status_code == 403


# ── Membership ────────────────────────────────────────────────────────────────

class TestMembership:
    def test_toggle_membership(self, client, candidate_token):
        # Get current status
        me = client.get("/api/auth/me", headers=auth(candidate_token)).get_json()
        initial = me["isMember"]

        res = client.post("/api/membership", headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["isMember"] != initial

    def test_premium_member_gets_all_recommendations(self, client, candidate_token):
        # Ensure user is a member
        me = client.get("/api/auth/me", headers=auth(candidate_token)).get_json()
        if not me["isMember"]:
            client.post("/api/membership", headers=auth(candidate_token))

        res = client.get("/api/recommendations/jobs", headers=auth(candidate_token))
        assert res.status_code == 200
        # Premium members should see all jobs (14 seeded)
        assert len(res.get_json()) >= 14


# ── My Jobs (Employer) ────────────────────────────────────────────────────────

class TestMyJobs:
    def test_employer_gets_own_jobs(self, client, employer_token):
        res = client.get("/api/my/jobs", headers=auth(employer_token))
        assert res.status_code == 200
        jobs = res.get_json()
        # Google (e1) has j1, j4, j7, j10, j13
        assert len(jobs) >= 4

    def test_candidate_cannot_get_my_jobs(self, client, candidate_token):
        res = client.get("/api/my/jobs", headers=auth(candidate_token))
        assert res.status_code == 403


# ── Search engine unit tests ──────────────────────────────────────────────────

class TestSearchEngine:
    def test_expand_query_it(self):
        from search_engine import expand_query
        terms = expand_query("it")
        assert "information technology" in terms
        assert "software" in terms

    def test_expand_query_cybersecurity(self):
        from search_engine import expand_query
        terms = expand_query("cybersecurity")
        assert "security" in terms
        assert "infosec" in terms

    def test_fuzzy_match_typo(self):
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("develper", "developer")

    def test_fuzzy_match_short_words(self):
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("it", "it")
        assert not fuzzy_word_match("it", "ux")

    def test_levenshtein_identical(self):
        from search_engine import levenshtein
        assert levenshtein("python", "python") == 0

    def test_levenshtein_one_edit(self):
        from search_engine import levenshtein
        assert levenshtein("python", "pyhton") == 2

    def test_job_matches_query_exact(self):
        from search_engine import job_matches_query
        job = {"title": "Cybersecurity Analyst", "company": "ACME",
               "description": "", "tags": [], "requiredSkills": [],
               "jobRole": "", "jobFunction": "", "location": "", "city": "", "country": ""}
        assert job_matches_query(job, "cybersecurity")

    def test_job_matches_query_synonym(self):
        from search_engine import job_matches_query
        job = {"title": "Information Security Manager", "company": "Corp",
               "description": "", "tags": ["infosec"], "requiredSkills": [],
               "jobRole": "", "jobFunction": "", "location": "", "city": "", "country": ""}
        assert job_matches_query(job, "cybersecurity")

    def test_score_job_for_candidate(self):
        from search_engine import score_job_for_candidate
        candidate = {"skills": ["Python", "React"], "yearsOfExperience": 3,
                     "preferredWorkMode": "remote", "preferredLocation": "Sydney",
                     "location": "Sydney", "educationLevel": "Bachelor's Degree"}
        job = {"requiredSkills": ["Python", "Django"], "requiredExperience": 2,
               "workMode": "remote", "city": "Sydney", "country": "Australia",
               "requiredEducation": "Bachelor's Degree"}
        score = score_job_for_candidate(candidate, job)
        assert 0 <= score <= 100
        assert score > 50  # Should be a good match

    def test_recommend_jobs_sorted(self):
        from search_engine import recommend_jobs_for_candidate
        candidate = {"skills": ["Python"], "yearsOfExperience": 2,
                     "preferredWorkMode": "remote", "preferredLocation": "",
                     "location": "", "educationLevel": "Bachelor's Degree"}
        jobs = [
            {"id": "a", "requiredSkills": ["Python", "Django"], "requiredExperience": 1,
             "workMode": "remote", "city": "", "country": "", "requiredEducation": ""},
            {"id": "b", "requiredSkills": ["Java", "Spring"], "requiredExperience": 5,
             "workMode": "on-site", "city": "", "country": "", "requiredEducation": "Master's Degree"},
        ]
        results = recommend_jobs_for_candidate(candidate, jobs)
        assert results[0]["matchScore"] >= results[1]["matchScore"]
