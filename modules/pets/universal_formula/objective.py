"""Create a reviewable, deterministic PETS objective task graph.

This planner converts an objective into explicit specialist tasks. It does not
call a model provider, infer facts, or initiate external actions.
"""
from .engine import Task
from .sacred_atom_pool import build_sacred_atom_engine


def build_objective_tasks(objective, evidence=None, domains=None, options=None):
    objective = str(objective or "").strip()
    if not objective:
        raise ValueError("objective is required")
    evidence = list(evidence or [])
    domains = list(domains or [])
    options = list(options or [])

    return [
        Task("01_scope", "ATOM_CORE", payload={"objective": objective}),
        Task("02_map", "FLOWER_MAP", depends_on=["01_scope"],
             payload={"evidence": evidence}),
        Task("03_dependencies", "METATRON_GRID", depends_on=["01_scope"],
             payload={"dependencies": {"scope": [], "map": ["scope"], "validate": ["map"]}}),
        Task("04_scenarios", "TESSERACT_FORESIGHT", depends_on=["01_scope"],
             payload={"subject": objective}),
        Task("05_cross_domain", "VESICA_BRIDGE", depends_on=["02_map"],
             payload={"domains": domains}),
        Task("06_alternatives", "ICOSA_ADAPTIVE", depends_on=["01_scope"],
             payload={"options": options}),
        Task("07_validate", "PLATONIC_VALIDATORS", depends_on=["02_map"],
             payload={"evidence": evidence}),
        Task("08_coordinate", "DODECA_COORDINATOR",
             depends_on=["03_dependencies", "04_scenarios", "05_cross_domain",
                         "06_alternatives", "07_validate"]),
        Task("09_report", "TORUS_FEEDBACK", depends_on=["08_coordinate"],
             payload={"feedback": [], "prior_output": None}),
    ]


def run_objective(objective, evidence=None, domains=None, options=None,
                  max_workers=25, checkpoint_path=None):
    engine = build_sacred_atom_engine(
        max_workers=max_workers, checkpoint_path=checkpoint_path
    )
    engine.add_tasks(build_objective_tasks(
        objective, evidence=evidence, domains=domains, options=options
    ))
    return engine, engine.run_until_blocked()
