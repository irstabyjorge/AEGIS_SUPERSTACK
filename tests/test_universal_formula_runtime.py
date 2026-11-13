import unittest

from modules.pets.universal_formula import ExecutionEngine, RuntimeSupervisor, Task, TaskStatus


class RuntimeSupervisorTests(unittest.TestCase):
    def test_runs_objective_then_stops_when_no_new_work(self):
        engine = ExecutionEngine({"ok": lambda payload: {"done": True}})
        batches = iter([[Task("one", "ok")], []])
        supervisor = RuntimeSupervisor(engine, task_source=lambda health: next(batches))
        result = supervisor.run(max_cycles=5, max_runtime_seconds=10)
        self.assertEqual(result["state"], "stopped")
        self.assertEqual(result["stopped_reason"], "no_new_work_available")
        self.assertEqual(result["cycle_count"], 2)
        self.assertEqual(engine.tasks["one"].status, TaskStatus.PASSED.value)

    def test_honors_cycle_budget(self):
        engine = ExecutionEngine({"ok": lambda payload: {"ok": True}})
        counter = {"value": 0}
        def discover(_health):
            counter["value"] += 1
            return [Task("task-%d" % counter["value"], "ok")]
        supervisor = RuntimeSupervisor(engine, task_source=discover)
        result = supervisor.run(max_cycles=3, max_runtime_seconds=10)
        self.assertEqual(result["cycle_count"], 3)
        self.assertEqual(result["stopped_reason"], "cycle_budget_exhausted")

    def test_stop_requested_before_work(self):
        engine = ExecutionEngine({"ok": lambda payload: {}})
        supervisor = RuntimeSupervisor(engine, task_source=lambda health: [])
        result = supervisor.run(max_cycles=10, max_runtime_seconds=10,
                                stop_requested=lambda: True)
        self.assertEqual(result["cycle_count"], 0)
        self.assertEqual(result["stopped_reason"], "stop_requested")

    def test_no_source_stops_when_known_tasks_are_terminal(self):
        engine = ExecutionEngine({"ok": lambda payload: {"ok": True}})
        engine.add_tasks([Task("one", "ok")])
        supervisor = RuntimeSupervisor(engine)
        result = supervisor.run(max_cycles=10, max_runtime_seconds=10)
        self.assertEqual(result["stopped_reason"], "all_known_tasks_terminal")
        self.assertEqual(result["cycle_count"], 1)

    def test_captures_discovery_errors(self):
        engine = ExecutionEngine({"ok": lambda payload: {}})
        def broken(_health):
            raise RuntimeError("source unavailable")
        supervisor = RuntimeSupervisor(engine, task_source=broken)
        result = supervisor.run(max_cycles=2, max_runtime_seconds=10)
        self.assertEqual(result["state"], "error")
        self.assertEqual(result["stopped_reason"], "execution_error")
        self.assertIn("source unavailable", result["last_error"])


if __name__ == "__main__":
    unittest.main()
