#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Daemon — persistent background security service.
Runs continuously, survives reboots, auto-restarts on crash.
Performs scheduled scans, threat monitoring, and self-learning.
"""

__version__ = "2.0.0"

import json, os, sys, time, threading, signal
from pathlib import Path
from datetime import datetime, UTC

sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE = Path.home() / "aegis_omni_xeon"
LOGS = BASE / "logs"
BRAIN_DIR = BASE / "brain"
STATE_FILE = BRAIN_DIR / "daemon_state.json"
LOGS.mkdir(parents=True, exist_ok=True)
BRAIN_DIR.mkdir(parents=True, exist_ok=True)

DAEMON_LOG = LOGS / "daemon.jsonl"


def _log(event, payload=None):
    with open(DAEMON_LOG, "a") as f:
        f.write(json.dumps({
            "time": datetime.now(UTC).isoformat(),
            "event": event,
            "payload": payload or {},
        }, default=str) + "\n")


def _save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"started": datetime.now(UTC).isoformat(), "scans": 0, "threats_found": 0, "uptime_checks": 0}


def scheduled_threat_scan(state):
    try:
        from modules.ioc_scanner import full_scan as ioc_scan
        result = ioc_scan()
        state["scans"] += 1
        state["last_scan"] = datetime.now(UTC).isoformat()
        state["last_scan_result"] = result.get("compromise_likelihood", "UNKNOWN")
        findings = result.get("total_findings", 0)
        state["threats_found"] += findings
        _log("scheduled_ioc_scan", {
            "likelihood": result.get("compromise_likelihood"),
            "findings": findings,
        })
    except Exception as e:
        _log("scan_error", {"error": str(e)})


def scheduled_vuln_check(state):
    try:
        from modules.vuln_scanner import full_scan
        result = full_scan()
        state["last_vuln_scan"] = datetime.now(UTC).isoformat()
        state["last_vuln_score"] = result.get("security_score", 0)
        _log("scheduled_vuln_scan", {
            "score": result.get("security_score"),
            "critical": result.get("critical", 0),
        })
    except Exception as e:
        _log("vuln_error", {"error": str(e)})


def scheduled_uptime_check(state):
    try:
        from modules.uptime_monitor import run_checks
        result = run_checks()
        state["uptime_checks"] += 1
        state["last_uptime"] = datetime.now(UTC).isoformat()
        state["services_up"] = result.get("up", 0)
        state["services_total"] = result.get("checks", 0)
        _log("scheduled_uptime", {
            "up": result.get("up"),
            "total": result.get("checks"),
        })
    except Exception as e:
        _log("uptime_error", {"error": str(e)})


def scheduled_log_analysis(state):
    try:
        from modules.log_analyzer import analyze_system_logs
        result = analyze_system_logs()
        state["last_log_analysis"] = datetime.now(UTC).isoformat()
        state["last_log_findings"] = result.get("total_findings", 0)
        _log("scheduled_log_analysis", {
            "findings": result.get("total_findings", 0),
        })
    except Exception as e:
        _log("log_analysis_error", {"error": str(e)})


def self_learn(state):
    """Analyze accumulated data and store insights."""
    try:
        knowledge_file = BRAIN_DIR / "knowledge" / "auto_insights.jsonl"
        knowledge_file.parent.mkdir(parents=True, exist_ok=True)

        threat_log = LOGS / "threat_log.jsonl"
        if threat_log.exists():
            from collections import Counter
            actions = Counter()
            ips = Counter()
            with open(threat_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        actions[entry.get("action", "UNKNOWN")] += 1
                        ips[entry.get("ip", "?")] += 1
                    except json.JSONDecodeError:
                        pass

            if actions:
                insight = {
                    "time": datetime.now(UTC).isoformat(),
                    "type": "threat_pattern_summary",
                    "total_events": sum(actions.values()),
                    "action_distribution": dict(actions.most_common(5)),
                    "top_threat_ips": dict(ips.most_common(10)),
                }
                with open(knowledge_file, "a") as f:
                    f.write(json.dumps(insight) + "\n")
                state["last_learning"] = datetime.now(UTC).isoformat()
                _log("self_learning", {"events_analyzed": sum(actions.values())})

    except Exception as e:
        _log("learning_error", {"error": str(e)})


def run_daemon():
    _log("daemon_start", {"version": __version__, "pid": os.getpid()})
    state = _load_state()
    state["started"] = datetime.now(UTC).isoformat()
    state["pid"] = os.getpid()

    running = True

    def handle_signal(signum, frame):
        nonlocal running
        _log("daemon_stop", {"signal": signum})
        running = False

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    cycle = 0

    while running:
        try:
            cycle += 1

            # Every 5 minutes: uptime check
            if cycle % 1 == 0:
                scheduled_uptime_check(state)

            # Every 15 minutes: log analysis
            if cycle % 3 == 0:
                scheduled_log_analysis(state)

            # Every 30 minutes: IOC scan
            if cycle % 6 == 0:
                scheduled_threat_scan(state)

            # Every hour: vulnerability scan
            if cycle % 12 == 0:
                scheduled_vuln_check(state)

            # Every 2 hours: self-learning
            if cycle % 24 == 0:
                self_learn(state)

            _save_state(state)
            time.sleep(300)  # 5 minute intervals

        except Exception as e:
            _log("daemon_error", {"error": str(e), "cycle": cycle})
            time.sleep(60)

    _log("daemon_shutdown", {"cycles": cycle})
    _save_state(state)


if __name__ == "__main__":
    run_daemon()
