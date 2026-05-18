# How to Upload TalentMatch to GitHub

Follow these steps exactly. You only do Steps 1–4 once. After that, only Step 5 (daily commits).

---

## Step 1 — Create a GitHub Repository

1. Go to https://github.com and sign in
2. Click the **+** button (top right) → **New repository**
3. Fill in:
   - **Repository name**: `talentmatch`
   - **Description**: `A web-based job matching platform built with Python (Flask) backend and Vanilla HTML/CSS/JavaScript frontend`
   - **Visibility**: Public
   - **Do NOT** tick "Add a README file" (we already have one)
4. Click **Create repository**
5. Copy the URL shown — it looks like: `https://github.com/YOUR_USERNAME/talentmatch.git`

---

## Step 2 — Install Git (if not already installed)

Open PowerShell and type:
```
git --version
```

If you see a version number, skip this step.
If not, download Git from: https://git-scm.com/download/win and install it.

---

## Step 3 — Set Up Git (first time only)

In PowerShell:
```
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Use the same email as your GitHub account.

---

## Step 4 — Upload the Project (do this once)

Open PowerShell and navigate to the project folder:
```
cd "C:\Users\soult\OneDrive\Desktop\software development methodologies\Coding"
```

Then run these commands one by one:

```
git init
git add .
git commit -m "Initial commit: TalentMatch web app with Flask backend and Vanilla JS frontend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/talentmatch.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Step 5 — Daily Commits (do this every time you make changes)

After any change (even small ones), run:

```
cd "C:\Users\soult\OneDrive\Desktop\software development methodologies\Coding"
git add .
git commit -m "describe what you changed here"
git push
```

### Good commit message examples:
- `"Add job filtering by salary range"`
- `"Fix login redirect bug"`
- `"Update candidate profile page UI"`
- `"Add unit test for job application endpoint"`
- `"Update README with setup instructions"`

### Bad commit messages (avoid these):
- `"changes"`
- `"update"`
- `"fix"`
- `"asdf"`

---

## Step 6 — Verify Your Repository

After pushing, go to `https://github.com/YOUR_USERNAME/talentmatch` in your browser.

You should see:
- All your files listed
- The README displayed at the bottom of the page
- A "commits" count at the top (click it to see your version history)

---

## Tips for a Good Version History (for your assignment)

The grader will check your commit history. Aim for **20+ commits** by June 5.

Ideas for daily commits over the next 2.5 weeks:
- Improve the UI of any page
- Add input validation on forms
- Fix any bugs you notice
- Add more tests
- Improve the README or documentation
- Add comments to complex functions
- Add new seed data to the database
- Improve error messages shown to users

Even small improvements count — the goal is to show consistent development progress.
