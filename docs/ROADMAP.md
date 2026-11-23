# Roadmap

This roadmap is directional. An item is complete only when code, tests, documentation, and review evidence exist in the repository.

## Foundation
- [x] Repository baseline and development branch
- [x] Evidence-level model
- [x] Metric 3D envelope model
- [x] Conservative preliminary envelope assessment
- [x] Hosted CI on Windows and Linux
- [x] Initial typed records for vehicle platforms, power units, transmissions, mounting points and interfaces
- [x] Conservative interface-identity assessment
- [x] Field-level measurement records with explicit units and uncertainty
- [x] Immutable, contiguous measurement revision history
- [x] Required-data readiness gate
- [x] SQLite schema migration v1 and append-only measurement repository
- [ ] Per-field source conflict resolution and audit events
- [x] SQLite online backup and validated atomic restore (local file workflow)
- [ ] Encryption-at-rest strategy, backup scheduling, retention and off-site recovery
- [x] Strict versioned JSON export/import for measurement histories (schema v1, transactional no-overwrite import)

## Engineering workflows
- [x] Initial application service for measurement recording, readiness and JSON interchange\n- [ ] Vehicle and powertrain catalogue with source traceability
- [ ] Multi-constraint packaging and interface checks
- [ ] EV conversion planning and high-voltage safety checklist
- [ ] Measurement and 3D scan import workflow
- [ ] CAD adapter and preliminary parametric outputs
- [ ] Engineering review, sign-off and audit trail

## Product experience
- [ ] Desktop shell and navigation
- [ ] Simple, Technical and Workshop workflows
- [ ] Portuguese (Portugal) default localization and language packs
- [ ] ONER assistant with approval-gated changes
- [ ] Packaging, installer, update and recovery flows

## Release gates
- [ ] Domain and application test coverage
- [ ] Windows packaging and clean-machine installation tests
- [ ] Security and dependency review
- [ ] Engineering validation of every published calculation
- [ ] Legal, privacy and licensing review


## Compatibility screening increment

- Deterministic first-pass assessment for engine-bay envelope, bellhousing identity and declared torque limit.
- Missing evidence blocks a positive screening result; known mismatches mark the combination incompatible.
- Mounting geometry and transmission packaging are explicitly not assessed and force engineering review.
- This is not a fitment, safety, roadworthiness or manufacturing approval.


## CAD, visualization and manufacturing outputs (product requirement)

The product goal is to support the user from engine/vehicle selection through preliminary design of engine mounts, bellhousing adapters, plates, spacers and related swap components, with reviewable visualization and multi-format technical output. This is a roadmap requirement, not an implemented capability.

### Planned output formats
- **PDF**: readable technical drawing/report with orthographic views, sections, dimensions, tolerances, materials, notes, revision, evidence and engineering status.
- **SVG**: vector 2D profiles and presentation geometry where suitable; not a substitute for process-specific CAM validation.
- **DXF**: 2D manufacturing exchange for compatible CAD/CAM, laser/plasma/CNC workflows; validate units, scale, layers, kerf, nesting and machine/process constraints separately.
- **STEP (.step/.stp)**: interoperable solid model for downstream CAD inspection and editing.
- **STL / 3MF**: mesh exports for visualization/prototyping; never imply printed parts are structurally suitable merely because the mesh is valid.
- **Project JSON**: parameters, geometry, references, evidence/provenance, units, uncertainty, revisions and approvals.

### Planned CAD workflow
1. Gather verified engine, gearbox and vehicle data; ask for missing critical measurements.
2. Establish coordinate frames and calibrated scan/measurement references.
3. Create parametric design templates for mounts, adapter plates, bellhousing adapters and spacers.
4. Assemble the swap in an interactive 3D viewer; check placement, alignment, clearances and interference.
5. Run geometry and design-rule checks; structural adequacy remains a separate review/analysis scope.
6. Generate drawings and export formats from a single versioned source model.
7. Package outputs with revision, provenance, validation report and human approval record.

### Roadmap status
- [x] Conservative mounting-point set comparison (same explicitly registered datum; no transforms inferred)\n- [x] Explicit rigid coordinate transforms between named frames; measured registration workflow remains pending
- [ ] Installed powertrain placement / packaging model
- [ ] 3D scan/mesh import, scale calibration and datum registration
- [ ] CAD backend selection and parametric model abstraction
- [ ] Parametric mount and adapter/bellhousing templates
- [ ] Interactive 3D assembly viewer and interference checks
- [ ] Technical drawing generation (PDF)
- [ ] 2D exports (SVG and DXF) with process-specific checks
- [ ] Solid/mesh exports (STEP, STL, 3MF)
- [ ] Revision-controlled engineering package and approval gate

**Release gate:** all generated design/drawing/mesh outputs remain **PRELIMINARY — NOT FOR MANUFACTURE — ENGINEERING REVIEW REQUIRED** until an explicit documented engineering review is recorded. Automated geometric checks are not structural validation, alignment certification, vehicle approval or manufacturing release.


## Mounting-point geometry screening increment

Implemented comparison of two named 3D mounting-point sets only after caller explicitly declares a common registered datum and both sets use that frame. Coordinate tolerance is axis-wise in millimetres. Identifier correspondence is checked but coordinates must also match. Missing data, frame mismatch, point-count/ID mismatch and geometry mismatch are explicit outcomes. Confirmed geometry yields only a preliminary geometry match; non-confirmed evidence forces review. No coordinate transformations, structural/load-path assessment, fastener/weld design or dynamic-clearance checks are implemented.
