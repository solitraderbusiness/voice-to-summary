# Financial Bot

A Telegram bot and API that transcribes Persian financial market voice reports using OpenAI Whisper API, summarizes them in Persian (~200 words) with emojis and Markdown using OpenRouter's google/gemini-2.0-flash-001, and stores data in PostgreSQL. Runs via PM2 as `voice-to-summary` for reliability and supports Telegram channels.

## Setup

1. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip nginx ffmpeg curl
   curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs
   npm install -g pm2
