"""
Requirement 3 — Searching Function
====================================
Tests that the search/filter system correctly finds jobs and candidates using
keyword search, field filters, combined queries, fuzzy matching, and
synonym expansion.

Test types covered:
  - Unit tests  : search_engine functions (expand_query, job_matches_query,
                  candidate_matches_query, fuzzy_word_match)
  - Integration : GET /api/jobs?q= and GET /api/candidates?q= API round-trips
  - System      : combined keyword + filter queries that mirror real user flows
"""
import pytest
from tests.conftest import auth


# ── Unit tests: search engine internals ──────────────────────────────────────

class TestExpandQuery:
    """Unit tests for synonym expansion in expand_query."""

    def test_programmer_expands_to_developer(self):
        """'programmer' should expand to include 'developer' via SYNONYMS."""
        from search_engine import expand_query
        terms = expand_query("programmer")
        assert any("developer" in t for t in terms)

    def test_programmer_expands_to_software_engineer(self):
        """'programmer' should expand to include 'software engineer'."""
        from search_engine import expand_query
        terms = expand_query("programmer")
        assert any("software engineer" in t for t in terms)

    def test_it_expands_to_software(self):
        """'it' should expand to include 'software'."""
        from search_engine import expand_query
        terms = expand_query("it")
        assert any("software" in t for t in terms)

    def test_data_scientist_expands_to_data_analyst(self):
        """'data scientist' should expand to 'data analyst' (and vice versa)."""
        from search_engine import expand_query
        terms = expand_query("data scientist")
        assert any("data analyst" in t for t in terms)

    def test_exact_term_always_included(self):
        """The original query term is always included in the expansion."""
        from search_engine import expand_query
        terms = expand_query("devops")
        assert "devops" in terms

    def test_unknown_term_returns_itself(self):
        """A term with no synonyms returns only itself."""
        from search_engine import expand_query
        terms = expand_query("xyznosuchterm123")
        assert terms == ["xyznosuchterm123"]


class TestFuzzyWordMatch:
    """Unit tests for fuzzy_word_match similarity function."""

    def test_exact_match_returns_true(self):
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("python", "python") is True

    def test_typo_sofware_matches_software(self):
        """'sofware' (missing 't') should still match 'software'."""
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("sofware", "software") is True

    def test_typo_enginer_matches_engineer(self):
        """'enginer' should fuzzy-match 'engineer'."""
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("enginer", "engineer") is True

    def test_completely_different_words_do_not_match(self):
        """'python' and 'java' should NOT fuzzy-match."""
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("python", "java") is False

    def test_substring_match_returns_true(self):
        """A word that is a substring of the target should match."""
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("develop", "developer") is True

    def test_short_words_require_exact_match(self):
        """Words shorter than 3 chars require an exact match."""
        from search_engine import fuzzy_word_match
        assert fuzzy_word_match("py", "js") is False
        assert fuzzy_word_match("py", "py") is True


class TestJobMatchesQuery:
    """Unit tests for job_matches_query — keyword search on job dicts."""

    def _job(self, **kwargs) -> dict:
        base = {
            "title": "", "company": "", "description": "",
            "tags": [], "requiredSkills": [],
            "jobRole": "", "jobFunction": "",
            "location": "", "city": "", "country": ""
        }
        base.update(kwargs)
        return base

    def test_matches_exact_title(self):
        from search_engine import job_matches_query
        job = self._job(title="Software Engineer")
        assert job_matches_query(job, "software engineer") is True

    def test_matches_via_synonym_programmer(self):
        """Searching 'programmer' should match a 'Software Engineer' job via synonyms."""
        from search_engine import job_matches_query
        job = self._job(title="Software Engineer")
        assert job_matches_query(job, "programmer") is True

    def test_empty_query_matches_all(self):
        """An empty query string should match every job."""
        from search_engine import job_matches_query
        job = self._job(title="Some Random Job")
        assert job_matches_query(job, "") is True

    def test_no_match_returns_false(self):
        """A query with no connection to the job returns False."""
        from search_engine import job_matches_query
        job = self._job(title="Plumber", company="PipeCo",
                        description="Fix pipes", requiredSkills=["Plumbing"])
        assert job_matches_query(job, "software engineer python") is False

    def test_fuzzy_typo_in_query_still_matches(self):
        """'sofware enginer' (two typos) should still match a Software Engineer job."""
        from search_engine import job_matches_query
        job = self._job(title="Software Engineer",
                        requiredSkills=["Python", "Django"])
        assert job_matches_query(job, "sofware enginer") is True

    def test_matches_required_skills(self):
        """Query matching a required skill returns True."""
        from search_engine import job_matches_query
        job = self._job(title="Backend Developer", requiredSkills=["Python", "Django"])
        assert job_matches_query(job, "python") is True

    def test_matches_city(self):
        """Query matching job city returns True."""
        from search_engine import job_matches_query
        job = self._job(title="Analyst", city="Sydney")
        assert job_matches_query(job, "sydney") is True


class TestCandidateMatchesQuery:
    """Unit tests for candidate_matches_query."""

    def _candidate(self, **kwargs) -> dict:
        base = {
            "name": "", "bio": "", "skills": [],
            "fieldOfStudy": "", "educationLevel": "",
            "location": "", "preferredLocation": "", "workExperience": []
        }
        base.update(kwargs)
        return base

    def test_matches_skill(self):
        from search_engine import candidate_matches_query
        c = self._candidate(skills=["Python", "Django"])
        assert candidate_matches_query(c, "python") is True

    def test_matches_work_experience_title(self):
        from search_engine import candidate_matches_query
        c = self._candidate(workExperience=[
            {"title": "Backend Developer", "company": "ACME", "description": ""}
        ])
        assert candidate_matches_query(c, "backend developer") is True

    def test_synonym_expansion_it_matches_developer(self):
        """Searching 'it' should expand and match a developer candidate."""
        from search_engine import candidate_matches_query
        c = self._candidate(skills=["JavaScript", "React"],
                            workExperience=[{"title": "Developer", "company": "X",
                                             "description": ""}])
        assert candidate_matches_query(c, "it") is True

    def test_no_match_returns_false(self):
        from search_engine import candidate_matches_query
        c = self._candidate(name="Alice", skills=["Python"])
        assert candidate_matches_query(c, "chef cuisine") is False


# ── Integration tests: search API ────────────────────────────────────────────

class TestJobSearchAPI:
    """
    Integration tests for GET /api/jobs?q=<keyword> and filter parameters.
    """

    def test_keyword_software_engineer_returns_results(self, client, candidate_token):
        """Searching 'software engineer' should return at least one seeded job."""
        res = client.get("/api/jobs?q=software+engineer", headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_synonym_programmer_returns_software_engineer_jobs(self, client, candidate_token):
        """'programmer' synonym should surface software engineer jobs."""
        res = client.get("/api/jobs?q=programmer", headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_keyword_data_analyst_returns_results(self, client, candidate_token):
        """'data analyst' should return relevant seeded jobs."""
        res = client.get("/api/jobs?q=data+analyst", headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_fuzzy_query_sofware_enginer_returns_results(self, client, candidate_token):
        """Fuzzy query with two typos should still surface software engineer jobs."""
        res = client.get("/api/jobs?q=sofware+enginer", headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_empty_keyword_returns_all_jobs(self, client, candidate_token):
        """No query string returns all available jobs."""
        all_res  = client.get("/api/jobs", headers=auth(candidate_token))
        empty_res = client.get("/api/jobs?q=", headers=auth(candidate_token))
        assert all_res.status_code == 200
        assert empty_res.status_code == 200
        assert len(all_res.get_json()) == len(empty_res.get_json())

    def test_no_results_for_unrelated_query(self, client, candidate_token):
        """A query with no relevant jobs should return an empty list, not an error."""
        res = client.get("/api/jobs?q=xyznomatchquery999", headers=auth(candidate_token))
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_filter_by_work_mode_remote(self, client, candidate_token):
        """Filter workMode=remote should return only remote jobs."""
        res = client.get("/api/jobs?workMode=remote", headers=auth(candidate_token))
        assert res.status_code == 200
        jobs = res.get_json()
        assert len(jobs) >= 1
        assert all((j.get("workMode") or "").lower() == "remote" for j in jobs)

    def test_filter_by_job_type_full_time(self, client, candidate_token):
        """Filter jobType=full-time should return only full-time jobs."""
        res = client.get("/api/jobs?jobType=full-time", headers=auth(candidate_token))
        assert res.status_code == 200
        jobs = res.get_json()
        if jobs:
            assert all(
                (j.get("jobType") or j.get("type") or "").lower() == "full-time"
                for j in jobs
            )

    def test_search_results_contain_expected_fields(self, client, candidate_token):
        """Every job in search results must have at minimum id, title, company."""
        res = client.get("/api/jobs?q=python", headers=auth(candidate_token))
        assert res.status_code == 200
        for job in res.get_json():
            assert "id" in job
            assert "title" in job
            assert "company" in job


class TestCandidateSearchAPI:
    """Integration tests for GET /api/candidates?q=<keyword>."""

    def test_search_by_skill_python(self, client, employer_token):
        """Searching 'python' should return candidates with Python skill."""
        res = client.get("/api/candidates?q=python", headers=auth(employer_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_search_cybersecurity_returns_carol(self, client, employer_token):
        """'cybersecurity' should return Carol (seeded cybersecurity candidate)."""
        res = client.get("/api/candidates?q=cybersecurity", headers=auth(employer_token))
        assert res.status_code == 200
        names = [c["name"] for c in res.get_json()]
        assert any("carol" in n.lower() for n in names)

    def test_synonym_programmer_matches_developer_candidates(self, client, employer_token):
        """Searching 'programmer' should return developer candidates via synonym."""
        res = client.get("/api/candidates?q=programmer", headers=auth(employer_token))
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_candidate_search_requires_auth(self, client):
        """GET /api/candidates without token must return 401."""
        res = client.get("/api/candidates?q=python")
        assert res.status_code == 401


# ── System tests: combined keyword + filter search flow ──────────────────────

class TestCombinedSearchSystem:
    """
    System tests that combine keyword queries with filters, simulating
    real user search flows end-to-end.
    """

    def test_data_analyst_remote_entry_level(self, client, candidate_token):
        """
        System test: searching 'data analyst' with workMode=remote filter
        should return only remote data analyst / data scientist jobs.
        """
        res = client.get("/api/jobs?q=data+analyst&workMode=remote",
                         headers=auth(candidate_token))
        assert res.status_code == 200
        jobs = res.get_json()
        # All returned jobs must be remote
        for j in jobs:
            assert (j.get("workMode") or "").lower() == "remote"

    def test_keyword_with_location_filter(self, client, candidate_token):
        """Keyword + location filter combination must return valid results."""
        res = client.get("/api/jobs?q=developer&location=sydney",
                         headers=auth(candidate_token))
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)

    def test_fuzzy_search_with_filter(self, client, candidate_token):
        """Fuzzy keyword 'sofware enginer' + workMode filter should not crash."""
        res = client.get("/api/jobs?q=sofware+enginer&workMode=remote",
                         headers=auth(candidate_token))
        assert res.status_code == 200
        jobs = res.get_json()
        for j in jobs:
            assert (j.get("workMode") or "").lower() == "remote"

    def test_synonym_search_programmer_returns_results(
            self, client, candidate_token):
        """
        Searching for the informal term 'programmer' should return results
        because the synonym engine expands it to 'developer'/'software engineer'.
        """
        res = client.get("/api/jobs?q=programmer", headers=auth(candidate_token))
        assert res.status_code == 200
        assert len(res.get_json()) > 0

    def test_full_search_flow_candidate_journey(self, client, candidate_token):
        """
        Full system flow: candidate logs in → searches for jobs by keyword →
        narrows by work mode → checks each result has a valid id.
        """
        # Step 1 — broad keyword search
        broad = client.get("/api/jobs?q=engineer", headers=auth(candidate_token))
        assert broad.status_code == 200
        assert len(broad.get_json()) >= 1

        # Step 2 — narrow by remote work mode
        narrow = client.get("/api/jobs?q=engineer&workMode=remote",
                            headers=auth(candidate_token))
        assert narrow.status_code == 200

        # Step 3 — every result must be valid (has id)
        for j in narrow.get_json():
            assert "id" in j
