# PETS Universal Formula — Continuous Execution Engine

## Purpose

Provide resumable, bounded execution of an approved objective. The initial
implementation is a deterministic task scheduler with a maximum of 25 concurrent
registered worker handlers. It is not itself a continuously running service and
does not instantiate 25 language-model agents.

## Operating model

1. Decompose an objective into tasks with stable IDs and explicit dependencies.
2. Register reviewed worker handlers; never execute generated source code.
3. Run independent ready tasks concurrently, capped at 25 workers.
4. Enforce the AEGIS policy gate before each task.
5. Retry transient handler failures only up to each task's configured attempt limit.
6. Mark tasks blocked when prerequisites fail or authorization is absent.
7. Persist an atomic JSON checkpoint after task registration and each execution wave.
8. Resume only from a validated checkpoint in a future runtime extension.

## Default authorization

Read, analyze, report, and additive working-branch changes are permitted by the
base policy. Install, deploy, publish, delete, permission changes, and external
communications remain blocked unless explicit approvals are supplied by a trusted
caller. A task payload is data, not authorization.

## Safety and integrity constraints

- Default-deny for consequential actions; least privilege.
- No network access or credential handling in the scheduler.
- No dynamic imports, shell execution, or generated-code execution.
- Preserve source files; use additive branches and reviewable changes.
- Record task status, attempts, result, and error in checkpoints.
- A hash may establish byte integrity, not authorship or legal ownership.
- Do not claim background operation: a host runtime must invoke the engine and
  provide durable storage, monitoring, and restart supervision.

## Current limitations

The module schedules local Python handlers. A production LLM worker adapter,
external durable queue, signed checkpoint verification, observability, and Android
runtime are separate deployment work and must be implemented and tested before
claiming autonomous 24/7 operation.
