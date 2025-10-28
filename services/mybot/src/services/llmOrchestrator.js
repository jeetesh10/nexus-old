/**
 * llmOrchestrator.js
 *
 * This module is the central orchestrator for the bot.
 * It is designed to be clean and modular, delegating complex
 * logic to other services.
 */

const { v4: uuidv4 } = require('uuid'); // For generating session IDs if missing
const adapterRegistry = require('./adapterRegistry');
const mongoService = require('./mongoService');
const config = require('../../config/config');
const {
    sanitizeFinalText,
    extractSuggestedReply,
    normalizeText,
    similarity
} = require('./orchestrationUtils');

const { personaOrchestrator } = require('./personaOrchestrator');

const debug = process.env.DEBUG === 'true';

/**
 * Runs a simple, standard LLM conversation flow without personas.
 * @param {string} prompt - The user's input.
 * @param {object} opts - Orchestration options.
 * @returns {Promise<object>} The final response object.
 */
async function runStandardConversation(prompt, opts) {
    if (debug) console.log('[llmOrchestrator] Entering runStandardConversation', { prompt, opts });
    
    let sessionId = opts.sessionId;
    
    // Validate inputs
    if (typeof prompt !== 'string' || !prompt.trim()) {
        if (debug) console.log('[llmOrchestrator] Invalid prompt', { prompt });
        return { 
            reply: 'Invalid or empty prompt provided.', 
            sessionId: null, 
            status: 'error',
            orchestration: {}
        };
    }
    if (!sessionId || typeof sessionId !== 'string') {
        sessionId = uuidv4();
        if (debug) console.log('[llmOrchestrator] Generated new sessionId', { sessionId });
    }
    
    try {
        if (debug) console.log('[llmOrchestrator] Fetching conversation from mongo', { sessionId });
        const conversation = await mongoService.getConversation(sessionId) || { steps: [] };
        if (debug) console.log('[llmOrchestrator] Retrieved conversation', { conversation });
        
        // Make prompt configurable if needed; fallback to hardcoded for now
        let llmPrompt = config.llmPromptTemplate || `Please answer the following question. User prompt: "${prompt}"`;
        if (debug) console.log('[llmOrchestrator] Constructed llmPrompt', { llmPrompt });
        
        if (debug) console.log('[llmOrchestrator] Loading primary adapter', { primary: config.LLM_ROLE_MAP?.primary || opts.roleMap?.split(',')[0]?.split(':')[1] });
        const primarySvc = adapterRegistry.loadAdapter(config.LLM_ROLE_MAP.primary || opts.roleMap?.split(',')[0]?.split(':')[1]);
        if (!primarySvc || typeof primarySvc.generate !== 'function') {
            const message = `Primary LLM service '${config.LLM_ROLE_MAP.primary || opts.roleMap?.split(',')[0]?.split(':')[1]}' not found or not usable. Check config.LLM_ROLE_MAP.primary or opts.roleMap.`;
            console.error('[llmOrchestrator] Adapter load error:', message);
            return { 
                reply: 'Sorry, the configured assistant is not available right now.', 
                sessionId, 
                status: 'error',
                orchestration: {}
            };
        }
        if (debug) console.log('[llmOrchestrator] Primary adapter loaded successfully');
        
        if (debug) console.log('[llmOrchestrator] Generating LLM reply', { maxTokens: opts.maxTokensInitial || 200 });
        const initialReply = await primarySvc.generate(llmPrompt, { maxTokens: opts.maxTokensInitial || 200 });
        if (debug) console.log('[llmOrchestrator] Received initialReply', { text: initialReply?.text });

        // Update steps with new interaction
        const newStep = { prompt, reply: initialReply.text, timestamp: new Date() };
        conversation.steps.push(newStep);
        if (debug) console.log('[llmOrchestrator] Updated conversation steps', { steps: conversation.steps });

        const finalResponse = {
            reply: sanitizeFinalText(initialReply.text), // Use sanitizeFinalText
            sessionId,
            steps: conversation.steps,
            status: 'complete',
            orchestration: {
                final: initialReply.text,
                raw: initialReply // Add raw data for debugging
            }
        };
        if (debug) console.log('[llmOrchestrator] Saving conversation to mongo', { finalResponse });
        await mongoService.saveConversation(sessionId, finalResponse);
        if (debug) console.log('[llmOrchestrator] Conversation saved successfully');
        
        if (debug) console.log('[llmOrchestrator] Returning finalResponse', { finalResponse });
        return finalResponse;

    } catch (error) {
        console.error('[llmOrchestrator] Standard Orchestration error:', { message: error.message, stack: error.stack });
        return {
            reply: "I'm sorry, I encountered an error while processing your request.",
            sessionId,
            status: 'error',
            orchestration: {}
        };
    }
}

// Main orchestration function.
// This function is the entry point for all incoming user prompts.
async function orchestrateConversation(prompt, opts = {}) {
    if (debug) console.log('[llmOrchestrator] Entering orchestrateConversation', { prompt, opts });
    
    let sessionId = opts.sessionId;
    
    // Validate inputs
    if (typeof prompt !== 'string' || !prompt.trim()) {
        if (debug) console.log('[llmOrchestrator] Invalid prompt in orchestrateConversation', { prompt });
        return { 
            reply: 'Invalid or empty prompt provided.', 
            sessionId: null, 
            status: 'error',
            orchestration: {}
        };
    }
    if (!sessionId || typeof sessionId !== 'string') {
        sessionId = uuidv4();
        if (debug) console.log('[llmOrchestrator] Generated new sessionId in orchestrateConversation', { sessionId });
    }
    
    // Step 1: Check for and handle persona-based projects.
    if (debug) console.log('[llmOrchestrator] Calling personaOrchestrator');
    const personaResult = await personaOrchestrator(prompt, opts, sessionId, runStandardConversation);
    if (personaResult !== null) {
        if (debug) console.log('[llmOrchestrator] Persona result returned', { personaResult });
        return personaResult;
    }

    // Step 2: If it's not a persona-based project, run the standard conversation flow.
    if (debug) console.log('[llmOrchestrator] Falling back to runStandardConversation');
    const standardResult = await runStandardConversation(prompt, { ...opts, sessionId });
    if (debug) console.log('[llmOrchestrator] Standard result', { standardResult });
    return standardResult;
}

module.exports = { orchestrateConversation };