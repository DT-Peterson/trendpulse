import requests
from datetime import datetime, timedelta

CLAUDE_API_KEY = 'YOUR_CLAUDE_API_KEY'
TELEGRAM_BOT_TOKEN = 'YOUR_KIMI_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'
KIMI_BOT_TOKEN = 'YOUR_KIMI_BOT_TOKEN'
YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'
YOUTUBE_CHANNEL_ID = 'YOUR_YOUTUBE_CHANNEL_ID'

def get_channel_stats():
    url = f'https://www.googleapis.com/youtube/v3/channels'
    params = {
        'part': 'statistics',
        'id': YOUTUBE_CHANNEL_ID,
        'key': YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

def get_recent_videos():
    url = f'https://www.googleapis.com/youtube/v3/search'
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
    url = f'https://www.googleapis.com/youtube/v3/videos'
    params = {
        'part': 'statistics',
        'id': ','.join(video_ids),
        'key': YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

def send_telegram_message(text):
    requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
        json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'Markdown'
        }
    )
def get_claude_analysis(report):
    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 1000,
            'messages': [{
                'role': 'user',
                'content': f'''You are a social media growth strategist for TrendPulse, a short form video channel posting daily to TikTok, YouTube Shorts and Instagram Reels.

Here are the latest channel metrics:
{report}

Based on these metrics provide:
1. What is working and why
2. What needs improvement
3. Specific recommendations for tomorrows video topic and hook style
4. One actionable tip to increase retention

Keep response concise and actionable. Use plain text no markdown.'''
            }]
        }
    )
    data = response.json()
    return data['content'][0]['text']
def main():
    print('Fetching YouTube metrics...')
    
    channel_data = get_channel_stats()
    
    if 'items' not in channel_data or not channel_data['items']:
        send_telegram_message('❌ Could not fetch YouTube metrics. Check API key and channel ID.')
        return
    
    stats = channel_data['items'][0]['statistics']
    total_views = int(stats.get('viewCount', 0))
    total_subs = int(stats.get('subscriberCount', 0))
    total_videos = int(stats.get('videoCount', 0))
    
    videos_data = get_recent_videos()
    video_ids = [item['id']['videoId'] for item in videos_data.get('items', [])]
    
    report = f"📊 *TrendPulse Weekly Report*\n"
    report += f"_{datetime.now().strftime('%B %d, %Y')}_\n\n"
    report += f"*Channel Overview:*\n"
    report += f"👁 Total Views: {total_views:,}\n"
    report += f"👥 Subscribers: {total_subs:,}\n"
    report += f"🎬 Total Videos: {total_videos}\n\n"
    
    if video_ids:
        video_stats = get_video_stats(video_ids)
        report += "*Recent Video Performance:*\n"
        
        for i, item in enumerate(video_stats.get('items', [])[:5], 1):
            vid_stats = item['statistics']
            views = int(vid_stats.get('viewCount', 0))
            likes = int(vid_stats.get('likeCount', 0))
            comments = int(vid_stats.get('commentCount', 0))
            video_id = item['id']
            report += f"{i}. 👁 {views:,} views | 👍 {likes} | 💬 {comments} | youtube.com/shorts/{video_id}\n"
    
    report += "\n*Kimi Analysis Needed:*\n"
    report += "Review above metrics and suggest improvements for tomorrow's video topic and hook style."
    
    print(report)
    send_telegram_message(report)
    analysis = get_claude_analysis(report)
    send_telegram_message(f"🧠 *Claude Analysis:*\n\n{analysis}")
    requests.post(f'https://api.telegram.org/bot{KIMI_BOT_TOKEN}/sendMessage', json={'chat_id': TELEGRAM_CHAT_ID, 'text': report, 'parse_mode': 'Markdown'})
    requests.post(f'https://api.telegram.org/bot{KIMI_BOT_TOKEN}/sendMessage', json={'chat_id': TELEGRAM_CHAT_ID, 'text': 'Based on the metrics above, what improvements should we make to tomorrows video topic, hook style and script format to increase views and retention?'})
    print('Metrics sent to Telegram!')

if __name__ == '__main__':
    main()
