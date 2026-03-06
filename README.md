# TrendPulse — Automated Short-Form Video Pipeline

An end-to-end automation pipeline that detects trending topics, generates AI-written scripts, produces voiceover audio, assembles vertical short-form videos, and publishes them to TikTok, YouTube Shorts, and Instagram Reels — all without manual intervention.

Built and deployed on Ubuntu using Node.js, Python, and a suite of AI and media APIs. Developed with AI assistance (Claude) and optimized through iterative testing and deployment.

---

## How It Works

```
Google Trends RSS
       ↓
Claude AI (topic selection)
       ↓
Claude AI (script generation)
       ↓
ElevenLabs (text-to-speech voiceover)
       ↓
yt-dlp (background video download)
       ↓
Whisper (audio transcription + word timestamps)
       ↓
FFmpeg (video assembly + karaoke captions)
       ↓
Telegram (preview + manual approval gate)
       ↓
Taisly (publish to TikTok + YouTube Shorts + Instagram)
```

A separate metrics script runs on a weekly schedule, pulls YouTube analytics, and sends an AI-generated performance report and strategy recommendations to Telegram.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Node.js (pipeline), Python 3 (video assembly + metrics) |
| AI — Content | Anthropic Claude API |
| AI — Transcription | OpenAI Whisper (local) |
| Text-to-Speech | ElevenLabs API |
| Video Download | yt-dlp |
| Video Processing | FFmpeg |
| Social Publishing | Taisly API |
| Notifications / Approval | Telegram Bot API |
| Analytics | YouTube Data API v3 |
| Scheduler | Linux cron |
| Environment | Ubuntu (bare metal / VPS) |

---

## Project Structure

```
trendpulse/
├── scripts/
│   ├── pipeline.js         # Main automation pipeline (Node.js)
│   ├── assemble_video.py   # Video assembly: download, transcribe, caption, render
│   └── metrics.py          # YouTube analytics reporter + Claude analysis
├── .env.example            # Environment variable template
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/DT-Peterson/trendpulse.git
cd trendpulse
```

### 2. Install Node dependencies

```bash
npm install node-fetch formdata-node dotenv
```

### 3. Install Python dependencies

```bash
pip install requests python-dotenv
```

### 4. Install system dependencies

```bash
# FFmpeg
sudo apt install ffmpeg

# yt-dlp
pip install yt-dlp

# Whisper
pip install openai-whisper
```

### 5. Configure environment variables

```bash
cp .env.example .env
nano .env  # Fill in your API keys
```

See `.env.example` for all required variables.

### 6. Set up cron jobs

```bash
crontab -e
```

Add the following lines:

```cron
# Run video pipeline at 9 AM and 6 PM daily
0 9  * * * cd /path/to/trendpulse/scripts && node pipeline.js >> /tmp/pipeline.log 2>&1
0 18 * * * cd /path/to/trendpulse/scripts && node pipeline.js >> /tmp/pipeline.log 2>&1

# Run metrics report at 8 PM daily and every Monday at 9 AM
0 20 * * * cd /path/to/trendpulse/scripts && python3 metrics.py >> /tmp/metrics.log 2>&1
0 9  * * 1 cd /path/to/trendpulse/scripts && python3 metrics.py >> /tmp/metrics.log 2>&1
```

---

## Approval Workflow

When the pipeline runs, it sends the assembled video to your Telegram chat for review before publishing.

| Reply | Action |
|---|---|
| `✅` or `yes` or `approve` | Posts to all platforms |
| `❌` or `no` or `reject` | Skips, runs again next scheduled time |
| *(no reply within 10 min)* | Auto-skips |

---

## Metrics Report

`metrics.py` generates a weekly performance report delivered to Telegram:

- Total channel views, subscribers, and video count
- Per-video breakdown: views, likes, comments, and direct link
- Claude AI analysis: what's working, what to improve, and tomorrow's recommended topic and hook style
- Secondary analysis forwarded to Kimi bot for a second opinion

---

## Security Notes

- All API keys are stored in `.env` and never hardcoded
- `.env` is excluded from version control via `.gitignore`
- Background videos are cached in `/tmp` to reduce redundant downloads
- The Telegram approval gate prevents fully unsupervised publishing

---

## License

MIT
