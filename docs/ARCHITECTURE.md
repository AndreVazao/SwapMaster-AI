# Architecture baseline

## Implemented domain increments

- `domain/evidence.py`: provenance and confidence level for engineering inputs.
- `domain/dimensions.py`: validated axis-aligned metric envelope.
- `domain/fitment.py`: conservative bounding-box comparison.
- `domain/catalog.py`: immutable records for vehicle platforms, propulsion units, transmissions, mounting points and named interfaces; deterministic interface-identity assessment.

The domain layer has no GUI, network, database, CAD, or AI dependency. This keeps core rules independently testable.

## Units and coordinate conventions

- Envelope and mounting-point dimensions are expressed in millimetres.
- Mass is kilograms, power is kilowatts, and torque is newton-metres.
- Mounting-point coordinates must name their coordinate frame. Transformations between frames are not yet implemented.
- Catalogue records carry an evidence record. At this stage, evidence applies to the record as a whole; finer per-field provenance and revision history are required before production catalogue ingestion.

## Interface assessment limits

A matching interface kind and identifier is only a preliminary identity match. It does not establish dimensional interchangeability, tolerances, bolt pattern, material suitability, load capacity, fastener specification, alignment, or safety. A positive result must never be treated as a fitment approval.

## Planned boundaries

1. **Presentation** — desktop UI, localization, workflows and accessibility.
2. **Application services** — use cases, orchestration, approvals and audit events.
3. **Domain** — vehicles, powertrains, interfaces, measurements, constraints and assessments.
4. **Infrastructure** — repositories, import/export, external catalogues, CAD adapters and AI providers.

Dependencies should point inward. Domain logic must not import UI or provider SDKs.

## Data provenance

Every engineering datum should ultimately carry units, source, acquisition method, timestamp, author/device where appropriate, evidence level, uncertainty and revision. Conflicting sources must remain visible rather than silently overwritten.

## AI governance

AI can propose research, data changes, calculations to review, or code changes. It cannot silently apply a change. Every write action must present a human-readable diff and require explicit approval, then record who approved it and when.

## CAD and scanning roadmap

3D scanning and CAD generation are not implemented. Future work must preserve coordinate systems, scale calibration, reference points, uncertainty, source meshes, and review history. Generated parts must be marked NOT FOR MANUFACTURE until independent engineering validation.
