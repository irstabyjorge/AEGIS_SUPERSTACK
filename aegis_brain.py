#!/usr/bin/env python3
# Copyright (c) 2024-2026 Jorge Francisco Paredes (irstabyjorge)
# Licensed under dual MIT/Commercial license. See LICENSE and COMMERCIAL_LICENSE.md
"""
AEGIS Brain — AI-powered conversational security engine.
Connects to Claude (Anthropic) and GPT (OpenAI) APIs for real AI conversations.
Falls back to local intent matching when APIs are unavailable.
Includes persistent memory, self-learning, and auto-enhancement.
"""

__version__ = "2.0.0"

import json, os, sys, time, hashlib, threading
from pathlib import Path
from datetime import datetime, UTC

BASE = Path.home() / "aegis_omni_xeon"
BRAIN_DIR = BASE / "brain"
MEMORY_DIR = BRAIN_DIR / "memory"
KNOWLEDGE_DIR = BRAIN_DIR / "knowledge"
LOGS = BASE / "logs"
CONFIG_FILE = BRAIN_DIR / "config.json"

for d in [BRAIN_DIR, MEMORY_DIR, KNOWLEDGE_DIR, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are AEGIS AI, an autonomous cybersecurity assistant created by Jorge Francisco Paredes (irstabyjorge). You run on the user's local machine and have direct access to security tools.

Your capabilities:
- Vulnerability scanning (SUID, SSH, firewall, kernel hardening)
- Indicators of Compromise detection (processes, persistence, SSH keys)
- Digital forensics (volatile state capture, file timeline, binary hashing)
- Password & credential auditing
- Web attack payload detection (SQLi, XSS, command injection, web shells)
- Honeypot management (decoy ports with realistic banners)
- Network monitoring (connections, listeners, uptime, DNS, SSL)
- IP threat analysis with QByte-22 engine (50+ signal vectors)
- ML-based threat prediction (Random Forest on real data)
- Log analysis (auth.log, syslog pattern matching)
- Linux security tools (nmap, whois, dig, traceroute, etc.)

When the user asks you to do something security-related, explain what you're doing and provide the results. Be direct, technical, and actionable. You are a real security tool, not a simulator.

You have persistent memory — you remember past conversations and learn from them."""


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_api_keys():
    config = load_config()
    anthropic_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
    return anthropic_key, openai_key


def set_api_key(provider, key):
    config = load_config()
    config[f"{provider}_api_key"] = key
    save_config(config)


class Memory:
    def __init__(self):
        self.conversations_file = MEMORY_DIR / "conversations.jsonl"
        self.facts_file = MEMORY_DIR / "learned_facts.jsonl"
        self.scan_history_file = MEMORY_DIR / "scan_history.jsonl"

    def save_conversation(self, user_msg, assistant_msg):
        with open(self.conversations_file, "a") as f:
            f.write(json.dumps({
                "time": datetime.now(UTC).isoformat(),
                "user": user_msg[:1000],
                "assistant": assistant_msg[:2000],
            }) + "\n")

    def save_fact(self, fact, source="conversation"):
        with open(self.facts_file, "a") as f:
            f.write(json.dumps({
                "time": datetime.now(UTC).isoformat(),
                "fact": fact,
                "source": source,
            }) + "\n")

    def save_scan_result(self, scan_type, summary):
        with open(self.scan_history_file, "a") as f:
            f.write(json.dumps({
                "time": datetime.now(UTC).isoformat(),
                "type": scan_type,
                "summary": summary[:500],
            }) + "\n")

    def get_recent_conversations(self, n=10):
        if not self.conversations_file.exists():
            return []
        lines = self.conversations_file.read_text().strip().splitlines()
        entries = []
        for line in lines[-n:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return entries

    def get_facts(self):
        if not self.facts_file.exists():
            return []
        facts = []
        for line in self.facts_file.read_text().strip().splitlines():
            try:
                facts.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return facts[-50:]

    def get_context_summary(self):
        recent = self.get_recent_conversations(5)
        facts = self.get_facts()
        parts = []
        if recent:
            parts.append("Recent conversation context:")
            for c in recent[-3:]:
                parts.append(f"  User: {c['user'][:100]}")
                parts.append(f"  AEGIS: {c['assistant'][:100]}")
        if facts:
            parts.append("\nLearned facts:")
            for f in facts[-5:]:
                parts.append(f"  - {f['fact'][:100]}")
        return "\n".join(parts) if parts else ""


class AegisBrain:
    def __init__(self):
        self.memory = Memory()
        self.conversation_history = []
        self._anthropic_client = None
        self._openai_client = None

    def _get_anthropic(self):
        if self._anthropic_client is None:
            key, _ = get_api_keys()
            if key:
                try:
                    import anthropic
                    self._anthropic_client = anthropic.Anthropic(api_key=key)
                except ImportError:
                    pass
        return self._anthropic_client

    def _get_openai(self):
        if self._openai_client is None:
            _, key = get_api_keys()
            if key:
                try:
                    import openai
                    self._openai_client = openai.OpenAI(api_key=key)
                except ImportError:
                    pass
        return self._openai_client

    def _build_messages(self, user_msg):
        context = self.memory.get_context_summary()
        system = SYSTEM_PROMPT
        if context:
            system += f"\n\n{context}"

        messages = []
        for entry in self.conversation_history[-10:]:
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["assistant"]})
        messages.append({"role": "user", "content": user_msg})
        return system, messages

    def chat_claude(self, user_msg):
        client = self._get_anthropic()
        if not client:
            return None
        system, messages = self._build_messages(user_msg)
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            return f"[Claude API error: {e}]"

    def chat_openai(self, user_msg):
        client = self._get_openai()
        if not client:
            return None
        system, messages = self._build_messages(user_msg)
        oai_messages = [{"role": "system", "content": system}] + messages
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=oai_messages,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI API error: {e}]"

    def chat_local(self, user_msg):
        sys.path.insert(0, str(BASE))
        from aegis_chat import match_intent, execute_intent
        intent, args = match_intent(user_msg)
        return execute_intent(intent, args)

    def chat(self, user_msg):
        if user_msg.lower().startswith("set key anthropic "):
            key = user_msg.split("set key anthropic ", 1)[1].strip()
            set_api_key("anthropic", key)
            self._anthropic_client = None
            return "Anthropic API key saved. AEGIS can now use Claude AI."

        if user_msg.lower().startswith("set key openai "):
            key = user_msg.split("set key openai ", 1)[1].strip()
            set_api_key("openai", key)
            self._openai_client = None
            return "OpenAI API key saved. AEGIS can now use GPT."

        if user_msg.lower() in ("config", "show config", "settings"):
            ak, ok = get_api_keys()
            return f"Configuration:\n  Anthropic API: {'configured' if ak else 'not set'}\n  OpenAI API: {'configured' if ok else 'not set'}\n\nTo set keys:\n  set key anthropic sk-ant-...\n  set key openai sk-..."

        response = None

        # Try Claude first
        response = self.chat_claude(user_msg)
        if response and not response.startswith("[Claude API error"):
            source = "claude"
        else:
            # Try OpenAI
            response = self.chat_openai(user_msg)
            if response and not response.startswith("[OpenAI API error"):
                source = "openai"
            else:
                # Fall back to local
                response = self.chat_local(user_msg)
                source = "local"

        self.conversation_history.append({"user": user_msg, "assistant": response})
        self.memory.save_conversation(user_msg, response)

        if "remember" in user_msg.lower() or "learn" in user_msg.lower():
            self.memory.save_fact(user_msg, source)

        return response

    def get_provider_status(self):
        ak, ok = get_api_keys()
        return {
            "claude": "ready" if ak else "no key",
            "openai": "ready" if ok else "no key",
            "local": "always available",
        }
