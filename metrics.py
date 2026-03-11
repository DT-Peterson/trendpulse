import os
import json
import requests
from datetime import datetime

# --- Load from .env ---
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPTS_DIR, '.env')

def load_env():
    """Load .env file manually (no external deps needed)."""
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip()
                    os.environ[key.strip()] = val.strip()
    return env

load_env()

CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
YOUTUBE_CHANNEL_ID = os.environ.get('YOUTUBE_CHANNEL_ID', '')

# OpenClaw Kimi bot for second opinion (if configured)
KIMI_BOT_TOKEN = os.environ.get('KIMI_BOT_TOKEN', '')


def get_channel_stats():
    url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {
        'part': 'statistics',
        'id': YOUTUBE_CHANNEL_ID,
        'key': YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()


def get_recent_videos():
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'channelId': YOUTUBE_CHANNEL_ID,
        'type': 'video',
        'order': 'date',
        'maxResults': 10,
        'key': YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()


def get_video_stats(video_ids):
    url = 'https://www.googleapis.com/youtube/v3/videos'
    params = {
        'part': 'statistics,contentDetails',
        'id': ','.join(video_ids),
        'key': YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()


def send_telegram_message(text, bot_token=None):
    token = bot_token or TELEGRAM_BOT_TOKEN
    if not token or token.startswith('YOUR_'):
        print(f'Skipping Telegram send (token not configured)')
        return
    requests.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown'
        }
    )


def get_run_history():
    """Load pipeline run history for context in analysis."""
    log_path = '/tmp/trendpulse_runs.jsonl'
    runs = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        runs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return runs[-14:]  # Last 14 runs (1 week of 2x daily)


def get_claude_analysis(report, run_history):
    history_text = ''
    if run_history:
        recent_topics = [r.get('topic', '?') for r in run_history[-7:]]
        voices_used = [r.get('voiceStyle', '?') for r in run_history[-7:]]
        approved_count = sum(1 for r in run_history if r.get('approved'))
        history_text = f"""
Recent topics posted: {', '.join(recent_topics)}
Voice styles used: {', '.join(voices_used)}
Approval rate: {approved_count}/{len(run_history)} ({100*approved_count//max(len(run_history),1)}%)
"""

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 1200,
            'messages': [{
                'role': 'user',
                'content': f"""You are a short-form video growth strategist for TrendPulse, a faceless AI content channel posting 2x daily to TikTok, YouTube Shorts, and Instagram Reels.

Channel metrics:
{report}

Pipeline history:
{history_text}

Provide a concise analysis:
1. PERFORMANCE: What's working and what isn't (cite specific numbers)
2. HOOK QUALITY: Based on recent topics, are hooks likely grabbing attention in first 3 seconds?
3. TOPIC STRATEGY: Are we chasing trends too late or hitting them early? Suggest topic timing improvements.
4. TOMORROW'S PLAY: Specific topic category + hook style to try tomorrow
5. ONE CHANGE: The single highest-impact change to make this week for more views

Keep it actionable. No filler. Plain text, no markdown."""
            }]
        }
    )
    data = response.json()
    return data['content'][0]['text']


def main():
    print('Fetching YouTube metrics...')

    # Validate config
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY.startswith('YOUR_'):
        send_telegram_message('⚠️ YouTube API key not configured in .env')
        print('ERROR: YOUTUBE_API_KEY not set')
        return

    valid_channel_id = bool(YOUTUBE_CHANNEL_ID) and YOUTUBE_CHANNEL_ID.startswith('UC') and len(YOUTUBE_CHANNEL_ID) >= 20
    if not valid_channel_id:
        send_telegram_message('⚠️ YouTube Channel ID not configured in .env — update YOUTUBE_CHANNEL_ID')
        print('ERROR: YOUTUBE_CHANNEL_ID not set properly')
        return

    channel_data = get_channel_stats()

    if 'items' not in channel_data or not channel_data['items']:
        err = channel_data.get('error', {}).get('message', 'Unknown error')
        send_telegram_message(f'❌ YouTube API error: {err}')
        print(f'YouTube API error: {json.dumps(channel_data, indent=2)}')
        return

    stats = channel_data['items'][0]['statistics']
    total_views = int(stats.get('viewCount', 0))
    total_subs = int(stats.get('subscriberCount', 0))
    total_videos = int(stats.get('videoCount', 0))

    videos_data = get_recent_videos()
    video_ids = [item['id']['videoId'] for item in videos_data.get('items', [])]

    report = f"📊 TrendPulse Report\n"
    report += f"{datetime.now().strftime('%B %d, %Y')}\n\n"
    report += f"Channel Overview:\n"
    report += f"  Views: {total_views:,}\n"
    report += f"  Subscribers: {total_subs:,}\n"
    report += f"  Videos: {total_videos}\n\n"

    if video_ids:
        video_stats = get_video_stats(video_ids)
        report += "Recent Videos:\n"

        for i, item in enumerate(video_stats.get('items', [])[:7], 1):
            vid_stats = item['statistics']
            views = int(vid_stats.get('viewCount', 0))
            likes = int(vid_stats.get('likeCount', 0))
            comments = int(vid_stats.get('commentCount', 0))
            video_id = item['id']

            # Calculate engagement rate
            eng_rate = ((likes + comments) / max(views, 1)) * 100

            report += f"  {i}. {views:,} views | {likes} likes | {comments} comments | {eng_rate:.1f}% eng\n"
            report += f"     youtube.com/shorts/{video_id}\n"

    print(report)

    # Send report
    send_telegram_message(f"📊 *TrendPulse Report*\n\n{report}")

    # Get Claude analysis with run history
    run_history = get_run_history()
    analysis = get_claude_analysis(report, run_history)
    send_telegram_message(f"🧠 *Analysis:*\n\n{analysis}")

    # Send to Kimi bot for second opinion (if configured)
    if KIMI_BOT_TOKEN and not KIMI_BOT_TOKEN.startswith('YOUR_'):
        send_telegram_message(report, bot_token=KIMI_BOT_TOKEN)
        send_telegram_message(
            'Based on these metrics, what improvements should we make to topic selection, hook style, and video format to increase views and retention?',
            bot_token=KIMI_BOT_TOKEN
        )

    print('Metrics sent!')


if __name__ == '__main__':
    main()
