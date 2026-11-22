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


## CAD/drawing export and manufacturing-release policy

Planned formats include PDF technical drawings, SVG, DXF, STEP and STL/3MF, with a project-data JSON package. File generation or a valid CAD model does not constitute manufacturing approval.

- Geometric checks (dimensions, interfaces, clearance, alignment and collision) must be reported separately from structural, fatigue, fastener, weld, material, process and vehicle-safety validation.
- DXF/SVG outputs require process-specific checks for scale, units, layers, kerf/toolpath, tolerances and machine constraints before use.
- STEP is an exchange model; STL/3MF are meshes and are not proof of suitability for structural automotive use.
- Every preliminary output must carry revision and status: **PRELIMINARY — NOT FOR MANUFACTURE — ENGINEERING REVIEW REQUIRED**.
- Only documented, qualified human review may authorize release, and the approval record must be traceable to the exact model revision and output package.


## Mounting-point comparison boundary

Mount-point comparisons are permitted only when both point sets are already registered to the same explicitly named coordinate datum. The software does not infer rotations, translations, best-fit alignments or transformations in this increment. A geometric match is preliminary and must not be interpreted as mount design or proof of structural adequacy, load paths, fasteners, welds, fatigue, vibration, dynamic clearance or safety.
