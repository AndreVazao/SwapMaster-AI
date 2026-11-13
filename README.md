# SwapMaster AI

**Engineering workspace for planning and validating engine swaps and electric-vehicle conversions.**

SwapMaster AI is an engineering-support desktop application. It is being developed in small, reviewable increments, with evidence-aware compatibility checks and explicit separation between measured, documented, estimated, and unknown data.

> **Development status:** early foundation. This repository is not a released product and must not be used as the sole basis for manufacturing or road-vehicle modifications.

## Project principles

- Never present an unverified fitment as confirmed.
- Keep source, measurement method, units, and confidence with engineering data.
- Treat mounts, adapters, battery enclosures, and drivetrain interfaces as safety-critical.
- Generate preliminary CAD only; outputs remain **NOT FOR MANUFACTURE** until independently checked and approved by qualified engineering review.
- Keep the desktop UI responsive and the calculation/domain layer testable without a GUI.
- Require explicit human approval before applying AI-proposed changes to project data or code.

## Initial technical direction

- Python 3.11+
- PySide6 desktop UI (introduced in a later implementation increment)
- Typed domain models and deterministic engineering calculations
- pytest for automated tests
- GitHub Actions for CI on hosted runners

The first increment establishes the domain foundation and CI. It intentionally does not claim automatic 3D scanning, validated CAD generation, structural analysis, homologation, or production readiness.

## Development

Create an environment and install development dependencies:

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Evidence levels

| Level | Meaning |
|---|---|
| Confirmed | Verified against a traceable, applicable source or measurement |
| Documented | Stated by a source, not independently validated |
| Estimated | Approximation with method and assumptions recorded |
| Unknown | Missing, conflicting, or insufficient evidence |

## Safety boundary

SwapMaster AI is a planning and engineering-support tool, not a substitute for vehicle-specific inspection, load calculations, material and fastener verification, fatigue/vibration assessment, professional engineering sign-off, or applicable legal approval.

## Repository

- `main`: stable integration baseline
- `develop`: active development
- Changes should be delivered through focused pull requests with tests and documentation.

## Credits

Development: André Vazão  
AI-assisted architecture and engineering support: ChatGPT
