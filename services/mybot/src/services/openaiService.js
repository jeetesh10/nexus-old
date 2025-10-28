// Minimal OpenAI adapter with a generate(prompt, opts) function that returns { text, raw }
const fetch = global.fetch;
const config = require('../../config/config');

async function generate(prompt, opts = {}) {
  const apiKey = config.OPENAI_API_KEY || process.env.OPENAI_API_KEY || '';
  if (!apiKey) return { text: 'OpenAI not configured', raw: null };
  const apiUrl = 'https://api.openai.com/v1/chat/completions';
  const body = {
    model: opts.model || 'gpt-4o-mini',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: opts.maxTokens || 200
  };
  try {
    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => '<no body>');
      throw new Error(`OpenAI error ${res.status}: ${txt}`);
    }
    const json = await res.json();
    const text = json?.choices?.[0]?.message?.content || '';
    return { text, raw: json };
  } catch (err) {
    console.error('openaiService.generate error', err && err.message ? err.message : err);
    return { text: '', raw: { error: err && err.message ? err.message : String(err) } };
  }
}

module.exports = { generate };
