#!/bin/bash
# FeedForge - RSS Feed Generator
# Startup script

echo "========================================="
echo "  FeedForge - RSS Feed Generator"
echo "========================================="

cd "$(dirname "$0")/backend"

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "Starting server..."
echo "Open http://localhost:8000 in your browser"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
