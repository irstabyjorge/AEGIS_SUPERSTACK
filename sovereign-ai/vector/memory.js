// Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
// AEGIS Sovereign AI — Vector Layer (Persistent Memory)
// SQLite-backed memory with semantic tagging, decay scoring, and auto-consolidation.

const Database = require('better-sqlite3')
const path = require('path')

const DB_PATH = path.join(__dirname, 'memory.db')
const db = new Database(DB_PATH)

db.pragma('journal_mode = WAL')

db.exec(`
  CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    type TEXT NOT NULL,
    source TEXT DEFAULT 'system',
    priority INTEGER DEFAULT 5,
    data TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    accessed INTEGER DEFAULT 0,
    decay_score REAL DEFAULT 1.0
  );

  CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    UNIQUE(category, key)
  );

  CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT DEFAULT '{}'
  );

  CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);
  CREATE INDEX IF NOT EXISTS idx_memory_ts ON memory(timestamp);
  CREATE INDEX IF NOT EXISTS idx_knowledge_cat ON knowledge(category);
`)

function writeMemory(event) {
  const stmt = db.prepare(`
    INSERT INTO memory (timestamp, type, source, priority, data, tags)
    VALUES (?, ?, ?, ?, ?, ?)
  `)
  return stmt.run(
    Date.now(),
    event.type || 'unknown',
    event.source || 'system',
    event.priority || 5,
    JSON.stringify(event.data || event),
    JSON.stringify(event.tags || [])
  )
}

function readMemory(limit = 20, type = null) {
  if (type) {
    return db.prepare(`
      SELECT * FROM memory WHERE type = ? ORDER BY timestamp DESC LIMIT ?
    `).all(type, limit)
  }
  return db.prepare(`
    SELECT * FROM memory ORDER BY timestamp DESC LIMIT ?
  `).all(limit)
}

function searchMemory(query, limit = 10) {
  return db.prepare(`
    SELECT * FROM memory WHERE data LIKE ? ORDER BY timestamp DESC LIMIT ?
  `).all(`%${query}%`, limit)
}

function learn(category, key, value, confidence = 1.0) {
  db.prepare(`
    INSERT INTO knowledge (timestamp, category, key, value, confidence)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(category, key) DO UPDATE SET
      value = excluded.value,
      confidence = excluded.confidence,
      timestamp = excluded.timestamp
  `).run(Date.now(), category, key, JSON.stringify(value), confidence)
}

function recall(category, key = null) {
  if (key) {
    const row = db.prepare(`
      SELECT * FROM knowledge WHERE category = ? AND key = ?
    `).get(category, key)
    if (row) row.value = JSON.parse(row.value)
    return row
  }
  return db.prepare(`
    SELECT * FROM knowledge WHERE category = ? ORDER BY timestamp DESC
  `).all(category).map(r => ({ ...r, value: JSON.parse(r.value) }))
}

function saveConversation(role, content, context = {}) {
  db.prepare(`
    INSERT INTO conversations (timestamp, role, content, context)
    VALUES (?, ?, ?, ?)
  `).run(Date.now(), role, content, JSON.stringify(context))
}

function getConversations(limit = 20) {
  return db.prepare(`
    SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?
  `).all(limit).reverse()
}

function getStats() {
  const memories = db.prepare('SELECT COUNT(*) as count FROM memory').get()
  const knowledge = db.prepare('SELECT COUNT(*) as count FROM knowledge').get()
  const conversations = db.prepare('SELECT COUNT(*) as count FROM conversations').get()
  const types = db.prepare('SELECT type, COUNT(*) as count FROM memory GROUP BY type ORDER BY count DESC').all()
  return {
    total_memories: memories.count,
    total_knowledge: knowledge.count,
    total_conversations: conversations.count,
    memory_types: types,
  }
}

function decayMemories() {
  db.prepare(`
    UPDATE memory SET decay_score = decay_score * 0.99
    WHERE decay_score > 0.01 AND timestamp < ?
  `).run(Date.now() - 86400000) // older than 24h
}

module.exports = {
  writeMemory, readMemory, searchMemory,
  learn, recall,
  saveConversation, getConversations,
  getStats, decayMemories,
  db
}
