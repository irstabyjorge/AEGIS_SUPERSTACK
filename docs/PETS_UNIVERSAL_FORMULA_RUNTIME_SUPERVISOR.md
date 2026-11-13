# PETS Universal Formula Runtime Supervisor

The `RuntimeSupervisor` repeatedly discovers work and invokes the bounded
`ExecutionEngine`. It is a finite execution loop, not a perpetual daemon and
not a claim of continuous consciousness or autonomous self-modification.

## Universal Formula cycle

Each cycle evaluates the current state, objective, constraints, and verified
history; discovers eligible work; executes registered handlers; checkpoints
the engine state; and evaluates whether useful work remains.

```
OBSERVE STATE -> EVALUATE OBJECTIVE -> DISCOVER WORK -> CHECK POLICY
      ^                                           |
      |                                           v
UPDATE VERIFIED HISTORY <- VALIDATE <- EXECUTE AUTHORIZED TASKS
      |
      +-- repeat while useful, feasible work remains and budgets permit
```

## Finite operation

Callers must provide `max_cycles` and `max_runtime_seconds`. The optional
`stop_requested` callback is checked between cycles. A handler already running
is allowed to finish; the supervisor does not kill worker threads. Optional
idle waiting is bounded by the remaining runtime budget.

The supervisor stops on a requested stop, elapsed-time budget, cycle budget,
known-task completion (when no discovery source is configured), no newly
available work, or an execution error. Its health snapshot reports the reason.

## Discovery contract

A local `task_source(health_snapshot)` returns a batch of new `Task` objects.
It must use stable unique task IDs and should be deterministic/idempotent.
Discovery cannot grant permissions: each task still passes the engine's
`PolicyGate`. Protected actions such as publish, deploy, delete, permission
changes, external communication, and installation remain blocked unless an
independent trusted authorization mechanism explicitly approves them.

## Persistence and limits

Use the engine's checkpoint path for durable task state. The supervisor itself
does not persist external queues, create model agents, access a network, execute
generated code, or run as a background service. A host service, durable queue,
monitoring, signed checkpoint verification, and platform-specific deployment
remain separate engineering work. The configured 25-worker limit is a ceiling
on concurrent registered task handlers, not 25 language models.
