// vectorDbService.js
// Minimal vector DB stub. Replace with actual Chroma/Pinecone adapter.

async function addDocument(id, embedding, meta) {
  // stub
  return { ok: true, id };
}

async function similaritySearch(query, opts = {}) {
  // stub returns empty hits for now
  return [];
}

module.exports = { addDocument, similaritySearch };
