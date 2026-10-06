# 3D Model Architecture & Import Specification

## Model Catalog
HoloMechanix automatically scans the `assets/models/` folder on startup. Any subdirectory containing a valid `metadata.json` is registered without requiring Python code modifications.

### Built-in Models:
1. **2025 Apex Sports Motorcycle** (`sports_bike`): Complete 1000cc superbike with frame, engine, tank, battery, spark plug, air filter, exhaust, wheels, brakes, and USD suspension.
2. **Four-Stroke Internal Combustion Engine** (`combustion_engine`): Cutaway reciprocating engine with block, cylinder head, spark plug, piston, connecting rod, crankshaft, and flywheel.
3. **Precision Constant-Mesh Gearbox** (`mechanical_gearbox`): Manual transmission showcasing shafts, dog teeth gears, and selector forks.
4. **Quantum 16 Ultra Smartphone** (`smartphone`): Flagship mobile device showing chassis, display panel, battery pack, logic board, and periscope camera array.

## `metadata.json` Schema

```json
{
  "id": "model_unique_id",
  "name": "Human-Readable Model Name",
  "category": "Automotive | Electronics | Mechanical",
  "description": "High-level summary of the machine",
  "root_component_id": "root_part_id",
  "components": [
    {
      "id": "spark_plug_01",
      "name": "Spark Plug",
      "category": "Ignition",
      "description": "Ceramic-insulated ignition electrode",
      "function": "Ignites the air-fuel mixture with electric arc",
      "parent": "cylinder_head",
      "removable": true,
      "movement_axis": [0.0, 1.0, 0.0],
      "explosion_vector": [0.0, 1.5, 0.0],
      "explosion_distance": 2.0,
      "material": "Alumina Ceramic & Iridium",
      "common_failure": "Electrode erosion",
      "educational_level": "Beginner",
      "connected_components": ["cylinder_head", "ignition_coil"]
    }
  ],
  "learning_steps": [ ... ],
  "quiz_questions": [ ... ]
}
```
