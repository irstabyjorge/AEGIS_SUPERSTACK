# PETS Universal Formula — Continuous Execution Engine

## Purpose

Provide resumable, bounded execution of an approved objective. The current
implementation is a deterministic task scheduler with a configurable ceiling
of 25 concurrent task executions. It registers the existing 12 deterministic
Sacred Atom specialists as handler types; it does not instantiate 25 language
models or claim subjective AI consciousness.

## Objective workflow

Use `run_objective(...)` to construct and execute a nine-task graph:

1. Scope and decompose the objective.
2. Map supplied evidence.
3. Validate a declared dependency graph.
4. Generate ten bounded scenario questions.
5. Identify candidate cross-domain links.
6. List supplied alternatives without selecting or executing them.
7. Validate evidence provenance.
8. Aggregate actual upstream specialist outputs.
9. Produce a final feedback/report record.

The planner does not invent evidence or retrieve external sources. Evidence
must be supplied by an authorized caller with provenance fields.

## Operating model

- Decompose objectives into tasks with stable IDs and explicit dependencies.
- Register reviewed worker handlers; never execute generated source code.
- Run independent ready tasks concurrently, capped at 25.
- Pass completed dependency outputs to downstream handlers.
- Enforce the AEGIS policy gate before each task.
- Retry handler failures only up to each task's configured attempt limit.
- Block tasks when prerequisites fail or authorization is absent.
- Persist atomic JSON checkpoints after task registration and execution waves.
- Resume only from a validated checkpoint; interrupted handlers are requeued.
  Handlers that can have side effects must be idempotent.

## Default authorization

Read, analyze, report, and additive working-branch changes are permitted by
the base policy. Install, deploy, publish, delete, permission changes, and
external communications remain blocked unless explicit approvals are supplied
by a trusted caller. A task payload is data, not authorization.

## Safety and integrity constraints

- Default-deny for consequential actions; least privilege.
- No network access or credential handling in the scheduler.
- No dynamic imports, shell execution, or generated-code execution.
- Preserve source files; use additive branches and reviewable changes.
- Record task status, attempts, result, and error in checkpoints.
- A hash may establish byte integrity, not authorship or legal ownership.
- Do not claim background operation: a host runtime must invoke the engine and
  provide durable storage, monitoring, restart supervision, and a stop policy.

## Current limitations

The module schedules local Python handlers, not remote LLM instances. A
production model-provider adapter, external durable queue, signed checkpoint
verification, observability, runtime supervision, and Android deployment are
separate work and must be implemented and tested before claiming autonomous
24/7 operation. The 25-worker setting is a concurrency ceiling, not a target
that must be filled.
