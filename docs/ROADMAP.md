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
- [ ] Vehicle and powertrain catalogue with source traceability
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
