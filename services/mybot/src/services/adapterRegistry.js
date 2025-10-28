const path = require('path');
const serviceCache = {};

const debug = process.env.DEBUG === 'true';

// Centralized adapter loader and registry.
// Purpose: single responsibility for locating/validating adapters by name,
// caching loaded modules, and providing discovery helpers.
function loadAdapter(name) {
  if (debug) console.log('[adapterRegistry] Entering loadAdapter', { name });
  if (!name || typeof name !== 'string') {
    if (debug) console.log('[adapterRegistry] Invalid name, returning null');
    return null;
  }
  if (serviceCache[name]) {
    if (debug) console.log('[adapterRegistry] Cache hit for', { name });
    return serviceCache[name];
  }
  
  const candidates = [
    `./${name}Service`,
    `./${name}`
  ];
  
  const logDebug = debug ? (console.debug || console.log) : () => {};
  
  logDebug(`[adapterRegistry] Loading adapter '${name}', candidates: ${candidates.join(',')}`);
  
  for (const cand of candidates) {
    try {
      logDebug(`[adapterRegistry] Attempting require ${path.join(__dirname, cand)}`);
      const mod = require(path.join(__dirname, cand));
      if (mod) { 
        serviceCache[name] = mod; 
        if (debug) console.log('[adapterRegistry] Loaded and cached', { name, modKeys: Object.keys(mod) });
        return mod; 
      }
    } catch (e) {
      if (debug) {
        console.warn(`[adapterRegistry] Require failed for ${cand}:`, { message: e.message, stack: e.stack });
      }
      // ignore and continue
    }
  }
  if (debug) console.log('[adapterRegistry] No adapter found for', { name });
  return null;
}

function listCachedAdapterNames() {
  if (debug) console.log('[adapterRegistry] Listing cached adapters', { cached: Object.keys(serviceCache) });
  return Object.keys(serviceCache);
}

// Optional: Function to clear cache (e.g., for testing or reload)
function clearCache() {
  if (debug) console.log('[adapterRegistry] Clearing cache', { before: Object.keys(serviceCache) });
  Object.keys(serviceCache).forEach(key => delete serviceCache[key]);
  if (debug) console.log('[adapterRegistry] Cache cleared');
}

module.exports = { loadAdapter, listCachedAdapterNames, clearCache };