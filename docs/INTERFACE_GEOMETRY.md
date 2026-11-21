# Measured drivetrain interface geometry

## Purpose

The interface geometry module screens a measured engine-to-gearbox mating-face pattern. It compares nominal bolt-hole centres, hole diameters, and an optional pilot diameter.

## Required measurement discipline

- Use a documented coordinate frame and physical datum on both parts.
- Record the measurement method, instrument, calibration, units and uncertainty in the measurement register.
- Do not compare coordinates from unrelated datums.
- Do not assume rotation, mirroring, scaling or translation; a future transform workflow must be explicit and independently checked.
- The current comparison uses millimetres and a caller-supplied absolute tolerance.

## Interpretation

- INSUFFICIENT_DATA: a geometry, hole pattern, or pilot measurement is missing.
- DATUM_MISMATCH: the coordinate-frame identifiers differ.
- HOLE_COUNT_MISMATCH: the patterns have different hole counts.
- HOLE_PATTERN_MISMATCH: one or more hole centres or diameters differ beyond tolerance.
- PILOT_MISMATCH: measured pilot diameters differ beyond tolerance.
- MATCH_REQUIRES_REVIEW: nominal geometry matches but evidence is not confirmed.
- PRELIMINARY_GEOMETRY_MATCH: supplied geometry and evidence meet this limited comparison.

A preliminary geometry match is not a compatible gearbox verdict. The software does not yet assess concentricity, crankshaft pilot engagement, input-shaft length/splines, flywheel and clutch stack, starter engagement, release system, axial offsets, bellhousing stiffness, fastener design, torque transients, fatigue, vibration, material strength or manufacturability.

Any adapter drawing generated in future increments must be labelled **PRELIMINARY — NOT FOR MANUFACTURE — ENGINEERING REVIEW REQUIRED**.
