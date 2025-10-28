// summarizationChain.js
// Calls the orchestrator to get a summary.

const orchestrator = require('../services/llmOrchestrator');

const debug = process.env.DEBUG === 'true';

async function summarizeDocument(text) {
  if (debug) console.log('[summarizationChain] Entering summarizeDocument', { textLength: text?.length });
  // Validate input
  if (typeof text !== 'string' || !text.trim()) {
    if (debug) console.log('[summarizationChain] Invalid text, returning warning');
    return { summary: '', warning: 'Invalid or empty input text' };
  }
  
  // Use the orchestrator to generate a summary.
  const prompt = `Summarize the following text in 3 sentences:\n\n${text}`;
  if (debug) console.log('[summarizationChain] Constructed prompt', { prompt });
  const response = await orchestrator.orchestrateConversation(prompt, { maxTokens: 120 });
  if (debug) console.log('[summarizationChain] Received response', { response });
  
  // Access the correct field from the response structure
  const summaryText = response?.orchestration?.final || response?.reply || '';
  if (debug) console.log('[summarizationChain] Extracted summaryText', { summaryText });
  
  // Return the final, sanitized text from the orchestrator's response.
  return { summary: summaryText, raw: response };
}

module.exports = { summarizeDocument };