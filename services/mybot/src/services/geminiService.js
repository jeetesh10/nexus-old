/**
 * geminiService.js
 *
 * This adapter provides a clean API for interacting with the Gemini model.
 * It handles the API call, error handling, and response parsing.
 * The API endpoint and key should be configured externally.
 */
const fetch = global.fetch;
const config = require('../../config/config');

async function generate(prompt, opts = {}) {
    // Correctly get API key from config or environment variables
    const apiKey = config.GEMINI_API_KEY || process.env.GEMINI_API_KEY;
    if (!apiKey) {
        console.warn('Gemini API key not configured.');
        return { text: 'Gemini service not configured.', raw: { error: 'missing_api_key' } };
    }

    // Use the official Gemini API endpoint
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${apiKey}`;
    
    const payload = {
        contents: [{ parts: [{ text: prompt }] }],
    };

    const retries = Number(process.env.GEMINI_RETRIES || opts.retries || 2);
    const timeoutMs = Number(process.env.GEMINI_TIMEOUT_MS || opts.timeoutMs || 15000);

    for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        let timeoutId;
        try {
            if (controller) timeoutId = setTimeout(() => controller.abort(), timeoutMs);

            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller ? controller.signal : undefined
            });

            if (!res.ok) {
                const txt = await res.text().catch(() => '<no body>');
                console.error(`Gemini generate non-2xx status: ${res.status}, body: ${txt}, attempt: ${attempt}`);
                if (res.status >= 500 && attempt < retries) {
                    const backoff = Math.pow(2, attempt) * 1000;
                    console.debug(`Gemini retrying in ${backoff}ms (attempt ${attempt + 1}/${retries})`);
                    await new Promise(r => setTimeout(r, backoff));
                    continue;
                }
                throw new Error(`Gemini API error ${res.status}: ${txt}`);
            }

            const json = await res.json();
            const aiText = json?.candidates?.[0]?.content?.parts?.[0]?.text || '';
            
            return { text: aiText, raw: json };
        } catch (err) {
            const isAbort = err && err.name === 'AbortError';
            const msg = err && err.message ? err.message : String(err);
            console.error(`Gemini generate error: ${msg}, attempt: ${attempt}, isAbort: ${isAbort}`);

            if (attempt < retries) {
                const backoff = Math.pow(2, attempt) * 1000;
                console.debug(`Gemini retry after error in ${backoff}ms (attempt ${attempt + 1}/${retries})`);
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
