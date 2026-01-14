# Deploy to Render (Free) - Quick Guide

## 🚀 5-Minute Deployment

### Step 1: Push to GitHub

```bash
cd /Users/taise/code/PERSONAL/max_formatter

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - CV Formatter app"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/cv-formatter.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to [render.com](https://render.com)** and sign up (free)

2. **Click "New" → "Web Service"**

3. **Connect GitHub:**
   - Click "Connect GitHub"
   - Authorize Render
   - Select your `cv-formatter` repository

4. **Configure Service:**
   - **Name:** `cv-formatter` (or your choice)
   - **Environment:** `Python 3`
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn server:app`

5. **Click "Create Web Service"**

6. **Wait ~5 minutes** for deployment

7. **Done!** Your app will be live at `https://cv-formatter.onrender.com`

### Step 3: Add Custom Domain (Optional)

1. In Render dashboard → Settings → Custom Domain
2. Add `formatter.taise.co.uk`
3. Render will show DNS records to add
4. Add those records in your Hostinger DNS settings
5. Wait for DNS propagation (~5-30 minutes)

## ✅ That's It!

Your app is now live and free!

**Note:** Free tier spins down after 15 min of inactivity. First request after spin-down takes ~30 seconds to wake up.

## 🔧 Troubleshooting

**Build fails?**
- Check that `requirements.txt` includes `gunicorn`
- Verify `Procfile` exists with `web: gunicorn server:app`

**App crashes?**
- Check logs in Render dashboard
- Verify `template/template.docx` exists
- Make sure all files are committed to Git

**Slow first request?**
- Normal on free tier (cold start)
- Consider Railway for no cold starts

## 📊 Free Tier Limits

- ✅ 750 hours/month (enough for 24/7)
- ✅ Free SSL
- ✅ Custom domains
- ⚠️ Spins down after 15 min inactivity
- ⚠️ 512MB RAM limit

## 💡 Pro Tips

1. **Monitor usage** in Render dashboard
2. **Check logs** if something breaks
3. **Test thoroughly** after deployment
4. **Keep GitHub repo updated** for easy redeploys

---

**Need help?** Check `FREE_HOSTING.md` for other options!

