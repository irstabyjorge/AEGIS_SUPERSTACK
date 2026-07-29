// Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
// AEGIS Sovereign AI — Economic Layer (Usage Tracking & Billing)
// Tracks API calls, scan usage, resource consumption, and license tiers.

const Database = require('better-sqlite3')
const path = require('path')

const DB_PATH = path.join(__dirname, 'economic.db')
const db = new Database(DB_PATH)

db.pragma('journal_mode = WAL')

db.exec(`
  CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    user_id TEXT DEFAULT 'local',
    action TEXT NOT NULL,
    module TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    cost_units REAL DEFAULT 0.0,
    metadata TEXT DEFAULT '{}'
  );

  CREATE TABLE IF NOT EXISTS quotas (
    user_id TEXT PRIMARY KEY,
    tier TEXT DEFAULT 'free',
    daily_limit INTEGER DEFAULT 100,
    monthly_limit INTEGER DEFAULT 2000,
    api_calls_today INTEGER DEFAULT 0,
    api_calls_month INTEGER DEFAULT 0,
    last_reset_day INTEGER DEFAULT 0,
    last_reset_month INTEGER DEFAULT 0
  );

  CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    period TEXT NOT NULL,
    total_actions INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    tier TEXT DEFAULT 'free',
    status TEXT DEFAULT 'generated'
  );

  CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(timestamp);
  CREATE INDEX IF NOT EXISTS idx_usage_user ON usage(user_id);
  CREATE INDEX IF NOT EXISTS idx_usage_action ON usage(action);
`)

const TIERS = {
  free:       { daily: 100,   monthly: 2000,   cost_per_action: 0 },
  starter:    { daily: 1000,  monthly: 25000,  cost_per_action: 0.001 },
  pro:        { daily: 10000, monthly: 250000, cost_per_action: 0.0005 },
  enterprise: { daily: -1,    monthly: -1,     cost_per_action: 0.0002 },
}

function ensureUser(userId = 'local') {
  const existing = db.prepare('SELECT * FROM quotas WHERE user_id = ?').get(userId)
  if (!existing) {
    db.prepare(`
      INSERT INTO quotas (user_id, tier, daily_limit, monthly_limit)
      VALUES (?, 'free', 100, 2000)
    `).run(userId)
  }
}

function trackUsage(action, module, opts = {}) {
  const userId = opts.userId || 'local'
  const tokens = opts.tokens || 0
  const metadata = opts.metadata || {}

  ensureUser(userId)
  _resetCountersIfNeeded(userId)

  const quota = db.prepare('SELECT * FROM quotas WHERE user_id = ?').get(userId)
  const tierInfo = TIERS[quota.tier] || TIERS.free

  if (tierInfo.daily > 0 && quota.api_calls_today >= tierInfo.daily) {
    return { allowed: false, reason: 'daily_limit_reached', limit: tierInfo.daily }
  }
  if (tierInfo.monthly > 0 && quota.api_calls_month >= tierInfo.monthly) {
    return { allowed: false, reason: 'monthly_limit_reached', limit: tierInfo.monthly }
  }

  const costUnits = tokens * tierInfo.cost_per_action

  db.prepare(`
    INSERT INTO usage (timestamp, user_id, action, module, tokens_used, cost_units, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(Date.now(), userId, action, module, tokens, costUnits, JSON.stringify(metadata))

  db.prepare(`
    UPDATE quotas SET api_calls_today = api_calls_today + 1,
                      api_calls_month = api_calls_month + 1
    WHERE user_id = ?
  `).run(userId)

  return { allowed: true, cost: costUnits, remaining_today: (tierInfo.daily > 0 ? tierInfo.daily - quota.api_calls_today - 1 : -1) }
}

function _resetCountersIfNeeded(userId) {
  const now = new Date()
  const today = now.getDate()
  const month = now.getMonth()

  const quota = db.prepare('SELECT * FROM quotas WHERE user_id = ?').get(userId)
  if (!quota) return

  if (quota.last_reset_day !== today) {
    db.prepare('UPDATE quotas SET api_calls_today = 0, last_reset_day = ? WHERE user_id = ?').run(today, userId)
  }
  if (quota.last_reset_month !== month) {
    db.prepare('UPDATE quotas SET api_calls_month = 0, last_reset_month = ? WHERE user_id = ?').run(month, userId)
  }
}

function setTier(userId, tier) {
  if (!TIERS[tier]) return { error: `Unknown tier: ${tier}` }
  ensureUser(userId)
  const tierInfo = TIERS[tier]
  db.prepare(`
    UPDATE quotas SET tier = ?, daily_limit = ?, monthly_limit = ?
    WHERE user_id = ?
  `).run(tier, tierInfo.daily, tierInfo.monthly, userId)
  return { userId, tier, limits: tierInfo }
}

function getUsageStats(userId = 'local', days = 30) {
  const since = Date.now() - (days * 86400000)
  const rows = db.prepare(`
    SELECT action, module, COUNT(*) as count, SUM(tokens_used) as tokens, SUM(cost_units) as cost
    FROM usage WHERE user_id = ? AND timestamp > ?
    GROUP BY action, module ORDER BY count DESC
  `).all(userId, since)

  const total = db.prepare(`
    SELECT COUNT(*) as actions, SUM(tokens_used) as tokens, SUM(cost_units) as cost
    FROM usage WHERE user_id = ? AND timestamp > ?
  `).get(userId, since)

  const quota = db.prepare('SELECT * FROM quotas WHERE user_id = ?').get(userId)

  return {
    period_days: days,
    total_actions: total.actions,
    total_tokens: total.tokens || 0,
    total_cost: total.cost || 0,
    tier: quota ? quota.tier : 'free',
    breakdown: rows,
    quota: quota || null,
  }
}

function generateInvoice(userId = 'local', periodLabel = null) {
  const now = new Date()
  const period = periodLabel || `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  const stats = getUsageStats(userId, 30)

  const inv = db.prepare(`
    INSERT INTO invoices (timestamp, user_id, period, total_actions, total_tokens, total_cost, tier)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(Date.now(), userId, period, stats.total_actions, stats.total_tokens, stats.total_cost, stats.tier)

  return {
    invoice_id: inv.lastInsertRowid,
    user_id: userId,
    period,
    total_actions: stats.total_actions,
    total_tokens: stats.total_tokens,
    total_cost: stats.total_cost,
    tier: stats.tier,
    status: 'generated',
  }
}

function getInvoices(userId = 'local') {
  return db.prepare('SELECT * FROM invoices WHERE user_id = ? ORDER BY timestamp DESC').all(userId)
}

module.exports = {
  trackUsage,
  setTier,
  getUsageStats,
  generateInvoice,
  getInvoices,
  ensureUser,
  TIERS,
  db,
}
