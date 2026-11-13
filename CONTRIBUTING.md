# Contributing

## Branch strategy

- `main` is the stable integration baseline.
- `develop` is the active development branch.
- Use focused branches from `develop` for substantial changes and merge through pull requests.

## Local checks

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy src
```

## Engineering data

Never invent vehicle specifications, dimensions, material properties, or interface measurements. Record units and provenance. Label estimates explicitly. Do not convert an estimate into a confirmed value without verifiable evidence.

## Safety-critical changes

Changes affecting mounts, adapters, drivetrain, high-voltage systems, structural parts, braking, steering, or vehicle dynamics require an explicit safety review. Automated tests do not replace engineering validation.

## AI-assisted changes

AI-proposed edits must be shown as a reviewable diff. No autonomous merge, release, or silent modification of engineering data is permitted.
