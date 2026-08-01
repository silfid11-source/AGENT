# GitHub + Codex + Pull Request Workflow

This project uses a safe Pull Request workflow:

```text
main
-> feature/*
-> Codex edits and checks
-> Pull Request
-> review
-> merge into main
```

## Branch Strategy

- `main`: stable version of the project.
- `feature/*`: one task or feature at a time.
- Do not edit directly on `main` for normal work.
- Keep generated files, secrets, logs, and local experiments out of Git.

## Standard Codex Request

Use this shape when asking Codex to change the project:

```text
Goal:
<what you want to change>

Completion conditions:
- Keep existing features working.
- Do not commit .env, generated results, logs, or API keys.
- Run a basic check before finishing.
- Summarize changed files.
- Prepare the work as a Pull Request.
```

Example:

```text
Goal:
Add image preview to the generation history screen.

Completion conditions:
- Existing saved prompt history still works.
- Missing image files do not crash the app.
- Streamlit app starts without syntax errors.
- Put the change on a feature branch and prepare a PR.
```

## Beginner PowerShell Commands

Check the current branch and changed files:

```powershell
git status
```

Create a new work branch:

```powershell
git switch main
git pull
git switch -c feature/my-task-name
```

Save finished work:

```powershell
git add .
git commit -m "Describe the change"
```

Upload the branch to GitHub:

```powershell
git push -u origin feature/my-task-name
```

Then open GitHub and create a Pull Request from `feature/my-task-name` into `main`.

## Before Every PR

Run these checks:

```powershell
git status
python -m compileall .
```

If the Streamlit app should be tested manually:

```powershell
streamlit run app_v2.py
```

## Files That Should Not Be Committed

- `.env`
- `.streamlit/secrets.toml`
- `projects/`
- `results/`
- `workflow_outputs/`
- `*.log`
- temporary local test files

