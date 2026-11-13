# PETS Universal Formula — Durable Local Work Queue

The SQLite queue stores declarative task records and leases them to a local
Universal Formula engine. It is designed for process restart and bounded
polling, not distributed execution across untrusted hosts.

## Wiring

    from modules.pets.universal_formula import (
        RuntimeSupervisor, DurableTaskQueue, build_sacred_atom_engine
    )

    engine = build_sacred_atom_engine(checkpoint_path="state/tasks.json")
    engine.load_checkpoint()  # only when a validated checkpoint already exists

    queue = DurableTaskQueue("state/work_queue.sqlite", lease_seconds=300)
    supervisor = RuntimeSupervisor(
        engine,
        task_source=lambda health: queue.discover(engine, limit=25),
        after_cycle=queue.after_cycle,
        idle_wait_seconds=2,
    )

    # Each invocation has explicit resource budgets.
    status = supervisor.run(max_cycles=500, max_runtime_seconds=3600)

Enqueue only JSON-serializable Task payloads. Handler names are identifiers
resolved against the engine's pre-registered handler map; the queue cannot
supply code or grant policy permissions. The engine's PolicyGate remains the
final authorization check.

## Recovery semantics

- SQLite uses WAL and FULL synchronous mode.
- Queue claims use an immediate transaction and expiring leases.
- A task already present in a restored engine checkpoint is not enqueued twice.
- Tasks are discovered only when their dependencies are already in the engine
  or included in the same discovery batch.
- Terminal engine outcomes reconcile queue rows as completed, failed, or blocked.
- A leased item becomes discoverable after lease expiry if the process stops
  before checkpoint/reconciliation completes.

Handlers with external side effects must be idempotent. This queue does not
provide exactly-once execution; it provides recoverable at-least-once dispatch.
Do not place credentials, personal sensitive data, or executable source in
queue payloads. Protect the database file with operating-system permissions
and backups.

## Continuous service

This component supplies durable local work storage, not an installed service.
A host supervisor must provide restart policy, bounded polling, health checks,
disk-space monitoring, backup, and a user-accessible stop control. Android
background execution and APK packaging remain separate platform work.