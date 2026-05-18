#!/usr/bin/env python3
"""Entry point to start the TalentMatch backend server."""
import os
os.environ.setdefault("TM_SECRET", "change-me-in-production")

from app import app, bootstrap_db
from database import init_db, seed_db

if __name__ == "__main__":
    init_db()
    seed_db()
    print("TalentMatch API running at http://localhost:5000")
    print("Open index.html in your browser to use the frontend.")
    app.run(debug=True, port=5000, host="0.0.0.0")
