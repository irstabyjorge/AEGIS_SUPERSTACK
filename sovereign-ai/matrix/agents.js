// Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
// AEGIS Sovereign AI — Matrix Layer (Event-Driven Agent System)
// Routes security events to specialized agents, bridges to AEGIS Python modules.

const { EventEmitter } = require('events')
const { execSync, spawn } = require('child_process')
const path = require('path')

const AEGIS_DIR = path.resolve(__dirname, '..', '..')
const VENV_PYTHON = path.join(AEGIS_DIR, '.venv', 'bin', 'python3')

class AgentBus extends EventEmitter {
  constructor(memory) {
    super()
    this.memory = memory
    this.agents = new Map()
    this.running = true
    this.taskQueue = []
    this.processing = false
  }

  register(name, handler) {
    this.agents.set(name, handler)
    this.emit('agent:registered', { name, time: Date.now() })
  }

  unregister(name) {
    this.agents.delete(name)
    this.emit('agent:unregistered', { name, time: Date.now() })
  }

  async dispatch(eventType, payload = {}) {
    const event = {
      id: `evt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      type: eventType,
      payload,
      timestamp: Date.now(),
      results: [],
    }

    this.memory.writeMemory({
      type: 'event_dispatch',
      source: 'matrix',
      priority: payload.priority || 5,
      data: { eventType, payload },
      tags: ['matrix', 'dispatch', eventType],
    })

    for (const [name, handler] of this.agents) {
      if (handler.handles && !handler.handles(eventType)) continue
      try {
        const result = await handler.execute(event)
        event.results.push({ agent: name, result, status: 'ok' })
      } catch (err) {
        event.results.push({ agent: name, error: err.message, status: 'error' })
      }
    }

    this.emit('event:completed', event)
    return event
  }

  enqueue(eventType, payload = {}) {
    this.taskQueue.push({ eventType, payload })
    if (!this.processing) this._processQueue()
  }

  async _processQueue() {
    this.processing = true
    while (this.taskQueue.length > 0) {
      const task = this.taskQueue.shift()
      await this.dispatch(task.eventType, task.payload)
    }
    this.processing = false
  }

  listAgents() {
    return Array.from(this.agents.keys())
  }
}

function callAegisModule(moduleName, functionName, args = '{}') {
  const script = `
import sys, json
sys.path.insert(0, '${AEGIS_DIR}')
from modules.${moduleName} import ${functionName}
result = ${functionName}(${args === '{}' ? '' : `**json.loads('${args}')`})
print(json.dumps(result, default=str))
`
  try {
    const out = execSync(`${VENV_PYTHON} -c "${script.replace(/"/g, '\\"')}"`, {
      cwd: AEGIS_DIR,
      timeout: 120000,
      encoding: 'utf-8',
      env: { ...process.env, HOME: process.env.HOME },
    })
    return JSON.parse(out.trim())
  } catch (err) {
    return { error: err.message, module: moduleName, function: functionName }
  }
}

class BaseAgent {
  constructor(name, eventTypes = []) {
    this.name = name
    this.eventTypes = eventTypes
  }

  handles(eventType) {
    if (this.eventTypes.length === 0) return true
    return this.eventTypes.includes(eventType)
  }

  async execute(event) {
    throw new Error(`Agent ${this.name} must implement execute()`)
  }
}

class ThreatScanAgent extends BaseAgent {
  constructor() {
    super('threat-scanner', ['scan:ioc', 'scan:full', 'alert:threat'])
  }

  async execute(event) {
    const result = callAegisModule('ioc_scanner', 'full_scan')
    return {
      agent: this.name,
      scan_type: 'ioc',
      likelihood: result.compromise_likelihood || 'UNKNOWN',
      findings: result.total_findings || 0,
      details: result,
    }
  }
}

class VulnScanAgent extends BaseAgent {
  constructor() {
    super('vuln-scanner', ['scan:vuln', 'scan:full'])
  }

  async execute(event) {
    const result = callAegisModule('vuln_scanner', 'full_scan')
    return {
      agent: this.name,
      scan_type: 'vulnerability',
      score: result.security_score || 0,
      critical: result.critical || 0,
      details: result,
    }
  }
}

class ForensicsAgent extends BaseAgent {
  constructor() {
    super('forensics', ['scan:forensics', 'incident:response', 'scan:full'])
  }

  async execute(event) {
    const result = callAegisModule('forensics', 'full_forensic_capture')
    return {
      agent: this.name,
      scan_type: 'forensics',
      sections: Object.keys(result),
      details: result,
    }
  }
}

class PasswordAuditAgent extends BaseAgent {
  constructor() {
    super('password-auditor', ['scan:passwords', 'audit:passwords', 'scan:full'])
  }

  async execute(event) {
    const result = callAegisModule('password_audit', 'full_audit')
    return {
      agent: this.name,
      scan_type: 'password_audit',
      score: result.password_security_score || 0,
      findings: result.total_findings || 0,
      details: result,
    }
  }
}

class UptimeAgent extends BaseAgent {
  constructor() {
    super('uptime-monitor', ['monitor:uptime', 'check:services'])
  }

  async execute(event) {
    const result = callAegisModule('uptime_monitor', 'run_checks')
    return {
      agent: this.name,
      scan_type: 'uptime',
      up: result.up || 0,
      total: result.checks || 0,
      details: result,
    }
  }
}

class LogAnalysisAgent extends BaseAgent {
  constructor() {
    super('log-analyzer', ['analyze:logs', 'scan:full'])
  }

  async execute(event) {
    const result = callAegisModule('log_analyzer', 'analyze_system_logs')
    return {
      agent: this.name,
      scan_type: 'log_analysis',
      findings: result.total_findings || 0,
      details: result,
    }
  }
}

class PayloadDetectorAgent extends BaseAgent {
  constructor() {
    super('payload-detector', ['scan:payloads', 'detect:attack'])
  }

  async execute(event) {
    const target = event.payload.path || '/var/log'
    const script = `
import sys, json
sys.path.insert(0, '${AEGIS_DIR}')
from modules.payload_detector import scan_web_logs
result = scan_web_logs()
print(json.dumps(result, default=str))
`
    try {
      const out = execSync(`${VENV_PYTHON} -c "${script.replace(/"/g, '\\"')}"`, {
        cwd: AEGIS_DIR,
        timeout: 60000,
        encoding: 'utf-8',
      })
      return { agent: this.name, scan_type: 'payload', details: JSON.parse(out.trim()) }
    } catch (err) {
      return { agent: this.name, scan_type: 'payload', error: err.message }
    }
  }
}

function createDefaultAgents() {
  return [
    new ThreatScanAgent(),
    new VulnScanAgent(),
    new ForensicsAgent(),
    new PasswordAuditAgent(),
    new UptimeAgent(),
    new LogAnalysisAgent(),
    new PayloadDetectorAgent(),
  ]
}

module.exports = {
  AgentBus,
  BaseAgent,
  ThreatScanAgent,
  VulnScanAgent,
  ForensicsAgent,
  PasswordAuditAgent,
  UptimeAgent,
  LogAnalysisAgent,
  PayloadDetectorAgent,
  createDefaultAgents,
  callAegisModule,
}
