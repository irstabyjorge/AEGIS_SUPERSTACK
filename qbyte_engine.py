#!/usr/bin/env python3
"""QByte-22 Quantum Security Engine — AEGIS Production v2"""
import hashlib
import ipaddress
import json
import os
import re
import socket
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AEGIS_HOME = Path(os.environ.get("AEGIS_HOME", Path.home() / "AEGIS"))
ENGINE_VERSION = "2.0.0"
BLOCKLIST_FILE = AEGIS_HOME / "aegis_blocklist.txt"
THREAT_LOG = AEGIS_HOME / "threat_log.jsonl"
KNOWN_GOOD_FILE = AEGIS_HOME / "known_good_ips.txt"
GEO_CACHE = {}


def load_lines(path):
    if path.exists():
        return set(path.read_text().strip().splitlines())
    return set()


BLOCKLIST = load_lines(BLOCKLIST_FILE)
KNOWN_GOOD = load_lines(KNOWN_GOOD_FILE)

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


def ip_entropy(ip_str):
    """Higher entropy = more random-looking IP = more suspicious."""
    octets = ip_str.split(".")
    if len(octets) != 4:
        return 0.5
    vals = [int(o) for o in octets]
    spread = max(vals) - min(vals)
    return min(spread / 255.0, 1.0)


def is_bogon(ip_str):
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in BOGON_RANGES)
    except ValueError:
        return False


def reverse_dns_check(ip_str):
    try:
        host = socket.gethostbyaddr(ip_str)[0]
        return host
    except (socket.herror, socket.gaierror, OSError):
        return None


def matches_prefix_set(ip_str, prefix_set):
    return any(ip_str.startswith(p) for p in prefix_set)


def compute_event_hash(event):
    raw = json.dumps(event, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


class QuantumSecurityEngine:
    def __init__(self):
        self.session_ips = {}
        self.session_start = time.time()

    def analyze(self, event):
        ip = event.get("ip", "0.0.0.0")
        now = datetime.now(timezone.utc)
        signals = []
        score = 0.0

        # ── Auth failure ──
        if event.get("failed_auth"):
            score += 0.25
            signals.append("failed_auth")

        fail_count = int(event.get("failed_auth_count", 0))
        if fail_count >= 10:
            score += 0.30
            signals.append(f"brute_force({fail_count})")
        elif fail_count >= 5:
            score += 0.15
            signals.append(f"repeated_fail({fail_count})")

        # ── Device / location anomalies ──
        if event.get("new_device"):
            score += 0.20
            signals.append("new_device")

        if event.get("impossible_travel"):
            score += 0.30
            signals.append("impossible_travel")

        if event.get("geo_mismatch"):
            score += 0.15
            signals.append("geo_mismatch")

        # ── IP reputation ──
        if event.get("suspicious_ip") or ip in BLOCKLIST:
            score += 0.25
            signals.append("flagged_ip")

        if matches_prefix_set(ip, TOR_EXIT_SIGNATURES):
            score += 0.20
            signals.append("tor_exit_node")

        if matches_prefix_set(ip, THREAT_INTEL_PATTERNS):
            score += 0.15
            signals.append("threat_intel_match")

        if matches_prefix_set(ip, SCANNER_NETS):
            score += 0.20
            signals.append("known_scanner")

        if is_bogon(ip):
            score += 0.10
            signals.append("bogon_range")

        # ── Reverse DNS ──
        rdns = reverse_dns_check(ip)
        if rdns:
            if any(x in rdns.lower() for x in ("vps", "cloud", "server", "host", "dedicated")):
                score += 0.10
                signals.append(f"hosting_rdns({rdns})")
        else:
            score += 0.05
            signals.append("no_rdns")

        # ── Behavioral signals ──
        if event.get("credential_stuffing"):
            score += 0.30
            signals.append("credential_stuffing")

        if event.get("password_spray"):
            score += 0.25
            signals.append("password_spray")

        if event.get("api_abuse"):
            score += 0.20
            signals.append("api_abuse")

        if event.get("port_scan"):
            score += 0.25
            signals.append("port_scan")

        if event.get("sql_injection") or event.get("xss") or event.get("injection"):
            score += 0.35
            signals.append("injection_attempt")

        if event.get("path_traversal"):
            score += 0.30
            signals.append("path_traversal")

        rate = int(event.get("requests_per_minute", 0))
        if rate > 500:
            score += 0.30
            signals.append(f"rate_flood({rate}rpm)")
        elif rate > 100:
            score += 0.15
            signals.append(f"high_rate({rate}rpm)")

        user_agent = event.get("user_agent", "")
        if user_agent:
            ua_lower = user_agent.lower()
            if any(x in ua_lower for x in ("sqlmap", "nikto", "nmap", "masscan", "zmap", "dirbuster", "gobuster", "hydra", "metasploit")):
                score += 0.35
                signals.append(f"attack_tool_ua")
            elif any(x in ua_lower for x in ("bot", "crawler", "spider", "scan")):
                score += 0.10
                signals.append("bot_ua")
            elif user_agent == "" or len(user_agent) < 10:
                score += 0.05
                signals.append("suspicious_ua")

        # ── Session velocity (cross-event tracking) ──
        self.session_ips.setdefault(ip, []).append(time.time())
        hits = self.session_ips[ip]
        if len(hits) > 5:
            window = hits[-1] - hits[-6]
            if window < 30:
                score += 0.15
                signals.append(f"velocity({len(hits)}hits/{window:.0f}s)")

        # ── Time-of-day risk ──
        hour = int(event.get("hour", now.hour))
        if 1 <= hour <= 5:
            score += 0.05
            signals.append("off_hours")

        # ── Privilege escalation signals ──
        if event.get("privilege_escalation"):
            score += 0.35
            signals.append("priv_esc")

        if event.get("lateral_movement"):
            score += 0.30
            signals.append("lateral_movement")

        if event.get("data_exfiltration"):
            score += 0.35
            signals.append("data_exfil")

        # ── Known good override ──
        if ip in KNOWN_GOOD and score < 0.60:
            score *= 0.5
            signals.append("known_good_dampened")

        # ── Clamp and classify ──
        score = min(1.0, score)

        if score >= 0.80:
            action = "BLOCK"
            level = "CRITICAL"
        elif score >= 0.60:
            action = "BLOCK"
            level = "HIGH"
        elif score >= 0.40:
            action = "CHALLENGE_MFA"
            level = "MEDIUM"
        elif score >= 0.25:
            action = "MONITOR"
            level = "LOW"
        else:
            action = "ALLOW"
            level = "CLEAR"

        # ── Correlation: repeated offender escalation ──
        history_hits = self._check_history(ip)
        if history_hits >= 5:
            score += 0.20
            signals.append(f"repeat_offender({history_hits})")
        elif history_hits >= 2:
            score += 0.10
            signals.append(f"prior_hit({history_hits})")

        # ── Clamp and classify ──
        score = min(1.0, score)

        if score >= 0.80:
            action = "BLOCK"
            level = "CRITICAL"
        elif score >= 0.60:
            action = "BLOCK"
            level = "HIGH"
        elif score >= 0.40:
            action = "CHALLENGE_MFA"
            level = "MEDIUM"
        elif score >= 0.25:
            action = "MONITOR"
            level = "LOW"
        else:
            action = "ALLOW"
            level = "CLEAR"

        result = {
            "timestamp": now.isoformat(),
            "event_hash": compute_event_hash(event),
            "ip": ip,
            "threat_score": round(score, 4),
            "threat_level": level,
            "confidence": round(min(0.95, 0.50 + len(signals) * 0.08), 4),
            "recommended_action": action,
            "signals": signals,
            "signal_count": len(signals),
            "engine": f"qbyte-22-v{ENGINE_VERSION}",
        }

        self._log_threat(result)
        return result

    def _check_history(self, ip):
        try:
            if not THREAT_LOG.exists():
                return 0
            count = 0
            with open(THREAT_LOG) as f:
                for line in f:
                    if f'"ip": "{ip}"' in line or f'"ip":"{ip}"' in line:
                        count += 1
            return count
        except OSError:
            return 0

    def _log_threat(self, result):
        try:
            THREAT_LOG.parent.mkdir(parents=True, exist_ok=True)
            self._rotate_log()
            with open(THREAT_LOG, "a") as f:
                f.write(json.dumps(result) + "\n")
        except OSError:
            pass

    def _rotate_log(self):
        try:
            if THREAT_LOG.exists() and THREAT_LOG.stat().st_size > 10 * 1024 * 1024:
                rotated = THREAT_LOG.with_suffix(".jsonl.1")
                if rotated.exists():
                    rotated.unlink()
                THREAT_LOG.rename(rotated)
        except OSError:
            pass


def auto_blocklist(result):
    ip = result["ip"]
    if result["recommended_action"] == "BLOCK" and ip not in BLOCKLIST:
        try:
            BLOCKLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(BLOCKLIST_FILE, "a") as f:
                f.write(ip + "\n")
            BLOCKLIST.add(ip)
            return True
        except OSError:
            pass
    return False


def load_events():
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            data = json.loads(raw)
            return data if isinstance(data, list) else [data]

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.is_dir():
            events = []
            for f in sorted(path.glob("*.json")):
                with open(f) as fh:
                    events.append(json.load(fh))
            return events
        elif path.is_file():
            with open(path) as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]

    return [
        {"ip": "1.2.3.4", "failed_auth": True, "new_device": True},
        {"ip": "8.8.8.8", "failed_auth": False, "new_device": False},
        {
            "ip": "45.33.22.11",
            "failed_auth": True,
            "new_device": True,
            "impossible_travel": True,
            "suspicious_ip": True,
        },
    ]


def print_banner():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  QByte-22 Quantum Security Engine :: AEGIS Production ║")
    print("╚═══════════════════════════════════════════════════════╝")


def print_result(result):
    level = result["threat_level"]
    colors = {"CRITICAL": "\033[91m", "HIGH": "\033[91m", "MEDIUM": "\033[93m", "LOW": "\033[96m", "CLEAR": "\033[92m"}
    reset = "\033[0m"
    color = colors.get(level, "")

    print(f"\n  IP: {result['ip']}")
    print(f"  {color}▌ {level} — {result['recommended_action']}{reset}  (score: {result['threat_score']}, confidence: {result['confidence']})")
    if result["signals"]:
        print(f"  Signals: {', '.join(result['signals'])}")
    print(f"  Hash: {result['event_hash']}  |  {result['timestamp']}")


def main():
    print_banner()

    engine = QuantumSecurityEngine()
    events = load_events()

    blocked = 0
    challenged = 0
    monitored = 0
    allowed = 0

    for event in events:
        result = engine.analyze(event)
        print_result(result)

        if auto_blocklist(result):
            print(f"  \033[91m>> AUTO-BLOCKLISTED {result['ip']}\033[0m")

        action = result["recommended_action"]
        if action == "BLOCK":
            blocked += 1
        elif action == "CHALLENGE_MFA":
            challenged += 1
        elif action == "MONITOR":
            monitored += 1
        else:
            allowed += 1

    print(f"\n{'─' * 55}")
    print(f"  Analyzed: {len(events)}  |  BLOCK: {blocked}  CHALLENGE: {challenged}  MONITOR: {monitored}  ALLOW: {allowed}")
    print(f"  Blocklist: {BLOCKLIST_FILE} ({len(BLOCKLIST)} IPs)")
    print(f"  Threat log: {THREAT_LOG}")


if __name__ == "__main__":
    main()
