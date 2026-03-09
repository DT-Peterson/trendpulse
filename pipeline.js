require('dotenv').config({ path: __dirname + '/.env' });
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const fs = require('fs');
const { execSync } = require('child_process');

// --- Config from .env ---
const CLAUDE_API_KEY = process.env.CLAUDE_API_KEY;
const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;
const TAISLY_API_KEY = process.env.TAISLY_API_KEY;
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

const PLATFORM_IDS = [
  '69a93ca768be3afaed6028b3',
  '69a93cbe68be3afaed6028da',
  '69a93cca68be3afaed6028ea'
];

// --- Voice rotation: news, hype, storytelling ---
const VOICES = [
  { id: '21m00Tcm4TlvDq8ikWAM', name: 'Rachel', style: 'news', stability: 0.85, similarity: 0.80, styleVal: 0.15 },
  { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Bella', style: 'hype', stability: 0.70, similarity: 0.85, styleVal: 0.45 },
  { id: 'ErXwobaYiN019PkySvjV', name: 'Antoni', style: 'storytelling', stability: 0.80, similarity: 0.75, styleVal: 0.30 }
];

const TOPIC_VOICE_MAP = {
  news: ['politics', 'economy', 'government', 'law', 'policy', 'election', 'war', 'climate'],
  hype: ['viral', 'challenge', 'celebrity', 'music', 'sports', 'nfl', 'nba', 'movie', 'game', 'bitcoin', 'crypto', 'tesla'],
  storytelling: ['science', 'health', 'ai', 'space', 'history', 'food', 'travel', 'nature', 'weather']
};

function pickVoice(topic) {
  const lower = topic.toLowerCase();
  for (const [style, keywords] of Object.entries(TOPIC_VOICE_MAP)) {
    if (keywords.some(k => lower.includes(k))) {
      return VOICES.find(v => v.style === style);
    }
  }
  return VOICES[Math.floor(Math.random() * VOICES.length)];
}

// --- Trend sourcing: Google Trends + Reddit Rising ---
async function getTrendingTopics() {
  const topics = [];

  // Source 1: Google Trends RSS
  try {
    const gRes = await fetch('https://trends.google.com/trends/trendingsearches/daily/rss?geo=US', {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }
    });
    const gText = await gRes.text();
    const regex = /<title><!\[CDATA\[(.+?)\]\]><\/title>/g;
    let match;
    while ((match = regex.exec(gText)) !== null) {
      if (match[1] !== 'Daily Search Trends') topics.push({ source: 'google', topic: match[1] });
    }
  } catch (e) { console.error('Google Trends fetch failed:', e.message); }

  // Source 2: Reddit Rising (r/all) — catches trends 4-6 hours earlier
  try {
    const rRes = await fetch('https://www.reddit.com/r/all/rising.json?limit=10', {
      headers: { 'User-Agent': 'TrendPulse/1.0' }
    });
    const rData = await rRes.json();
    if (rData?.data?.children) {
      for (const post of rData.data.children.slice(0, 10)) {
        const title = post.data.title;
        if (title && title.length > 10 && title.length < 120) {
          topics.push({ source: 'reddit', topic: title });
        }
      }
    }
  } catch (e) { console.error('Reddit fetch failed:', e.message); }

  if (topics.length === 0) {
    return [
      { source: 'fallback', topic: 'AI news' },
      { source: 'fallback', topic: 'Bitcoin' },
      { source: 'fallback', topic: 'viral challenge' },
      { source: 'fallback', topic: 'celebrity drama' },
      { source: 'fallback', topic: 'stock market' }
    ];
  }
  return topics.slice(0, 20);
}

async function getBestTopic(topics) {
  const topicList = topics.map(t => `[${t.source}] ${t.topic}`).join('\n');
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 300,
      messages: [{
        role: 'user',
        content: `You are a viral content strategist for short-form video (TikTok, YouTube Shorts, Instagram Reels).

Here are today's trending topics from multiple sources:
${topicList}

Pick the ONE topic with the highest viral potential for a 30-60 second faceless AI voiceover video.

Prioritize:
- Reddit rising topics (these are 4-6 hours ahead of Google Trends)
- Emotionally engaging: shocking, inspiring, controversial, or funny
- Broad appeal across demographics
- Can be explained in 30-60 seconds without visuals of specific people

Avoid:
- Topics that peaked more than 12 hours ago
- Extremely niche topics
- Anything requiring face-cam or specific footage
- Topics that could violate community guidelines

Reply with ONLY the topic name (cleaned up, concise), nothing else.`
      }]
    })
  });
  const data = await response.json();
  return data.content[0].text.trim();
}

async function generateScript(topic) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      messages: [{
        role: 'user',
        content: `Write a 30-60 second voiceover script for a faceless short-form video about: ${topic}

HOOK (first 3 seconds — this is everything):
Choose the best hook style for this specific topic:
- Pattern interrupt: Start mid-thought as if continuing a conversation
- Bold claim: State something counterintuitive that demands proof
- Direct address: "If you [specific situation], stop scrolling"
- Shock stat: Lead with a number that sounds wrong but is true
- Story open: "So this just happened..." or "I need to tell you about..."

DO NOT use these overused hooks:
- "You won't believe..."
- "Nobody is talking about..."
- "What they don't want you to know..."
- Any hook that sounds like a 2023 AI video

SCRIPT RULES:
- Conversational, like texting a friend who's smart
- Short punchy sentences. One idea per line.
- Add [pause] markers where the speaker should breathe (every 2-3 sentences)
- Build tension: reveal information progressively, save the best detail for the end
- End with a specific CTA: ask a question that demands a comment, or tell them to follow for part 2
- Plain text only. No labels, headers, or stage directions except [pause]
- Maximum 140 words
- Write for AUDIO — this will be read aloud by AI, make it sound natural spoken`
      }]
    })
  });
  const data = await response.json();
  return data.content[0].text.trim();
}

async function generateHashtags(topic) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 200,
      messages: [{
        role: 'user',
        content: `Generate hashtags for a short form video about: ${topic}

Rules:
- 12 hashtags total
- 3 large volume: #viral #trending #fyp #foryou (pick 3)
- 4 medium: topic-relevant hashtags with 100K-10M posts
- 3 niche: specific to this exact topic, lower competition
- 2 engagement: #debate #thoughts #didyouknow #learnontiktok (pick 2)
- All lowercase with # symbol
- Return ONLY hashtags separated by spaces`
      }]
    })
  });
  const data = await response.json();
  return data.content[0].text.trim();
}

async function generateVoiceover(script, topic) {
  const voice = pickVoice(topic);
  console.log(`Using voice: ${voice.name} (${voice.style}) for topic: ${topic}`);

  // Strip [pause] markers — ElevenLabs handles pacing via SSML-like breaks
  const cleanScript = script.replace(/\[pause\]/gi, '... ');

  const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice.id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'xi-api-key': ELEVENLABS_API_KEY
    },
    body: JSON.stringify({
      text: cleanScript,
      model_id: 'eleven_turbo_v2_5',
      voice_settings: {
        stability: voice.stability,
        similarity_boost: voice.similarity,
        style: voice.styleVal,
        use_speaker_boost: true
      }
    })
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`ElevenLabs API error: ${error}`);
  }
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength < 1000) {
    throw new Error(`ElevenLabs returned empty audio: ${buffer.byteLength} bytes`);
  }
  const path = `/tmp/voiceover_${Date.now()}.mp3`;
  fs.writeFileSync(path, Buffer.from(buffer));
  return { path, voiceName: voice.name, voiceStyle: voice.style };
}

async function assembleVideo(audioPath, topic) {
  const outputPath = `/tmp/final_video_${Date.now()}.mp4`;
  execSync(`python3 ~/.openclaw/skills/video-pipeline/scripts/assemble_video.py "${audioPath}" "${outputPath}" "${topic.replace(/"/g, '\\"')}"`);
  return outputPath;
}

async function sendTelegramMessage(text) {
  await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: text,
      parse_mode: 'Markdown'
    })
  });
}

async function sendTelegramVideo(videoPath, caption) {
  try {
    const FormData = (await import('formdata-node')).FormData;
    const { fileFromPath } = await import('formdata-node/file-from-path');
    const form = new FormData();
    form.set('chat_id', TELEGRAM_CHAT_ID);
    form.set('caption', caption);
    form.set('video', await fileFromPath(videoPath, { type: 'video/mp4' }));
    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo`, {
      method: 'POST',
      body: form
    });
    const data = await response.json();
    if (!data.ok) throw new Error('Telegram sendVideo failed: ' + JSON.stringify(data));
  } catch (error) {
    console.error('sendTelegramVideo error: ' + error.message);
    throw error;
  }
}

async function postToSocials(videoPath, topic) {
  console.log('Posting to all platforms via Taisly...');
  const FormData = (await import('formdata-node')).FormData;
  const { fileFromPath } = await import('formdata-node/file-from-path');
  const form = new FormData();
  form.set('platforms', JSON.stringify(PLATFORM_IDS));
  const hashtags = await generateHashtags(topic);
  form.set('description', `${topic} | Follow for daily trending content! ${hashtags}`);
  form.set('video', await fileFromPath(videoPath, { type: 'video/mp4' }));
  const response = await fetch('https://app.taisly.com/api/private/post', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${TAISLY_API_KEY}` },
    body: form
  });
  const data = await response.json();
  console.log('Taisly response: ' + JSON.stringify(data));
  return data;
}

async function waitForApproval(topic) {
  return new Promise(async (resolve) => {
    console.log('Waiting for Telegram approval...');
    const initialResponse = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates`);
    const initialData = await initialResponse.json();
    let offset = 0;
    if (initialData.result && initialData.result.length > 0) {
      offset = initialData.result[initialData.result.length - 1].update_id + 1;
    }

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?offset=${offset}&timeout=10`);
        const data = await response.json();
        if (data.result && data.result.length > 0) {
          for (const update of data.result) {
            offset = update.update_id + 1;
            const text = update.message?.text?.toLowerCase();
            if (text === '✅' || text === 'yes' || text === 'approve') {
              clearInterval(interval);
              resolve(true);
              return;
            } else if (text === '❌' || text === 'no' || text === 'reject') {
              clearInterval(interval);
              resolve(false);
              return;
            }
          }
        }
      } catch (error) {
        console.error('Polling error: ' + error.message);
      }
    }, 3000);

    // 10 minute timeout
    setTimeout(() => {
      clearInterval(interval);
      resolve(false);
    }, 600000);
  });
}

// --- Main pipeline ---
async function main() {
  try {
    await sendTelegramMessage('🔍 Starting video pipeline...');

    console.log('Fetching trending topics...');
    const topics = await getTrendingTopics();
    const googleCount = topics.filter(t => t.source === 'google').length;
    const redditCount = topics.filter(t => t.source === 'reddit').length;
    console.log(`Found ${topics.length} topics (Google: ${googleCount}, Reddit: ${redditCount})`);

    console.log('Selecting best topic...');
    const bestTopic = await getBestTopic(topics);
    console.log('Best topic: ' + bestTopic);
    await sendTelegramMessage(`🎯 Topic: *${bestTopic}*\nSources: Google(${googleCount}) Reddit(${redditCount})\n\nWriting script...`);

    console.log('Writing script...');
    const script = await generateScript(bestTopic);
    console.log('Script written (' + script.split(' ').length + ' words)');

    console.log('Generating voiceover...');
    const { path: audioPath, voiceName, voiceStyle } = await generateVoiceover(script, bestTopic);
    console.log(`Voiceover done (${voiceName}/${voiceStyle}): ${audioPath}`);
    await sendTelegramMessage(`🎙️ Voice: ${voiceName} (${voiceStyle})\nAssembling video...`);

    console.log('Assembling video...');
    const videoPath = await assembleVideo(audioPath, bestTopic);
    console.log('Video done: ' + videoPath);

    await sendTelegramVideo(videoPath, `📹 *${bestTopic}*\nVoice: ${voiceName} (${voiceStyle})\n\nReply ✅ to post or ❌ to skip`);

    const approved = await waitForApproval(bestTopic);
    if (approved) {
      await sendTelegramMessage('✅ Posting to TikTok, YouTube and Instagram...');
      await postToSocials(videoPath, bestTopic);
      await sendTelegramMessage('🎉 Posted to all platforms!');
    } else {
      await sendTelegramMessage('❌ Skipped.');
    }

    // Log run for metrics tracking
    const logEntry = {
      date: new Date().toISOString(),
      topic: bestTopic,
      voice: voiceName,
      voiceStyle,
      approved,
      sources: { google: googleCount, reddit: redditCount }
    };
    const logPath = '/tmp/trendpulse_runs.jsonl';
    fs.appendFileSync(logPath, JSON.stringify(logEntry) + '\n');

  } catch (error) {
    console.error('Pipeline error: ' + error.message);
    await sendTelegramMessage(`❌ Pipeline error: ${error.message}`);
  }
}

main();
