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
