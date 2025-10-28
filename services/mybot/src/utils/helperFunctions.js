// helperFunctions.js

function safeString(s) {
  if (!s && s !== 0) return '';
  return String(s);
}

function nowIso() {
  return new Date().toISOString();
}

module.exports = { safeString, nowIso };
