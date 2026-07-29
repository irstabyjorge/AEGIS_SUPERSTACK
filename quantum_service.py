import asyncio, json, os, time, random
from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "nats://nats.aegis.svc.cluster.local:4222")
BLOCK_RISK = float(os.getenv("BLOCK_RISK", "0.90"))


def quantum_security_decision(event):
    base = float(
        event.get("risk_score", event.get("task", {}).get("risk_score", 0.35))
    )
    payload = event.get("payload", event.get("task", {}).get("payload", {}))
    signals = sum(
        1
        for k in (
            "failed_auth",
            "new_device",
            "impossible_travel",
            "crypto_port",
            "suspicious_ip",
        )
        if payload.get(k)
    )
    threat = min(1.0, base + signals * 0.12 + random.uniform(0, 0.03))
    action = (
        "block"
        if threat >= BLOCK_RISK
        else "challenge_mfa"
        if threat >= 0.72
        else "allow"
    )
    return {
        "stage": "quantum_security_complete",
        "threat_level": "HIGH" if threat >= 0.9 else "MEDIUM" if threat >= 0.72 else "LOW",
        "confidence": round(threat, 4),
        "action": action,
        "event": event,
        "ts": time.time(),
    }


async def main():
    nc = NATS()
    await nc.connect(NATS_URL)

    async def handler(msg):
        decision = quantum_security_decision(json.loads(msg.data.decode()))
        await nc.publish("scheduler.feedback", json.dumps(decision).encode())
        await nc.publish("security.alerts", json.dumps(decision).encode())

    await nc.subscribe("tasks.quantum", cb=handler)

    while True:
        await asyncio.sleep(1)


asyncio.run(main())
