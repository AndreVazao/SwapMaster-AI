# Vehicle and powertrain data model

## Scope of this increment

The domain currently defines typed records for:

- Vehicle identity, engine-bay and gearbox-space envelopes, and body-side mounting points.
- Power units (petrol, diesel, electric, hybrid or other), dimensions, mass, power, torque, mount points and gearbox mating interface.
- Gearboxes (manual, automatic, DCT, CVT, single-speed or other), envelope, mass, input-torque limit, mating interface and mounting points.
- Mechanical interfaces expressed in an explicitly named coordinate system.

The records are empty-capable where information may not yet be known. Missing data must remain missing; do not substitute guessed specifications.

## Units

- Linear dimensions and coordinates: mm.
- Mass: kg.
- Power: kW.
- Torque: N·m.
- Model year: Gregorian calendar year.

Unit conversion belongs in a dedicated, tested boundary layer before values enter these domain records.

## Coordinate frames

Hole coordinates may only be compared when both sides use the same named coordinate system and datum. A matching frame label is a necessary software precondition, not proof that the physical datums were correctly established.

The first interface comparison checks nominal hole centres and diameters, optional pilot diameter, and optional face-to-datum distance. It does not calculate arbitrary 3D transforms or infer adapter geometry.

## Compatibility is a multi-stage process

A nominal bellhousing pattern match is only one condition. A complete assessment must additionally consider:

- crankshaft and gearbox input-shaft concentricity and axial engagement;
- flywheel, clutch, pressure plate, release mechanism and starter geometry;
- torque capacity and transient loads;
- engine/gearbox mounts, load paths, vibration and fatigue;
- packaging, steering, suspension, cooling, exhaust and service access;
- electronics, controls, emissions, braking, vehicle dynamics and legal approval.

No single result from this module should be interpreted as a recommendation to manufacture or install a component.
