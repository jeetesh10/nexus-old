/**
 * Minimal GROQ adapter
 */
const fetch = global.fetch;
const config = require('../../config/config');

async function generate(prompt, opts = {}) {
    const apiKey = config.GROQ_API_KEY || process.env.GROQ_API_KEY || '';
    const apiUrl = opts.url || config.GROQ_API_URL || process.env.GROQ_API_URL || 'https://api.groq.com/openai/v1/chat/completions';
    if (!apiKey || !apiUrl) {
        console.warn('groqService not configured: missing apiKey or apiUrl', { hasKey: !!apiKey, apiUrl });
        return { text: 'GROQ not configured', raw: null };
    }
    // Decide which payload shape to send:
    // - OpenAI-compatible chat completions: { model, messages: [...] }
    // - Legacy/generic generate: { prompt, max_tokens }
    const forceOpenAI = opts.useOpenAICompat || (process.env.GROQ_USE_OPENAI_COMPAT === 'true');
    const looksOpenAI = /openai|chat|completions/i.test(apiUrl || '');
    const useOpenAI = forceOpenAI || looksOpenAI;

    let body;
    if (useOpenAI) {
        body = {
            // Updated model name to a currently supported version
            model: opts.model || 'openai/gpt-oss-120b',
            messages: [{ role: 'user', content: prompt }],
            max_tokens: opts.maxTokens || 200,
        };
        console.debug('groqService: sending OpenAI-style chat payload');
    } else {
        body = { prompt, max_tokens: opts.maxTokens || 200 };
        console.debug('groqService: sending prompt-style payload');
    }
    // retries with exponential backoff
    const retries = Number(process.env.GROQ_RETRIES || opts.retries || 2);
    const timeoutMs = Number(process.env.GROQ_TIMEOUT_MS || opts.timeoutMs || 15_000);
    for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        let timeoutId;
        try {
            if (controller) timeoutId = setTimeout(() => controller.abort(), timeoutMs);
            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
                body: JSON.stringify(body),
                signal: controller ? controller.signal : undefined
            });
            if (!res.ok) {
                const txt = await res.text().catch(() => '<no body>');
                console.error('groqService.generate non-2xx', { status: res.status, body: txt, attempt });
                throw new Error(`GROQ error ${res.status}: ${txt}`);
            }
            const json = await res.json();
            // Parse common response shapes:
            let text = '';
            if (json) {
                if (json.choices && json.choices[0]) {
                    text = json.choices[0].message?.content || json.choices[0].text || '';
                }
                if (!text && Array.isArray(json.output) && json.output[0]) {
                    text = json.output[0].content || json.output[0] || '';
                }
                if (!text && typeof json.output === 'string') {
                    text = json.output;
                }
            }
            return { text, raw: json };
        } catch (err) {
            const isAbort = err && err.name === 'AbortError';
            const msg = err && err.message ? err.message : String(err);
            console.error('groqService.generate error', { message: msg, attempt, isAbort });
            if (attempt < retries) {
                // backoff before retrying
                const backoff = Math.pow(2, attempt) * 1000;
                console.debug(`groqService retrying in ${backoff}ms (attempt ${attempt + 1}/${retries})`);
                await new Promise(r => setTimeout(r, backoff));
                continue;
            }
            return { text: '', raw: { error: msg } };
        } finally {
            if (timeoutId) clearTimeout(timeoutId);
            }
        }
    }

module.exports = { generate };
