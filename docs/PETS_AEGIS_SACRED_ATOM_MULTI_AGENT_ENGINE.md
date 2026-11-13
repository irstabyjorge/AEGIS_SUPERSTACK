# PETS/AEGIS — Sacred Atom Multi-Agent Engine

**Status:** additive implementation proposal committed as a local orchestration library; not a daemon, service, or production deployment.

## Design intent

Treat the Sacred Atom and sacred-geometry families as independent software agents with distinct responsibilities, isolated invocation state, and a common evidence/metadata contract. Geometry is a symbolic organization and visualization model; it does not imply biological or subjective machine consciousness.

The conscious center in the Divinity–Earth Circle framework is represented operationally by a human-defined objective, policy, constraints, and approval boundary. The Circle remains the persistent field; temporary task structures branch in multiple directions and return feedback to the center.

## Agent roster

| Agent | Function | Output |
|---|---|---|
| ATOM_CORE | Decompose objectives | Bounded work packages |
| FLOWER_MAP | Map knowledge/source relationships | Knowledge graph nodes and edges |
| METATRON_GRID | Resolve dependencies | Stable dependency order; cycle rejection |
| TORUS_FEEDBACK | Compare prior output with feedback | Revision proposal; no source mutation |
| TESSERACT_FORESIGHT | Explore up to ten planning horizons | Scenario questions, not predictions |
| DODECA_COORDINATOR | Aggregate specialist results | Participation summary; disagreement remains visible |
| ICOSA_ADAPTIVE | Generate alternatives | Unselected options |
| SPIRAL_LEARNING | Extract learning candidates | Review-only learning proposal |
| VESICA_BRIDGE | Identify cross-domain links | Hypothesis-labelled candidate links |
| PLATONIC_VALIDATORS | Check provenance and epistemic labels | Validation results |
| ORBITAL_SCHEDULER | Prioritize task queue | Proposal-only queue; no background worker |
| CENTER_GOVERNOR | Enforce objective and capability boundaries | Allow/deny report |

Each agent has a unique ID, a single responsibility, a bounded input/output contract, and no authority to grant itself new permissions. The shared evidence representation requires a stable evidence ID and source label; a hash may be added by a future provenance adapter but does not independently establish authorship or legal ownership.

## Orchestration lifecycle

1. Observe the user-supplied objective and constraints.
2. Decompose it into bounded work packages.
3. Map available sources, projects, evidence, and dependencies.
4. Identify research questions; source retrieval remains an explicitly invoked adapter.
5. Classify claims as verified, unverified, inference, hypothesis, or symbolic.
6. Generate scenario questions for horizons 1–10.
7. Run independent provenance and dependency checks.
8. Aggregate results while preserving disagreement and missing data.
9. Prepare a report and proposed next actions.
10. Record learning candidates for review; never rewrite canonical memory automatically.

## Security contract

- Local deterministic library; no network calls or hidden discovery.
- No background scheduler or continuous research loop is started by this package.
- No dynamic imports, plugin loading, subprocesses, shell commands, or generated-code execution.
- Safe baseline capabilities are read, analyze, and report.
- No writes to source evidence or canonical memory.
- No external actions, publishing, messages, or permission changes.
- Privileged work requires a separate authorization layer and explicit human approval.
- Symbolic material remains separate from empirical claims.
- The engine reports operational state, not subjective consciousness.

## Integration boundary

This package is a new, additive module. It does not silently replace the earlier Sacred Atom engine in the separate open PR #8. Reconcile the two implementations only after that PR's review and merge state are resolved. Do not claim that a scheduler, persistent memory, web-research worker, mobile UI, or multi-agent runtime is installed.

## Verification

The accompanying unit tests cover agent registration, objective decomposition, bounded foresight, provenance checks, dependency-cycle rejection, capability denial, and disabled background/external execution. Run:

```bash
python -m unittest tests.test_sacred_atom_agents -v
```

Passing these unit tests validates only the pure-Python orchestration primitives. It does not validate production deployment, persistent operation, or external integrations.
