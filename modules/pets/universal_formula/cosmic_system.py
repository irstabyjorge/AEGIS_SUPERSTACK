"""UF-COSMIC: domain-aware representation of evolving interconnected systems.

This module is a general systems representation, not a replacement for
domain-specific physical laws. Scientific observations, hypotheses, and
symbolic interpretations remain explicitly classified.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from typing import Any, Dict, List, Optional

EPISTEMIC_CLASSES = {
    "measured", "established_model", "user_report", "inference",
    "hypothesis", "symbolic_interpretation", "unknown",
}
DOMAINS = {
    "matter", "energy", "gravity", "sound", "space", "time", "life",
    "consciousness", "information", "science", "religion", "spirituality",
    "concept", "purpose", "other",
}


def _finite_tree(value: Any, path: str = "value") -> None:
    """Reject non-finite numbers and non-JSON values in model records."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(path + " must be finite")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _finite_tree(item, "%s[%d]" % (path, index))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(path + " keys must be strings")
            _finite_tree(item, path + "." + key)
        return
    raise ValueError(path + " must contain JSON-compatible values")


@dataclass(frozen=True)
class Entity:
    """A represented entity with domain-specific properties and provenance."""
    entity_id: str
    label: str
    domain: str
    properties: Dict[str, Any] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)
    epistemic_class: str = "unknown"
    source: str = "unspecified"
    observed_at: Optional[str] = None

    def validate(self) -> None:
        for name, value in (("entity_id", self.entity_id), ("label", self.label),
                            ("source", self.source)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(name + " is required")
        if self.domain not in DOMAINS:
            raise ValueError("unsupported domain: " + str(self.domain))
        if self.epistemic_class not in EPISTEMIC_CLASSES:
            raise ValueError("unsupported epistemic_class")
        if not isinstance(self.properties, dict) or not isinstance(self.units, dict):
            raise ValueError("properties and units must be objects")
        _finite_tree(self.properties, "properties")
        _finite_tree(self.units, "units")


@dataclass(frozen=True)
class Relationship:
    """A typed, directed or undirected relationship between two entities."""
    relationship_id: str
    source_id: str
    target_id: str
    relation_type: str
    directed: bool = True
    attributes: Dict[str, Any] = field(default_factory=dict)
    epistemic_class: str = "hypothesis"
    source: str = "unspecified"

    def validate(self, entity_ids) -> None:
        for name, value in (("relationship_id", self.relationship_id),
                            ("relation_type", self.relation_type),
                            ("source", self.source)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(name + " is required")
        if self.source_id not in entity_ids or self.target_id not in entity_ids:
            raise ValueError("relationship endpoints must exist")
        if self.epistemic_class not in EPISTEMIC_CLASSES:
            raise ValueError("unsupported epistemic_class")
        _finite_tree(self.attributes, "relationship.attributes")


@dataclass
class Transition:
    """A proposed state change; applying it creates a new versioned snapshot."""
    transition_id: str
    additions: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    rationale: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    epistemic_class: str = "hypothesis"


class CosmicSystem:
    """Versioned entity/relationship model with explicit provenance and history."""

    def __init__(self, system_id="UF-COSMIC", created_at=None):
        if not isinstance(system_id, str) or not system_id.strip():
            raise ValueError("system_id is required")
        self.system_id = system_id
        self.version = 0
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.purposes: List[Dict[str, Any]] = []
        self.constraints: List[Dict[str, Any]] = []
        self.possibilities: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []

    def add_entity(self, entity: Entity) -> None:
        entity.validate()
        if entity.entity_id in self.entities:
            raise ValueError("entity_id already exists")
        self.entities[entity.entity_id] = entity
        self._record("entity_added", {"entity_id": entity.entity_id})

    def connect(self, relationship: Relationship) -> None:
        relationship.validate(set(self.entities))
        if relationship.relationship_id in self.relationships:
            raise ValueError("relationship_id already exists")
        self.relationships[relationship.relationship_id] = relationship
        self._record("relationship_added", {
            "relationship_id": relationship.relationship_id,
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
        })

    def add_purpose(self, purpose_id: str, description: str, source="user_defined") -> None:
        if not purpose_id.strip() or not description.strip():
            raise ValueError("purpose_id and description are required")
        item = {"purpose_id": purpose_id, "description": description, "source": source}
        _finite_tree(item)
        if any(p["purpose_id"] == purpose_id for p in self.purposes):
            raise ValueError("purpose_id already exists")
        self.purposes.append(item)
        self._record("purpose_added", {"purpose_id": purpose_id})

    def add_constraint(self, constraint_id: str, description: str, domain="other") -> None:
        if not constraint_id.strip() or not description.strip():
            raise ValueError("constraint_id and description are required")
        item = {"constraint_id": constraint_id, "description": description, "domain": domain}
        _finite_tree(item)
        if any(c["constraint_id"] == constraint_id for c in self.constraints):
            raise ValueError("constraint_id already exists")
        self.constraints.append(item)
        self._record("constraint_added", {"constraint_id": constraint_id})

    def add_possibility(self, possibility_id: str, description: str,
                        status="hypothesis", conditions=None) -> None:
        if status not in EPISTEMIC_CLASSES:
            raise ValueError("unsupported possibility status")
        item = {"possibility_id": possibility_id, "description": description,
                "status": status, "conditions": conditions or {}}
        _finite_tree(item)
        if not possibility_id.strip() or not description.strip():
            raise ValueError("possibility_id and description are required")
        if any(p["possibility_id"] == possibility_id for p in self.possibilities):
            raise ValueError("possibility_id already exists")
        self.possibilities.append(item)
        self._record("possibility_added", {"possibility_id": possibility_id})

    def apply_transition(self, transition: Transition) -> None:
        if not transition.transition_id.strip():
            raise ValueError("transition_id is required")
        if transition.epistemic_class not in EPISTEMIC_CLASSES:
            raise ValueError("unsupported transition epistemic_class")
        candidate_ids = set(self.entities)
        for entity in transition.additions:
            entity.validate()
            if entity.entity_id in candidate_ids:
                raise ValueError("transition contains duplicate entity_id")
            candidate_ids.add(entity.entity_id)
        relationship_ids = set(self.relationships)
        for relationship in transition.relationships:
            if relationship.relationship_id in relationship_ids:
                raise ValueError("transition contains duplicate relationship_id")
            relationship.validate(candidate_ids)
            relationship_ids.add(relationship.relationship_id)
        _finite_tree(transition.evidence_refs)
        for entity in transition.additions:
            self.entities[entity.entity_id] = entity
        for relationship in transition.relationships:
            self.relationships[relationship.relationship_id] = relationship
        self._record("transition_applied", {
            "transition_id": transition.transition_id,
            "added_entities": [e.entity_id for e in transition.additions],
            "added_relationships": [r.relationship_id for r in transition.relationships],
            "rationale": transition.rationale,
            "evidence_refs": list(transition.evidence_refs),
            "epistemic_class": transition.epistemic_class,
        })

    def neighbors(self, entity_id: str) -> List[str]:
        if entity_id not in self.entities:
            raise KeyError(entity_id)
        result = []
        for edge in self.relationships.values():
            if edge.source_id == entity_id:
                result.append(edge.target_id)
            if not edge.directed and edge.target_id == entity_id:
                result.append(edge.source_id)
        return sorted(set(result))

    def _record(self, event_type, details):
        self.version += 1
        self.history.append({
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
        })

    def snapshot(self) -> Dict[str, Any]:
        result = {
            "system_id": self.system_id,
            "version": self.version,
            "created_at": self.created_at,
            "entities": {key: asdict(value) for key, value in sorted(self.entities.items())},
            "relationships": {key: asdict(value) for key, value in sorted(self.relationships.items())},
            "purposes": list(self.purposes),
            "constraints": list(self.constraints),
            "possibilities": list(self.possibilities),
            "history": list(self.history),
        }
        _finite_tree(result)
        return result

    def to_json(self) -> str:
        return json.dumps(self.snapshot(), sort_keys=True, indent=2, ensure_ascii=False)
