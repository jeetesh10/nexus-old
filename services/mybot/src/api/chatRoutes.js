// src/api/chatRoutes.js
const express = require('express');
const router = express.Router();
const chains = require('../chains');
const vectorDb = require('../services/vectorDbService');
const mongo = require('../services/mongoService');
const orchestrator = require('../services/llmOrchestrator');
const mongoService = require('../services/mongoService');
const fs = require('fs');
const path = require('path');
const config = require('../../config/config');

// POST /intent -> detect user intent and return project, persona, and initial task
router.post('/intent', async (req, res) => {
  const { text, userId, appId } = req.body || {};
  if (!text) return res.status(400).json({ error: 'no_text' });

  try {
    const projects = await mongoService.getCollection('projects');
    // Improved intent detection based on keywords (expandable)
    let projectId = null;
    let persona = null;
    let task = { index: 0 };

    if (text.toLowerCase().includes('create an app') || text.toLowerCase().includes('build an app') || text.toLowerCase().includes('develop an app') || text.toLowerCase().includes('software development')) {
      projectId = 'software-development-101';
      persona = 'Analyst';
    } else if (text.toLowerCase().includes('analysis') || text.toLowerCase().includes('analyze')) {
      projectId = 'analysis-project'; // Add if needed
      persona = 'Analyst';
    } // Add more intent patterns as needed

    if (!projectId || !persona) {
      // Fallback to normal conversation
      return res.json({ projectId: null, persona: null, task: null });
    }

    const project = await projects.findOne({ projectId });
    if (project && project.personas) {
      const selectedPersona = project.personas.find(p => p.name === persona);
      if (selectedPersona && selectedPersona.tasks && selectedPersona.tasks.length > 0) {
        task = { index: 0, taskId: selectedPersona.tasks[0].taskId };
      }
    }

    return res.json({ projectId, persona, task });
  } catch (err) {
    console.error('intent error', err);
    return res.status(500).json({ error: 'internal_server_error', detail: err.message });
  }
});

// POST /project -> fetch project data with filtered personas
router.post('/project', async (req, res) => {
  const { projectId, persona } = req.body || {};
  if (!projectId) return res.status(400).json({ error: 'no_projectId' });

  try {
    const projects = await mongoService.getCollection('projects');
    const project = await projects.findOne({ projectId });
    if (!project || !project.personas) {
      return res.status(404).json({ error: 'project_not_found' });
    }
    const filteredPersonas = persona ? project.personas.filter(p => p.name === persona) : project.personas;
    return res.json({ ...project, personas: filteredPersonas });
  } catch (err) {
    console.error('project error', err);
    return res.status(500).json({ error: 'internal_server_error', detail: err.message });
  }
});

// POST /chat -> basic router that can dispatch to different chains
router.post('/chat', async (req, res) => {
  const { type, input, user } = req.body || {};
  try {
    if (type === 'greeting') {
      const result = chains.handleGreeting(user?.name);
      return res.json(result);
    }
    if (type === 'summarize') {
      const docs = input?.text;
      const result = await chains.summarizeDocument(docs);
      return res.json(result);
    }
    const hits = input?.query ? await vectorDb.similaritySearch(input.query, { topK: 3 }) : [];
    return res.json({ echo: input, retrieval: hits });
  } catch (err) {
    console.error('chat error', err);
    return res.status(500).json({ error: 'internal_server_error', detail: err.message });
  }
});

// POST /messages -> save a user message, generate AI reply, save reply, and return both
router.post('/messages', async (req, res) => {
  console.log('[chatRoutes] Entering /messages POST');
  const { appId = 'default-app-id', conversationId = null, text, userId = 'anonymous', conversationTitle = null, persona, goal, taskId, prompt, taskIndex } = req.body || {};
  if (!text && !prompt) return res.status(400).json({ error: 'no_text_or_prompt' });
  try {
    console.log('[chatRoutes] Saving user message', { appId, conversationId, text, userId, persona, goal, taskId, taskIndex });
    const convId = conversationId || `${appId}:${new Date().toISOString()}`;
    if (conversationTitle) {
      console.log('[chatRoutes] Saving conversation title', { conversationTitle });
      try { await mongo.saveConversation({ appId, conversationId: convId, title: conversationTitle }); } catch(_) {}
    }
    const userMsg = await mongo.saveMessage({ appId, conversationId: convId, text, userId, role: 'user' });

    console.log('[chatRoutes] Calling orchestrateConversation with persona, goal, and task', { persona, goal, taskId, taskIndex });
    const orchestrationResult = await (async () => {
      try {
        const persisted = await mongoService.getSetting('LLM_ROLE_MAP');
        const roleMap = persisted || undefined;
        const personaOrchestrator = require('../services/personaOrchestrator');
        const enhancedPrompt = prompt || personaOrchestrator.applyPersona(`${goal}: ${text}`, persona);
        const r = await orchestrator.orchestrateConversation(enhancedPrompt, { maxTokensInitial: 200, roleMap });
        console.log('[chatRoutes] Orchestrator final reply (truncated):', (r.reply || '').slice(0, 200));
        return r;
      } catch (err) {
        console.warn('[chatRoutes] Orchestrator failed', err && err.message);
        return { reply: `Sorry, I could not ${goal}.`, orchestration: { raw: {}, candidates: { primary: `Sorry, I could not ${goal}.` }, chosen: 'primary', steps: [] } };
      }
    })();

    console.log('[chatRoutes] Building orchestrationMeta', { orchestrationResult });
    const mergedCandidates = Object.assign({}, orchestrationResult.orchestration?.candidates || {});
    const mergedRaw = Object.assign({}, orchestrationResult.orchestration?.raw || {});

    const orchestrationMeta = {
      chosen: orchestrationResult.orchestration?.chosen,
      candidates: mergedCandidates,
      raw: mergedRaw,
      steps: [],
      aligned: orchestrationResult.orchestration?.aligned || false,
      rounds: typeof orchestrationResult.orchestration?.rounds === 'number' ? orchestrationResult.orchestration.rounds : 0,
      reason: orchestrationResult.orchestration?.reason || null,
      taskId,
      taskIndex
    };

    try {
      const primaryText = mergedCandidates.primary || orchestrationResult.reply || null;
      if (primaryText) {
        orchestrationMeta.steps.push({ role: 'primary', svc: orchestrationResult.primarySvc || null, text: primaryText, goal, taskId, taskIndex });
      }
      const modelsCol = await mongoService.getCollection('models');
      if (modelsCol) {
        const modelDocs = await modelsCol.find({ active: true }).sort({ name: 1 }).toArray();
        for (const m of modelDocs) {
          const name = m.name;
          if (!name) continue;
          const ctext = mergedCandidates[name];
          if (ctext) {
            orchestrationMeta.steps.push({ role: 'candidate', svc: name, text: ctext, goal, taskId, taskIndex });
          }
        }
      }
      if (Array.isArray(orchestrationResult.orchestration?.steps) && orchestrationResult.orchestration.steps.length > 0) {
        orchestrationMeta.steps.push(...orchestrationResult.orchestration.steps);
      }
    } catch (e) {
      console.warn('[chatRoutes] Failed to build orchestration steps', e && e.message);
    }

    const chosenText = orchestrationResult.reply || `Sorry, I could not ${goal}.`;
    console.log('[chatRoutes] Saving AI message', { chosenText });
    const aiMsg = await mongo.saveMessage({ appId, conversationId: convId, text: chosenText, userId: 'AI Assistant', role: 'assistant', orchestration: orchestrationMeta });

    try {
      if (Array.isArray(orchestrationMeta.steps)) {
        for (const [i, s] of orchestrationMeta.steps.entries()) {
          const stepRole = s.role === 'reviewer' ? 'assistant-review' : (s.role === 'primary' ? 'assistant-draft' : 'assistant-candidate');
          console.log('[chatRoutes] Saving orchestration step', { stepIndex: i + 1, stepRole, svc: s.svc });
          await mongo.saveMessage({ appId, conversationId: convId, text: s.text, userId: `orchestrator.${s.svc || s.role}`, role: stepRole, meta: { stepIndex: i + 1, svc: s.svc || null }, goal: s.goal, taskId: s.taskId, taskIndex: s.taskIndex });
        }
      }
    } catch (e) {
      console.warn('[chatRoutes] Failed to persist orchestration steps', e && e.message);
    }

    try {
      const candidates = orchestrationMeta.candidates || {};
      for (const [crole, ctext] of Object.entries(candidates)) {
        if (!ctext) continue;
        console.log('[chatRoutes] Saving candidate', { crole });
        await mongo.saveMessage({ appId, conversationId: convId, text: ctext, userId: `orchestrator.candidate.${crole}`, role: 'assistant-candidate', meta: { candidateRole: crole }, goal, taskId, taskIndex });
      }
    } catch (e) {
      console.warn('[chatRoutes] Failed to persist orchestration candidates', e && e.message);
    }

    console.log('[chatRoutes] Exiting /messages with success', { user: userMsg, ai: aiMsg, orchestration: orchestrationMeta });
    return res.json({ user: userMsg, ai: aiMsg, orchestration: orchestrationMeta, taskIndex: currentTaskIndex });
  } catch (err) {
    console.error('messages error', err);
    return res.status(500).json({ error: 'internal_server_error', detail: err.message });
  }
});

// ... other routes

module.exports = router;