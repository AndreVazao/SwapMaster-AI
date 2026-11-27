# Compatibility screening engine

The domain service `assess_powertrain_candidate` is a conservative first screening
for a vehicle, power unit and transmission.

## Current checks

- Engine axis-aligned bounding envelope against the declared engine-bay envelope.
- Bellhousing interface identifier and evidence level.
- Declared power-unit torque against the transmission input torque limit.

## Deliberately unassessed

- Mounting-point transformations, bracket design, load paths and fasteners.
- Transmission tunnel/package envelope and installed drivetrain position.
- Crankshaft/input-shaft concentricity, axial stack, clutch, flywheel and starter.
- Gear ratios, prop/drive shafts, differential, axle capacity and lubrication.
- Cooling, fuel, exhaust, electrical/high-voltage, steering, brakes and service access.
- Fatigue, vibration, crashworthiness, roadworthiness and legal approval.

Any unassessed critical item forces engineering review. Missing required inputs
block a positive screening result. A known failed criterion takes precedence and
marks the candidate incompatible.

A `PRELIMINARY_CANDIDATE` outcome is not an installation or manufacturing approval.
All outputs require review against source drawings, measurements, tolerances and
the complete vehicle configuration. Never use estimated or unknown data as
confirmed engineering evidence.
