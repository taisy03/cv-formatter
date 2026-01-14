# Free Hosting Options for CV Formatter

Here are the best **free** hosting options for your Flask app:

## 🏆 Top Recommendations

### 1. **Render** (Best Overall) ⭐
**Free Tier:**
- ✅ 750 hours/month (enough for 24/7)
- ✅ Free SSL certificate
- ✅ Automatic deployments from Git
- ✅ Custom domains supported
- ⚠️ Spins down after 15 min inactivity (wakes up on request)

**How to Deploy:**
1. Push code to GitHub
2. Sign up at [render.com](https://render.com)
3. Create new "Web Service"
4. Connect GitHub repo
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`
   - Environment: Python 3

**Pros:** Easy setup, reliable, good free tier
**Cons:** Cold starts after inactivity (~30 seconds)

---

### 2. **Railway** ⭐
**Free Tier:**
- ✅ $5 credit/month (usually enough for small apps)
- ✅ Free SSL
- ✅ No cold starts
- ✅ Easy Git deployments

**How to Deploy:**
1. Sign up at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Railway auto-detects Flask
5. Add environment variables if needed

**Pros:** No cold starts, generous free tier
**Cons:** Credit-based (may need to upgrade eventually)

---

### 3. **PythonAnywhere**
**Free Tier:**
- ✅ Always-on Python hosting
- ✅ Free subdomain: `yourusername.pythonanywhere.com`
- ✅ Good for Python apps
- ⚠️ Limited to 1 web app

**How to Deploy:**
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload files via web interface or Git
3. Configure web app in dashboard
4. Set WSGI file to point to `server.py`

**Pros:** Python-focused, always-on
**Cons:** Less modern interface, limited customization

---

### 4. **Fly.io**
**Free Tier:**
- ✅ 3 shared VMs free
- ✅ Global edge network
- ✅ Free SSL
- ✅ Good performance

**How to Deploy:**
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. In project: `fly launch`
4. Follow prompts

**Pros:** Fast, global CDN
**Cons:** More complex setup

---

### 5. **Replit**
**Free Tier:**
- ✅ Always-on option available
- ✅ Easy Git integration
- ✅ Built-in editor
- ⚠️ May have resource limits

**How to Deploy:**
1. Sign up at [replit.com](https://replit.com)
2. Import from GitHub
3. Run `pip install -r requirements.txt`
4. Use "Always On" feature (may require upgrade)

**Pros:** Easy to use, built-in IDE
**Cons:** Resource limits on free tier

---

## 📋 Quick Comparison

| Platform | Free Tier | Cold Starts | Ease | Best For |
|----------|-----------|-------------|------|----------|
| **Render** | 750 hrs/mo | Yes (15min) | ⭐⭐⭐⭐⭐ | Best overall |
| **Railway** | $5 credit | No | ⭐⭐⭐⭐⭐ | No cold starts |
| **PythonAnywhere** | Always-on | No | ⭐⭐⭐⭐ | Python apps |
| **Fly.io** | 3 VMs | No | ⭐⭐⭐ | Performance |
| **Replit** | Limited | No | ⭐⭐⭐⭐ | Learning |

---

## 🚀 Recommended: Render (Easiest)

### Step-by-Step Render Deployment

1. **Prepare your code:**
   ```bash
   # Make sure you have a Procfile or render.yaml
   ```

2. **Create `Procfile`** (for Render):
   ```
   web: gunicorn server:app
   ```

3. **Update `requirements.txt`** to include gunicorn:
   ```
   flask>=3.0.0
   flask-cors>=4.0.0
   openai>=1.0.0
   python-docx>=1.0.0
   docxtpl>=0.16.0
   pymupdf>=1.23.0
   gunicorn>=21.0.0
   ```

4. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin your-github-repo-url
   git push -u origin main
   ```

5. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Sign up/login
   - Click "New" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - **Name:** cv-formatter (or your choice)
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn server:app`
   - Click "Create Web Service"
   - Wait for deployment (~5 minutes)

6. **Set Custom Domain (Optional):**
   - In Render dashboard → Settings → Custom Domain
   - Add `formatter.taise.co.uk`
   - Update DNS records as instructed

---

## 🔧 Additional Setup Files Needed

### For Render/Railway: Create `Procfile`
```
web: gunicorn server:app
```

### For Render: Create `render.yaml` (optional)
```yaml
services:
  - type: web
    name: cv-formatter
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn server:app
    envVars:
      - key: FLASK_ENV
        value: production
```

### Update `server.py` for Production
Make sure it uses `0.0.0.0` host (already done ✅)

---

## 💡 Tips

1. **Use Gunicorn** for production (better than Flask dev server)
2. **Set FLASK_ENV=production** in environment variables
3. **Monitor usage** - free tiers have limits
4. **Backup your template** file
5. **Test after deployment** with a sample PDF

---

## 🎯 My Recommendation

**Start with Render** - it's the easiest and most reliable free option. If you need no cold starts, try Railway.

Would you like me to create the deployment files (Procfile, etc.) for Render?

