# Deploying to Koyeb

This guide walks you through deploying the RSS Feed Generator to Koyeb.

## Prerequisites

- [Koyeb account](https://app.koyeb.com) (free tier available)
- GitHub account (to link your repository)
- Git installed locally

## Deployment Steps

### Option 1: Docker Deployment (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/rss-feed-generator.git
   git push -u origin main
   ```

2. **Deploy to Koyeb**
   - Go to [Koyeb Dashboard](https://app.koyeb.com)
   - Click **"Create"** → **"From Git"**
   - Select your GitHub repository
   - Choose the branch (e.g., `main`)
   - **Builder**: Keep default (Auto-detected Docker)
   - **Service name**: `rss-feed-generator` (or your choice)
   - **HTTP port**: `8000`
   - Click **"Deploy"**

3. **Environment Variables (if needed)**
   - No additional environment variables required for basic deployment
   - Your app uses SQLite for the database (stored in the container)

### Option 2: Using Procfile (Alternative)

If you prefer Koyeb's buildpack system:

1. Push to GitHub (same as above)
2. Deploy to Koyeb using the same steps, but Koyeb will auto-detect and use the `Procfile`

## Important Notes

### Database Persistence

The current setup uses SQLite with a local file (`feeds.db`). **This data will be lost when the container is restarted** on Koyeb's free tier.

**For persistent storage**, consider:

#### Option A: Use Koyeb's Volumes (Paid Feature)
- Add a persistent volume to store `feeds.db`
- This requires Koyeb's paid plan

#### Option B: Migrate to PostgreSQL (Recommended)
- Update `main.py` to use PostgreSQL instead of SQLite
- Use a free PostgreSQL database like [ElephantSQL](https://www.elephantsql.com/) or [Railway](https://railway.app/)
- Example PostgreSQL setup:
  ```python
  import psycopg2
  
  DB_URL = os.getenv("DATABASE_URL", "sqlite:///feeds.db")
  # Update init_db() to support PostgreSQL
  ```

## Testing Your Deployment

After deployment:

1. Koyeb will provide a URL like `https://rss-feed-generator-xxx.koyeb.app`
2. Open that URL in your browser
3. Test creating a feed (e.g., enter a keyword or RSS feed URL)

## Troubleshooting

### View Logs
- In Koyeb Dashboard → Your Service → **"Logs"** tab

### Common Issues

**Port not responding:**
- Ensure `--host 0.0.0.0` and `--port 8000` are correct in Dockerfile/Procfile

**Feeds not persisting:**
- Expected behavior on free tier. Consider migrating to PostgreSQL for persistence.

**CORS errors:**
- The app already has CORS enabled globally (all origins allowed). If needed, restrict in `main.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["your-domain.com"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

## Next Steps

1. **Custom Domain**: Add your domain in Koyeb settings
2. **Environment Variables**: Add any secret keys or API tokens in Koyeb → Settings → Environment Variables
3. **Upgrade for Persistence**: Consider moving to Koyeb's paid plan for persistent storage

## Helpful Links

- [Koyeb Docs](https://docs.koyeb.com)
- [Koyeb Docker Deployment Guide](https://docs.koyeb.com/docs/deploy/docker)
- [Koyeb Procfile Guide](https://docs.koyeb.com/docs/deploy/procfile)
