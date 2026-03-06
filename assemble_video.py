import sys
import os
import json
import subprocess

def download_background_video(topic):
    print(f'Downloading background video for topic: {topic}...')
    search_terms = {
        'bitcoin': 'futuristic city timelapse 4k',
        'crypto': 'neon city night timelapse 4k',
        'celebrity': 'luxury penthouse interior cinematic',
        'sports': 'stadium crowd energy cinematic',
        'nfl': 'american football cinematic 4k',
        'taylor swift': 'concert stage lights cinematic',
        'ai': 'futuristic technology hologram 4k',
        'tesla': 'electric car highway night 4k',
        'stock': 'wall street city finance timelapse',
        'finance': 'luxury office city view cinematic',
        'viral': 'extreme sports action cinematic 4k',
        'challenge': 'urban city timelapse 4k',
        'news': 'city aerial drone footage 4k',
        'weather': 'storm clouds timelapse cinematic',
        'movie': 'cinematic dark aesthetic 4k',
        'music': 'music visualizer neon lights 4k',
        'food': 'gourmet food cinematic close up',
        'health': 'nature forest peaceful cinematic',
        'science': 'space galaxy 4k cinematic',
        'politics': 'capitol building aerial drone 4k',
    }
    search_query = 'aerial city drone footage 4k cinematic'
    topic_lower = topic.lower()
    for keyword, query in search_terms.items():
        if keyword in topic_lower:
            search_query = query
            break
    output_path = f'/tmp/background_{topic_lower[:20].replace(" ", "_")}.mp4'
    if not os.path.exists(output_path):
        subprocess.run([
            '/home/daniel/.local/bin/yt-dlp',
            f'ytsearch1:{search_query}',
            '-f', 'bestvideo[ext=mp4][height<=1080]',
            '-o', output_path,
            '--reject-title', 'minecraft|parkour|GTA|gameplay|mobile game|subway surfers',
            '--no-playlist'
        ], check=True)
    return output_path

def transcribe_audio(audio_path):
    print('Transcribing audio with Whisper...')
    wav_path = audio_path.replace('.mp3', '.wav')
    subprocess.run([
        'ffmpeg', '-y', '-i', audio_path,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        wav_path
    ], check=True)
    result = subprocess.run([
        '/home/daniel/.local/bin/whisper', wav_path,
        '--model', 'base',
        '--output_dir', '/tmp',
        '--output_format', 'json',
        '--word_timestamps', 'True',
        '--language', 'en'
    ], capture_output=False, text=True)
    base = os.path.splitext(os.path.basename(wav_path))[0]
    json_path = f'/tmp/{base}.json'
    if not os.path.exists(json_path):
        raise Exception(f'Whisper failed to create {json_path}')
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def create_ass_subtitles(whisper_data, output_path):
    print('Creating karaoke subtitles...')
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,70,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,5,20,20,200,1
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
    for segment in whisper_data['segments']:
        if 'words' not in segment:
            continue
        words = segment['words']
        seg_end = segment['end']
        for i, word in enumerate(words):
            start = word['start']
            if i + 1 < len(words):
                end = words[i + 1]['start']
            else:
                end = seg_end
            line_words = []
            for j, w in enumerate(words):
                if j == i:
                    line_words.append('{\\c&H00FFFF&}' + w['word'].strip() + '{\\c&HFFFFFF&}')
                else:
                    line_words.append(w['word'].strip())
            line = ' '.join(line_words)
            events.append(f'Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{line}')
    with open(output_path, 'w') as f:
        f.write(ass_header)
        f.write('\n'.join(events))

def assemble_video(audio_path, background_path, subtitles_path, output_path):
    print('Assembling final video...')
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', audio_path
    ], capture_output=True, text=True)
    duration = float(json.loads(result.stdout)['format']['duration'])
    print(f'Audio duration: {duration:.1f} seconds')
    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1',
        '-i', background_path,
        '-i', audio_path,
        '-t', str(duration),
        '-vf', f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={subtitles_path}',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f'Done! Final video: {output_path}')

if __name__ == '__main__':
    audio_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/final_video.mp4'
    topic = sys.argv[3] if len(sys.argv) > 3 else 'general'
    background_path = download_background_video(topic)
    subtitles_path = '/tmp/subtitles.ass'
    whisper_data = transcribe_audio(audio_path)
    create_ass_subtitles(whisper_data, subtitles_path)
    assemble_video(audio_path, background_path, subtitles_path, output_path)
