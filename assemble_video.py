import sys
import argparse
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

def generate_local_bg_music(output_path):
    """Generate a simple local ambient fallback track so the pipeline never depends on remote audio hosts."""
    print('Generating local ambient fallback track...')
    tmp_path = output_path + '.tmp.mp3'
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'sine=frequency=220:sample_rate=44100:duration=90',
        '-f', 'lavfi', '-i', 'sine=frequency=330:sample_rate=44100:duration=90',
        '-filter_complex', '[0:a]volume=0.018[a0];[1:a]volume=0.012[a1];[a0][a1]amix=inputs=2:duration=longest,lowpass=f=1200,highpass=f=120,volume=1.5[aout]',
        '-map', '[aout]',
        '-c:a', 'libmp3lame',
        '-b:a', '128k',
        tmp_path
    ], check=True, capture_output=True)
    os.replace(tmp_path, output_path)
    return output_path


def download_bg_music():
    """Download a background music track if available, otherwise generate a reliable local fallback."""
    cache_dir = '/tmp/trendpulse_music'
    os.makedirs(cache_dir, exist_ok=True)

    cached_tracks = [
        os.path.join(cache_dir, name)
        for name in os.listdir(cache_dir)
        if name.startswith('bg_') and name.endswith('.mp3')
    ]
    usable_cached = [path for path in cached_tracks if os.path.getsize(path) > 10000]
    if usable_cached:
        return random.choice(sorted(usable_cached))

    indices = list(range(len(BG_MUSIC_URLS)))
    random.shuffle(indices)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
        'Referer': 'https://pixabay.com/',
    }

    for idx in indices:
        cached = os.path.join(cache_dir, f'bg_{idx}.mp3')
        try:
            print(f'Downloading background music track {idx}...')
            req = urllib.request.Request(BG_MUSIC_URLS[idx], headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                with open(cached, 'wb') as f:
                    f.write(resp.read())
            if os.path.getsize(cached) > 10000:
                return cached
        except Exception as e:
            print(f'Background music download failed for track {idx}: {e}')

    fallback = os.path.join(cache_dir, 'bg_fallback.mp3')
    if os.path.exists(fallback) and os.path.getsize(fallback) > 10000:
        return fallback

    try:
        return generate_local_bg_music(fallback)
    except Exception as e:
        print(f'Local background music generation failed: {e}')
        return None


def download_background_video(topic):
    """Download background B-roll via yt-dlp and verify the file exists before returning."""
    print(f'Downloading background video for: {topic}')

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

    topic_lower = topic.lower()
    search_query = 'cinematic drone footage 4k city aerial'
    for keyword, query in search_terms.items():
        if keyword in topic_lower:
            search_query = query
            break

    suffixes = ['vertical', 'aesthetic', 'cinematic background', 'no copyright']
    primary_query = search_query + ' ' + random.choice(suffixes)

    safe_name = topic_lower[:20].replace(' ', '_').replace('"', '').replace("'", '')
    output_path = f'/tmp/bg_{safe_name}_{random.randint(100,999)}.mp4'

    import glob
    cached = glob.glob(f'/tmp/bg_{safe_name}_*.mp4')
    if cached and os.path.getsize(cached[0]) > 100000:
        print(f'Using cached: {cached[0]}')
        return cached[0]

    reject_pattern = 'minecraft|parkour|GTA|gameplay|mobile game|subway surfers|compilation'

    def cleanup_partial_files():
        for suffix in ('', '.part'):
            candidate = output_path + suffix
            if os.path.exists(candidate):
                os.remove(candidate)

    def try_download(search_spec, reject_title=None):
        cleanup_partial_files()
        cmd = [
            '/home/daniel/.local/bin/yt-dlp',
            search_spec,
            '--js-runtimes', 'node:/usr/bin/node',
            '--remote-components', 'ejs:github',
            '-f', 'bestvideo[ext=mp4][height<=480]/bestvideo[height<=480]/best[ext=mp4][height<=480]/best[height<=480]',
            '-o', output_path,
            '--max-filesize', '50M',
            '--max-downloads', '1',
            '--no-playlist',
        ]
        if reject_title:
            cmd.extend(['--reject-title', reject_title])
        try:
            subprocess.run(cmd, check=True, timeout=120)
        except subprocess.CalledProcessError as exc:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
                print(f'yt-dlp exited with {exc.returncode} after writing a usable file; continuing with {output_path}')
                return True
            raise
        return os.path.exists(output_path) and os.path.getsize(output_path) > 100000

    attempts = [
        (f'ytsearch10:{primary_query}', reject_pattern),
        ('ytsearch10:vertical cinematic 4k background no copyright', reject_pattern),
        ('ytsearch5:cinematic drone footage vertical 4k', None),
    ]

    for index, (search_spec, reject_title) in enumerate(attempts, start=1):
        try:
            print(f'yt-dlp attempt {index}: {search_spec}')
            if try_download(search_spec, reject_title):
                return output_path
            print(f'yt-dlp attempt {index} produced no usable file, retrying...')
        except Exception as e:
            print(f'yt-dlp attempt {index} failed: {e}')

    raise FileNotFoundError(f'No usable background video was downloaded for topic: {topic}')


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


def create_ass_subtitles(whisper_data, output_path, layout='option1'):
    """Create layout-aware ASS subtitles."""
    if layout == 'option2':
        print('Creating Option 2 subtitles (single word, center overlay)...')
        font_size = 64
        margin_v = 0
        alignment = 5
        outline = 5
        shadow = 1
    else:
        print('Creating Option 1 subtitles (word-by-word, 2-3 word chunks)...')
        font_size = 80
        margin_v = 250
        alignment = 5
        outline = 4
        shadow = 2

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1
Style: Active,Montserrat,{font_size},&H0000DDFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1

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

    for segment in whisper_data.get('segments', []):
        for word_data in segment.get('words', []):
            w = word_data.get('word', '').strip()
            if w:
                all_words.append({
                    'word': w,
                    'start': word_data['start'],
                    'end': word_data['end']
                })

    if layout == 'option2':
        hold_after_word = 0.06
        for idx, word in enumerate(all_words):
            w_start = word['start']
            next_start = all_words[idx + 1]['start'] if idx + 1 < len(all_words) else None
            if next_start is not None:
                w_end = next_start
            else:
                w_end = word['end'] + hold_after_word
            w_end = max(w_end, w_start + 0.06)
            line = '{\\c&H00DDFF&\\fscx108\\fscy108}' + word['word'] + '{\\c&HFFFFFF&\\fscx100\\fscy100}'
            events.append(f'Dialogue: 0,{fmt(w_start)},{fmt(w_end)},Default,,0,0,0,,{line}')
    else:
        chunk_size = 3
        hold_after_chunk = 0.18
        for i in range(0, len(all_words), chunk_size):
            chunk = all_words[i:i + chunk_size]
            next_chunk = all_words[i + chunk_size:i + (chunk_size * 2)]
            next_chunk_start = next_chunk[0]['start'] if next_chunk else None

            for j, active_word in enumerate(chunk):
                w_start = active_word['start']
                if j < len(chunk) - 1:
                    w_end = chunk[j + 1]['start']
                elif next_chunk_start is not None and next_chunk_start - active_word['end'] <= 0.45:
                    w_end = next_chunk_start
                else:
                    w_end = active_word['end'] + hold_after_chunk

                w_end = max(w_end, w_start + 0.08)

                parts = []
                for k, w in enumerate(chunk):
                    if k == j:
                        parts.append('{\\c&H00DDFF&\\fscx110\\fscy110}' + w['word'] + '{\\c&HFFFFFF&\\fscx100\\fscy100}')
                    else:
                        parts.append(w['word'])

                line = ' '.join(parts)
                events.append(f'Dialogue: 0,{fmt(w_start)},{fmt(w_end)},Default,,0,0,0,,{line}')

    with open(output_path, 'w') as f:
        f.write(ass_header)
        f.write('\n'.join(events))

    print(f'Subtitles: {len(events)} events from {len(all_words)} words')


def escape_filter_path(path_value):
    return (path_value
        .replace('\\', '\\\\')
        .replace(':', '\\:')
        .replace(',', '\\,')
        .replace('[', '\\[')
        .replace(']', '\\]')
        .replace("'", "\\'"))



def has_video_stream(path_value):
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', path_value
    ], capture_output=True, text=True)
    if result.returncode != 0:
        return False
    data = json.loads(result.stdout or '{}')
    return any(stream.get('codec_type') == 'video' for stream in data.get('streams', []))


def validate_option2_sources(background_path, user_clip_path):
    if not user_clip_path or not os.path.exists(user_clip_path):
        raise FileNotFoundError('Option 2 requires a valid user clip path')
    if os.path.realpath(background_path) == os.path.realpath(user_clip_path):
        raise ValueError('Option 2 requires two separate videos: generated top and user bottom clip')
    if not has_video_stream(background_path):
        raise ValueError(f'Generated top clip is missing a video stream: {background_path}')
    if not has_video_stream(user_clip_path):
        raise ValueError(f'User clip is missing a video stream: {user_clip_path}')

def assemble_video(audio_path, background_path, subtitles_path, output_path, bg_music_path=None, layout='option1', user_clip_path=None):
    """Assemble the final video in either the standard or split layout."""
    print('Assembling final video...')

    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', audio_path
    ], capture_output=True, text=True)
    duration = float(json.loads(result.stdout)['format']['duration'])
    print(f'Audio duration: {duration:.1f}s')

    inputs = [
        '-stream_loop', '-1', '-i', background_path,
        '-i', audio_path,
    ]

    user_clip_index = None
    if layout == 'option2':
        validate_option2_sources(background_path, user_clip_path)
        print(f'Option 2 top clip: {background_path}')
        print(f'Option 2 bottom clip: {user_clip_path}')
        inputs.extend(['-stream_loop', '-1', '-i', user_clip_path])
        user_clip_index = 2

    music_index = None
    if bg_music_path and os.path.exists(bg_music_path):
        music_index = sum(1 for token in inputs if token == '-i')
        inputs.extend(['-stream_loop', '-1', '-i', bg_music_path])

    subtitle_filter_path = escape_filter_path(subtitles_path)
    filter_parts = []

    if layout == 'option2':
        split_height = 960
        filter_parts.extend([
            f'[0:v]scale=1080:{split_height}:force_original_aspect_ratio=increase,crop=1080:{split_height}[topv]',
            f'[{user_clip_index}:v]scale=1080:{split_height}:force_original_aspect_ratio=increase,crop=1080:{split_height}[bottomv]',
            '[topv][bottomv]vstack=inputs=2[stacked]',
            f'[stacked]ass={subtitle_filter_path}[vout]',
        ])
    else:
        filter_parts.append(f'[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={subtitle_filter_path}[vout]')

    audio_out = '[1:a]'
    if music_index is not None:
        filter_parts.append(f'[{music_index}:a]volume=0.12[bgm]')
        filter_parts.append('[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]')
        audio_out = '[aout]'

    cmd = ['ffmpeg', '-y'] + inputs + [
        '-t', str(duration),
        '-filter_complex', ';'.join(filter_parts),
        '-map', '[vout]',
        '-map', audio_out,
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
    ]

    print('Running FFmpeg...')
    subprocess.run(cmd, check=True)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f'Done! {output_path} ({size_mb:.1f} MB, {duration:.1f}s)')


if __name__ == '__main__':
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        audio_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/final_video.mp4'
        topic = sys.argv[3] if len(sys.argv) > 3 else 'general'
        layout = 'option1'
        user_clip_path = None
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('--audio', required=True)
        parser.add_argument('--output', default='/tmp/final_video.mp4')
        parser.add_argument('--topic', default='general')
        parser.add_argument('--layout', choices=['option1', 'option2'], default='option1')
        parser.add_argument('--user-clip', dest='user_clip_path')
        args = parser.parse_args()
        audio_path = args.audio
        output_path = args.output
        topic = args.topic
        layout = args.layout
        user_clip_path = args.user_clip_path

    background_path = download_background_video(topic)
    subtitles_path = '/tmp/subtitles.ass'
    bg_music_path = download_bg_music()

    whisper_data = transcribe_audio(audio_path)
    create_ass_subtitles(whisper_data, subtitles_path, layout=layout)
    assemble_video(audio_path, background_path, subtitles_path, output_path, bg_music_path, layout=layout, user_clip_path=user_clip_path)


