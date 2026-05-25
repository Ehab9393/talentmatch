"""
Requirement 1 — Candidate Profile Enhancement
==============================================
Tests that the candidate profile correctly stores and returns the new fields
introduced in the 2nd submission: Work Experience, Skills, Preferred Working
Mode, and Preferred Location.

Test types covered:
  - Unit tests  : scoring algorithm responds to the new profile fields
  - Integration : API round-trip for storing and retrieving profile fields
"""
import pytest
from tests.conftest import auth


# ── Unit tests: scoring algorithm ─────────────────────────────────────────────

class TestScoringWithNewFields:
    """
    Unit tests for search_engine.score_job_for_candidate.
    Verifies that each new profile field influences the match score correctly.
    """

    def test_skills_match_increases_score(self):
        """Candidates whose skills match job requirements score higher."""
        from search_engine import score_job_for_candidate
        base = {
            "skills": [], "yearsOfExperience": 2,
            "preferredWorkMode": "remote", "preferredLocation": "",
            "location": "", "educationLevel": ""
        }
        job = {
            "requiredSkills": ["Python", "Django"],
            "requiredExperience": 2, "workMode": "remote",
            "city": "", "country": "", "requiredEducation": ""
        }
        score_no_skills   = score_job_for_candidate(base, job)
        score_with_skills = score_job_for_candidate({**base, "skills": ["Python", "Django"]}, job)
        assert score_with_skills > score_no_skills

    def test_preferred_work_mode_remote_matches(self):
        """Candidate preferring remote scores higher against a remote job."""
        from search_engine import score_job_for_candidate
        base = {
            "skills": ["Python"], "yearsOfExperience": 2,
            "preferredLocation": "", "location": "", "educationLevel": ""
        }
        job = {
            "requiredSkills": ["Python"], "requiredExperience": 2,
            "workMode": "remote", "city": "", "country": "", "requiredEducation": ""
        }
        score_remote  = score_job_for_candidate({**base, "preferredWorkMode": "remote"}, job)
        score_onsite  = score_job_for_candidate({**base, "preferredWorkMode": "on-site"}, job)
        assert score_remote > score_onsite

    def test_preferred_work_mode_hybrid_matches(self):
        """Candidate preferring hybrid scores higher against a hybrid job."""
        from search_engine import score_job_for_candidate
        base = {
            "skills": [], "yearsOfExperience": 1,
            "preferredLocation": "", "location": "", "educationLevel": ""
        }
        job = {
            "requiredSkills": [], "requiredExperience": 1,
            "workMode": "hybrid", "city": "", "country": "", "requiredEducation": ""
        }
        score_hybrid = score_job_for_candidate({**base, "preferredWorkMode": "hybrid"}, job)
        score_remote = score_job_for_candidate({**base, "preferredWorkMode": "remote"}, job)
        assert score_hybrid > score_remote

    def test_preferred_location_match_increases_score(self):
        """Candidate whose preferred location matches job city scores higher."""
        from search_engine import score_job_for_candidate
        base = {
            "skills": ["Python"], "yearsOfExperience": 2,
            "preferredWorkMode": "on-site", "educationLevel": ""
        }
        job = {
            "requiredSkills": ["Python"], "requiredExperience": 2,
            "workMode": "on-site", "city": "Sydney",
            "country": "Australia", "requiredEducation": ""
        }
        score_match    = score_job_for_candidate({**base, "preferredLocation": "Sydney", "location": "Sydney"}, job)
        score_no_match = score_job_for_candidate({**base, "preferredLocation": "London", "location": "London"}, job)
        assert score_match > score_no_match

    def test_score_range_is_always_0_to_100(self):
        """Score must always be between 0 and 100 regardless of profile completeness."""
        from search_engine import score_job_for_candidate
        empty_candidate = {
            "skills": [], "yearsOfExperience": 0, "preferredWorkMode": "",
            "preferredLocation": "", "location": "", "educationLevel": ""
        }
        full_job = {
            "requiredSkills": ["Python", "Django", "AWS", "Docker"],
            "requiredExperience": 10, "workMode": "remote",
            "city": "Sydney", "country": "Australia", "requiredEducation": "Master's Degree"
        }
        score = score_job_for_candidate(empty_candidate, full_job)
        assert 0 <= score <= 100

    def test_partial_skill_overlap_gives_partial_score(self):
        """Having half the required skills gives a lower score than having all."""
        from search_engine import score_job_for_candidate
        base = {
            "yearsOfExperience": 3, "preferredWorkMode": "remote",
            "preferredLocation": "", "location": "", "educationLevel": ""
        }
        job = {
            "requiredSkills": ["Python", "Django", "AWS"],
            "requiredExperience": 3, "workMode": "remote",
            "city": "", "country": "", "requiredEducation": ""
        }
        score_all  = score_job_for_candidate({**base, "skills": ["Python", "Django", "AWS"]}, job)
        score_half = score_job_for_candidate({**base, "skills": ["Python"]}, job)
        assert score_all > score_half

    def test_work_experience_years_influence_score(self):
        """More years of experience (up to requirement) should not reduce score."""
        from search_engine import score_job_for_candidate
        base = {
            "skills": ["Python"], "preferredWorkMode": "remote",
            "preferredLocation": "", "location": "", "educationLevel": ""
        }
        job = {
            "requiredSkills": ["Python"], "requiredExperience": 3,
            "workMode": "remote", "city": "", "country": "", "requiredEducation": ""
        }
        score_exact = score_job_for_candidate({**base, "yearsOfExperience": 3}, job)
        score_under = score_job_for_candidate({**base, "yearsOfExperience": 0}, job)
        assert score_exact >= score_under


# ── Integration tests: API round-trips ────────────────────────────────────────

class TestProfileFieldsViaAPI:
    """
    Integration tests that update candidate profile via PUT /api/auth/me
    and verify the fields are persisted and returned correctly.
    """

    def test_update_skills_field(self, client, candidate_token):
        """PUT /api/auth/me should save and return the skills list."""
        res = client.put("/api/auth/me",
                         json={"skills": ["Python", "React", "Docker"]},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert set(res.get_json()["skills"]) == {"Python", "React", "Docker"}

    def test_update_preferred_work_mode_remote(self, client, candidate_token):
        """Preferred work mode 'remote' should be saved and returned."""
        res = client.put("/api/auth/me",
                         json={"preferredWorkMode": "remote"},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["preferredWorkMode"] == "remote"

    def test_update_preferred_work_mode_hybrid(self, client, candidate_token):
        """Preferred work mode 'hybrid' should be saved and returned."""
        res = client.put("/api/auth/me",
                         json={"preferredWorkMode": "hybrid"},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["preferredWorkMode"] == "hybrid"

    def test_update_preferred_work_mode_onsite(self, client, candidate_token):
        """Preferred work mode 'on-site' should be saved and returned."""
        res = client.put("/api/auth/me",
                         json={"preferredWorkMode": "on-site"},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["preferredWorkMode"] == "on-site"

    def test_update_preferred_location(self, client, candidate_token):
        """Preferred location should be saved and returned."""
        res = client.put("/api/auth/me",
                         json={"preferredLocation": "Sydney"},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert res.get_json()["preferredLocation"] == "Sydney"

    def test_update_work_experience(self, client, candidate_token):
        """Work experience list should be saved and returned with correct fields."""
        experience = [
            {"title": "Backend Developer", "company": "TechCorp",
             "duration": "2021-2023", "description": "Built REST APIs"}
        ]
        res = client.put("/api/auth/me",
                         json={"workExperience": experience},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        saved = res.get_json()["workExperience"]
        assert len(saved) == 1
        assert saved[0]["title"] == "Backend Developer"
        assert saved[0]["company"] == "TechCorp"

    def test_update_multiple_work_experiences(self, client, candidate_token):
        """Multiple work experience entries should all be stored."""
        experience = [
            {"title": "Junior Dev", "company": "StartupA", "duration": "2019-2020"},
            {"title": "Senior Dev", "company": "StartupB", "duration": "2020-2023"},
        ]
        res = client.put("/api/auth/me",
                         json={"workExperience": experience},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()["workExperience"]) == 2

    def test_profile_fields_persist_across_requests(self, client, candidate_token):
        """Updated profile fields should be visible in a subsequent GET /api/auth/me."""
        client.put("/api/auth/me",
                   json={"preferredLocation": "Melbourne", "skills": ["Java", "Spring"]},
                   headers=auth(candidate_token))
        res = client.get("/api/auth/me", headers=auth(candidate_token))
        assert res.status_code == 200
        data = res.get_json()
        assert data["preferredLocation"] == "Melbourne"
        assert "Java" in data["skills"]

    def test_update_profile_requires_auth(self, client):
        """Profile update without token should return 401."""
        res = client.put("/api/auth/me", json={"skills": ["Python"]})
        assert res.status_code == 401

    def test_profile_update_does_not_expose_password(self, client, candidate_token):
        """Response from profile update must never include the password field."""
        res = client.put("/api/auth/me",
                         json={"bio": "Updated bio"},
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert "password" not in res.get_json()
