# Architecture baseline

## Current increment

The first implementation increment is deliberately small and deterministic:

- `domain/evidence.py`: provenance and confidence level for engineering inputs.
- `domain/dimensions.py`: validated axis-aligned metric envelope.
- `domain/fitment.py`: conservative bounding-box comparison.

The domain layer has no GUI, network, database, CAD, or AI dependency. This keeps core rules independently testable.

## Planned boundaries

1. **Presentation** — desktop UI, localization, workflows and accessibility.
2. **Application services** — use cases, orchestration, approvals and audit events.
3. **Domain** — vehicles, powertrains, interfaces, measurements, constraints and assessments.
4. **Infrastructure** — repositories, import/export, external catalogues, CAD adapters and AI providers.

Dependencies should point inward. Domain logic must not import UI or provider SDKs.

## Data provenance

Every engineering datum should carry units, source, acquisition method, timestamp, author/device where appropriate, evidence level, and revision. Conflicting sources must remain visible rather than silently overwritten.

## AI governance

AI can propose research, data changes, calculations to review, or code changes. It cannot silently apply a change. Every write action must present a human-readable diff and require explicit approval, then record who approved it and when.

## CAD and scanning roadmap

3D scanning and CAD generation are not implemented in this increment. Future work must preserve coordinate systems, scale calibration, reference points, uncertainty, source meshes, and review history. Generated parts must be marked NOT FOR MANUFACTURE until independent engineering validation.
