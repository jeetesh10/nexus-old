// src/chains/index.js
const { handleGreeting } = require('./greetingChain');
const { summarizeDocument } = require('./summarizationChain');

module.exports = {
  handleGreeting,
  summarizeDocument
};