#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md

__version__ = "2.0.0"

import os, time, json, hashlib, ipaddress, socket, queue, threading
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, Any, List
from pathlib import Path
from collections import Counter
import psutil
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from rich.console import Console
from rich.table import Table
from cryptography.fernet import Fernet

console = Console()
BASE = Path.home() / "aegis_omni_xeon"
LOG_DIR = BASE / "logs"
DATA_DIR = BASE / "data"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
BLOCKLIST_FILE = DATA_DIR / "blocklist.txt"
KNOWN_GOOD_FILE = DATA_DIR / "known_good.txt"
THREAT_LOG = LOG_DIR / "threat_log.jsonl"

def _load_lines(path):
    if path.exists():
        return set(path.read_text().strip().splitlines())
    return set()

BLOCKLIST = _load_lines(BLOCKLIST_FILE)
KNOWN_GOOD = _load_lines(KNOWN_GOOD_FILE)

BOGON_RANGES = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
]

TOR_EXIT_SIGNATURES = {
    "45.33.22.", "185.220.100.", "185.220.101.", "185.220.102.",
    "171.25.193.", "199.249.230.", "204.85.191.", "104.244.76.",
    "109.70.100.", "51.15.", "62.210.", "91.218.203.",
}

THREAT_INTEL_PATTERNS = {
    "23.94.", "23.95.", "45.33.", "45.55.", "45.76.", "45.77.",
    "64.225.", "68.183.", "104.131.", "104.236.", "104.248.",
    "128.199.", "134.209.", "138.68.", "139.59.", "142.93.",
    "157.245.", "159.65.", "159.89.", "161.35.", "164.90.",
    "165.22.", "165.227.", "167.71.", "167.99.", "174.138.",
    "178.128.", "178.62.", "188.166.", "192.241.", "198.199.",
    "206.189.", "209.97.",
}

SCANNER_NETS = {
    "71.6.135.", "71.6.146.", "71.6.158.", "71.6.165.",
    "80.82.77.", "93.174.95.", "162.142.125.", "167.248.",
    "198.235.24.", "205.210.31.",
}

SUSPICIOUS_PORTS = {22, 23, 25, 3389, 4444, 5555, 6667, 8333, 9735, 18080, 18081}
CRYPTO_PORTS = {8332, 8333, 18332, 18333, 30303, 9735, 18080, 18081}

def log(event: str, payload: Dict[str, Any] = None):
    entry = {
        "time": datetime.now(UTC).isoformat(),
        "event": event,
        "payload": payload or {}
    }
    with open(LOG_DIR / "aegis_events.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

def _is_bogon(ip_str):
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in BOGON_RANGES)
    except ValueError:
        return False

def _matches_prefix(ip_str, prefix_set):
    return any(ip_str.startswith(p) for p in prefix_set)

def _reverse_dns(ip_str):
    try:
        return socket.gethostbyaddr(ip_str)[0]
    except (socket.herror, socket.gaierror, OSError):
        return None

def _compute_hash(data):
    raw = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass
class Threat:
    ip: str
    kind: str
    severity: int
    confidence: float
    signals: List[str] = field(default_factory=list)
    score: float = 0.0
    action: str = "MONITOR"
    level: str = "LOW"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class PolicyEngine:
    SAFE_AUTONOMOUS = {
        "STATUS", "HELP", "THREAT_SCAN", "NETWORK_SCAN",
        "PREDICT", "REPORT", "ENTROPY", "SYSTEM_ANALYSIS",
        "AUTH_AUDIT", "FIREWALL_STATUS", "CONNECTIONS",
        "LISTENERS", "FULL_AUDIT", "WATCH", "BLOCKLIST",
        "THREAT_FEED",
    }
    REQUIRES_MANUAL = {
        "FIREWALL_BLOCK", "SYSTEM_MODIFY", "SHUTDOWN"
    }

    def evaluate(self, intent: str) -> Dict[str, Any]:
        if intent in self.REQUIRES_MANUAL:
            return {"allowed": False, "reason": "manual authorization required"}
        return {"allowed": intent in self.SAFE_AUTONOMOUS, "reason": "autonomous mode"}


class QByteEngine:
    """QByte-22 Quantum Security Engine — real IP threat scoring."""

    def __init__(self):
        self.session_ips: Dict[str, List[float]] = {}
        self.threats: List[Threat] = []

    def analyze_ip(self, ip: str, context: Dict[str, Any] = None) -> Threat:
        context = context or {}
        signals = []
        score = 0.0

        if ip in BLOCKLIST:
            score += 0.30
            signals.append("blocklisted")

        if _matches_prefix(ip, TOR_EXIT_SIGNATURES):
            score += 0.20
            signals.append("tor_exit_node")

        if _matches_prefix(ip, THREAT_INTEL_PATTERNS):
            score += 0.15
            signals.append("threat_intel_match")

        if _matches_prefix(ip, SCANNER_NETS):
            score += 0.20
            signals.append("known_scanner")

        if _is_bogon(ip):
            score += 0.10
            signals.append("bogon_range")

        rdns = _reverse_dns(ip)
        if rdns:
            if any(x in rdns.lower() for x in ("vps", "cloud", "server", "host", "dedicated")):
                score += 0.10
                signals.append(f"hosting_rdns({rdns})")
        else:
            if not _is_bogon(ip):
                score += 0.05
                signals.append("no_rdns")

        port = context.get("port")
        if port:
            if port in CRYPTO_PORTS:
                score += 0.25
                signals.append(f"crypto_port({port})")
            elif port in SUSPICIOUS_PORTS:
                score += 0.15
                signals.append(f"suspicious_port({port})")

        if context.get("failed_auth"):
            score += 0.25
            signals.append("failed_auth")

        fail_count = int(context.get("failed_auth_count", 0))
        if fail_count >= 10:
            score += 0.30
            signals.append(f"brute_force({fail_count})")
        elif fail_count >= 5:
            score += 0.15
            signals.append(f"repeated_fail({fail_count})")

        if context.get("port_scan"):
            score += 0.25
            signals.append("port_scan")

        if context.get("injection"):
            score += 0.35
            signals.append("injection_attempt")

        self.session_ips.setdefault(ip, []).append(time.time())
        hits = self.session_ips[ip]
        if len(hits) > 5:
            window = hits[-1] - hits[-6]
            if window < 30:
                score += 0.15
                signals.append(f"velocity({len(hits)}hits/{window:.0f}s)")

        if ip in KNOWN_GOOD and score < 0.60:
            score *= 0.5
            signals.append("known_good_dampened")

        score = min(1.0, score)

        if score >= 0.80:
            action, level, kind = "BLOCK", "CRITICAL", "CRITICAL_THREAT"
        elif score >= 0.60:
            action, level, kind = "BLOCK", "HIGH", "HIGH_THREAT"
        elif score >= 0.40:
            action, level, kind = "CHALLENGE_MFA", "MEDIUM", "MEDIUM_THREAT"
        elif score >= 0.25:
            action, level, kind = "MONITOR", "LOW", "LOW_RISK"
        else:
            action, level, kind = "ALLOW", "CLEAR", "BENIGN"

        severity = int(score * 10)
        confidence = round(min(0.95, 0.50 + len(signals) * 0.08), 3)

        threat = Threat(
            ip=ip, kind=kind, severity=severity, confidence=confidence,
            signals=signals, score=round(score, 4), action=action, level=level,
        )
        self.threats.append(threat)
        log("qbyte_analysis", {
            "ip": ip, "score": threat.score, "level": level,
            "action": action, "signals": signals,
            "event_hash": _compute_hash({"ip": ip, **context}),
        })
        return threat

    def scan_live_connections(self) -> List[Threat]:
        findings = []
        for c in psutil.net_connections(kind="inet"):
            if c.raddr:
                remote_ip = c.raddr.ip
                remote_port = c.raddr.port
                if remote_port in SUSPICIOUS_PORTS or _matches_prefix(remote_ip, THREAT_INTEL_PATTERNS):
                    proc_name = None
                    try:
                        proc_name = psutil.Process(c.pid).name() if c.pid else None
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    threat = self.analyze_ip(remote_ip, {
                        "port": remote_port,
                        "process": proc_name,
                        "status": c.status,
                    })
                    findings.append(threat)
        log("live_connection_scan", {"threats_found": len(findings)})
        return findings

    def scan_listeners(self) -> List[Dict[str, Any]]:
        rows = []
        for c in psutil.net_connections(kind="inet"):
            if c.status == "LISTEN":
                proc_name = None
                try:
                    proc_name = psutil.Process(c.pid).name() if c.pid else None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                port = c.laddr.port if c.laddr else None
                rows.append({
                    "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                    "port": port,
                    "pid": c.pid,
                    "process": proc_name,
                    "suspicious": port in SUSPICIOUS_PORTS if port else False,
                })
        log("listener_scan", {"count": len(rows)})
        return rows

    def auto_blocklist(self, threat: Threat) -> bool:
        if threat.action == "BLOCK" and threat.ip not in BLOCKLIST:
            try:
                BLOCKLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(BLOCKLIST_FILE, "a") as f:
                    f.write(threat.ip + "\n")
                BLOCKLIST.add(threat.ip)
                log("auto_blocklist", {"ip": threat.ip, "score": threat.score})
                return True
            except OSError:
                pass
        return False


class PredictiveEngine:
    """ML-based threat prediction using real connection patterns."""

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._trained = False

    def train_on_history(self):
        if not THREAT_LOG.exists():
            return {"status": "no_training_data", "log": str(THREAT_LOG)}

        features, labels = [], []
        try:
            with open(THREAT_LOG) as f:
                for line in f:
                    entry = json.loads(line.strip())
                    score = entry.get("threat_score", entry.get("score", 0))
                    sig_count = entry.get("signal_count", len(entry.get("signals", [])))
                    features.append([score * 10, sig_count])
                    labels.append(1 if entry.get("recommended_action", entry.get("action", "")) == "BLOCK" else 0)
        except (json.JSONDecodeError, OSError):
            return {"status": "parse_error"}

        if len(features) < 6:
            return {"status": "insufficient_data", "samples": len(features)}

        X = np.array(features)
        y = np.array(labels)
        self.model.fit(X, y)
        self._trained = True
        accuracy = self.model.score(X, y)
        result = {
            "status": "trained",
            "samples": len(features),
            "accuracy": round(accuracy, 4),
            "features": ["threat_score_x10", "signal_count"],
        }
        log("predictive_training", result)
        return result

    def predict(self, score: float, signal_count: int) -> Dict[str, Any]:
        if not self._trained:
            self.train_on_history()
        if not self._trained:
            return {"prediction": "unknown", "reason": "no_model"}
        X = np.array([[score * 10, signal_count]])
        pred = self.model.predict(X)[0]
        proba = self.model.predict_proba(X)[0]
        result = {
            "prediction": "BLOCK" if pred == 1 else "ALLOW",
            "confidence": round(float(max(proba)), 4),
            "input": {"score": score, "signals": signal_count},
        }
        log("prediction", result)
        return result


class SystemAnalyzer:
    def status(self) -> Dict[str, Any]:
        data = {
            "hostname": os.uname().nodename,
            "user": os.getenv("USER"),
            "cpu_percent": psutil.cpu_percent(interval=0.5),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "logical_cpus": psutil.cpu_count(logical=True),
            "physical_cpus": psutil.cpu_count(logical=False),
            "boot_time": datetime.fromtimestamp(psutil.boot_time(), UTC).isoformat(),
            "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 1),
        }
        log("system_status", data)
        return data

    def auth_audit(self) -> List[Dict[str, Any]]:
        import subprocess
        files = ["/var/log/auth.log", "/var/log/syslog"]
        findings = []
        for fp in files:
            if Path(fp).exists():
                try:
                    r = subprocess.run(
                        f"sudo tail -n 300 {fp} | grep -Ei 'failed|invalid|authentication|sudo|session|password' || true",
                        shell=True, text=True, capture_output=True, timeout=8
                    )
                    findings.append({"file": fp, "events": r.stdout[-4000:]})
                except Exception as e:
                    findings.append({"file": fp, "error": str(e)})
        log("auth_audit", {"files_checked": len(findings)})
        return findings

    def firewall_status(self) -> Dict[str, Any]:
        import subprocess
        def _run(cmd):
            try:
                r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=8)
                return {"ok": r.returncode == 0, "stdout": r.stdout[-4000:], "stderr": r.stderr[-2000:]}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        data = {
            "ufw": _run("sudo ufw status verbose"),
            "iptables": _run("sudo iptables -S | head -n 120"),
        }
        log("firewall_status", data)
        return data


class EntropyModule:
    def generate(self) -> Dict[str, Any]:
        key = Fernet.generate_key()
        digest = hashlib.sha512(key).hexdigest()
        result = {
            "fernet_key_generated": True,
            "sha512_digest": digest,
            "key_bytes": len(key),
            "entropy_bits": len(key) * 8,
        }
        log("entropy_generation", {"sha512_digest": digest})
        return result


class CommandRouter:
    def parse(self, cmd: str):
        c = cmd.lower().strip()
        if c in {"help", "?"}: return "HELP", {}
        if c in {"status", "system status"}: return "STATUS", {}
        if c in {"threats", "scan", "threat scan"}: return "THREAT_SCAN", {}
        if c in {"network", "network scan"}: return "NETWORK_SCAN", {}
        if c in {"listeners", "ports"}: return "LISTENERS", {}
        if c in {"connections", "conns"}: return "CONNECTIONS", {}
        if c == "predict": return "PREDICT", {}
        if c == "report": return "REPORT", {}
        if c in {"entropy", "key"}: return "ENTROPY", {}
        if c in {"analyze system", "system analysis", "sysinfo"}: return "SYSTEM_ANALYSIS", {}
        if c in {"auth", "auth audit"}: return "AUTH_AUDIT", {}
        if c in {"firewall", "fw"}: return "FIREWALL_STATUS", {}
        if c in {"all", "full audit"}: return "FULL_AUDIT", {}
        if c == "watch": return "WATCH", {}
        if c in {"blocklist", "blocked"}: return "BLOCKLIST", {}
        if c.startswith("scan "):
            parts = c.split()
            payload = {}
            for token in parts[1:]:
                if token.count(".") == 3:
                    payload["ip"] = token
                if token.isdigit():
                    payload["port"] = int(token)
            return "THREAT_SCAN", payload
        if c in {"block", "firewall block"}: return "FIREWALL_BLOCK", {}
        if c == "shutdown": return "SHUTDOWN", {}
        return "UNKNOWN", {}


class Orchestrator:
    def __init__(self):
        self.policy = PolicyEngine()
        self.router = CommandRouter()
        self.qbyte = QByteEngine()
        self.predictor = PredictiveEngine()
        self.system = SystemAnalyzer()
        self.entropy = EntropyModule()

    def execute(self, cmd: str):
        intent, payload = self.router.parse(cmd)
        decision = self.policy.evaluate(intent)

        if intent == "UNKNOWN":
            return {"status": "unknown_command", "hint": "type help"}

        if not decision["allowed"]:
            return {
                "status": "blocked_by_policy",
                "intent": intent,
                "reason": decision["reason"],
            }

        if intent == "HELP":
            return self.help()
        if intent == "STATUS":
            return self.system.status()
        if intent == "THREAT_SCAN":
            if payload.get("ip"):
                t = self.qbyte.analyze_ip(payload["ip"], payload)
                return self._threat_dict(t)
            return self._live_scan()
        if intent == "NETWORK_SCAN":
            return self._live_scan()
        if intent == "LISTENERS":
            return self.qbyte.scan_listeners()
        if intent == "CONNECTIONS":
            return self._connections()
        if intent == "PREDICT":
            return self.predictor.train_on_history()
        if intent == "SYSTEM_ANALYSIS":
            return self.system.status()
        if intent == "AUTH_AUDIT":
            return self.system.auth_audit()
        if intent == "FIREWALL_STATUS":
            return self.system.firewall_status()
        if intent == "ENTROPY":
            return self.entropy.generate()
        if intent == "FULL_AUDIT":
            return self._full_audit()
        if intent == "WATCH":
            return self._watch()
        if intent == "BLOCKLIST":
            return {"blocklist": sorted(BLOCKLIST), "count": len(BLOCKLIST), "file": str(BLOCKLIST_FILE)}
        if intent == "REPORT":
            return self.report()

    def _threat_dict(self, t: Threat) -> Dict:
        return {
            "ip": t.ip, "kind": t.kind, "severity": t.severity,
            "confidence": t.confidence, "score": t.score,
            "action": t.action, "level": t.level,
            "signals": t.signals, "timestamp": t.timestamp,
        }

    def _live_scan(self) -> Dict:
        threats = self.qbyte.scan_live_connections()
        blocked = 0
        for t in threats:
            if self.qbyte.auto_blocklist(t):
                blocked += 1
        return {
            "scan": "live_connections",
            "threats_found": len(threats),
            "auto_blocked": blocked,
            "results": [self._threat_dict(t) for t in threats],
        }

    def _connections(self) -> List[Dict]:
        rows = []
        for c in psutil.net_connections(kind="inet"):
            if c.raddr:
                proc_name = None
                try:
                    proc_name = psutil.Process(c.pid).name() if c.pid else None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                rows.append({
                    "local": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                    "remote": f"{c.raddr.ip}:{c.raddr.port}",
                    "pid": c.pid,
                    "process": proc_name,
                    "status": c.status,
                })
        return rows[:200]

    def _full_audit(self) -> Dict:
        return {
            "system": self.system.status(),
            "listeners": self.qbyte.scan_listeners(),
            "threat_scan": self._live_scan(),
            "auth": self.system.auth_audit(),
            "firewall": self.system.firewall_status(),
            "entropy": self.entropy.generate(),
            "blocklist": {"count": len(BLOCKLIST)},
            "prediction_model": self.predictor.train_on_history(),
        }

    def _watch(self):
        console.print("[green]Live threat monitoring (10s interval). Ctrl+C to stop.[/green]")
        while True:
            threats = self.qbyte.scan_live_connections()
            for t in threats:
                self.qbyte.auto_blocklist(t)
            console.print_json(json.dumps({
                "time": datetime.now(UTC).isoformat(),
                "cpu": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory().percent,
                "active_threats": len(threats),
                "blocklist_size": len(BLOCKLIST),
                "findings": [self._threat_dict(t) for t in threats],
            }, default=str))
            time.sleep(10)

    def help(self):
        return {
            "commands": [
                "status           — system health overview",
                "scan             — scan live connections for threats",
                "scan <ip> [port] — analyze specific IP",
                "listeners        — show listening ports",
                "connections      — show active connections",
                "auth             — audit authentication logs",
                "firewall         — show firewall status",
                "predict          — train ML model on threat history",
                "entropy          — generate cryptographic key material",
                "blocklist        — show blocked IPs",
                "all              — run full security audit",
                "watch            — continuous threat monitoring",
                "report           — summary report",
                "help             — this menu",
                "exit             — quit",
            ],
            "engine": f"QByte-22 v{__version__}",
            "blocked_for_safety": [
                "firewall block (requires manual authorization)",
                "system modify (requires manual authorization)",
                "shutdown (requires manual authorization)",
            ],
        }

    def report(self):
        table = Table(title="AEGIS OMNI-XEON Report")
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Engine", f"QByte-22 v{__version__}")
        table.add_row("Threats analyzed", str(len(self.qbyte.threats)))
        table.add_row("IPs blocked", str(len(BLOCKLIST)))
        table.add_row("Mode", "Autonomous — real system analysis")
        table.add_row("Threat log", str(THREAT_LOG))
        table.add_row("Event log", str(LOG_DIR / "aegis_events.jsonl"))
        console.print(table)
        return {
            "report": "displayed",
            "threats_analyzed": len(self.qbyte.threats),
            "blocklist_size": len(BLOCKLIST),
        }


def main():
    console.print(f"[bold cyan]AEGIS OMNI-XEON v{__version__} — QByte-22 Engine[/bold cyan]")
    console.print("Autonomous security platform. Type [bold]help[/bold]. Type [bold]exit[/bold] to quit.")
    orch = Orchestrator()
    while True:
        try:
            cmd = input("AEGIS> ").strip()
            if cmd.lower() in {"exit", "quit"}:
                print("Exiting.")
                break
            result = orch.execute(cmd)
            console.print_json(json.dumps(result, default=str))
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            log("error", {"error": str(e)})
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
