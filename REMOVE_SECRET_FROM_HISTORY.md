# Remove API Key from Git History

GitHub detected an API key in your git history. Here's how to fix it:

## ⚠️ IMPORTANT: Rotate Your API Key First!

**Before proceeding, go to OpenAI and:**
1. Revoke/delete the exposed API key
2. Create a new API key
3. Update your local `.env` file with the new key

## Option 1: Use git-filter-repo (Recommended)

```bash
# Install git-filter-repo if needed
pip install git-filter-repo

# Remove .env from entire history
git filter-repo --path .env --invert-paths

# Force push (this rewrites history!)
git push origin --force --all
```

## Option 2: Use BFG Repo-Cleaner

```bash
# Download BFG (or install via homebrew: brew install bfg)
# Remove .env from history
bfg --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

## Option 3: Use GitHub's Secret Scanning Allow (Not Recommended)

GitHub provided this URL to allow the secret:
https://github.com/taisy03/cv-formatter/security/secret-scanning/unblock-secret/38G65gGu7Turhz7NC07Q6wcm1ux

**⚠️ Only use this if you've already rotated the key!**

## Option 4: Start Fresh (Easiest)

If this is a new repo with few commits:

```bash
# Create a fresh repo without history
rm -rf .git
git init
git add .
git commit -m "Initial commit - CV Formatter"
git branch -M main
git remote add origin https://github.com/taisy03/cv-formatter.git
git push -u origin main --force
```

## ✅ After Cleaning History

1. Verify `.env` is in `.gitignore` ✅ (already done)
2. Verify no keys in current code ✅ (already done)
3. Rotate your API key ✅ (do this now!)
4. Push again

## 🎯 Quick Fix (If repo is new/small)

Since you only have a few commits, the easiest is to start fresh:

```bash
cd /Users/taise/code/PERSONAL/max_formatter

# Backup current state
cp -r . ../max_formatter_backup

# Remove git history
rm -rf .git

# Start fresh
git init
git add .
git commit -m "Initial commit - CV Formatter web app"

# Force push to replace everything
git remote add origin https://github.com/taisy03/cv-formatter.git
git branch -M main
git push -u origin main --force
```

**This will completely replace the GitHub repo with a clean history.**

