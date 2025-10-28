/**
 * personaOrchestrator.js
 *
 * This module handles the complete persona-based, task-driven workflow.
 * It is called by the main llmOrchestrator when a project is detected.
 */

const mongoService = require('./mongoService');
const googleDriveService = require('./googleDriveService');
const { isTaskComplete, sanitizeFinalText } = require('./orchestrationUtils');

const debug = process.env.DEBUG === 'true';

/**
 * Finds a project goal from the database based on the user's prompt.
 * @param {string} prompt - The user's prompt.
 * @returns {Promise<object|null>} The project goal if found, otherwise null.
 */
async function findProjectGoal(prompt) {
    if (debug) console.log('[personaOrchestrator] Entering findProjectGoal', { prompt });
    const goals = await mongoService.getGoals();
    if (debug) console.log('[personaOrchestrator] Retrieved goals', { goalsLength: goals.length });
    if (typeof prompt === 'string') {
        const lowerPrompt = prompt.toLowerCase();
        if (lowerPrompt.includes('software development') || lowerPrompt.includes('build this app') || lowerPrompt.includes('create an app') || lowerPrompt.includes('start a project')) {
            const goal = goals.find(g => g.projectId === 'software-development-101');
            if (debug) console.log('[personaOrchestrator] Found project goal', { goal });
            return goal;
        }
    }
    if (debug) console.log('[personaOrchestrator] No project goal found');
    return null;
}

/**
 * Main orchestrator for the persona-based flow.
 * @param {string} prompt - The user's initial prompt.
 * @param {object} opts - Orchestration options.
 * @param {string} sessionId - The session ID for state management.
 * @param {function} runStandardOrchestration - The function to call for the standard LLM orchestration.
 * @returns {Promise<object|null>} The final response for the user if it's a project, otherwise null.
 */
async function personaOrchestrator(prompt, opts = {}, sessionId, runStandardOrchestration) {
    if (debug) console.log('[personaOrchestrator] Entering personaOrchestrator', { prompt, opts, sessionId });
    
    // Validate inputs
    if (typeof prompt !== 'string' || !prompt.trim()) {
        if (debug) console.log('[personaOrchestrator] Invalid prompt');
        return { 
            reply: 'Invalid or empty prompt provided.', 
            sessionId: null, 
            status: 'error',
            orchestration: {}
        };
    }
    if (!sessionId || typeof sessionId !== 'string') {
        if (debug) console.log('[personaOrchestrator] Invalid sessionId');
        return { 
            reply: 'Invalid session ID.', 
            sessionId: null, 
            status: 'error',
            orchestration: {}
        };
    }
    
    try {
        const userText = prompt;
        
        // 1. Check for an existing project in the database
        if (debug) console.log('[personaOrchestrator] Fetching project from mongo', { sessionId });
        let project = await mongoService.getProject(sessionId);
        if (debug) console.log('[personaOrchestrator] Retrieved project', { project });
        let projectGoal = null;

        if (!project) {
            if (debug) console.log('[personaOrchestrator] No existing project, finding project goal');
            projectGoal = await findProjectGoal(userText);
            if (projectGoal) {
                // Validate projectGoal structure
                if (!projectGoal || !Array.isArray(projectGoal.personas) || projectGoal.personas.length === 0) {
                    if (debug) console.log('[personaOrchestrator] Invalid projectGoal structure', { projectGoal });
                    return { 
                        reply: 'Invalid project goal configuration.', 
                        sessionId, 
                        status: 'error',
                        orchestration: {}
                    };
                }
                
                // New project detected. Initialize state and return a confirmation message.
                if (debug) console.log('[personaOrchestrator] Creating new project', { projectData: { projectId: projectGoal.projectId, projectName: projectGoal.projectName } });
                project = await mongoService.createProject(sessionId, {
                    projectId: projectGoal.projectId,
                    projectName: projectGoal.projectName,
                    userInitialPrompt: userText,
                    currentPersonaIndex: 0,
                    currentTaskIndex: 0,
                    context: [] // Initialize as array for better management
                });
                if (debug) console.log('[personaOrchestrator] New project created', { project });
                
                const initialPersona = projectGoal.personas[project.currentPersonaIndex];
                const reply = `Starting the "${project.projectName}" project. I'm handing this over to the ${initialPersona.name}.`;
                if (debug) console.log('[personaOrchestrator] Returning initial reply for new project', { reply });
                return { reply, sessionId, status: 'continue', orchestration: {} };
            } else {
                // No project detected, fall back to standard chat.
                if (debug) console.log('[personaOrchestrator] No project detected, returning null');
                return null;
            }
        }
        
        // Project exists, continue the flow.
        if (debug) console.log('[personaOrchestrator] Fetching projectGoal', { projectId: project.projectId });
        projectGoal = await mongoService.getProjectGoal(project.projectId);
        if (debug) console.log('[personaOrchestrator] Retrieved projectGoal', { projectGoal });
        if (!projectGoal || !Array.isArray(projectGoal.personas) || projectGoal.personas.length === 0) {
            if (debug) console.log('[personaOrchestrator] Invalid projectGoal');
            return { 
                reply: 'Invalid project goal configuration.', 
                sessionId, 
                status: 'error',
                orchestration: {}
            };
        }
        
        const currentPersona = projectGoal.personas[project.currentPersonaIndex];
        if (!currentPersona || !Array.isArray(currentPersona.tasks) || currentPersona.tasks.length === 0) {
            if (debug) console.log('[personaOrchestrator] Invalid currentPersona or tasks', { currentPersonaIndex: project.currentPersonaIndex });
            return { 
                reply: 'Invalid persona or task configuration.', 
                sessionId, 
                status: 'error',
                orchestration: {}
            };
        }
        const currentTask = currentPersona.tasks[project.currentTaskIndex];
        if (debug) console.log('[personaOrchestrator] Current task', { currentTaskName: currentTask.name, currentTaskIndex: project.currentTaskIndex });

        // 2. Build the LLM prompt for the current task
        const llmPrompt = `Project Goal: ${project.projectName}\nCurrent Persona: ${currentPersona.name}\nTask: ${currentTask.name}\n\n${currentTask.prompt}\n\nPrevious Conversation:\n${(project.context || []).map(c => `${c.user ? `User: ${c.user}` : ''}\n${c.ai ? `AI: ${c.ai}` : ''}`).join('\n')}\n\nUser Input: ${userText}`;
        if (debug) console.log('[personaOrchestrator] Constructed llmPrompt', { llmPrompt });
        
        // 3. Run the core orchestration loop
        if (debug) console.log('[personaOrchestrator] Calling runStandardOrchestration');
        const orchestrationResult = await runStandardOrchestration(llmPrompt, opts);
        if (debug) console.log('[personaOrchestrator] Received orchestrationResult', { orchestrationResult });
        if (orchestrationResult.status === 'error') {
            if (debug) console.log('[personaOrchestrator] Orchestration error, returning result');
            return orchestrationResult;
        }
        const finalReply = sanitizeFinalText(orchestrationResult.orchestration?.final || orchestrationResult.reply || '');
        if (debug) console.log('[personaOrchestrator] Sanitized finalReply', { finalReply });

        // 4. Update the project state based on the LLM's reply and task completion.
        let newStatus = 'continue';
        let updatedReply = finalReply;
        
        if (debug) console.log('[personaOrchestrator] Checking task completion', { completionCriteria: currentTask.completionCriteria });
        if (isTaskComplete(finalReply, currentTask.completionCriteria)) {
            if (debug) console.log('[personaOrchestrator] Task complete');
            if (currentTask.outputFilename) {
                const documentContent = finalReply.split(currentTask.completionCriteria)[0].trim();
                if (debug) console.log('[personaOrchestrator] Uploading document to Google Drive', { outputFilename: currentTask.outputFilename });
                await googleDriveService.uploadDocument(project.projectName, currentTask.outputFilename, documentContent);
                if (debug) console.log('[personaOrchestrator] Document uploaded');
            }

            let nextPersonaIndex = project.currentPersonaIndex;
            let nextTaskIndex = project.currentTaskIndex + 1;

            if (nextTaskIndex >= currentPersona.tasks.length) {
                nextTaskIndex = 0;
                nextPersonaIndex++;
                if (nextPersonaIndex >= projectGoal.personas.length) {
                    newStatus = 'complete';
                    updatedReply = `The project "${project.projectName}" is now complete.`;
                    if (debug) console.log('[personaOrchestrator] Project complete');
                } else {
                    const nextPersona = projectGoal.personas[nextPersonaIndex];
                    updatedReply = `${finalReply}\n\nTask complete. Now handing over to the next persona: ${nextPersona.name}.`;
                    if (debug) console.log('[personaOrchestrator] Handing over to next persona', { nextPersona: nextPersona.name });
                }
            } else {
                const nextTask = currentPersona.tasks[nextTaskIndex];
                updatedReply = `${finalReply}\n\nTask complete. Now starting the next task: ${nextTask.name}.`;
                if (debug) console.log('[personaOrchestrator] Starting next task', { nextTask: nextTask.name });
            }

            if (debug) console.log('[personaOrchestrator] Updating project state', { nextPersonaIndex, nextTaskIndex, newStatus });
            await mongoService.updateProject(sessionId, {
                currentPersonaIndex: nextPersonaIndex,
                currentTaskIndex: nextTaskIndex,
                status: newStatus
            });
            if (debug) console.log('[personaOrchestrator] Project state updated');
        }
        
        // Update context as array of interactions
        const newInteraction = { user: userText, ai: finalReply, timestamp: new Date() };
        const updatedContext = [...(project.context || []), newInteraction];
        if (debug) console.log('[personaOrchestrator] Updating project context', { updatedContextLength: updatedContext.length });
        await mongoService.updateProject(sessionId, { context: updatedContext });
        if (debug) console.log('[personaOrchestrator] Context updated');

        const finalResult = {
            reply: updatedReply,
            sessionId,
            status: newStatus,
            orchestration: orchestrationResult
        };
        if (debug) console.log('[personaOrchestrator] Exiting with success', { finalResult });
        return finalResult;

    } catch (error) {
        console.error('[personaOrchestrator] Persona Orchestration error:', { message: error.message, stack: error.stack });
        return {
            reply: "I'm sorry, I encountered an error in the project flow.",
            sessionId,
            status: 'error',
            orchestration: {}
        };
    }
}

module.exports = {
    personaOrchestrator
};