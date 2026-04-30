#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Chat — AI-powered security assistant with desktop GUI.
Talk to AEGIS like you talk to Claude or ChatGPT.
Uses Anthropic Claude API / OpenAI GPT API with local fallback.
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
    (r"(?:set\s+key|api\s+key|configure\s+key)", "set_key"),
    (r"(?:config|settings|show\s+config)", "show_config"),
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
            for f in result.get("critical_findings", []):
                out += f"\n  [CRITICAL] {f['check']} (severity {f['severity']})"
            for f in result.get("warning_findings", []):
                out += f"\n  [WARNING] {f['check']} (severity {f['severity']})"
            return out
        elif intent == "ioc_scan":
            result = ioc_full_scan()
            return f"IOC Scan Complete\n  Compromise Likelihood: {result.get('compromise_likelihood', '?')}\n  Total Findings: {result.get('total_findings', 0)}\n  Critical: {result.get('critical', 0)}  Warnings: {result.get('warnings', 0)}  Clean: {result.get('clean', 0)}"
        elif intent == "forensics":
            result = full_forensic_capture()
            return f"Forensic Capture Complete\n  Risk Level: {result.get('risk_level', '?')}\n  Report saved to: {result.get('report_saved_to', 'N/A')}"
        elif intent == "password_audit":
            result = password_full_audit()
            return f"Password Audit Complete\n  Credential Security Score: {result.get('credential_security_score', '?')}/10\n  Critical: {result.get('critical', 0)}  Warnings: {result.get('warnings', 0)}  Passed: {result.get('passed', 0)}"
        elif intent == "payload_scan":
            result = payload_scan_web()
            return f"Payload Scan Complete\n  Files Scanned: {result.get('files_scanned', 0)}\n  Attack Detections: {result.get('total_detections', 0)}"
        elif intent == "honeypot_stats":
            result = analyze_honeypot_logs()
            if result.get("status") == "no_honeypot_data":
                return "No honeypot data yet. Start the honeypot first."
            return f"Honeypot Stats\n  Total Connections: {result.get('total_connections', 0)}\n  Unique IPs: {result.get('unique_ips', 0)}"
        elif intent == "uptime":
            result = uptime_checks()
            out = f"Uptime: {result.get('up', 0)}/{result.get('checks', 0)} services up\n"
            for r in result.get("results", []):
                name = r.get("url") or r.get("hostname") or f"{r.get('host')}:{r.get('port')}"
                status = r.get("status", "?")
                ms = r.get("response_ms", "?")
                icon = "UP" if status in ("up", "open", "resolved", "valid") else "DOWN"
                out += f"  [{icon}] {name} - {ms}ms\n"
            return out
        elif intent == "log_analysis":
            result = analyze_system_logs()
            return f"Log Analysis\n  Files: {result.get('files_analyzed', 0)}\n  Findings: {result.get('total_findings', 0)}\n  Categories: {json.dumps(result.get('categories', {}))}"
        elif intent == "threat_analysis":
            result = analyze_aegis_threats()
            return f"Threat History\n  Events: {result.get('total_events', 0)}\n  Actions: {json.dumps(result.get('action_distribution', {}))}"
        elif intent == "hashes":
            result = hash_critical_binaries()
            out = f"Binary Integrity ({result.get('binaries_hashed', 0)} files)\n"
            for b, info in result.get("hashes", {}).items():
                if isinstance(info, dict) and "sha256" in info:
                    out += f"  {b}: {info['sha256'][:16]}...\n"
            return out
        elif intent == "whois":
            return _run(f"whois {args[0]} 2>/dev/null | head -40") if args else "Usage: whois <domain or IP>"
        elif intent == "dns_lookup":
            return _run(f"dig {args[0]} +short 2>/dev/null || nslookup {args[0]} 2>/dev/null") if args else "Usage: lookup <domain>"
        elif intent == "ping":
            return _run(f"ping -c 4 {args[0]} 2>/dev/null") if args else "Usage: ping <host>"
        elif intent == "port_scan":
            target = args[0] if args else ""
            if _run("which nmap 2>/dev/null"):
                return _run(f"nmap -T4 -F {target} 2>/dev/null", timeout=60)
            return _run(f"timeout 10 bash -c 'for p in 21 22 23 25 53 80 443 3306 5432 6379 8080 8443 9200; do (echo >/dev/tcp/{target}/$p) 2>/dev/null && echo \"Port $p: OPEN\"; done'")
        elif intent == "traceroute":
            return _run(f"traceroute -m 15 {args[0]} 2>/dev/null || tracepath {args[0]} 2>/dev/null") if args else "Usage: traceroute <host>"
        elif intent == "listening_ports":
            return _run("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")
        elif intent == "connections":
            return _run("ss -tunapo 2>/dev/null | head -40")
        elif intent == "processes":
            return _run("ps aux --sort=-%cpu 2>/dev/null | head -25")
        elif intent == "firewall":
            return _run("sudo -n ufw status verbose 2>/dev/null || echo 'UFW not accessible'")
        elif intent == "disk":
            return _run("df -h 2>/dev/null")
        elif intent == "memory":
            return _run("free -h 2>/dev/null")
        elif intent == "cpu":
            return _run("top -bn1 | head -5 2>/dev/null; lscpu | grep -E 'Model name|CPU' 2>/dev/null")
        elif intent == "system_info":
            return _run("uname -a") + "\n" + _run("uptime") + "\n" + _run("free -h | head -2") + "\n" + _run("df -h / | tail -1")
        elif intent == "users":
            return _run("who 2>/dev/null") + "\n\nRecent:\n" + _run("last -n 10 2>/dev/null")
        elif intent == "my_ip":
            local = _run("hostname -I 2>/dev/null")
            public = _run("curl -s --max-time 5 ifconfig.me 2>/dev/null || echo 'unavailable'")
            return f"Local: {local}\nPublic: {public}"
        elif intent == "routes":
            return _run("ip route 2>/dev/null")
        elif intent == "arp":
            return _run("ip neigh 2>/dev/null")
        elif intent == "kernel":
            return _run("uname -a") + "\n" + _run("cat /etc/os-release 2>/dev/null | head -5")
        elif intent == "cron":
            return _run("crontab -l 2>/dev/null || echo 'No crontab'") + "\n\n" + _run("ls /etc/cron.d/ 2>/dev/null")
        elif intent == "services":
            return _run("systemctl list-units --type=service --state=running 2>/dev/null | head -30")
        elif intent == "wifi":
            return _run("iwconfig 2>/dev/null || echo 'No wireless'") + "\n" + _run("nmcli dev wifi list 2>/dev/null | head -15 || true")
        elif intent == "block_ip":
            ip = args[0] if args else ""
            bf = Path.home() / "aegis_omni_xeon" / "data" / "blocklist.txt"
            bf.parent.mkdir(parents=True, exist_ok=True)
            with open(bf, "a") as f:
                f.write(ip + "\n")
            return f"IP {ip} added to AEGIS blocklist."
        elif intent == "blocklist":
            bf = Path.home() / "aegis_omni_xeon" / "data" / "blocklist.txt"
            if bf.exists():
                ips = sorted(set(bf.read_text().strip().splitlines()))
                return f"Blocked IPs ({len(ips)}):\n" + "\n".join(f"  {ip}" for ip in ips)
            return "Blocklist is empty."
        elif intent == "full_audit":
            parts = ["=== FULL SECURITY AUDIT ==="]
            v = vuln_full_scan()
            parts.append(f"\nVulnerability Score: {v.get('security_score', '?')}/10  Critical: {v.get('critical', 0)}")
            i = ioc_full_scan()
            parts.append(f"IOC Likelihood: {i.get('compromise_likelihood', '?')}  Findings: {i.get('total_findings', 0)}")
            p = password_full_audit()
            parts.append(f"Credential Score: {p.get('credential_security_score', '?')}/10")
            u = uptime_checks()
            parts.append(f"Uptime: {u.get('up', 0)}/{u.get('checks', 0)} services up")
            return "\n".join(parts)
        elif intent == "set_key":
            return "To configure API keys, type:\n  set key anthropic sk-ant-...\n  set key openai sk-..."
        elif intent == "show_config":
            return "Type 'config' to see current settings."
        elif intent == "help":
            return """AEGIS AI — Talk to me naturally. Examples:

Security Scans:
  "scan my system for vulnerabilities"
  "check for malware"      "run forensics"
  "audit passwords"        "scan for web attacks"
  "show honeypot stats"    "hash system binaries"

Network:
  "scan IP 1.2.3.4"        "port scan 192.168.1.1"
  "what ports are open?"   "show connections"
  "ping google.com"        "traceroute 8.8.8.8"
  "lookup DNS github.com"  "whois cloudflare.com"
  "block IP 1.2.3.4"       "show blocked IPs"

System:
  "check disk/memory/cpu"  "show processes"
  "firewall status"        "check wifi"
  "show services"          "who is logged in"
  "what's my IP?"          "show cron jobs"

AI:
  "set key anthropic sk-ant-..."  (enable Claude AI)
  "set key openai sk-..."         (enable GPT AI)
  "config"                        (show settings)

Or just ask me anything — I'll figure it out!"""
        else:
            return None
    except Exception as e:
        return f"Error: {e}"


class AegisChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AEGIS AI — Security Assistant")
        self.root.geometry("950x700")
        self.root.configure(bg="#0a0a0a")
        self.root.minsize(700, 500)

        try:
            icon_path = Path(__file__).parent / "aegis_icon.svg"
            if icon_path.exists():
                pass
        except Exception:
            pass

        self.brain = None
        try:
            from aegis_brain import AegisBrain
            self.brain = AegisBrain()
        except Exception:
            pass

        self._build_ui()
        self._show_welcome()

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#111111", height=55)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        tk.Label(header, text=" AEGIS AI", font=title_font, fg="#00ff88", bg="#111111").pack(side=tk.LEFT, padx=10)

        sub_font = tkfont.Font(family="Helvetica", size=9)
        status_text = "QByte-22 Engine"
        if self.brain:
            providers = self.brain.get_provider_status()
            if providers.get("claude") == "ready":
                status_text += " | Claude AI"
            if providers.get("openai") == "ready":
                status_text += " | GPT"
        tk.Label(header, text=status_text, font=sub_font, fg="#555555", bg="#111111").pack(side=tk.LEFT, padx=5)

        ver_label = tk.Label(header, text=f"v{__version__}", font=sub_font, fg="#333333", bg="#111111")
        ver_label.pack(side=tk.RIGHT, padx=15)

        chat_frame = tk.Frame(self.root, bg="#0a0a0a")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 4))

        chat_font = tkfont.Font(family="Consolas", size=11)
        self.chat = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, bg="#0d0d0d", fg="#cccccc",
            insertbackground="#00ff88", font=chat_font,
            relief=tk.FLAT, borderwidth=0, state=tk.DISABLED,
            selectbackground="#1a3a1a", selectforeground="#00ff88",
            padx=12, pady=10, spacing3=4,
        )
        self.chat.pack(fill=tk.BOTH, expand=True)

        self.chat.tag_configure("user_label", foreground="#00aaff", font=tkfont.Font(family="Consolas", size=11, weight="bold"))
        self.chat.tag_configure("user_text", foreground="#ffffff")
        self.chat.tag_configure("aegis_label", foreground="#00ff88", font=tkfont.Font(family="Consolas", size=11, weight="bold"))
        self.chat.tag_configure("aegis_text", foreground="#cccccc")
        self.chat.tag_configure("system", foreground="#ff6644", font=tkfont.Font(family="Consolas", size=10))
        self.chat.tag_configure("dim", foreground="#555555", font=tkfont.Font(family="Consolas", size=9))
        self.chat.tag_configure("thinking", foreground="#666666", font=tkfont.Font(family="Consolas", size=10, slant="italic"))

        input_frame = tk.Frame(self.root, bg="#151515", height=55)
        input_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        input_frame.pack_propagate(False)

        input_font = tkfont.Font(family="Consolas", size=12)
        self.entry = tk.Entry(
            input_frame, bg="#1a1a1a", fg="#ffffff",
            insertbackground="#00ff88", font=input_font,
            relief=tk.FLAT, borderwidth=10,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", self._on_send)
        self.entry.focus_set()

        send_btn = tk.Button(
            input_frame, text=" SEND ", command=self._on_send,
            bg="#00ff88", fg="#000000", font=("Consolas", 11, "bold"),
            relief=tk.FLAT, padx=20, pady=5,
            activebackground="#00cc66", cursor="hand2",
        )
        send_btn.pack(side=tk.RIGHT, pady=8)

    def _show_welcome(self):
        self._append_aegis(f"""Welcome to AEGIS AI Security Assistant v{__version__}

Talk to me like you'd talk to Claude or ChatGPT.
I can scan your system, analyze threats, check networks, and more.

Type 'help' for examples, or just ask me anything!""")

        if self.brain:
            providers = self.brain.get_provider_status()
            if providers.get("claude") == "ready" or providers.get("openai") == "ready":
                active = [k for k, v in providers.items() if v == "ready"]
                self._append_system(f"AI engines active: {', '.join(active)}")
            else:
                self._append_system("No AI API keys configured. Using local engine.\nType: set key anthropic YOUR_KEY  or  set key openai YOUR_KEY")

    def _append_user(self, text):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "You\n", "user_label")
        self.chat.insert(tk.END, text + "\n\n", "user_text")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _append_aegis(self, text):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "AEGIS\n", "aegis_label")
        self.chat.insert(tk.END, text + "\n\n", "aegis_text")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _append_system(self, text):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, text + "\n\n", "dim")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _append_thinking(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, "AEGIS\n", "aegis_label")
        self.chat.insert(tk.END, "Thinking...\n\n", "thinking")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def _remove_thinking(self):
        self.chat.config(state=tk.NORMAL)
        content = self.chat.get("1.0", tk.END)
        lines = content.split("\n")
        new_lines = []
        skip_next = False
        for i, line in enumerate(lines):
            if line.strip() == "Thinking..." and i > 0 and lines[i-1].strip() == "AEGIS":
                new_lines.pop()
                skip_next = True
                continue
            if skip_next and line.strip() == "":
                skip_next = False
                continue
            skip_next = False
            new_lines.append(line)
        self.chat.delete("1.0", tk.END)
        self.chat.insert("1.0", "\n".join(new_lines))
        self.chat.config(state=tk.DISABLED)

    def _on_send(self, event=None):
        msg = self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, tk.END)
        self._append_user(msg)
        self._append_thinking()
        threading.Thread(target=self._process, args=(msg,), daemon=True).start()

    def _process(self, msg):
        response = None

        if self.brain:
            response = self.brain.chat(msg)
        else:
            intent, args = match_intent(msg)
            local_result = execute_intent(intent, args)
            if local_result:
                response = local_result
            else:
                response = f"I understood your request but couldn't process it. Try 'help' for examples."

        self.root.after(0, self._show_response, response)

    def _show_response(self, response):
        self._remove_thinking()
        self._append_aegis(response)

    def run(self):
        self.root.mainloop()


def cli_chat():
    brain = None
    try:
        from aegis_brain import AegisBrain
        brain = AegisBrain()
    except Exception:
        pass

    print(f"\nAEGIS AI Security Assistant v{__version__} — QByte-22 Engine")
    if brain:
        providers = brain.get_provider_status()
        active = [k for k, v in providers.items() if v == "ready"]
        print(f"AI engines: {', '.join(active) if active else 'local only'}")
    print("Talk naturally. 'help' for examples. 'exit' to quit.\n")

    while True:
        try:
            msg = input("You> ").strip()
            if msg.lower() in ("exit", "quit", "bye"):
                print("Goodbye.")
                break
            if not msg:
                continue

            if brain:
                response = brain.chat(msg)
            else:
                intent, args = match_intent(msg)
                response = execute_intent(intent, args) or "Unknown request. Try 'help'."

            print(f"\nAEGIS> {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break


if __name__ == "__main__":
    if "--cli" in sys.argv or not HAS_TK:
        cli_chat()
    else:
        app = AegisChatGUI()
        app.run()
