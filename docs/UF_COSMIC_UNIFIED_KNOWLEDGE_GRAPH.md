# UF-COSMIC Unified Knowledge Graph

## Core invariant

UF-COSMIC uses one canonical entity registry and one canonical relationship registry across all represented domains. A domain view is a projection over that shared graph; it is not a separately owned graph or a copied source of truth.

**One connected whole; many domain perspectives; one provenance-aware state.**

## Shared model

- Entities have stable IDs, domain labels, typed properties, units, source provenance, and epistemic classification.
- Relationships connect canonical entity IDs and may cross domain boundaries.
- Claims are append-only records. Multiple claims for the same subject and predicate are retained, including contradictory claims.
- Evidence references and source labels remain attached to each claim.
- Domain views expose their entities plus every relationship touching those entities, preserving cross-domain boundary edges.
- The full snapshot contains all domains, relationships, claims, and history.

## Epistemic handling

Claims retain one of the supported classes: measured, established_model, user_report, inference, hypothesis, symbolic_interpretation, or unknown. Adding a claim does not promote it to a stronger class. Conflicts are surfaced through competing_claims; they are not silently resolved or overwritten.

A source string and evidence reference are provenance pointers, not proof that a claim is true. Downstream validation must inspect the referenced material.

## Example

    from modules.pets.universal_formula import Entity, Relationship, UnifiedCosmicGraph

    graph = UnifiedCosmicGraph()
    graph.add_entity(Entity("earth", "Earth", "space", epistemic_class="established_model", source="curated reference"))
    graph.add_entity(Entity("life", "Living systems", "life", epistemic_class="established_model", source="curated reference"))
    graph.connect(Relationship("earth-life", "earth", "life", "ecological_context", epistemic_class="established_model", source="curated reference"))

    space_projection = graph.domain_view("space")
    life_projection = graph.domain_view("life")

Both projections reference the same canonical Earth/Life entities and shared cross-domain relationship. They do not create independent graph copies.

## Boundaries

This is a software data model, not a claim that all physical domains obey one equation or that the graph establishes universal consciousness. Physical models keep their own laws, units, assumptions, and uncertainty. Symbolic and spiritual records remain distinguishable from empirical measurements.

The graph does not autonomously collect external data, infer hidden links, contact institutions, or execute external actions. Inputs must be supplied through authorized, provenance-preserving workflows.
