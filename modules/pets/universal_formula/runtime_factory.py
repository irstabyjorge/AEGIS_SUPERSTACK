"""Convenience wiring for the bounded engine and durable local queue."""
from .runtime import RuntimeSupervisor


def build_durable_runtime(engine, queue, *, batch_size=25, idle_wait_seconds=2.0,
                          wait_fn=None, clock=None):
    """Bind queue discovery and reconciliation to a finite RuntimeSupervisor.

    The returned supervisor still requires explicit max_cycles and
    max_runtime_seconds at run time. This helper does not start a background
    service or bypass the engine PolicyGate.
    """
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    return RuntimeSupervisor(
        engine,
        task_source=lambda _health: queue.discover(engine, limit=batch_size),
        after_cycle=queue.after_cycle,
        idle_wait_seconds=idle_wait_seconds,
        wait_fn=wait_fn,
        clock=clock,
    )
