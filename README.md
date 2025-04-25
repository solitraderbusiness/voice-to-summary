# Voice-to-Summary: Persian Financial Voice Report Bot

**Voice-to-Summary** is a Telegram bot and API that transcribes Persian financial market voice reports using OpenAI's Whisper API, summarizes them into ~200-word Persian summaries with emojis and Markdown formatting using OpenRouter's `google/gemini-2.0-flash-001` model, and stores data in a PostgreSQL database. It runs reliably under PM2 as `voice-to-summary` and supports Telegram channels for real-time financial updates.

The bot processes voice messages (e.g., 30 seconds to 12 minutes), ignores non-voice inputs, and delivers visually appealing summaries with actionable insights, making it ideal for financial analysts sharing market reports in Persian.

## Features

- **Transcription**: Converts Persian voice messages to text using OpenAI Whisper API.
- **Summarization**: Generates ~200-word Persian summaries with emojis (📈, ⚠️, ✅) and MarkdownV2.
- **Database**: Stores transcripts and summaries in PostgreSQL for retrieval and export.
- **Telegram Integration**: Replies with summaries in channels or direct chats, ignoring text messages.
- **Concurrency**: Handles multiple voice messages sequentially with `asyncio.Lock` for stability.
- **Deployment**: Runs via PM2 for auto-restarts and reliability on low-resource servers (1GB RAM).

## Prerequisites

To run or develop this project, you need:

- **Operating System**: Ubuntu 20.04+ (tested on 22.04).
- **Hardware**: Minimum 1GB RAM, 3GB swap (for stability with long audios).
- **Accounts**:
  - **Telegram**: Bot token from [BotFather](https://t.me/BotFather).
  - **OpenAI**: API key for Whisper transcription (https://platform.openai.com).
  - **OpenRouter**: API key for summarization (https://openrouter.ai).
  - **PostgreSQL**: Hosted database (e.g., DigitalOcean Managed Database).
- **Tools**:
  - Python 3.8+ (3.12 recommended).
  - Node.js 18.x (for PM2).
  - Git, curl, ffmpeg.
- **GitHub**: Repository access (https://github.com/solitraderbusiness/voice-to-summary).

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/solitraderbusiness/voice-to-summary.git
cd voice-to-summary
