# TalentMatch — System Architecture

## Overview

TalentMatch is a three-tier web application connecting job seekers (candidates) with employers. It follows a client-server architecture where a Vanilla JavaScript frontend communicates with a Python Flask REST API, which reads from and writes to a SQLite database.

---

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                     CLIENT LAYER                    │
│                                                     │
│   Browser                                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│   │  HTML5   │  │  CSS3    │  │ Vanilla JS        │ │
│   │  Pages   │  │ Styles   │  │ (auth, search,    │ │
│   │  (11)    │  │          │  │  api, recommend.) │ │
│   └──────────┘  └──────────┘  └──────────────────┘ │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP requests (JSON)
                      │ Authorization: Bearer <JWT>
┌─────────────────────▼───────────────────────────────┐
│                    SERVER LAYER                     │
│                                                     │
│   Python Flask REST API (port 5000)                 │
│   ┌────────────┐  ┌──────────────┐  ┌───────────┐  │
│   │  app.py    │  │ search_      │  │ database  │  │
│   │  (routes,  │  │ engine.py    │  │ .py       │  │
│   │   auth,    │  │ (matching,   │  │ (schema,  │  │
│   │   JWT)     │  │  scoring)    │  │  seed)    │  │
│   └────────────┘  └──────────────┘  └───────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │ SQL queries
┌─────────────────────▼───────────────────────────────┐
│                   DATABASE LAYER                    │
│                                                     │
│   SQLite — talentmatch.db                           │
│   ┌────────┐ ┌───────────┐ ┌──────┐ ┌───────────┐  │
│   │ users  │ │   jobs    │ │ app- │ │  saved_   │  │
│   │        │ │           │ │ lica-│ │  jobs     │  │
│   └────────┘ └───────────┘ │ tion │ └───────────┘  │
│                             └──────┘                │
└─────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

The frontend is built with plain HTML5, CSS3, and Vanilla JavaScript — no frameworks or build tools required.

| File | Responsibility |
|---|---|
| `index.html` | Landing page |
| `find-jobs.html` | Job search and filtering |
| `candidates.html` | Candidate browsing (employers only) |
| `dashboard-candidate.html` | Candidate dashboard (applications, saved jobs, recommendations) |
| `dashboard-employer.html` | Employer dashboard (job listings, applicants) |
| `login.html` / `register.html` | Authentication pages |
| `profile.html` | User profile editing |
| `membership.html` | Membership upgrade page |
| `about.html` / `employers.html` | Static informational pages |
| `js/api.js` | Centralised API communication layer |
| `js/auth.js` | JWT token management, login/logout, route guards |
| `js/search.js` | Client-side search, fuzzy matching, synonym expansion |
| `js/recommendations.js` | Recommendations UI rendering |
| `js/data.js` | Static data and constants |
| `css/styles.css` | Global stylesheet |

**Communication flow:**
1. Page loads → `auth.js` checks JWT token in localStorage
2. If authenticated → `api.js` attaches `Authorization: Bearer <token>` to every request
3. Response data is rendered directly into the DOM

---

## Backend Architecture

The backend is a RESTful API built with **Python 3.11** and **Flask**.

| Module | Responsibility |
|---|---|
| `app.py` | Route definitions, JWT middleware, request validation, response formatting |
| `database.py` | SQLite schema creation, seed data, row-to-dict serialisation helpers |
| `search_engine.py` | Fuzzy keyword matching, synonym expansion, recommendation scoring algorithm |
| `run.py` | Application entry point |

**Request lifecycle:**
```
Request → Flask router → JWT middleware (require_auth)
       → Route handler → database.py (SQL query)
       → search_engine.py (if search/recommend)
       → JSON response
```

**Authentication flow:**
1. User registers or logs in → server returns a signed JWT (7-day expiry)
2. Client stores token in localStorage
3. Every protected request includes `Authorization: Bearer <token>`
4. `require_auth` decorator decodes and validates the token on each request

---

## Database Schema

| Table | Purpose |
|---|---|
| `users` | Stores both candidates and employers (distinguished by `type` field) |
| `user_skills` | Many-to-many: user ↔ skills |
| `work_experience` | Work history entries per candidate |
| `jobs` | Job listings posted by employers |
| `job_skills` | Many-to-many: job ↔ required skills |
| `job_tags` | Searchable tags per job |
| `applications` | Tracks which candidate applied to which job |
| `saved_jobs` | Tracks jobs saved by candidates |

**Key relationships:**
- `users.id` → `user_skills.user_id` (cascade delete)
- `users.id` → `work_experience.user_id` (cascade delete)
- `users.id` (employer) → `jobs.employer_id` (cascade delete)
- `jobs.id` → `applications.job_id` (cascade delete)
- `jobs.id` → `saved_jobs.job_id` (cascade delete)

---

## Recommendation Engine

The matching algorithm in `search_engine.py` scores each job against a candidate (or vice versa) across four dimensions:

| Factor | Weight |
|---|---|
| Skill match (fuzzy) | 40% |
| Years of experience | 20% |
| Preferred work mode | 20% |
| Location match | 10% |
| Education level | 10% |

Scores range from 0–100. Results are sorted descending. Free users see a maximum of 10 recommendations; premium members see all.

---

## CI/CD Pipeline

GitHub Actions runs automatically on every push to `main`:

```
Push to main
    │
    ├── Backend Tests job
    │   ├── Python 3.11
    │   └── Python 3.12
    │       ├── pip install -r requirements.txt
    │       ├── pytest tests/ --cov
    │       └── Upload coverage report (artifact)
    │
    └── Code Quality job
        └── pyflakes (lint check)
```
