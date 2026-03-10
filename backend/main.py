from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sqlite3
import feedparser
import httpx
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import hashlib
import asyncio
from datetime import datetime, timezone
import re
from urllib.parse import quote_plus
import uuid
import time
from bs4 import BeautifulSoup

app = FastAPI(title="RSS Feed Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "feeds.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS feeds (
            id TEXT PRIMARY KEY,
            input TEXT NOT NULL,
            input_type TEXT NOT NULL,
            title TEXT,
            description TEXT,
            created_at TEXT,
            last_updated TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS feed_items (
            id TEXT PRIMARY KEY,
            feed_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            link TEXT,
            pub_date TEXT,
            guid TEXT UNIQUE,
            image_url TEXT,
            FOREIGN KEY (feed_id) REFERENCES feeds(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "tamplates")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def root():
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "FeedForge API - visit /docs"}

class GenerateRequest(BaseModel):
    input: str

def detect_input_type(inp: str) -> str:
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    if url_pattern.match(inp.strip()):
        return "url"
    return "keyword"

async def extract_image(url: str, client: httpx.AsyncClient) -> str:
    """Extract image from article page using og:image meta tag"""
    try:
        resp = await client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=5,
            follow_redirects=True
        )
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Primary: og:image meta tag
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content'].strip()
        
        # Secondary: twitter:image
        twitter_image = soup.find('meta', {'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content'].strip()
        
        # Fallback: first img tag in article
        for img in soup.find_all('img', limit=20):
            src = img.get('src', '').strip()
            if src and src.startswith('http') and len(src) > 20:
                if not any(skip in src.lower() for skip in ['logo', 'icon', 'tracking', 'pixel']):
                    return src
        
        return None
    except:
        return None

async def fetch_rss_from_url(url: str):
    """Fetch and parse RSS/Atom feed from URL with image extraction"""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 FeedBot/1.0"})
        resp.raise_for_status()
        content = resp.text
    
    feed = feedparser.parse(content)
    items = []
    
    # Use separate client for parallel image extraction
    async with httpx.AsyncClient(timeout=30, limits=httpx.Limits(max_connections=5)) as client:
        tasks = []
        
        for entry in feed.entries[:25]:
            image_url = None
            
            # Check feed-provided media first
            if hasattr(entry, 'media_content') and entry.media_content:
                image_url = entry.media_content[0].get('url')
            elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get('url')
            
            # Check description for images
            if not image_url and hasattr(entry, 'summary'):
                img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.get('summary', ''))
                if img_match:
                    image_url = img_match.group(1)
            
            # Fetch from article page if needed
            article_link = entry.get("link", "")
            if not image_url and article_link:
                task = extract_image(article_link, client)
            else:
                task = None
            
            tasks.append((entry, image_url, task))
        
        # Execute all image extraction tasks in parallel
        for entry, cached_image, task in tasks:
            try:
                final_image = cached_image or (await task if task else None)
            except:
                final_image = cached_image
            
            items.append({
                "title": entry.get("title", "No Title"),
                "description": re.sub('<[^<]+?>', '', entry.get("summary", ""))[:250],
                "link": entry.get("link", ""),
                "pub_date": entry.get("published", datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")),
                "guid": entry.get("id", entry.get("link", str(uuid.uuid4()))),
                "image_url": final_image,
            })
    
    title = feed.feed.get("title", url)
    description = feed.feed.get("description", f"Feed from {url}")
    return title, description, items

async def fetch_rss_from_keyword(keyword: str):
    """Generate RSS feed from keyword using Google News RSS - with image extraction"""
    encoded = quote_plus(keyword)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 FeedBot/1.0"})
        resp.raise_for_status()
        content = resp.text
    
    feed = feedparser.parse(content)
    items = []
    
    # Use separate client for parallel image extraction
    async with httpx.AsyncClient(timeout=30, limits=httpx.Limits(max_connections=5)) as client:
        tasks = []
        
        for entry in feed.entries[:20]:  # Google News: top 20 articles
            article_link = entry.get("link", "")
            # Queue image extraction task for each article
            task = extract_image(article_link, client) if article_link else None
            tasks.append((entry, task))
        
        # Execute all image extraction tasks in parallel
        for entry, task in tasks:
            try:
                image_url = await task if task else None
            except:
                image_url = None
            
            items.append({
                "title": entry.get("title", "No Title"),
                "description": re.sub('<[^<]+?>', '', entry.get("summary", ""))[:250],
                "link": entry.get("link", ""),
                "pub_date": entry.get("published", datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")),
                "guid": entry.get("id", entry.get("link", str(uuid.uuid4()))),
                "image_url": image_url,
            })
    
    return f"{keyword} - News Feed", f"Latest news about {keyword}", items

def save_feed_to_db(feed_id: str, inp: str, input_type: str, title: str, description: str, items: list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    c.execute("""
        INSERT OR REPLACE INTO feeds (id, input, input_type, title, description, created_at, last_updated)
        VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM feeds WHERE id=?), ?), ?)
    """, (feed_id, inp, input_type, title, description, feed_id, now, now))
    
    for item in items:
        item_id = hashlib.md5(item["guid"].encode()).hexdigest()
        c.execute("""
            INSERT OR IGNORE INTO feed_items (id, feed_id, title, description, link, pub_date, guid, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, feed_id, item["title"], item["description"], item["link"], item["pub_date"], item["guid"], item.get("image_url")))
    
    conn.commit()
    conn.close()

async def refresh_feed(feed_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT input, input_type FROM feeds WHERE id=?", (feed_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return
    inp, input_type = row
    try:
        if input_type == "url":
            title, description, items = await fetch_rss_from_url(inp)
        else:
            title, description, items = await fetch_rss_from_keyword(inp)
        save_feed_to_db(feed_id, inp, input_type, title, description, items)
    except Exception as e:
        print(f"Error refreshing feed {feed_id}: {e}")

@app.post("/api/generate")
async def generate_feed(req: GenerateRequest):
    inp = req.input.strip()
    if not inp:
        raise HTTPException(400, "Input cannot be empty")
    
    input_type = detect_input_type(inp)
    feed_id = hashlib.md5(inp.encode()).hexdigest()[:16]
    
    # Check if already exists
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM feeds WHERE id=?", (feed_id,))
    exists = c.fetchone()
    conn.close()
    
    try:
        if input_type == "url":
            title, description, items = await fetch_rss_from_url(inp)
        else:
            title, description, items = await fetch_rss_from_keyword(inp)
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch feed: {str(e)}")
    
    save_feed_to_db(feed_id, inp, input_type, title, description, items)
    
    return {
        "feed_id": feed_id,
        "title": title,
        "description": description,
        "item_count": len(items),
        "xml_url": f"/api/feed/{feed_id}.xml",
        "json_url": f"/api/feed/{feed_id}.json",
    }

def get_feed_items(feed_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM feeds WHERE id=?", (feed_id,))
    feed = c.fetchone()
    if not feed:
        conn.close()
        return None, None
    c.execute("SELECT * FROM feed_items WHERE feed_id=? ORDER BY pub_date DESC LIMIT 50", (feed_id,))
    items = c.fetchall()
    conn.close()
    return feed, items

@app.get("/api/feed/{feed_id}.xml")
async def get_feed_xml(feed_id: str, background_tasks: BackgroundTasks):
    feed, items = get_feed_items(feed_id)
    if not feed:
        raise HTTPException(404, "Feed not found")
    
    # Trigger background refresh
    background_tasks.add_task(refresh_feed, feed_id)
    
    f_id, f_input, f_type, f_title, f_desc, f_created, f_updated = feed
    
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = f_title or f_input
    ET.SubElement(channel, "description").text = f_desc or ""
    ET.SubElement(channel, "link").text = f_input if f_type == "url" else f"https://news.google.com/search?q={quote_plus(f_input)}"
    ET.SubElement(channel, "lastBuildDate").text = f_updated or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    for item in items:
        i_id, i_feed_id, i_title, i_desc, i_link, i_pub_date, i_guid, i_image = item
        item_el = ET.SubElement(channel, "item")
        ET.SubElement(item_el, "title").text = i_title or ""
        ET.SubElement(item_el, "description").text = i_desc or ""
        ET.SubElement(item_el, "link").text = i_link or ""
        ET.SubElement(item_el, "pubDate").text = i_pub_date or ""
        ET.SubElement(item_el, "guid").text = i_guid or i_link or ""
        if i_image:
            enclosure = ET.SubElement(item_el, "enclosure")
            enclosure.set("url", i_image)
            enclosure.set("type", "image/jpeg")
    
    xml_str = minidom.parseString(ET.tostring(rss, encoding="unicode")).toprettyxml(indent="  ")
    xml_str = "\n".join(xml_str.split("\n")[1:])  # remove xml declaration duplicate
    
    return Response(
        content=f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}',
        media_type="application/xml"
    )

@app.get("/api/feed/{feed_id}.json")
async def get_feed_json(feed_id: str, background_tasks: BackgroundTasks):
    feed, items = get_feed_items(feed_id)
    if not feed:
        raise HTTPException(404, "Feed not found")
    
    background_tasks.add_task(refresh_feed, feed_id)
    
    f_id, f_input, f_type, f_title, f_desc, f_created, f_updated = feed
    
    result = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": f_title or f_input,
        "description": f_desc or "",
        "feed_url": f"/api/feed/{feed_id}.json",
        "home_page_url": f_input if f_type == "url" else f"https://news.google.com/search?q={quote_plus(f_input)}",
        "date_modified": f_updated,
        "items": []
    }
    
    for item in items:
        i_id, i_feed_id, i_title, i_desc, i_link, i_pub_date, i_guid, i_image = item
        result["items"].append({
            "id": i_guid or i_link,
            "title": i_title,
            "summary": i_desc,
            "url": i_link,
            "date_published": i_pub_date,
            "image": i_image,
        })
    
    return JSONResponse(result)

@app.get("/api/feeds")
async def list_feeds():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT f.id, f.input, f.input_type, f.title, f.last_updated,
               COUNT(fi.id) as item_count
        FROM feeds f
        LEFT JOIN feed_items fi ON fi.feed_id = f.id
        GROUP BY f.id
        ORDER BY f.last_updated DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "input": r[1], "type": r[2],
            "title": r[3], "last_updated": r[4], "item_count": r[5],
            "xml_url": f"/api/feed/{r[0]}.xml",
            "json_url": f"/api/feed/{r[0]}.json",
        } for r in rows
    ]

@app.get("/api/feed/{feed_id}/items")
async def get_feed_items_preview(feed_id: str):
    feed, items = get_feed_items(feed_id)
    if not feed:
        raise HTTPException(404, "Feed not found")
    f_id, f_input, f_type, f_title, f_desc, f_created, f_updated = feed
    result = []
    for item in items:
        i_id, i_feed_id, i_title, i_desc, i_link, i_pub_date, i_guid, i_image = item
        # Extract domain from link
        domain = ""
        try:
            from urllib.parse import urlparse
            domain = urlparse(i_link).netloc.replace("www.", "")
        except:
            pass
        result.append({
            "title": i_title,
            "description": i_desc,
            "link": i_link,
            "pub_date": i_pub_date,
            "image_url": i_image,
            "domain": domain,
        })
    return {"feed_title": f_title, "items": result}

@app.delete("/api/feeds/{feed_id}")
async def delete_feed(feed_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM feed_items WHERE feed_id=?", (feed_id,))
    c.execute("DELETE FROM feeds WHERE id=?", (feed_id,))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/feeds/{feed_id}/refresh")
async def refresh_feed_endpoint(feed_id: str):
    await refresh_feed(feed_id)
    return {"success": True, "message": "Feed refreshed"}
