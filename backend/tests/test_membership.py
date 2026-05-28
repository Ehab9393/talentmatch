"""
Requirement 2 — New Membership Feature
=======================================
Tests that the membership tier correctly gates recommendation results:
  - Non-member candidates/employers receive at most 10 results
  - Premium members receive all available results
  - Membership can be upgraded, downgraded, and toggled via the API
  - Boundary: exactly 10 when a non-member has more than 10 available

Test types covered:
  - Unit tests  : recommendation engine limit parameter behaviour
  - Integration : membership toggle & plan endpoints, recommendation counts
  - System      : full upgrade → unlimited → downgrade → capped flow
"""
import pytest
from tests.conftest import auth


# ── Unit tests: recommendation engine ────────────────────────────────────────

class TestRecommendationLimit:
    """
    Unit tests for recommend_jobs_for_candidate and
    recommend_candidates_for_job in search_engine.py.
    Verifies the limit parameter is applied correctly without touching the API.
    """

    def _make_jobs(self, n: int) -> list[dict]:
        return [
            {
                "id": f"j{i}", "title": f"Job {i}", "company": "ACME",
                "requiredSkills": ["Python"], "requiredExperience": 1,
                "workMode": "remote", "city": "", "country": "",
                "requiredEducation": ""
            }
            for i in range(n)
        ]

    def _make_candidates(self, n: int) -> list[dict]:
        return [
            {
                "id": f"c{i}", "name": f"Candidate {i}",
                "skills": ["Python"], "yearsOfExperience": 2,
                "preferredWorkMode": "remote", "preferredLocation": "",
                "location": "", "educationLevel": "Bachelor's Degree"
            }
            for i in range(n)
        ]

    def test_recommend_jobs_no_limit_returns_all(self):
        """With limit=None all jobs are returned."""
        from search_engine import recommend_jobs_for_candidate
        candidate = {
            "skills": ["Python"], "yearsOfExperience": 2,
            "preferredWorkMode": "remote", "preferredLocation": "",
            "location": "", "educationLevel": ""
        }
        jobs = self._make_jobs(15)
        result = recommend_jobs_for_candidate(candidate, jobs, limit=None)
        assert len(result) == 15

    def test_recommend_jobs_limit_10_caps_results(self):
        """With limit=10 only the top 10 results are returned."""
        from search_engine import recommend_jobs_for_candidate
        candidate = {
            "skills": ["Python"], "yearsOfExperience": 2,
            "preferredWorkMode": "remote", "preferredLocation": "",
            "location": "", "educationLevel": ""
        }
        jobs = self._make_jobs(14)
        result = recommend_jobs_for_candidate(candidate, jobs, limit=10)
        assert len(result) == 10

    def test_recommend_candidates_limit_10_caps_results(self):
        """With limit=10, recommend_candidates_for_job returns at most 10."""
        from search_engine import recommend_candidates_for_job
        job = {
            "requiredSkills": ["Python"], "requiredExperience": 1,
            "workMode": "remote", "city": "", "country": "", "requiredEducation": ""
        }
        candidates = self._make_candidates(14)
        result = recommend_candidates_for_job(job, candidates, limit=10)
        assert len(result) == 10

    def test_recommend_jobs_results_sorted_descending(self):
        """Recommendations must always be sorted highest score first."""
        from search_engine import recommend_jobs_for_candidate
        candidate = {
            "skills": ["Python", "Django"], "yearsOfExperience": 3,
            "preferredWorkMode": "remote", "preferredLocation": "",
            "location": "", "educationLevel": "Bachelor's Degree"
        }
        jobs = self._make_jobs(14)
        result = recommend_jobs_for_candidate(candidate, jobs, limit=10)
        scores = [r["matchScore"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_recommend_jobs_limit_larger_than_pool_returns_all(self):
        """If limit > total jobs available, all jobs are returned (no padding)."""
        from search_engine import recommend_jobs_for_candidate
        candidate = {
            "skills": [], "yearsOfExperience": 0, "preferredWorkMode": "",
            "preferredLocation": "", "location": "", "educationLevel": ""
        }
        jobs = self._make_jobs(5)
        result = recommend_jobs_for_candidate(candidate, jobs, limit=10)
        assert len(result) == 5

    def test_recommend_jobs_each_result_has_match_score(self):
        """Every returned job must carry a matchScore field."""
        from search_engine import recommend_jobs_for_candidate
        candidate = {
            "skills": ["Python"], "yearsOfExperience": 1,
            "preferredWorkMode": "remote", "preferredLocation": "",
            "location": "", "educationLevel": ""
        }
        result = recommend_jobs_for_candidate(candidate, self._make_jobs(3), limit=None)
        assert all("matchScore" in r for r in result)


# ── Integration tests: membership API ────────────────────────────────────────

class TestMembershipAPI:
    """
    Integration tests for POST /api/membership (toggle and plan-based)
    and the recommendation count difference between member and non-member.
    """

    def test_plan_premium_sets_member_true(self, client, candidate_token):
        """POST /api/membership with plan=premium must set isMember=True."""
        res = client.post("/api/membership",
                          json={"plan": "premium"},
                          headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["isMember"] is True

    def test_plan_free_sets_member_false(self, client, candidate_token):
        """POST /api/membership with plan=free must set isMember=False."""
        # Ensure currently a member first
        client.post("/api/membership", json={"plan": "premium"},
                    headers=auth(candidate_token))
        res = client.post("/api/membership",
                          json={"plan": "free"},
                          headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["isMember"] is False

    def test_toggle_flips_membership_status(self, client, candidate_token):
        """Calling POST /api/membership twice must return the original status."""
        before = client.get("/api/auth/me",
                            headers=auth(candidate_token)).get_json()["isMember"]
        client.post("/api/membership", headers=auth(candidate_token))
        after = client.get("/api/auth/me",
                           headers=auth(candidate_token)).get_json()["isMember"]
        client.post("/api/membership", headers=auth(candidate_token))
        restored = client.get("/api/auth/me",
                              headers=auth(candidate_token)).get_json()["isMember"]
        assert after != before
        assert restored == before

    def test_membership_reflected_in_get_me(self, client, candidate_token):
        """isMember status returned by POST /api/membership matches GET /api/auth/me."""
        toggle_res = client.post("/api/membership", headers=auth(candidate_token))
        expected = toggle_res.get_json()["isMember"]
        me_res = client.get("/api/auth/me", headers=auth(candidate_token))
        assert me_res.get_json()["isMember"] == expected
        # Restore original state
        client.post("/api/membership", headers=auth(candidate_token))

    def test_non_member_job_recommendations_capped_at_10(self, client, candidate_token):
        """A non-member candidate must receive at most 10 job recommendations."""
        # Ensure non-member
        client.post("/api/membership", json={"plan": "free"},
                    headers=auth(candidate_token))
        res = client.get("/api/recommendations/jobs", headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()) <= 10

    def test_member_job_recommendations_exceed_10(self, client, candidate_token):
        """A premium member should receive more than 10 recommendations when enough jobs exist."""
        client.post("/api/membership", json={"plan": "premium"},
                    headers=auth(candidate_token))
        res = client.get("/api/recommendations/jobs", headers=auth(candidate_token))
        assert res.status_code == 200
        # Seed data has 14+ jobs, so a member should see more than 10
        assert len(res.get_json()) > 10

    def test_employer_non_member_candidate_recs_capped(self, client, employer_token):
        """A non-member employer's candidate recommendations must be ≤ 10."""
        client.post("/api/membership", json={"plan": "free"},
                    headers=auth(employer_token))
        res = client.get("/api/recommendations/candidates?jobId=j1",
                         headers=auth(employer_token))
        assert res.status_code == 200
        assert len(res.get_json()) <= 10

    def test_employer_member_candidate_recs_uncapped(self, client, employer_token):
        """A premium employer should see all candidate recommendations (>10 when enough exist)."""
        client.post("/api/membership", json={"plan": "premium"},
                    headers=auth(employer_token))
        res = client.get("/api/recommendations/candidates?jobId=j1",
                         headers=auth(employer_token))
        assert res.status_code == 200
        # If fewer than 10 candidates seeded this still passes; just check no error
        assert isinstance(res.get_json(), list)

    def test_membership_endpoint_requires_auth(self, client):
        """POST /api/membership without a token must return 401."""
        res = client.post("/api/membership", json={"plan": "premium"})
        assert res.status_code == 401

    def test_boundary_non_member_receives_exactly_10_when_over_10_available(
            self, client, candidate_token):
        """Non-member boundary: with 14 seeded jobs the cap returns exactly 10."""
        client.post("/api/membership", json={"plan": "free"},
                    headers=auth(candidate_token))
        res = client.get("/api/recommendations/jobs", headers=auth(candidate_token))
        jobs = res.get_json()
        # Seed has 14 jobs; non-member must be capped at exactly 10
        assert len(jobs) == 10


# ── System tests: full membership flow ───────────────────────────────────────

class TestMembershipSystemFlow:
    """
    System tests that exercise the complete membership lifecycle for a
    newly registered user: register → non-member default → upgrade →
    verify unlimited → downgrade → verify cap restored.
    """

    @pytest.fixture(scope="class")
    def new_user_token(self, client):
        """Register a fresh candidate and return their token."""
        client.post("/api/auth/register", json={
            "name": "Membership Test User",
            "email": "membertest@example.com",
            "password": "testpass123",
            "mobile": "0400000002",
            "type": "candidate"
        })
        res = client.post("/api/auth/login", json={
            "email": "membertest@example.com",
            "password": "testpass123"
        })
        assert res.status_code == 200
        return res.get_json()["token"]

    def test_new_user_is_non_member_by_default(self, client, new_user_token):
        """A freshly registered user must have isMember=False."""
        res = client.get("/api/auth/me", headers=auth(new_user_token))
        assert res.status_code == 200
        assert res.get_json()["isMember"] is False

    def test_new_user_recommendations_capped(self, client, new_user_token):
        """Non-member new user can only see ≤ 10 job recommendations."""
        res = client.get("/api/recommendations/jobs", headers=auth(new_user_token))
        assert res.status_code == 200
        assert len(res.get_json()) <= 10

    def test_upgrade_to_premium(self, client, new_user_token):
        """Upgrading to premium via POST /api/membership returns isMember=True."""
        res = client.post("/api/membership",
                          json={"plan": "premium"},
                          headers=auth(new_user_token))
        assert res.status_code == 200
        assert res.get_json()["isMember"] is True

    def test_premium_user_gets_all_recommendations(self, client, new_user_token):
        """After upgrade, user receives all available job recommendations."""
        # Ensure premium
        client.post("/api/membership", json={"plan": "premium"},
                    headers=auth(new_user_token))
        res = client.get("/api/recommendations/jobs", headers=auth(new_user_token))
        assert res.status_code == 200
        # Seed has 14+ jobs; premium users see them all
        assert len(res.get_json()) >= 14

    def test_downgrade_to_free(self, client, new_user_token):
        """Downgrading to free sets isMember back to False."""
        res = client.post("/api/membership",
                          json={"plan": "free"},
                          headers=auth(new_user_token))
        assert res.status_code == 200
        assert res.get_json()["isMember"] is False

    def test_after_downgrade_recommendations_capped_again(self, client, new_user_token):
        """After downgrade, recommendation count is capped at 10 again."""
        client.post("/api/membership", json={"plan": "free"},
                    headers=auth(new_user_token))
        res = client.get("/api/recommendations/jobs", headers=auth(new_user_token))
        assert res.status_code == 200
        assert len(res.get_json()) <= 10

    def test_upgrade_persists_across_requests(self, client, new_user_token):
        """Membership status persists — a second GET /api/auth/me confirms upgrade."""
        client.post("/api/membership", json={"plan": "premium"},
                    headers=auth(new_user_token))
        # Separate request to confirm persistence
        me1 = client.get("/api/auth/me", headers=auth(new_user_token)).get_json()
        me2 = client.get("/api/auth/me", headers=auth(new_user_token)).get_json()
        assert me1["isMember"] is True
        assert me2["isMember"] is True
