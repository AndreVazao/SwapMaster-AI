# Architecture baseline

## Implemented domain increments

- `domain/evidence.py`: provenance and confidence level for engineering inputs.
- `domain/dimensions.py`: validated axis-aligned metric envelope.
- `domain/fitment.py`: conservative bounding-box comparison.
- `domain/catalog.py`: immutable records for vehicle platforms, propulsion units, transmissions, mounting points and named interfaces; deterministic interface-identity assessment.
- `domain/measurement.py`: field-level values with explicit units, evidence, absolute uncertainty and immutable revision history; required-data readiness gate.
- `infrastructure/persistence/sqlite.py`: SQLite schema migration v1, append-only measurement repository, consistent backup, validated atomic restore and all-or-nothing history import.\n- `infrastructure/persistence/measurement_json.py`: strict schema-v1 JSON export/import with deterministic ordering, duplicate-key rejection and domain-model validation.

The domain layer has no GUI, network, database, CAD, or AI dependency. Infrastructure adapts persistence to domain records.

## Units and coordinate conventions

- Envelope and mounting-point dimensions are expressed in millimetres.
- Mass is kilograms, power is kilowatts, and torque is newton-metres.
- Measurement units are explicit and never silently converted.
- Mounting-point coordinates must name their coordinate frame. Transformations between frames are not yet implemented.
- Catalogue-level evidence is retained for backward compatibility; new measurement workflows should use field-level `EngineeringDatum` records.

## Measurement provenance and revision history

Each datum stores a field path, numeric value (or explicit unknown), unit, evidence level, uncertainty, revision, timestamp and optional operator/source reference. Histories are immutable, contiguous and unit-consistent. Corrections append a new revision rather than overwriting prior evidence. Unit changes require an explicit migration.

The required-data gate returns blocked when a required value is absent, review-required when evidence is estimated/documented or uncertainty is unstated, and ready-for-engineering-review only when all required values are confirmed with uncertainty. The last state is not a fitment or safety approval.

## Persistence boundary

SQLite is the initial local persistence adapter. Schema migrations are versioned through `PRAGMA user_version` and recorded in `schema_migrations`. Measurement revisions use a composite primary key and are inserted in an explicit immediate transaction. The repository rejects revision overwrites and gaps. This is a local single-process persistence foundation, not yet a synchronized multi-user database or a full audit/event system. File backups use SQLite's online backup API and are integrity/schema checked before atomic publication. Restore validates the source and stages it beside the destination before `os.replace`; callers must close all destination users first. WAL sidecars block replacement. This does not provide encryption-at-rest, backup scheduling, retention, off-site replication, or recovery-point guarantees. Measurement histories can be exported as deterministic JSON schema v1. Import rejects unknown versions, extra/missing keys, duplicate JSON keys and duplicate field paths, and validates each datum through the domain models. Repository import is transactional and rejects any existing field path rather than merging or overwriting it.

## Interface assessment limits

A matching interface kind and identifier is only a preliminary identity match. It does not establish dimensional interchangeability, tolerances, bolt pattern, material suitability, load capacity, fastener specification, alignment, or safety. A positive result must never be treated as a fitment approval.

## Application service boundary\n\n`application/measurement_service.py` exposes measurement recording, history retrieval, readiness assessment and JSON import/export through a repository protocol. The desktop presentation should call this service rather than SQLite directly. Domain validation remains authoritative; repository conflicts are surfaced to the caller and import is all-or-nothing.\n\n## Planned boundaries

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


### Compatibility screening

The domain-level `assess_powertrain_candidate` composes existing envelope and interface assessments with a torque-limit check. It returns named criterion results and a conservative aggregate status. Checks not yet implemented (mounting transformations and transmission packaging) are represented as `NOT_ASSESSED`, which prevents a positive candidate result. The service has no database, network or UI dependencies.
