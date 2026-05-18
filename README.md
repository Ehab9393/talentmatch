# TalentMatch

A web-based job matching platform that connects job seekers with employers. Candidates can search and apply for jobs, while employers can post listings and discover matching candidates.

## Features

- **Candidate side**: Register, build a profile, search and filter jobs, apply, save listings, get AI-powered recommendations
- **Employer side**: Post and manage job listings, browse and filter candidates, get candidate recommendations
- **Membership system**: Unlock unlimited recommendations with a premium membership
- **JWT authentication**: Secure login for both user types

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python 3.11+, Flask, Flask-CORS |
| Database | SQLite |
| Authentication | JWT (PyJWT) |
| Testing | pytest, pytest-cov |
| CI/CD | GitHub Actions |

## Project Structure

```
TalentMatch/
├── backend/
│   ├── app.py              # Flask REST API
│   ├── database.py         # Database setup, schema, seed data
│   ├── search_engine.py    # Job/candidate matching logic
│   ├── run.py              # Entry point
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # pytest test suite
├── css/
│   └── styles.css          # Global styles
├── js/
│   ├── api.js              # API communication layer
│   ├── auth.js             # Authentication logic
│   ├── search.js           # Search and filter logic
│   ├── recommendations.js  # Recommendations UI
│   └── data.js             # Static data / constants
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI pipeline
├── index.html              # Home page
├── find-jobs.html          # Job search page
├── candidates.html         # Candidate search page
├── dashboard-candidate.html
├── dashboard-employer.html
├── login.html
├── register.html
├── profile.html
├── employers.html
├── membership.html
└── about.html
```

## Getting Started

### Prerequisites

- Python 3.11 or higher
- A modern web browser

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/talentmatch.git
   cd talentmatch
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Start the backend server:
   ```bash
   python backend/run.py
   ```
   The API will run at `http://localhost:5000`

4. Open `index.html` in your browser (or use a local server such as Live Server in VS Code).

### Demo Accounts

| Role | Email | Password |
|---|---|---|
| Candidate | alice@example.com | password123 |
| Employer | recruiter@google.com | password123 |

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=.
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register | Register a new user |
| POST | /api/auth/login | Login and receive JWT |
| GET | /api/auth/me | Get current user profile |
| PUT | /api/auth/me | Update profile |
| GET | /api/jobs | List / search jobs |
| POST | /api/jobs | Create a job listing (employer) |
| DELETE | /api/jobs/:id | Delete a job listing (employer) |
| POST | /api/jobs/:id/apply | Apply to a job (candidate) |
| POST | /api/jobs/:id/saved | Save / unsave a job |
| GET | /api/candidates | List / search candidates |
| GET | /api/recommendations/jobs | Job recommendations for candidate |
| GET | /api/recommendations/candidates | Candidate recommendations for employer |
| POST | /api/membership | Toggle membership status |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| TM_SECRET | dev-secret-change-in-prod | JWT signing secret |
| TM_DB_PATH | backend/talentmatch.db | SQLite database path |
| TM_TESTING | (unset) | Set to "1" during testing to skip DB seed |

## CI/CD

GitHub Actions automatically runs on every push to `main`, `master`, or `develop`:
- Runs the full pytest suite on Python 3.11 and 3.12
- Generates a coverage report
- Runs pyflakes linting on backend code
