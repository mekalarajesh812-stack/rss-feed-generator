# FeedForge — RSS Feed Generator

Turn any URL, keyword, or topic into a live RSS/JSON feed.

## Features
- Enter any **news URL** or **keyword/topic** → get an RSS or JSON feed URL
- Feeds **auto-update** on each request (background refresh)
- Copy feed URL in **XML or JSON** format
- **Save & manage** all your feeds
- Manually refresh any feed
- Delete feeds you no longer need

## Stack
- **Backend**: Python FastAPI + SQLite
- **Frontend**: Vanilla HTML/CSS/JS (served by FastAPI)

## Quick Start

### Option 1: Shell script
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** in your browser.

## Deploy to Production

### Deploy to Render (Recommended - Free Tier ✨)

1. Push code to GitHub
2. Go to [https://render.com](https://render.com)
3. Click **New Web Service**
4. Connect GitHub repo → Select branch
5. Configure:
   - Environment: Docker
   - Plan: Starter (free tier available)
6. Deploy!

**For detailed instructions**: See [DEPLOYMENT-RENDER.md](DEPLOYMENT-RENDER.md)

**Free tier info**:
- ✅ Free to deploy
- ⚠️ Data resets on restart (add persistent disk for $12/mo)
- ✅ Auto-deploys on GitHub push

### Deploy to Other Platforms

- **Railway**: [DEPLOYMENT-RENDER.md](DEPLOYMENT-RENDER.md) instructions work here too
- **Heroku**: Use the `Procfile` (though Heroku's free tier is discontinued)
- **DigitalOcean**: Docker support available
- **AWS/Azure**: Any Docker-compatible platform

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/generate` | Generate a feed from URL or keyword |
| GET | `/api/feeds` | List all saved feeds |
| GET | `/api/feed/{id}.xml` | Get feed as RSS XML |
| GET | `/api/feed/{id}.json` | Get feed as JSON Feed |
| POST | `/api/feeds/{id}/refresh` | Manually refresh a feed |
| DELETE | `/api/feeds/{id}` | Delete a feed |

## How it works
- **URL input**: Fetches and parses the RSS/Atom feed at that URL
- **Keyword input**: Searches Google News RSS for the keyword
- **Auto-refresh**: Every time you access a feed URL, it triggers a background refresh so your feed always has the latest items
- **SQLite**: All feeds and items are stored locally in `backend/feeds.db`
