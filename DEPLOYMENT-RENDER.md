# Deploying to Render

Complete guide to deploy your RSS Feed Generator to **Render** (free tier available).

## Prerequisites

- [Render account](https://render.com) (free tier works great)
- GitHub account with your repository
- Git installed locally

## Step-by-Step Deployment

### 1. Push Your Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - RSS Feed Generator"

# Add GitHub remote
git remote add origin https://github.com/YOUR-USERNAME/rss-feed-generator.git

# Push to main branch
git branch -M main
git push -u origin main
```

### 2. Connect GitHub to Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click **"New Web Service"**
3. Click **"Connect GitHub account"** (or use existing connection)
4. Authorize Render to access your GitHub repositories
5. Search for and select your `rss-feed-generator` repository
6. Click **"Connect"**

### 3. Configure Deployment Settings

**Service Configuration:**
- **Name**: `rss-feed-generator` (or your preferred name)
- **Environment**: `Docker`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Plan**: Starter (free tier)

**Build Settings:**
- **Root Directory**: Leave empty
- **Dockerfile**: `Dockerfile`
- **Docker Command**: Leave empty (uses CMD from Dockerfile)

**Environment Variables:**
- **PYTHONUNBUFFERED**: `true`

### 4. Deploy

1. Click **"Create Web Service"**
2. Render will start building (takes 2-3 minutes)
3. Once deployed, you'll get a URL like: `https://rss-feed-generator-xyz.onrender.com`

✅ **Your app is now live!**

---

## Testing Your Deployment

1. Open your Render URL in browser
2. Fill in the search box:
   - **Keyword**: `python` → should show tech news
   - **URL**: `https://www.eenadu.net/andhra-pradesh/districts` → should scrape articles

3. Copy the **XML or JSON feed URL** and test in your RSS reader

---

## Database Persistence

⚠️ **Important**: SQLite database is stored in container's `/app/feeds.db`

**On free tier**, data will be lost when:
- Service restarts
- You redeploy code
- Monthly maintenance

### Solution 1: Permanent Storage (Recommended)

Upgrade to Render's **Starter Plus** ($12/month) to add persistent disk:

1. Go to Service Settings → **Disk**
2. Click **"Add Disk"**
3. Mount path: `/app`
4. Size: 5 GB (more than enough)

Now feeds will persist across restarts.

### Solution 2: PostgreSQL Database (Free)

1. Create new PostgreSQL database in Render (free tier):
   - Click "New" → "PostgreSQL"
   - Note the connection string
   
2. Update `backend/main.py` to use PostgreSQL:
   ```python
   import os
   from sqlalchemy import create_engine
   
   DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///feeds.db")
   # Replace uses of sqlite3 with SQLAlchemy
   ```

3. Add environment variable to your web service:
   - `DATABASE_URL`: Your PostgreSQL connection string

---

## Auto-Deploy from Git

Render automatically redeploys when you push to GitHub.

To trigger a deployment:
```bash
git add .
git commit -m "Update feed parser"
git push
```

The deployment starts automatically!

---

## Monitoring & Logs

1. Go to your service in Render dashboard
2. Click **"Logs"** tab to view:
   - Build output
   - Runtime errors
   - Application logs

3. Common issues:
   - **500 Error**: Check logs for Python errors
   - **Feed not loading**: May be a timeout (check network requests)
   - **No data after restart**: Database not persistent (add disk above)

---

## Useful Commands

### View logs in real-time
```bash
# Use the Render dashboard Logs tab (easiest)
# Or via render CLI if installed
render logs --service rss-feed-generator
```

### Force redeploy without code change
1. Go to service dashboard
2. Click **"Manual Deploy"** → **"Deploy Latest"**

### Update environment variables
1. Service Settings → **Environment**
2. Update any variables
3. Changes take effect on next deployment/restart

---

## Pricing

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0/month | 0.5 GB RAM, auto-sleep after 15 min inactivity |
| **Starter** | $7/month | 2.5 GB RAM, always on, better performance |
| **Starter Plus** | $12/month | + 5 GB persistent disk storage |

**Recommendation**: Start free, upgrade to **Starter Plus** ($12/month) when you need persistent data storage.

---

## Troubleshooting

### Service keeps going to sleep (free tier)
- Free tier services sleep after 15 minutes of inactivity
- Users will experience 30-second delay on first request
- **Solution**: Upgrade to Starter plan for always-on service

### Deployment fails with error
1. Check build logs in Render dashboard
2. Common issues:
   - Missing dependencies (add to `requirements.txt`)
   - Port not set correctly (check Dockerfile)
   - Memory limit exceeded (upgrade plan)

### Database errors
- SQLite on free tier has limitations
- **Best practice**: Use PostgreSQL or persistent disk

### Slow response times
- Free tier has limited resources
- **Solution**: Upgrade to Starter or Starter Plus plan

---

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test with a few feeds
3. ✅ Upgrade limits if needed:
   - Always-on service (Starter)
   - Persistent storage (Starter Plus)
4. ✅ Add custom domain in Render settings
5. ✅ Consider PostgreSQL for scaling

---

## Helpful Links

- [Render Docs](https://render.com/docs)
- [Render Docker Guide](https://render.com/docs/deploy-docker)
- [Render PostgreSQL Guide](https://render.com/docs/databases)
- [Render Environment Variables](https://render.com/docs/environment-variables)

---

## Support

**Issue with Render?**
- Check [Render Status Page](https://status.render.com)
- Render community: [discord.gg/render](https://discord.gg/render)

**Issue with your app?**
- Check logs in Render dashboard
- Test locally: `uvicorn backend/main:app --host 0.0.0.0 --port 8000`
