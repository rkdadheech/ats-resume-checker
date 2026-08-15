# ATS Resume Checker (MVP)

Paste a job description, upload a resume (PDF/DOCX), and get:
- An overall ATS score (0-100)
- Keyword match % between resume and JD
- A list of missing keywords to add
- Basic formatting/readability checks
- A visual dashboard (gauge + bar chart)

## 1. Run it locally

```bash
cd ats-checker
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

It'll open at `http://localhost:8501`.

## 2. Deploy free on Streamlit Community Cloud

1. Create a free GitHub account if you don't have one: https://github.com
2. Create a new repo (e.g. `ats-checker`) and push this folder to it:
   ```bash
   git init
   git add .
   git commit -m "Initial ATS checker MVP"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/ats-checker.git
   git push -u origin main
   ```
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click "New app", select your repo, branch `main`, and main file `app.py`.
5. Click Deploy. You'll get a free public URL like:
   `https://your-app-name.streamlit.app`

That's it — no server, no cost, no card required.

## 3. What to improve next (in priority order)

1. **Better keyword extraction**: expand `utils/skills_db.py` with more
   role-specific terms (add more supply chain / your target niche skills).
   This one file is the highest-leverage place to improve match quality.
2. **Feedback loop**: add a simple "Was this helpful?" thumbs up/down to
   learn what's working.
3. **Paywall**: gate the "missing keywords" detail view behind a Razorpay
   Payment Link once you're ready to monetize (free tier = score only,
   paid = full breakdown).
4. **PWA / mobile**: once validated, wrap as a Progressive Web App so
   people can "install" it from their phone browser — no app store needed.
5. **Auth + history**: let users save past scans (needs a small database
   like Supabase's free tier).

## Project structure

```
ats-checker/
├── app.py                 # Streamlit UI + dashboard
├── requirements.txt
├── utils/
│   ├── parser.py           # PDF/DOCX text extraction, formatting checks
│   ├── matcher.py           # keyword extraction + ATS scoring logic
│   └── skills_db.py         # curated skill taxonomy (edit this to tune accuracy)
└── README.md
```
