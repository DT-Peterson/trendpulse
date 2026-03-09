import sys
import os
import json
import subprocess
import random
import urllib.request

PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', '')
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Royalty-free background music URLs (lo-fi/ambient) ---
BG_MUSIC_URLS = [
    'https://cdn.pixabay.com/audio/2024/11/28/audio_3a4b0e3c30.mp3',  # lofi chill
    'https://cdn.pixabay.com/audio/2024/02/14/audio_8e647e66a7.mp3',  # ambient
    'https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3',  # soft beats
]

def download_bg_music():
    """Download a random background music track if not cached."""
    cache_dir = '/tmp/trendpulse_music'
    os.makedirs(cache_dir, exist_ok=True)

    idx = random.randint(0, len(BG_MUSIC_URLS) - 1)
    cached = os.path.join(cache_dir, f'bg_{idx}.mp3')
    if os.path.exists(cached) and os.path.getsize(cached) > 10000:
        return cached

    try:
        print(f'Downloading background music track {idx}...')
        req = urllib.request.Request(BG_MUSIC_URLS[idx], headers={'User-Agent': 'TrendPulse/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(cached, 'wb') as f:
                f.write(resp.read())
        return cached
    except Exception as e:
        print(f'Background music download failed: {e}')
        return None


def download_background_video(topic):
    """Download background B-roll via yt-dlp with improved search queries."""
    print(f'Downloading background video for: {topic}')

    # More specific, higher quality search mappings
    search_terms = {
        'bitcoin': 'cryptocurrency trading screen close up 4k',
        'crypto': 'digital currency blockchain visualization 4k',
        'celebrity': 'red carpet paparazzi lights cinematic',
        'sports': 'sports arena crowd energy slow motion 4k',
        'nfl': 'football game highlights slow motion cinematic',
        'nba': 'basketball court arena lights cinematic 4k',
        'ai': 'artificial intelligence neural network visualization 4k',
        'tesla': 'electric vehicle driving highway night drone 4k',
        'stock': 'stock market trading floor screens 4k',
        'finance': 'financial district city night timelapse 4k',
        'viral': 'social media phone scrolling close up 4k',
        'challenge': 'crowd people energy festival cinematic 4k',
        'news': 'breaking news city aerial helicopter 4k',
        'weather': 'dramatic storm clouds timelapse 4k nature',
        'movie': 'cinema theater screen dark aesthetic 4k',
        'music': 'concert lights stage performance cinematic 4k',
        'food': 'cooking kitchen close up gourmet cinematic 4k',
        'health': 'wellness nature sunrise peaceful 4k drone',
        'science': 'laboratory science experiment close up 4k',
        'space': 'galaxy nebula stars 4k nasa footage',
        'politics': 'city government building sunset aerial 4k',
        'war': 'military documentary historical footage cinematic',
        'climate': 'nature environmental earth from space 4k',
    }

    search_query = 'cinematic drone footage 4k city aerial'
    topic_lower = topic.lower()
    for keyword, query in search_terms.items():
        if keyword in topic_lower:
            search_query = query
            break

    # Add randomness to avoid same clips
    suffixes = ['vertical', 'aesthetic', 'cinematic background', 'no copyright']
    search_query += ' ' + random.choice(suffixes)

    safe_name = topic_lower[:20].replace(' ', '_').replace('"', '').replace("'", '')
    output_path = f'/tmp/bg_{safe_name}_{random.randint(100,999)}.mp4'

    # Skip download if recent cached version exists
    import glob
    cached = glob.glob(f'/tmp/bg_{safe_name}_*.mp4')
    if cached and os.path.getsize(cached[0]) > 100000:
        print(f'Using cached: {cached[0]}')
        return cached[0]

    try:
        subprocess.run([
            '/home/daniel/.local/bin/yt-dlp',
            f'ytsearch3:{search_query}',
            '--playlist-items', str(random.randint(1, 3)),
            '-f', 'bestvideo[ext=mp4][height<=1080]',
            '-o', output_path,
            '--reject-title', 'minecraft|parkour|GTA|gameplay|mobile game|subway surfers|compilation',
            '--no-playlist',
            '--max-filesize', '50M'
        ], check=True, timeout=120)
    except Exception as e:
        print(f'yt-dlp failed: {e}, trying fallback query...')
        subprocess.run([
            '/home/daniel/.local/bin/yt-dlp',
            'ytsearch1:cinematic 4k background no copyright vertical',
            '-f', 'bestvideo[ext=mp4][height<=1080]',
            '-o', output_path,
            '--no-playlist'
        ], check=True, timeout=120)

    return output_path


def transcribe_audio(audio_path):
    """Transcribe with Whisper for word-level timestamps."""
    print('Transcribing audio with Whisper...')
    wav_path = audio_path.replace('.mp3', '.wav')
    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        wav_path
    ], check=True, capture_output=True)

    subprocess.run([
        '/home/daniel/.local/bin/whisper', wav_path,
        '--model', 'base',
        '--output_dir', '/tmp',
        '--output_format', 'json',
        '--word_timestamps', 'True',
        '--language', 'en'
    ], capture_output=True, text=True)

    base = os.path.splitext(os.path.basename(wav_path))[0]
    json_path = f'/tmp/{base}.json'
    if not os.path.exists(json_path):
        raise Exception(f'Whisper failed to create {json_path}')

    with open(json_path, 'r') as f:
        data = json.load(f)
    return data


def create_ass_subtitles(whisper_data, output_path):
    """Create modern word-by-word subtitles — bold, chunked, colored highlight."""
    print('Creating modern subtitles (word-by-word, 2-3 word chunks)...')

    # Modern style: bold white text, colored active word, black outline, bottom-center
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,80,&H00FFFFFF,&H0000FFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,250,1
Style: Active,Montserrat,80,&H0000DDFF,&H0000FFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        cs = int((t % 1) * 100)
        return f'{h}:{m:02d}:{s:02d}.{cs:02d}'

    events = []
    all_words = []

    # Collect all words with timestamps
    for segment in whisper_data.get('segments', []):
        for word_data in segment.get('words', []):
            w = word_data.get('word', '').strip()
            if w:
                all_words.append({
                    'word': w,
                    'start': word_data['start'],
                    'end': word_data['end']
                })

    # Chunk into groups of 2-3 words
    chunk_size = 3
    for i in range(0, len(all_words), chunk_size):
        chunk = all_words[i:i + chunk_size]
        chunk_start = chunk[0]['start']
        chunk_end = chunk[-1]['end']

        # For each word in the chunk, create a frame where that word is highlighted
        for j, active_word in enumerate(chunk):
            w_start = active_word['start']
            w_end = active_word['end'] if j < len(chunk) - 1 else chunk_end

            parts = []
            for k, w in enumerate(chunk):
                if k == j:
                    # Active word: yellow/gold color, slightly larger
                    parts.append('{\\c&H00DDFF&\\fscx110\\fscy110}' + w['word'] + '{\\c&HFFFFFF&\\fscx100\\fscy100}')
                else:
                    parts.append(w['word'])

            line = ' '.join(parts)
            events.append(f'Dialogue: 0,{fmt(w_start)},{fmt(w_end)},Default,,0,0,0,,{line}')

    with open(output_path, 'w') as f:
        f.write(ass_header)
        f.write('\n'.join(events))

    print(f'Subtitles: {len(events)} events from {len(all_words)} words')


def assemble_video(audio_path, background_path, subtitles_path, output_path, bg_music_path=None):
    """Assemble final video with background music, modern subs, and optimized encoding."""
    print('Assembling final video...')

    # Get audio duration
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', audio_path
    ], capture_output=True, text=True)
    duration = float(json.loads(result.stdout)['format']['duration'])
    print(f'Audio duration: {duration:.1f}s')

    # Build FFmpeg command
    inputs = [
        '-stream_loop', '-1', '-i', background_path,
        '-i', audio_path,
    ]

    filter_parts = []
    audio_mix = '[1:a]'

    if bg_music_path and os.path.exists(bg_music_path):
        inputs.extend(['-stream_loop', '-1', '-i', bg_music_path])
        # Mix voiceover (loud) with bg music (quiet) — music at 12% volume
        filter_parts.append('[2:a]volume=0.12[bgm]')
        filter_parts.append('[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]')
        audio_mix = '[aout]'
    
    # Video filter: scale to 9:16, crop, burn subtitles
    vf = f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={subtitles_path}'

    filter_complex = ';'.join(filter_parts) if filter_parts else None

    cmd = ['ffmpeg', '-y'] + inputs + ['-t', str(duration)]

    if filter_complex:
        cmd.extend(['-filter_complex', filter_complex])
        cmd.extend(['-vf', vf])
        cmd.extend(['-map', '0:v', '-map', audio_mix])
    else:
        cmd.extend(['-vf', vf])

    cmd.extend([
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '20',
        '-maxrate', '8M',
        '-bufsize', '10M',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-movflags', '+faststart',
        output_path
    ])

    print('Running FFmpeg...')
    subprocess.run(cmd, check=True)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f'Done! {output_path} ({size_mb:.1f} MB, {duration:.1f}s)')


if __name__ == '__main__':
    audio_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/final_video.mp4'
    topic = sys.argv[3] if len(sys.argv) > 3 else 'general'

    background_path = download_background_video(topic)
    subtitles_path = '/tmp/subtitles.ass'
    bg_music_path = download_bg_music()

    whisper_data = transcribe_audio(audio_path)
    create_ass_subtitles(whisper_data, subtitles_path)
    assemble_video(audio_path, background_path, subtitles_path, output_path, bg_music_path)
