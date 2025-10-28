// greetingChain.js
// Simple greeting chain handler

function handleGreeting(userName) {
  const name = userName || 'there';
  return {
    reply: `Hello, ${name}! How can I help you today?`,
    timestamp: new Date().toISOString()
  };
}

module.exports = { handleGreeting };
