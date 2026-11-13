# PETS/AEGIS Sacred Atom integration

## Status

This change adds a compatibility layer on top of the merged multi-agent
orchestrator. It keeps geometry and task orchestration as separate concerns.

- `sacred_atom_geometry.py`: deterministic 19-node organizational model.
- `sacred_atom_agents.py`: bounded specialist agents and central governor.
- `sacred_atom_integration.py`: read-only adapter from geometry into the
  agents' knowledge-graph representation.

## Data flow

1. Construct and validate the geometry model.
2. Convert its nodes and edges into an in-memory `KnowledgeGraph`.
3. Dispatch only an explicitly named specialist agent.
4. Return status and results for caller review.

## Safety and epistemic boundaries

The geometry is a design metaphor, not a physical law or evidence of machine
consciousness. The adapter is local and in-memory. It does not add network
access, background execution, external actions, source writes, autonomous
memory writes, or generated-code execution. Agent capabilities remain
restricted to `read`, `analyze`, and `report`.

## Verification

Run:

```sh
python -m py_compile modules/pets/sacred_atom_geometry.py modules/pets/sacred_atom_integration.py
python -m unittest discover -s tests -p "test_sacred_atom_agents.py" -v
python -m unittest discover -s tests -p "test_sacred_atom_integration.py" -v
```

A successful source commit is not a substitute for a passing CI run or a
physical Android build.
