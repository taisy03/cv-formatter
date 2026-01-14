# Fix: GitHub Push Declined - Repository Rule Violations

## Common Causes & Solutions

### 1. **Branch Protection Rules** (Most Likely)

GitHub might have branch protection enabled on `main` branch.

**Solution A: Push to a different branch first**
```bash
# Create and push to a new branch
git checkout -b deploy
git add .
git commit -m "Add deployment files"
git push origin deploy

# Then create a Pull Request on GitHub to merge into main
```

**Solution B: Disable branch protection (if you own the repo)**
1. Go to GitHub repo → Settings → Branches
2. Find branch protection rules for `main`
3. Temporarily disable or adjust rules
4. Push again
5. Re-enable protection

### 2. **Required Status Checks**

If you have CI/CD checks that haven't passed.

**Solution:**
- Check GitHub Actions tab for failed checks
- Fix any issues
- Or temporarily disable required checks

### 3. **File Size Limits**

GitHub has limits (100MB warning, 50MB hard limit for individual files).

**Check:**
```bash
git ls-files | xargs ls -lh | awk '$5 ~ /M/ {print $5, $9}'
```

**Solution:** Your template.docx is only 51K, so this shouldn't be the issue.

### 4. **Sensitive Data Detection**

GitHub might be flagging something as sensitive.

**Check what's in your commit:**
```bash
git show HEAD --name-only
```

**Solution:** Review the files being pushed. Your `.env` is ignored, so this shouldn't be it.

### 5. **Commit Message Format**

Some repos require specific commit message formats.

**Your last commit:** `febfe4f key save`

**Solution:** Try a more descriptive commit:
```bash
git commit --amend -m "Add API key caching feature"
git push --force-with-lease
```

## 🚀 Quick Fix (Recommended)

**Push to a feature branch instead:**

```bash
# Stage your changes
git add .

# Commit
git commit -m "Add deployment configuration and documentation"

# Create new branch
git checkout -b add-deployment-files

# Push to new branch
git push origin add-deployment-files
```

Then merge via Pull Request on GitHub (or merge locally if you disable protection).

## 🔍 Check GitHub Settings

1. Go to: `https://github.com/taisy03/cv-formatter/settings/branches`
2. Check if there are branch protection rules
3. Look for:
   - "Require pull request reviews"
   - "Require status checks"
   - "Require linear history"
   - "Restrict pushes"

## ✅ Alternative: Force Push (Use Carefully)

If you're the only one working on this repo:

```bash
# Check what you're pushing
git log origin/main..HEAD

# Force push (ONLY if safe!)
git push --force-with-lease origin main
```

**Warning:** Only do this if you're sure no one else has pushed changes!

## 🎯 Most Likely Solution

Try pushing to a new branch:

```bash
git checkout -b main-update
git push origin main-update
```

Then merge on GitHub or locally.

