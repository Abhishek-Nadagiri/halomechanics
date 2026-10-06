# Dismantling, Kinematics & Educational Systems

## Kinematic Constraints (Phase 18)
Components do not float haphazardly. Each joint is constrained using engineering physics:
- **`FixedConstraint`**: Structural chassis elements (e.g. engine mounts, frame).
- **`SliderConstraint`**: Linear degree of freedom with hard stops (e.g. piston travel in cylinder bore).
- **`HingeConstraint`**: Rotational degree of freedom within angular bounds (e.g. doors, levers, calipers).
- **`RotationalConstraint`**: Continuous shaft rotation (e.g. crankshaft, transmission gears, wheels).

## Exploded-View Kinematics (Phase 16)
Explosion vectors are computed outward from the component's center of mass relative to its parent node or origin. Each part glides smoothly via cubic ease-out interpolation:
$$\text{offset}(t) = \vec{v}_{\text{explosion}} \cdot d \cdot \text{easeOutCubic}(t)$$

## Reassembly & Verification (Phase 20)
When the user executes **Push Together** or clicks Reassemble:
1. Components smoothly ease back to their original transforms.
2. Parent hierarchy and alignment tolerances are validated.
3. The disassembly history log is cleared.

## Grounded AI Diagnostics Assistant (Phase 29)
The AI assistant answers four core engineering questions:
1. *What does this component do?*
2. *Why is it connected here?*
3. *What happens if it fails?*
4. *What should I remove next?*

All answers are strictly synthesized from validated metadata fields, completely eliminating hallucinations.
