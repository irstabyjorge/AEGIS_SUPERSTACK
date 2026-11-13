// Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
// AEGIS Sovereign AI — Core System (Orchestration)
// Wires Vector (memory), Matrix (agents), and Economic (billing) into one runtime.

const path = require('path')
const memory = require('../vector/memory')
const { AgentBus, createDefaultAgents } = require('../matrix/agents')
const economic = require('../economic/economic')
const { SacredAtomEngine } = require('../../frameworks/sacred-atom')
const { DivinityEarthCircle } = require('../../frameworks/divinity-earth-circle')

class AegisSovereignSystem {
  constructor(opts = {}) {
    this.version = '1.0.0'
    this.startTime = Date.now()
    this.userId = opts.userId || 'local'

    this.memory = memory
    this.bus = new AgentBus(memory)
    this.economic = economic
    this.sacredAtom = new SacredAtomEngine()
    this.divinityEarthCircle = new DivinityEarthCircle()

    this._registerAgents()
    this._wireEvents()

    economic.ensureUser(this.userId)

    memory.writeMemory({
      type: 'system_boot',
      source: 'core',
      priority: 10,
      data: { version: this.version, userId: this.userId, time: new Date().toISOString() },
      tags: ['core', 'boot'],
    })
  }

  _registerAgents() {
    const agents = createDefaultAgents()
    for (const agent of agents) this.bus.register(agent.name, agent)
  }

  _wireEvents() {
    this.bus.on('event:completed', (event) => {
      this.memory.writeMemory({
        type: 'event_result',
        source: 'matrix',
        priority: event.payload.priority || 5,
        data: {
          eventType: event.type,
          resultCount: event.results.length,
          agents: event.results.map(r => r.agent),
          errors: event.results.filter(r => r.status === 'error').length,
        },
        tags: ['matrix', 'result', event.type],
      })

      this.economic.trackUsage('event_dispatch', event.type, {
        userId: this.userId,
        tokens: 1,
        metadata: { agents: event.results.length },
      })
    })

    this.bus.on('agent:registered', (info) => {
      this.memory.writeMemory({
        type: 'agent_lifecycle',
        source: 'matrix',
        data: { action: 'registered', agent: info.name },
        tags: ['matrix', 'agent', 'lifecycle'],
      })
    })
  }

  async runScan(scanType) {
    const billing = this.economic.trackUsage('scan', scanType, {
      userId: this.userId,
      tokens: 10,
    })
    if (!billing.allowed) return { error: 'quota_exceeded', details: billing }

    const result = await this.bus.dispatch(`scan:${scanType}`, { priority: 8 })
    return {
      scan: scanType,
      agents_invoked: result.results.length,
      results: result.results,
      timestamp: new Date().toISOString(),
    }
  }

  async fullAudit() {
    const billing = this.economic.trackUsage('full_audit', 'all', {
      userId: this.userId,
      tokens: 50,
    })
    if (!billing.allowed) return { error: 'quota_exceeded', details: billing }

    const result = await this.bus.dispatch('scan:full', { priority: 10 })
    this.memory.learn('audit', 'last_full_audit', {
      time: new Date().toISOString(),
      agents: result.results.length,
      errors: result.results.filter(r => r.status === 'error').length,
    })
    return {
      scan: 'full_audit',
      agents_invoked: result.results.length,
      results: result.results,
      timestamp: new Date().toISOString(),
    }
  }

  async checkUptime() { return this.runScan('uptime') }

  remember(category, key, value) {
    this.memory.learn(category, key, value)
    this.economic.trackUsage('learn', 'memory', { userId: this.userId, tokens: 1 })
    return { stored: true, category, key }
  }

  recall(category, key = null) { return this.memory.recall(category, key) }

  chat(role, content, context = {}) {
    this.memory.saveConversation(role, content, context)
    this.economic.trackUsage('chat', 'conversation', {
      userId: this.userId,
      tokens: Math.ceil(content.length / 4),
    })
    return { saved: true, role, length: content.length }
  }

  getHistory(limit = 20) { return this.memory.getConversations(limit) }

  status() {
    const memStats = this.memory.getStats()
    const usageStats = this.economic.getUsageStats(this.userId, 7)
    const uptimeMs = Date.now() - this.startTime
    return {
      version: this.version,
      uptime_seconds: Math.floor(uptimeMs / 1000),
      userId: this.userId,
      agents: this.bus.listAgents(),
      frameworks: {
        sacred_atom: this.sacredAtom.status(),
        divinity_earth_circle: this.divinityEarthCircle.status(),
      },
      memory: memStats,
      usage_7d: {
        actions: usageStats.total_actions,
        tokens: usageStats.total_tokens,
        cost: usageStats.total_cost,
        tier: usageStats.tier,
      },
    }
  }

  billing() { return this.economic.getUsageStats(this.userId, 30) }
  generateInvoice() { return this.economic.generateInvoice(this.userId) }
}

// Safe boot: report status only. Scanning and audit routines require an explicit call.
if (require.main === module) {
  const system = new AegisSovereignSystem()
  console.log(JSON.stringify(system.status(), null, 2))
}

module.exports = { AegisSovereignSystem }
