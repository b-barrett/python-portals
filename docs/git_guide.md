# 🐍 Python Portals — Git Version Control Guide

This guide walks you through clean version control for your Pygame project using Git and GitHub — including dev/test syncing, remote-safe setup, and good practices for managing local changes.

---

## 🛠️ Pre-Steps: Set Up Git + GitHub

### 1. Check Git is Installed

```bash
git --version
```

### 2. Check GitHub Account (optional)

If you're signed into multiple accounts in VS Code or your shell:

```bash
git config user.name
```

To change it:

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

To verify remote GitHub connection:

```bash
git remote -v  # Should show nothing before adding remote
```

---

## ✅ Git Setup for New Project

### 1. Initialize Git

```bash
cd snake  # or your project folder
git init
```

### 2. Add GitHub Remote

```bash
git remote add origin https://github.com/YOUR_USERNAME/python-portals.git
```

Then verify:

```bash
git remote -v
```

---

## 🚀 First Push to GitHub (Clean Setup)

If GitHub repo is **completely empty** (no README):

```bash
git add -A
git commit -m "Initial commit"
git push -u origin main
```

If GitHub repo has auto-generated README or .gitignore:

```bash
git pull origin main --allow-unrelated-histories
# Resolve any conflicts (if any)
git add -A
git commit -m "Merge remote changes with local repo"
git push -u origin main
```

> ❗️ Avoid `--force` unless you’re absolutely sure — it overwrites remote history.

---

## 🔁 Subsequent Workflow

### Make Local Changes

```bash
git add -A
git commit -m "Describe the change"
git push
```

**Pro Tip:** Combine in one line:

```bash
git add -A && git commit -m "Fix bug with food spawn" && git push
git add -A && git commit -m "Update leaderboard" && git push
```

---

## 🔄 Pulling Remote Changes

```bash
git pull origin main
```

> Always pull first if multiple people are pushing to the repo.

---

## 🩠 One-Line Git Sync (Leaderboard + Code)

Use this when you want to fetch any changes (like leaderboard updates), stage all your own changes, commit them, and push them in one go:

```bash
git pull origin main && git add -A && git commit -m "Update leaderboard" && git push
```

---

## 🩠 .gitignore for Cleanup

Create a `.gitignore` file to exclude unwanted files:

```bash
__pycache__/
*.pyc
*.pyo
*.save
.DS_Store
```

---

## 🧑‍💼 Track Your Python Environment

Freeze and save dependencies:

```bash
pip freeze > requirements.txt
```

Then others can install:

```bash
pip install -r requirements.txt
```

---

## 📂 Deleting Files or Folders

### Recommended:

Delete files normally, then run:

```bash
git add -A
```

This ensures Git stages the deletions properly.

### Alternate:

Use `git rm`:

```bash
git rm file.py
```

But `add -A` handles both deletions and new files at once.

---

## 👥 Co-Developer Setup (First-Time Only)

### ✉️ Accept GitHub Invite

Before pushing, the repo owner must:

1. Invite you as a **collaborator** via GitHub > Settings > Collaborators
2. You must **accept the invite via email**
3. Then you can pull/push to the repo normally

### 1. Clone the Repo

```bash
git clone https://github.com/minchodos/python-portals.git
cd python-portals
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

```bash
conda create -n portals python=3.10
conda activate portals
pip install -r requirements.txt
```

### 3. Run the Game

```bash
python snake.py
```

### 4. Git Workflow

* Pull latest leaderboard before playing:

  ```bash
  git pull origin main
  ```
* Push updated leaderboard after playing: Automatically done by the game after each round!

> ❗️ **Only cloned repos support Git syncing**. Zipped folders skip sync and use a local leaderboard instead.

---

## ⚠️ Sync Conflicts — Leaderboard Race Conditions

### ❓ Scenario

> A co-developer plays and updates `leaderboard.json` **but doesn’t push**, and meanwhile **you’re about to push your own changes.**

### ✅ Safe Protocol (Always Do This Before You Push)

```bash
git pull origin main  # Make sure you have latest leaderboard.json
git add -A
git commit -m "Update game logic"
git push
```

### ⚠️ Why It Matters

* Git doesn’t know `leaderboard.json` is updated by gameplay.
* If you push **without pulling first**, you may overwrite their local leaderboard scores.

---

## 📊 Pull Conflicts + Fixes

### ❌ Problem

```bash
git pull origin main
...
error: Your local changes to the following files would be overwritten by merge:
  assets/leaderboard/leaderboard.json
Please commit your changes or stash them before you merge.
Aborting
```

### ✅ Fix It: You Don’t Care About Your Local Leaderboard

Just discard your local changes and pull:

```bash
git restore assets/leaderboard/leaderboard.json
git pull origin main
```

### ❌ Nuke All Uncommitted Changes (Caution!)

```bash
git reset --hard HEAD
git pull origin main
```

> Only do this if you’re *completely sure* you don’t need anything uncommitted.

---


## 🪛 Typical Developer Flow (Daily Use)

### 🎁 1. Sync Before You Start

```bash
git fetch        # Check for remote changes without modifying your files
git status       # See if your branch is behind
```

If you see:

```
Your branch is behind 'origin/main' by X commits.
```

Then do:

```bash
git pull         # Only if you’re ready to bring in remote changes
```

### 🛠️ 2. Make Local Changes

Edit your code, run the game, test new features, etc.

### 💾 3. Save Your Work

```bash
git add -A                                      # Stage everything
git commit -m "<Concise but descriptive message>"  # Save a snapshot
```

### ☁️ 4. Push Changes to GitHub

```bash
git push
```

---

## 👯‍♀️ Working With Multiple Devs

### 🔄 Everyone Should:

* Pull changes **before starting work** (see step 1)
* Push changes after committing

### 🧪 Testing Tournament Workflow

* Each dev saves their leaderboard as `assets/leaderboard/<name>.json`
* One dev runs `merge_named_leaderboards()` locally
* After verifying the new top 10, they push `leaderboard.json`

---

## 🔍 Bonus Git Tips

### See Remote Differences Without Pulling

```bash
git fetch
git diff main origin/main    # Compare local vs remote main
```

### View Incoming Commits

```bash
git log origin/main --oneline --decorate --graph --all
```

### Revert a File to Match Remote

```bash
git checkout origin/main -- path/to/file.py
```

Let me know if you want this guide rendered into a README.md or printed to terminal!

## 📅 Packaging (Future Step)

You can optionally convert the game into a `.exe` (Windows) or `.app` (Mac) for easier sharing with:

* `pyinstaller`
* `py2app`

Let’s revisit this after your Git/GitHub workflow is stable.

---

## ✅ Recap Checklist

| Feature                                 | Done? |
| --------------------------------------- | ----- |
| Git-aware push/pull leaderboard sync    | ✅     |
| `.git` check to skip syncing for zips   | ✅     |
| Devs share one leaderboard via Git      | ✅     |
| Testers get zipped folder, local scores | ✅     |
| `.gitignore` used for junk cleanup      | ✅     |
| Pygame + Python requirements tracked    | ✅     |

You're fully Git-enabled now. Ready to level up.

# Merge Leaderboards

# STEP 1: Each dev saves their leaderboard as a named file

## Each dev runs this once:

```bash
cp assets/leaderboard/leaderboard.json assets/leaderboard/<yourname>.json
```

```bash
git add assets/leaderboard/<yourname>.json
git commit -m "Add <YourName>'s leaderboard"
git push origin main
```

## One-liner:
```bash
git add <name>.json && git commit -m "Add my scores" && git push
```

## Examples:

```bash
cp assets/leaderboard/leaderboard.json assets/leaderboard/thomas.json
git add assets/leaderboard/thomas.json
git commit -m "Add Thomas's leaderboard"
git push origin main
```

## Name Leaderboard Testing Commonly Used Commanda

```bash
find assets/leaderboard -maxdepth 1 -type f -name "*.json" ! -name "leaderboard.json"
```

```bash
find assets/leaderboard -maxdepth 1 -type f -name "*.json" ! -name "leaderboard.json" -exec rm {} +
```


## Each dev repeats this with their own name:

* elisa.json
* ben.json
* julia.json

These files all live in the same folder:
`assets/leaderboard`

# STEP 2: One dev runs the merge (e.g. Thomas)

You (Thomas) now:

```bash
git pull origin main  # Get everyone's jsons including yours
```

# Or:
```bash
git pull
```

Then launch the game and press M on the leaderboard screen to trigger:

```bash
merge_named_leaderboards()
```

That does:

* Reads thomas.json, jamie.json, ari.json
* Deduplicates scores
* Sorts and keeps top 10
* Saves them into leaderboard.json
* Auto-commits & pushes back to GitHub

# STEP 3: The final leaderboard is now shared

All devs can now run:

```bash
git pull origin main
```