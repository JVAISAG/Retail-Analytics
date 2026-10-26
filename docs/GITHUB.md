# Publish this project on GitHub

## Before publishing

Use the extracted project folder as the repository root. Keep .gitignore and .github/workflows/ci.yml; these dotfiles are part of the project.

The original workbook, SQLite database and ledger.csv.gz are generated local files. They remain usable on your computer, but Git ignores them. New users recreate them with `python src/pipeline.py --download`. Published CSV summaries, dashboard, Excel workbook and preview image remain in the repository.

## GitHub Desktop

1. Choose File > Add local repository and select this project folder.
2. If the folder is not a repository, use the offered option to create a repository there. Avoid creating a second nested project directory. Select no extra README, license or gitignore, because the project already contains these files.
3. Review Changes. The raw workbook, database, compressed ledger, environment files and Python caches should be absent.
4. Commit the project locally, then select Publish repository and choose your desired visibility.
5. After publishing, inspect the Actions tab. Unit checks run on Windows and Linux; the full dataset check also runs for a push to main.

## Command line alternative

Run in this project folder:

```bash
git init -b main
git add .
python scripts/check_project.py
git status --short
git commit -m "Add retail sales and customer retention analytics"
```

Create an empty repository in your GitHub account. Copy its HTTPS or SSH remote URL from GitHub, then add that actual URL as `origin` using `git remote add origin YOUR_COPIED_REPOSITORY_URL`. Replace the placeholder; no real remote is configured by this project. Then run `git push -u origin main`.

If the folder is already a repository, inspect its branch and remotes before changing them. Do not replace a configured remote. Git may ask you to configure your own author name/email and sign in. Keep credentials out of project files.

## Confirm the published repository

- README displays the Excel preview and opens the findings/methodology links.
- Workflow runs are visible in Actions; hosted CI success is established by those runs, not by the presence of a workflow file.
- Downloading index.html and opening it locally displays the analysis; GitHub's file view shows HTML source.
- No database, raw workbook, environment files or project ZIP appears in the tracked file list.
- A clean checkout can install requirements-lock.txt, run unit tests, download/rebuild the data and run full tests.

Publishing the repository does not host the dashboard as a live website. GitHub Pages can be configured separately if you want a hosted demo. The Power BI folder contains build materials rather than a native report.
