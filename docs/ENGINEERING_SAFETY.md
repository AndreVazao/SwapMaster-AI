# Engineering safety and validation boundary

SwapMaster AI is an engineering-support and planning tool. It is not a substitute for qualified engineering judgment, physical inspection, certification, or applicable vehicle approval.

## A bounding-box pass does not establish fitment

The initial envelope check only compares three axis-aligned dimensions. It does not account for:

- component orientation, shape, mounting points or tolerances;
- engine movement, vibration, torque reaction or service access;
- suspension, steering, crash structure or occupant safety;
- gearbox interfaces, clutch, starter, propeller shafts or axle loads;
- cooling, exhaust, fuel, high-voltage isolation, wiring or fire protection;
- material strength, fatigue, weld design, fastener preload or FEA;
- braking performance, vehicle dynamics, emissions or homologation.

## Evidence policy

- Confirmed: traceable measurement or source with applicable scope.
- Documented: source statement not independently validated.
- Estimated: explicit assumptions and estimation method.
- Unknown: absent, contradictory, or insufficient data.

Missing critical values must block a positive engineering recommendation.

## Output labels

Any future preliminary CAD, drawing, or report must clearly state:

**PRELIMINARY — NOT FOR MANUFACTURE — ENGINEERING REVIEW REQUIRED**

Only a documented review and approval process may remove that label. The software must never imply that an automated result certifies a road vehicle or manufactured safety-critical part.
