#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Chat — Natural language security assistant with desktop GUI.
Ask AEGIS to do things in plain language instead of memorizing commands.
Integrates all AEGIS modules and common Linux security tools.
"""

__version__ = "2.0.0"

import sys, os, json, re, subprocess, threading, time
from pathlib import Path
from datetime import datetime, UTC

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import tkinter as tk
    from tkinter import scrolledtext, messagebox, font as tkfont
    HAS_TK = True
except ImportError:
    HAS_TK = False

from modules.uptime_monitor import run_checks as uptime_checks
from modules.log_analyzer import analyze_system_logs, analyze_aegis_threats
from modules.vuln_scanner import full_scan as vuln_full_scan
from modules.ioc_scanner import full_scan as ioc_full_scan
from modules.forensics import full_forensic_capture, hash_critical_binaries, capture_volatile_state
from modules.password_audit import full_audit as password_full_audit
from modules.payload_detector import scan_web_logs as payload_scan_web
from modules.honeypot import analyze_honeypot_logs

LOGS = Path.home() / "aegis_omni_xeon" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)


def _run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
    except subprocess.TimeoutExpired:
        return "[timed out]"
    except Exception as e:
        return f"[error: {e}]"


def _log_chat(user_msg, response):
    with open(LOGS / "chat_history.jsonl", "a") as f:
        f.write(json.dumps({
            "time": datetime.now(UTC).isoformat(),
            "user": user_msg,
            "response": response[:500],
        }) + "\n")


def _format_result(data):
    if isinstance(data, dict):
        return json.dumps(data, indent=2, default=str)
    return str(data)


INTENT_MAP = [
    (r"(?:scan|check|analyze)\s+(?:this\s+)?(?:ip|address)\s+(\d+\.\d+\.\d+\.\d+)", "scan_ip"),
    (r"(?:scan|check)\s+(?:for\s+)?vulnerabilit|vuln\s*scan|how\s+(?:secure|safe)\s+is\s+(?:my|this)\s+(?:system|machine|computer)", "vuln_scan"),
    (r"(?:check|scan)\s+(?:for\s+)?(?:compromise|ioc|malware|rootkit|trojan|virus)", "ioc_scan"),
    (r"(?:forensic|evidence|capture\s+state|volatile)", "forensics"),
    (r"(?:password|credential|passwd).*(?:audit|check|scan|weak|strong|policy)", "password_audit"),
    (r"(?:payload|attack|injection|xss|sqli|sql\s+injection|web\s+shell)", "payload_scan"),
    (r"(?:honeypot|decoy|trap).*(?:stat|analyz|result|data)", "honeypot_stats"),
    (r"(?:uptime|service|availability|website|http|site).*(?:check|monitor|status|up|down)", "uptime"),
    (r"(?:log|auth\.log|syslog).*(?:analy|scan|check|review)", "log_analysis"),
    (r"threat.*(?:log|history|analys)", "threat_analysis"),
    (r"(?:hash|integrity|binary|checksum).*(?:check|verify|scan)", "hashes"),
    (r"(?:who\s+is|whois)\s+(\S+)", "whois"),
    (r"(?:lookup|resolve|dns|nslookup|dig)\s+(\S+)", "dns_lookup"),
    (r"(?:ping)\s+(\S+)", "ping"),
    (r"(?:port\s*scan|nmap|scan\s+ports?)\s+(\S+)", "port_scan"),
    (r"(?:trace\s*route|tracepath|tracert)\s+(\S+)", "traceroute"),
    (r"(?:open|listening)\s+ports?|what.*listen|netstat|ss\s", "listening_ports"),
    (r"(?:connection|connected|active\s+connection|network\s+connection)", "connections"),
    (r"(?:process|running|top|what.+running|ps\s)", "processes"),
    (r"(?:firewall|ufw|iptables).*(?:status|check|show|rule)", "firewall"),
    (r"(?:disk|storage|space|drive).*(?:usage|check|free|full)", "disk"),
    (r"(?:memory|ram|swap).*(?:usage|check|free)", "memory"),
    (r"(?:cpu|processor|load).*(?:usage|check|load)", "cpu"),
    (r"(?:system|machine|computer).*(?:info|status|health|overview)", "system_info"),
    (r"(?:user|account|who\s+is\s+logged|w\s|who\b)", "users"),
    (r"(?:ip\s+address|my\s+ip|what.*(?:my|this).*ip)", "my_ip"),
    (r"(?:route|routing\s+table|gateway)", "routes"),
    (r"(?:arp|neighbor|mac\s+address)", "arp"),
    (r"(?:kernel|uname|os\s+version|linux\s+version)", "kernel"),
    (r"(?:cron|scheduled|crontab|job)", "cron"),
    (r"(?:service|systemctl|daemon).*(?:list|status|running|active)", "services"),
    (r"(?:wifi|wireless|wlan|iwconfig)", "wifi"),
    (r"(?:block|ban)\s+(?:ip\s+)?(\d+\.\d+\.\d+\.\d+)", "block_ip"),
    (r"(?:blocklist|blocked|banned).*(?:ip|list|show)", "blocklist"),
    (r"(?:full|complete|everything|all).*(?:audit|scan|check|report)", "full_audit"),
    (r"(?:help|what\s+can\s+you|command|menu|option)", "help"),
    (r"(?:status|health|overview)", "system_info"),
]


def match_intent(msg):
    msg_lower = msg.lower().strip()
    for pattern, intent in INTENT_MAP:
        m = re.search(pattern, msg_lower)
        if m:
            args = [g for g in m.groups() if g] if m.groups() else []
            return intent, args
    return "unknown", []


def execute_intent(intent, args):
    try:
        if intent == "scan_ip":
            ip = args[0] if args else "8.8.8.8"
            from aegis_omni import QByteEngine
            qb = QByteEngine()
            t = qb.analyze_ip(ip)
            return f"IP Analysis for {ip}:\n  Threat Score: {t.score}\n  Level: {t.level}\n  Action: {t.action}\n  Signals: {', '.join(t.signals) or 'none'}\n  Confidence: {t.confidence}"

        elif intent == "vuln_scan":
            result = vuln_full_scan()
            s = result.get("security_score", "?")
            c = result.get("critical", 0)
            w = result.get("warnings", 0)
            p = result.get("passed", 0)
            out = f"Vulnerability Scan Complete\n  Security Score: {s}/10\n  Critical: {c}  Warnings: {w}  Passed: {p}\n"
            for finding in result.get("critical_findings", []):
                out += f"\n  [CRITICAL] {finding['check']} (severity {finding['severity']})"
            for finding in result.get("warning_findings", []):
                out += f"\n  [WARNING] {finding['check']} (severity {finding['severity']})"
            return out

        elif intent == "ioc_scan":
            result = ioc_full_scan()
            return f"IOC Scan Complete\n  Compromise Likelihood: {result.get('compromise_likelihood', '?')}\n  Total Findings: {result.get('total_findings', 0)}\n  Critical: {result.get('critical', 0)}  Warnings: {result.get('warnings', 0)}  Clean: {result.get('clean', 0)}"

        elif intent == "forensics":
            result = full_forensic_capture()
            return f"Forensic Capture Complete\n  Risk Level: {result.get('risk_level', '?')}\n  Report saved to: {result.get('report_saved_to', 'N/A')}\n  Recent system file changes: {result.get('recent_changes', {}).get('total_changed', 0)}"

        elif intent == "password_audit":
            result = password_full_audit()
            return f"Password Audit Complete\n  Credential Security Score: {result.get('credential_security_score', '?')}/10\n  Critical: {result.get('critical', 0)}  Warnings: {result.get('warnings', 0)}  Passed: {result.get('passed', 0)}"

        elif intent == "payload_scan":
            result = payload_scan_web()
            return f"Payload Scan Complete\n  Files Scanned: {result.get('files_scanned', 0)}\n  Attack Detections: {result.get('total_detections', 0)}\n  Categories: {json.dumps(result.get('attack_categories', {}))}"

        elif intent == "honeypot_stats":
            result = analyze_honeypot_logs()
            if result.get("status") == "no_honeypot_data":
                return "No honeypot data yet. Run 'honeypot' command first to start capturing."
            return f"Honeypot Stats\n  Total Connections: {result.get('total_connections', 0)}\n  Unique IPs: {result.get('unique_ips', 0)}\n  Payloads Captured: {result.get('payloads_captured', 0)}"

        elif intent == "uptime":
            result = uptime_checks()
            out = f"Uptime Check: {result.get('up', 0)}/{result.get('checks', 0)} services up\n"
            for r in result.get("results", []):
                name = r.get("url") or r.get("hostname") or f"{r.get('host')}:{r.get('port')}"
                status = r.get("status", "?")
                ms = r.get("response_ms", "?")
                icon = "UP" if status in ("up", "open", "resolved", "valid") else "DOWN"
                out += f"  [{icon}] {name} — {ms}ms\n"
            return out

        elif intent == "log_analysis":
            result = analyze_system_logs()
            return f"Log Analysis Complete\n  Files Analyzed: {result.get('files_analyzed', 0)}\n  Total Findings: {result.get('total_findings', 0)}\n  Categories: {json.dumps(result.get('categories', {}))}"

        elif intent == "threat_analysis":
            result = analyze_aegis_threats()
            return f"Threat History\n  Total Events: {result.get('total_events', 0)}\n  Actions: {json.dumps(result.get('action_distribution', {}))}\n  Levels: {json.dumps(result.get('threat_levels', {}))}"

        elif intent == "hashes":
            result = hash_critical_binaries()
            out = f"Binary Integrity Check ({result.get('binaries_hashed', 0)} files)\n"
            for binary, info in result.get("hashes", {}).items():
                if isinstance(info, dict) and "sha256" in info:
                    out += f"  {binary}: {info['sha256'][:16]}...\n"
            return out

        elif intent == "whois":
            target = args[0] if args else ""
            return _run(f"whois {target} 2>/dev/null | head -40")

        elif intent == "dns_lookup":
            target = args[0] if args else ""
            return _run(f"dig {target} +short 2>/dev/null || nslookup {target} 2>/dev/null")

        elif intent == "ping":
            target = args[0] if args else ""
            return _run(f"ping -c 4 {target} 2>/dev/null")

        elif intent == "port_scan":
            target = args[0] if args else ""
            nmap = _run("which nmap 2>/dev/null")
            if nmap:
                return _run(f"nmap -T4 -F {target} 2>/dev/null", timeout=60)
            else:
                return _run(f"timeout 10 bash -c 'for p in 21 22 23 25 53 80 443 3306 5432 6379 8080 8443 9200; do (echo >/dev/tcp/{target}/$p) 2>/dev/null && echo \"Port $p: OPEN\"; done'")

        elif intent == "traceroute":
            target = args[0] if args else ""
            return _run(f"traceroute -m 15 {target} 2>/dev/null || tracepath {target} 2>/dev/null")

        elif intent == "listening_ports":
            return _run("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")

        elif intent == "connections":
            return _run("ss -tunapo 2>/dev/null | head -40")

        elif intent == "processes":
            return _run("ps aux --sort=-%cpu 2>/dev/null | head -25")

        elif intent == "firewall":
            return _run("sudo -n ufw status verbose 2>/dev/null || echo 'UFW not accessible'") + "\n" + _run("sudo -n iptables -L -n 2>/dev/null | head -30 || echo 'iptables not accessible'")

        elif intent == "disk":
            return _run("df -h 2>/dev/null")

        elif intent == "memory":
            return _run("free -h 2>/dev/null")

        elif intent == "cpu":
            return _run("top -bn1 | head -5 2>/dev/null; echo; lscpu | grep -E 'Model name|CPU\\(s\\)|MHz' 2>/dev/null")

        elif intent == "system_info":
            return _run("uname -a") + "\n" + _run("uptime") + "\n" + _run("free -h | head -2") + "\n" + _run("df -h / | tail -1")

        elif intent == "users":
            return _run("who 2>/dev/null") + "\n\nLast logins:\n" + _run("last -n 10 2>/dev/null")

        elif intent == "my_ip":
            local = _run("hostname -I 2>/dev/null")
            public = _run("curl -s --max-time 5 ifconfig.me 2>/dev/null || echo 'could not determine'")
            return f"Local IP(s): {local}\nPublic IP: {public}"

        elif intent == "routes":
            return _run("ip route 2>/dev/null || route -n 2>/dev/null")

        elif intent == "arp":
            return _run("ip neigh 2>/dev/null || arp -a 2>/dev/null")

        elif intent == "kernel":
            return _run("uname -a 2>/dev/null") + "\n" + _run("cat /etc/os-release 2>/dev/null | head -5")

        elif intent == "cron":
            return _run("crontab -l 2>/dev/null || echo 'No user crontab'") + "\n\nSystem cron:\n" + _run("ls -la /etc/cron.d/ 2>/dev/null")

        elif intent == "services":
            return _run("systemctl list-units --type=service --state=running 2>/dev/null | head -30")

        elif intent == "wifi":
            return _run("iwconfig 2>/dev/null || echo 'No wireless interfaces'") + "\n" + _run("nmcli dev wifi list 2>/dev/null | head -15 || true")

        elif intent == "block_ip":
            ip = args[0] if args else ""
            blocklist_file = Path.home() / "aegis_omni_xeon" / "data" / "blocklist.txt"
            blocklist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(blocklist_file, "a") as f:
                f.write(ip + "\n")
            return f"IP {ip} added to AEGIS blocklist."

        elif intent == "blocklist":
            blocklist_file = Path.home() / "aegis_omni_xeon" / "data" / "blocklist.txt"
            if blocklist_file.exists():
                ips = sorted(set(blocklist_file.read_text().strip().splitlines()))
                return f"Blocked IPs ({len(ips)}):\n" + "\n".join(f"  {ip}" for ip in ips)
            return "Blocklist is empty."

        elif intent == "full_audit":
            parts = []
            parts.append("=== SYSTEM STATUS ===")
            parts.append(_run("uname -a") + "\n" + _run("uptime"))
            parts.append("\n=== VULNERABILITY SCAN ===")
            v = vuln_full_scan()
            parts.append(f"Security Score: {v.get('security_score', '?')}/10  Critical: {v.get('critical', 0)}  Warnings: {v.get('warnings', 0)}")
            parts.append("\n=== IOC SCAN ===")
            i = ioc_full_scan()
            parts.append(f"Compromise Likelihood: {i.get('compromise_likelihood', '?')}  Findings: {i.get('total_findings', 0)}")
            parts.append("\n=== PASSWORD AUDIT ===")
            p = password_full_audit()
            parts.append(f"Credential Score: {p.get('credential_security_score', '?')}/10")
            parts.append("\n=== UPTIME ===")
            u = uptime_checks()
            parts.append(f"{u.get('up', 0)}/{u.get('checks', 0)} services up")
            return "\n".join(parts)

        elif intent == "help":
            return """AEGIS Chat — Ask me anything about your system's security.

Examples:
  "scan my system for vulnerabilities"
  "check for malware or compromise"
  "run a forensic capture"
  "audit my passwords"
  "scan IP 45.33.22.1"
  "what ports are listening?"
  "show my connections"
  "check firewall status"
  "port scan 192.168.1.1"
  "ping google.com"
  "lookup DNS for github.com"
  "whois 8.8.8.8"
  "traceroute to cloudflare.com"
  "show running processes"
  "check disk usage"
  "check memory"
  "block IP 1.2.3.4"
  "show blocked IPs"
  "run full audit"
  "check uptime of services"
  "analyze security logs"
  "scan for web attack payloads"
  "show honeypot stats"
  "what's my IP?"
  "check wifi networks"
  "show cron jobs"
  "show running services"
  "hash system binaries"
"""
        else:
            return f"I'm not sure what you mean. Type 'help' to see what I can do.\nYou said: {' '.join(args) if args else '(no specific target)'}"

    except Exception as e:
        return f"Error executing {intent}: {e}"


class AegisChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AEGIS AI — Security Assistant")
        self.root.geometry("900x650")
        self.root.configure(bg="#0a0a0a")
        self.root.minsize(700, 500)

        try:
            icon_path = Path(__file__).parent / "aegis_icon.png"
            if icon_path.exists():
                img = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, img)
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#111111", height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_font = tkfont.Font(family="monospace", size=14, weight="bold")
        tk.Label(header, text="AEGIS AI", font=title_font, fg="#00ff88", bg="#111111").pack(side=tk.LEFT, padx=15)
        tk.Label(header, text=f"QByte-22 v{__version__}", font=("monospace", 9), fg="#666666", bg="#111111").pack(side=tk.LEFT)

        chat_frame = tk.Frame(self.root, bg="#0a0a0a")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        chat_font = tkfont.Font(family="monospace", size=10)
        self.chat = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, bg="#0d0d0d", fg="#cccccc",
            insertbackground="#00ff88", font=chat_font,
            relief=tk.FLAT, borderwidth=0, state=tk.DISABLED,
            selectbackground="#1a3a1a", selectforeground="#00ff88",
        )
        self.chat.pack(fill=tk.BOTH, expand=True)

        self.chat.tag_configure("user", foreground="#00aaff")
        self.chat.tag_configure("aegis", foreground="#00ff88")
        self.chat.tag_configure("system", foreground="#ff6644")
        self.chat.tag_configure("dim", foreground="#555555")

        input_frame = tk.Frame(self.root, bg="#111111", height=45)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        input_frame.pack_propagate(False)

        input_font = tkfont.Font(family="monospace", size=11)
        self.entry = tk.Entry(
            input_frame, bg="#1a1a1a", fg="#ffffff",
            insertbackground="#00ff88", font=input_font,
            relief=tk.FLAT, borderwidth=8,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self._on_send)
        self.entry.focus_set()

        send_btn = tk.Button(
            input_frame, text="SEND", command=self._on_send,
            bg="#00ff88", fg="#000000", font=("monospace", 10, "bold"),
            relief=tk.FLAT, padx=15, activebackground="#00cc66",
        )
        send_btn.pack(side=tk.RIGHT)

        self._append("AEGIS", f"AEGIS AI Security Assistant v{__version__} — QByte-22 Engine\nType your request in plain language. Say 'help' for examples.\n", "aegis")

    def _append(self, sender, text, tag="dim"):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"[{sender}] ", tag)
        self.chat.insert(tk.END, text + "\n\n", tag if tag != "user" else "dim")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _on_send(self, event=None):
        msg = self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, tk.END)
        self._append("YOU", msg, "user")

        threading.Thread(target=self._process, args=(msg,), daemon=True).start()

    def _process(self, msg):
        self._append("AEGIS", "Processing...", "dim")
        intent, args = match_intent(msg)
        response = execute_intent(intent, args)
        _log_chat(msg, response)

        self.chat.config(state=tk.NORMAL)
        self.chat.delete("end-3l", "end-1l")
        self.chat.config(state=tk.DISABLED)

        self._append("AEGIS", response, "aegis")

    def run(self):
        self.root.mainloop()


def cli_chat():
    print(f"\nAEGIS AI Security Assistant v{__version__} — QByte-22 Engine")
    print("Type your request in plain language. Say 'help' for examples. 'exit' to quit.\n")

    while True:
        try:
            msg = input("YOU> ").strip()
            if msg.lower() in ("exit", "quit", "bye"):
                print("Goodbye.")
                break
            if not msg:
                continue
            intent, args = match_intent(msg)
            response = execute_intent(intent, args)
            _log_chat(msg, response)
            print(f"\n[AEGIS] {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    if "--cli" in sys.argv or not HAS_TK:
        cli_chat()
    else:
        app = AegisChatGUI()
        app.run()
