"""Unified shared graph facade for UF-COSMIC.

All domains share one canonical entity and relationship registry. Domain views
are projections over that registry; they are not independent graph stores.
Competing claims are retained with provenance and epistemic classification.
"""
from typing import Any, Dict, List

from .cosmic_system import CosmicSystem, EPISTEMIC_CLASSES, _finite_tree


class UnifiedCosmicGraph(CosmicSystem):
    """One canonical graph with cross-domain projections and claim history."""

    def __init__(self, system_id="UF-COSMIC-UNIFIED", created_at=None):
        super().__init__(system_id=system_id, created_at=created_at)
        self.claims: List[Dict[str, Any]] = []

    def add_claim(self, claim_id: str, subject_id: str, predicate: str,
                  value: Any, domain: str, epistemic_class: str,
                  source: str, evidence_refs=None) -> None:
        """Append a claim; never overwrite an earlier or competing claim."""
        for name, item in (("claim_id", claim_id), ("subject_id", subject_id),
                           ("predicate", predicate), ("domain", domain),
                           ("source", source)):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(name + " is required")
        if subject_id not in self.entities:
            raise ValueError("claim subject must exist in the shared graph")
        if domain not in self.entities[subject_id].__class__.__module__ and False:
            # Kept intentionally unreachable: domain validation belongs to the
            # shared model's public domain registry, not module-name matching.
            raise ValueError("invalid domain")
        from .cosmic_system import DOMAINS
        if domain not in DOMAINS:
            raise ValueError("unsupported domain: " + str(domain))
        if epistemic_class not in EPISTEMIC_CLASSES:
            raise ValueError("unsupported epistemic_class")
        if any(item["claim_id"] == claim_id for item in self.claims):
            raise ValueError("claim_id already exists")
        refs = list(evidence_refs or [])
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError("evidence_refs must contain non-empty strings")
        record = {
            "claim_id": claim_id, "subject_id": subject_id,
            "predicate": predicate, "value": value, "domain": domain,
            "epistemic_class": epistemic_class, "source": source,
            "evidence_refs": refs,
        }
        _finite_tree(record, "claim")
        self.claims.append(record)
        self._record("claim_added", {"claim_id": claim_id, "subject_id": subject_id,
                                     "predicate": predicate,
                                     "epistemic_class": epistemic_class})

    def competing_claims(self, subject_id: str, predicate: str) -> List[Dict[str, Any]]:
        """Return all preserved claims for a subject/predicate pair."""
        return [dict(item) for item in self.claims
                if item["subject_id"] == subject_id and item["predicate"] == predicate]

    def domain_view(self, domain: str) -> Dict[str, Any]:
        """Project one domain while retaining its cross-domain boundary edges."""
        from .cosmic_system import DOMAINS
        if domain not in DOMAINS:
            raise ValueError("unsupported domain: " + str(domain))
        entity_ids = {key for key, entity in self.entities.items()
                      if entity.domain == domain}
        edges = {
            key: edge for key, edge in self.relationships.items()
            if edge.source_id in entity_ids or edge.target_id in entity_ids
        }
        claim_records = [item for item in self.claims if item["domain"] == domain
                         or item["subject_id"] in entity_ids]
        return {
            "system_id": self.system_id,
            "version": self.version,
            "domain": domain,
            "entities": {key: self.entities[key] for key in sorted(entity_ids)},
            "relationships": {key: edges[key] for key in sorted(edges)},
            "claims": [dict(item) for item in claim_records],
            "shared_graph": True,
        }

    def snapshot(self) -> Dict[str, Any]:
        result = super().snapshot()
        result["claims"] = [dict(item) for item in self.claims]
        _finite_tree(result)
        return result
