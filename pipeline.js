const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));
const fs = require('fs');
const { execSync } = require('child_process');

const CLAUDE_API_KEY = 'YOUR_CLAUDE_API_KEY';
const ELEVENLABS_API_KEY = 'sk_2ee3de86bd9a3579a99e4bcb8f40df9f6b3dc73bfc393371';
const TAISLY_API_KEY = 'YOUR_TAISLY_API_KEY';
const TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN';
const TELEGRAM_CHAT_ID = '5914663399';
const VOICE_ID = '21m00Tcm4TlvDq8ikWAM';

const PLATFORM_IDS = [
  '69a93ca768be3afaed6028b3',
  '69a93cbe68be3afaed6028da',
  '69a93cca68be3afaed6028ea'
];

async function getTrendingTopics() {
  const response = await fetch('https://trends.google.com/trends/trendingsearches/daily/rss?geo=US', {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
  });
  const text = await response.text();
  const topics = [];
  const regex = /<title><!\[CDATA\[(.+?)\]\]><\/title>/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match[1] !== 'Daily Search Trends') {
      topics.push(match[1]);
    }
  }
  if (topics.length === 0) {
    return ['Taylor Swift', 'NFL', 'Bitcoin', 'AI news', 'Tesla', 'viral challenge', 'celebrity drama', 'stock market crash', 'new movie release', 'sports highlights'];
  }
  return topics.slice(0, 10);
}

async function getBestTopic(topics) {
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
        content: `Here are today's top trending topics in order of search volume: ${topics.join(', ')}. 

Analyze which ONE topic has the most viral potential for a 30-60 second faceless video on TikTok, YouTube Shorts and Instagram Reels.

Prioritize topics that are:
- RISING fast (just starting to trend, not yet peaked)
- Have broad appeal (not too niche)
- Emotionally engaging (shocking, inspiring, controversial, or funny)
- Can be covered quickly before the trend dies

Avoid topics that:
- Are already oversaturated
- Peaked more than 6 hours ago
- Are too politically divisive
- Could violate community guidelines

Reply with ONLY the topic name, nothing else.`
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
        content: `Write a 30-60 second viral video script about: ${topic}.

Choose the BEST hook formula from these proven viral formats:
- "You won't believe what just happened with [topic]..."
- "Stop doing X, here's what actually works..."
- "POV: You just discovered [topic]..."
- "This [common thing] is a scam, here's the truth..."
- "I tried [topic] for 30 days, here's what happened..."
- "Nobody is talking about this [topic] secret..."
- "The [topic] trick that changed everything..."

Rules:
- Pick the hook that fits the topic best
- Hook must grab attention in first 3 seconds
- Fast paced, punchy sentences, one idea per line
- Conversational tone like talking to a friend
- Build curiosity throughout, don't reveal everything upfront
- End with strong call to action (follow, comment, share)
- Written for AI voiceover, no stage directions
- Plain text only, no labels or headers
- Maximum 150 words`
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
        content: `Generate optimized hashtags for a short form video about: ${topic}.

Rules:
- Generate exactly 10 hashtags
- Mix of large (3), medium (4), and niche (3) hashtags
- All lowercase with # symbol
- Relevant to the topic and trending on TikTok/YouTube/Instagram
- Include at least one broad hashtag like #viral #trending #fyp
- Return ONLY the hashtags separated by spaces, nothing else`
      }]
    })
  });
  const data = await response.json();
  return data.content[0].text.trim();
}

async function generateVoiceover(script) {
  const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'xi-api-key': ELEVENLABS_API_KEY
    },
    body: JSON.stringify({
      text: script,
      model_id: 'eleven_turbo_v2_5',
      voice_settings: {
        stability: 0.85,
        similarity_boost: 0.80,
        style: 0.25,
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
  return path;
}

async function assembleVideo(audioPath, topic) {
  const outputPath = `/tmp/final_video_${Date.now()}.mp4`;
  execSync(`python3 ~/.openclaw/skills/video-pipeline/scripts/assemble_video.py ${audioPath} ${outputPath} "${topic}"`);
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
  const FormData = (await import('formdata-node')).FormData;
  const { fileFromPath } = await import('formdata-node/file-from-path');
  const form = new FormData();
  form.set('chat_id', TELEGRAM_CHAT_ID);
  form.set('caption', caption);
  form.set('video', await fileFromPath(videoPath));
  await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendVideo`, {
    method: 'POST',
    body: form
  });
}

async function postToSocials(videoPath, topic) {
  console.log('Posting to all platforms via Taisly...');
  const FormData = (await import('formdata-node')).FormData;
  const { fileFromPath } = await import('formdata-node/file-from-path');
  const form = new FormData();
  form.set('platforms', JSON.stringify(PLATFORM_IDS));
  const hashtags = await generateHashtags(topic);
  form.set('description', `${topic} 🔥 Follow for daily trending content! ${hashtags}`);
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
            const text = update.message?.text;
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

    setTimeout(() => {
      clearInterval(interval);
      resolve(false);
    }, 600000);
  });
}

async function main() {
  try {
    await sendTelegramMessage('🔍 Starting daily video pipeline...');
    console.log('Fetching trending topics...');
    const topics = await getTrendingTopics();
    console.log('Found topics: ' + topics.join(', '));
    console.log('Selecting best topic...');
    const bestTopic = await getBestTopic(topics);
    console.log('Best topic: ' + bestTopic);
    await sendTelegramMessage(`🎯 Today's topic: *${bestTopic}*\n\nWriting script...`);
    console.log('Writing script...');
    const script = await generateScript(bestTopic);
    console.log('Script written');
    console.log('Generating voiceover...');
    const audioPath = await generateVoiceover(script);
    console.log('Voiceover done: ' + audioPath);
    await sendTelegramMessage('🎙️ Voiceover generated! Assembling video...');
    console.log('Assembling video...');
    const videoPath = await assembleVideo(audioPath, bestTopic);
    console.log('Video done: ' + videoPath);
    await sendTelegramVideo(videoPath, `📹 *${bestTopic}*\n\nReply ✅ to post to all platforms or ❌ to skip`);
    const approved = await waitForApproval(bestTopic);
    if (approved) {
      await sendTelegramMessage('✅ Approved! Posting to TikTok, YouTube and Instagram...');
      await postToSocials(videoPath, bestTopic);
      await sendTelegramMessage('🎉 Posted to all platforms successfully!');
    } else {
      await sendTelegramMessage('❌ Skipped. Run again tomorrow!');
    }
  } catch (error) {
    console.error('Error: ' + error.message);
    await sendTelegramMessage(`❌ Pipeline error: ${error.message}`);
  }
}

main();
