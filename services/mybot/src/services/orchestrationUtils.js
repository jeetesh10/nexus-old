/**
 * orchestrationUtils.js
 *
 * This module provides a set of utility functions for the LLM orchestration process.
 */

const debug = process.env.DEBUG === 'true';

/**
 * Generic check for a task completion marker in the LLM's output.
 * @param {string} text - The LLM's output.
 * @param {string} completionCriteria - The marker string to check for.
 * @returns {boolean} True if the marker is present.
 */
function isTaskComplete(text, completionCriteria) {
    if (debug) console.log('[orchestrationUtils] Entering isTaskComplete', { textLength: text?.length, completionCriteria });
    if (typeof text !== 'string' || !completionCriteria) {
        if (debug) console.log('[orchestrationUtils] Invalid inputs, returning false');
        return false;
    }
    const isComplete = text.includes(completionCriteria);
    if (debug) console.log('[orchestrationUtils] Task complete check result', { isComplete });
    return isComplete;
}

/**
 * Sanitizes the final reply text, removing any internal markers.
 * @param {string} text - The text to sanitize.
 * @returns {string} The sanitized text.
 */
function sanitizeFinalText(text) {
    if (debug) console.log('[orchestrationUtils] Entering sanitizeFinalText', { textLength: text?.length });
    if (typeof text !== 'string') {
        if (debug) console.log('[orchestrationUtils] Invalid text, returning empty string');
        return '';
    }
    const markers = [
        '###Question###',
        '###Answer###',
        '###REQUIREMENTS_GATHERED###',
        '###BRD_CREATED###',
        '###BRD_REVIEWED###'
    ];
    let sanitized = text;
    for (const marker of markers) {
        sanitized = sanitized.replace(new RegExp(marker, 'g'), '');
    }
    sanitized = sanitized.trim();
    if (debug) console.log('[orchestrationUtils] Sanitized text', { sanitizedLength: sanitized.length });
    return sanitized;
}

/**
 * Extracts a suggested reply from a reviewer model's output.
 * @param {string} text - The reviewer's output.
 * @returns {string} The suggested reply.
 */
function extractSuggestedReply(text) {
    if (debug) console.log('[orchestrationUtils] Entering extractSuggestedReply', { textLength: text?.length });
    const parts = text.split('Suggested Reply:');
    const reply = parts.length > 1 ? parts[1].trim() : text;
    if (debug) console.log('[orchestrationUtils] Extracted reply', { reply });
    return reply;
}

/**
 * Normalizes text for similarity comparison.
 * @param {string} text - The text to normalize.
 * @returns {string} The normalized text.
 */
function normalizeText(text) {
    if (debug) console.log('[orchestrationUtils] Entering normalizeText', { textLength: text?.length });
    const normalized = text.toLowerCase().replace(/[^a-z0-9\s]/g, '');
    if (debug) console.log('[orchestrationUtils] Normalized text', { normalized });
    return normalized;
}

/**
 * Calculates a simple similarity score between two texts.
 * @param {string} text1 - The first text.
 * @param {string} text2 - The second text.
 * @returns {number} The similarity score (0 to 1).
 */
function similarity(text1, text2) {
    if (debug) console.log('[orchestrationUtils] Entering similarity', { text1Length: text1?.length, text2Length: text2?.length });
    const nText1 = normalizeText(text1);
    const nText2 = normalizeText(text2);
    const words1 = new Set(nText1.split(/\s+/));
    const words2 = new Set(nText2.split(/\s+/));
    const intersection = new Set([...words1].filter(x => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    const score = intersection.size / union.size;
    if (debug) console.log('[orchestrationUtils] Similarity score', { score });
    return score;
}


module.exports = {
    isTaskComplete,
    sanitizeFinalText,
    extractSuggestedReply,
    normalizeText,
    similarity
};