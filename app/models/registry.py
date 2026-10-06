import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .metadata import ModelMetadata, ComponentMetadata, LearningStep, QuizQuestion
from ..config.settings import settings

logger = logging.getLogger("holomechanix.models.registry")

class ModelRegistry:
    """Manages model catalog and dynamic loading from assets/models/."""

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or settings.MODELS_DIR
        self._models: Dict[str, ModelMetadata] = {}
        self._load_all_models()

    def _load_all_models(self):
        """Scans the models directory for metadata.json and registers them."""
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # 1. First ensure built-in default demonstration models exist on disk
        self._ensure_built_in_models()

        # 2. Discover all model directories
        for model_path in self.models_dir.iterdir():
            if model_path.is_dir():
                meta_file = model_path / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            raw = json.load(f)
                        model_meta = ModelMetadata(**raw)
                        self._models[model_meta.id] = model_meta
                        logger.info(f"Loaded 3D model metadata: {model_meta.name} ({model_meta.id})")
                    except Exception as e:
                        logger.error(f"Failed to load model metadata from {meta_file}: {e}")

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        return self._models.get(model_id)

    def list_models(self) -> List[Dict[str, str]]:
        return [
            {
                "id": m.id,
                "name": m.name,
                "category": m.category,
                "description": m.description,
                "component_count": len(m.components)
            }
            for m in self._models.values()
        ]

    def _ensure_built_in_models(self):
        """Generates standard models required by HoloMechanix specification."""
        builtins = [
            self._create_sports_bike_spec(),
            self._create_engine_spec(),
            self._create_gearbox_spec(),
            self._create_smartphone_spec(),
        ]
        for spec in builtins:
            target_dir = self.models_dir / spec.id
            target_dir.mkdir(parents=True, exist_ok=True)
            meta_path = target_dir / "metadata.json"
            if not meta_path.exists():
                with open(meta_path, "w", encoding="utf-8") as f:
                    f.write(spec.model_dump_json(indent=2))

    def _create_sports_bike_spec(self) -> ModelMetadata:
        """Phase 53 specification: 2025 Sports Motorcycle with full component set."""
        return ModelMetadata(
            id="sports_bike",
            name="2025 Apex Sports Motorcycle",
            category="Automotive",
            description="High-performance supersport 1000cc motorcycle with exposed trellis frame and electronic fuel injection.",
            root_component_id="frame",
            components=[
                ComponentMetadata(
                    id="frame",
                    name="Trellis Chassis Frame",
                    category="Structure",
                    description="High-tensile tubular steel trellis frame providing rigid torsional support.",
                    function="Houses and structurally anchors the powertrain, swingarm, and steering assembly.",
                    parent=None,
                    removable=False,
                    color_hex="#37474f",
                    local_position=[0.0, 0.0, 0.0],
                    explosion_vector=[0.0, 0.0, 0.0],
                    material="Chromoly Steel",
                    common_failure="Stress fractures under extreme track impacts",
                    educational_level="Intermediate"
                ),
                ComponentMetadata(
                    id="engine",
                    name="Inline-4 Engine Block",
                    category="Powertrain",
                    description="1000cc liquid-cooled dual overhead camshaft powerplant.",
                    function="Converts fuel chemical energy into rotational kinetic torque.",
                    parent="frame",
                    removable=True,
                    color_hex="#00e5ff",
                    local_position=[0.0, -0.2, 0.0],
                    explosion_vector=[0.0, -0.6, 0.0],
                    explosion_distance=1.6,
                    material="Cast Aluminum Alloy",
                    common_failure="Head gasket leak / thermal warping",
                    educational_level="Beginner",
                    connected_components=["frame", "spark_plug", "air_filter", "exhaust"]
                ),
                ComponentMetadata(
                    id="fuel_tank",
                    name="Pressurized Fuel Cell",
                    category="Fuel System",
                    description="Aerodynamic fuel tank with internal high-pressure swirl pot and pump.",
                    function="Safely stores combustible gasoline and feeds the rail injectors.",
                    parent="frame",
                    removable=True,
                    color_hex="#ff1744",
                    local_position=[0.0, 0.7, 0.2],
                    explosion_vector=[0.0, 1.2, 0.4],
                    explosion_distance=1.8,
                    material="Composite Polymer",
                    common_failure="Internal sender unit corrosion",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="battery",
                    name="Lithium-Iron Battery",
                    category="Electrical",
                    description="12V lightweight lithium starter accumulator with BMS.",
                    function="Supplies starter current and stabilizes the electrical harness.",
                    parent="frame",
                    removable=True,
                    color_hex="#ffea00",
                    local_position=[-0.3, 0.2, -0.1],
                    explosion_vector=[-1.2, 0.5, 0.0],
                    explosion_distance=2.0,
                    material="LiFePO4",
                    common_failure="Cell imbalance / deep discharge",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="air_filter",
                    name="High-Flow Air Filter",
                    category="Intake",
                    description="Multi-layer cotton gauze intake filter assembly.",
                    function="Traps particulate contaminants before air enters intake manifolds.",
                    parent="engine",
                    removable=True,
                    color_hex="#76ff03",
                    local_position=[0.0, 0.3, 0.3],
                    explosion_vector=[0.0, 0.9, 0.6],
                    explosion_distance=1.9,
                    material="Cotton / Oiled Mesh",
                    common_failure="Particulate clogging and power starvation",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="spark_plug",
                    name="Iridium Spark Plug",
                    category="Ignition",
                    description="Fine-wire iridium tip center electrode spark plug.",
                    function="Generates 25,000V electric spark arc to ignite compressed fuel-air mixture.",
                    parent="engine",
                    removable=True,
                    color_hex="#00b0ff",
                    local_position=[0.2, 0.1, 0.1],
                    explosion_vector=[0.8, 0.8, 0.4],
                    explosion_distance=2.2,
                    material="High-Alumina Ceramic & Iridium",
                    common_failure="Carbon fouling / gap erosion",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="exhaust",
                    name="Titanium Exhaust Header & Muffler",
                    category="Exhaust",
                    description="Hydroformed 4-into-1 titanium tuned exhaust system.",
                    function="Expels combustion gases, muffles acoustic pressure waves, and scavenges cylinders.",
                    parent="engine",
                    removable=True,
                    color_hex="#ffd600",
                    local_position=[0.0, -0.6, -0.8],
                    explosion_vector=[0.0, -1.0, -1.2],
                    explosion_distance=1.8,
                    material="Grade 1 Titanium",
                    common_failure="Weld fatigue from thermal cycling",
                    educational_level="Intermediate"
                ),
                ComponentMetadata(
                    id="front_wheel",
                    name="Front Forged Wheel & Tire",
                    category="Running Gear",
                    description="17-inch lightweight forged aluminum wheel with sticky radial rubber.",
                    function="Provides directional steering traction and gyroscopic stability.",
                    parent="frame",
                    removable=True,
                    color_hex="#2979ff",
                    local_position=[0.0, -0.5, 1.4],
                    explosion_vector=[0.0, 0.0, 1.8],
                    explosion_distance=2.2,
                    material="Forged 6061 Aluminum",
                    common_failure="Rim denting / bead leakage",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="rear_wheel",
                    name="Rear Drive Wheel & Tire",
                    category="Running Gear",
                    description="17x6.0-inch rear wheel receiving drive torque.",
                    function="Transfers engine propulsion torque to tarmac.",
                    parent="frame",
                    removable=True,
                    color_hex="#2979ff",
                    local_position=[0.0, -0.5, -1.4],
                    explosion_vector=[0.0, 0.0, -1.8],
                    explosion_distance=2.2,
                    material="Forged Aluminum",
                    common_failure="Tread delamination / uneven wear",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="brakes",
                    name="Radial Monobloc Brake Calipers",
                    category="Braking",
                    description="Dual 330mm floating drilled discs with 4-piston radial monobloc calipers.",
                    function="Converts rotational kinetic energy into heat through friction braking.",
                    parent="front_wheel",
                    removable=True,
                    color_hex="#ff3d00",
                    local_position=[0.3, -0.4, 1.3],
                    explosion_vector=[1.2, 0.0, 1.2],
                    explosion_distance=2.0,
                    material="Sintered Friction Compound & Cast Aluminum",
                    common_failure="Brake pad glazing / rotor warping",
                    educational_level="Beginner"
                ),
                ComponentMetadata(
                    id="suspension",
                    name="Inverted Upside-Down (USD) Front Forks",
                    category="Suspension",
                    description="43mm fully-adjustable nitrogen-charged cartridge forks.",
                    function="Damps road irregularities and manages pitch dynamics during cornering.",
                    parent="frame",
                    removable=True,
                    color_hex="#c51162",
                    local_position=[0.0, 0.2, 1.0],
                    explosion_vector=[0.0, 1.0, 1.0],
                    explosion_distance=1.7,
                    material="Hard-Anodized Aluminum",
                    common_failure="Fork oil seal breach",
                    educational_level="Intermediate"
                )
            ],
            learning_steps=[
                LearningStep(
                    step_number=1,
                    component_id="fuel_tank",
                    instruction="Remove the fuel tank to access electrical harness and upper intake.",
                    required_gesture="PINCH",
                    explanation="Disconnect quick-release fuel couplings and electrical sender harness."
                ),
                LearningStep(
                    step_number=2,
                    component_id="battery",
                    instruction="Disconnect and remove the lithium battery.",
                    required_gesture="PINCH",
                    explanation="Always isolate negative ground lead first to prevent accidental short circuits."
                ),
                LearningStep(
                    step_number=3,
                    component_id="air_filter",
                    instruction="Extract the intake air filter element.",
                    required_gesture="PINCH",
                    explanation="Inspect pleats for debris ingress or airflow restriction."
                ),
                LearningStep(
                    step_number=4,
                    component_id="spark_plug",
                    instruction="Unthread the iridium spark plug from cylinder 1.",
                    required_gesture="PINCH",
                    explanation="Examine electrode color to diagnose combustion stoichiometry (rich vs lean)."
                ),
                LearningStep(
                    step_number=5,
                    component_id="engine",
                    instruction="Detrend engine mounting bolts and pull the powertrain assembly.",
                    required_gesture="PULL_APART",
                    explanation="Supporting the engine cradle allows comprehensive bench inspection."
                )
            ],
            quiz_questions=[
                QuizQuestion(
                    id="q1",
                    question="Which component produces the high-voltage electrical arc to ignite the compressed mixture?",
                    options=["Fuel Tank", "Spark Plug", "Lithium Battery", "Air Filter"],
                    correct_index=1,
                    explanation="The Spark Plug receives high ignition coil voltage and arcs across its gap to initiate combustion."
                ),
                QuizQuestion(
                    id="q2",
                    question="Why is the battery disconnected before major powertrain servicing?",
                    options=["To save battery juice", "To avoid electrical shorts and accidental cranking", "To cool the engine", "To reset tire pressure"],
                    correct_index=1,
                    explanation="Isolating the electrical source prevents sparks near fuel vapors and unintended starter motor activation."
                )
            ]
        )

    def _create_engine_spec(self) -> ModelMetadata:
        """Phase 8 & 12 specification: Internal Combustion Engine Assembly."""
        return ModelMetadata(
            id="combustion_engine",
            name="Four-Stroke Internal Combustion Engine",
            category="Mechanical",
            description="Precision cutaway of a 4-stroke overhead cam single-cylinder engine demonstrating reciprocating kinematics.",
            root_component_id="engine_block",
            components=[
                ComponentMetadata(
                    id="engine_block",
                    name="Crankcase Engine Block",
                    category="Structure",
                    description="Cast iron/aluminum structural block containing cylinder bore and main journal bearings.",
                    function="Houses reciprocating piston and rotating crankshaft assembly.",
                    removable=False,
                    color_hex="#455a64",
                    local_position=[0.0, 0.0, 0.0],
                    explosion_vector=[0.0, 0.0, 0.0]
                ),
                ComponentMetadata(
                    id="cylinder_head",
                    name="Cylinder Head Assembly",
                    category="Combustion",
                    description="Upper chamber enclosing valves, camshaft, and combustion dome.",
                    function="Regulates intake air/fuel admission and exhaust scavenging.",
                    parent="engine_block",
                    removable=True,
                    color_hex="#00bcd4",
                    local_position=[0.0, 0.8, 0.0],
                    explosion_vector=[0.0, 1.4, 0.0],
                    explosion_distance=1.8,
                    connected_components=["spark_plug", "engine_block"]
                ),
                ComponentMetadata(
                    id="spark_plug",
                    name="High-Voltage Spark Plug",
                    category="Ignition",
                    description="Ceramic insulator body with nickel-alloy ground electrode.",
                    function="Ignites compressed air-fuel charge via high-voltage spark arc.",
                    parent="cylinder_head",
                    removable=True,
                    color_hex="#ff9100",
                    local_position=[0.0, 1.4, 0.0],
                    explosion_vector=[0.0, 2.2, 0.0],
                    explosion_distance=2.4
                ),
                ComponentMetadata(
                    id="piston",
                    name="Reciprocating Piston",
                    category="Kinematics",
                    description="Lightweight aluminum piston with compression and oil scraper rings.",
                    function="Translates combustion gas expansion pressure into linear downward thrust.",
                    parent="engine_block",
                    removable=True,
                    color_hex="#00e676",
                    local_position=[0.0, 0.2, 0.0],
                    explosion_vector=[0.0, 0.8, 0.5],
                    explosion_distance=1.6
                ),
                ComponentMetadata(
                    id="connecting_rod",
                    name="H-Beam Connecting Rod",
                    category="Kinematics",
                    description="Forged steel rod connecting wrist pin to crank journal.",
                    function="Converts piston reciprocating linear motion into crankshaft rotation.",
                    parent="piston",
                    removable=True,
                    color_hex="#ffd600",
                    local_position=[0.0, -0.3, 0.0],
                    explosion_vector=[0.6, -0.3, 0.0],
                    explosion_distance=1.8
                ),
                ComponentMetadata(
                    id="crankshaft",
                    name="Forged Counterweighted Crankshaft",
                    category="Kinematics",
                    description="Heat-treated alloy steel shaft with offset crankpins and counterweights.",
                    function="Outputs rotary torque to transmission flywheel.",
                    parent="engine_block",
                    removable=True,
                    color_hex="#e040fb",
                    local_position=[0.0, -0.7, 0.0],
                    explosion_vector=[0.0, -1.5, 0.0],
                    explosion_distance=1.9
                ),
                ComponentMetadata(
                    id="flywheel",
                    name="Inertial Heavy Flywheel",
                    category="Kinematics",
                    description="Cast steel rotational mass bolted to crankshaft flange.",
                    function="Stores kinetic energy to smooth out torque fluctuations between power strokes.",
                    parent="crankshaft",
                    removable=True,
                    color_hex="#ff5252",
                    local_position=[-0.8, -0.7, 0.0],
                    explosion_vector=[-1.6, -0.7, 0.0],
                    explosion_distance=2.1
                )
            ]
        )

    def _create_gearbox_spec(self) -> ModelMetadata:
        """Phase 8 Mechanical Gearbox specification."""
        return ModelMetadata(
            id="mechanical_gearbox",
            name="Precision Constant-Mesh Gearbox",
            category="Mechanical",
            description="Multi-ratio mechanical transmission showing gear mesh pairs, dog teeth, and selector forks.",
            root_component_id="casing",
            components=[
                ComponentMetadata(
                    id="casing",
                    name="Cast Aluminum Casing",
                    category="Structure",
                    description="Rigid split case enclosing gear shafts in lubrication oil bath.",
                    function="Locates shaft roller bearings and contains transmission fluid.",
                    removable=False,
                    color_hex="#37474f",
                    local_position=[0.0, 0.0, 0.0]
                ),
                ComponentMetadata(
                    id="input_shaft",
                    name="Primary Input Shaft",
                    category="Drivetrain",
                    description="Splined shaft receiving engine input torque.",
                    function="Drives countershaft gear cluster.",
                    parent="casing",
                    removable=True,
                    color_hex="#00e5ff",
                    local_position=[0.0, 0.4, 0.0],
                    explosion_vector=[0.0, 1.2, 0.0],
                    explosion_distance=1.8
                ),
                ComponentMetadata(
                    id="output_shaft",
                    name="Secondary Output Shaft",
                    category="Drivetrain",
                    description="Hardened steel output shaft driving final drive sprocket.",
                    function="Delivers chosen gear ratio speed and torque to load.",
                    parent="casing",
                    removable=True,
                    color_hex="#76ff03",
                    local_position=[0.0, -0.4, 0.0],
                    explosion_vector=[0.0, -1.2, 0.0],
                    explosion_distance=1.8
                ),
                ComponentMetadata(
                    id="selector_fork",
                    name="Hardened Shift Selector Fork",
                    category="Control",
                    description="Bronze-tipped fork riding on shift drum track.",
                    function="Slides gear dogs into engagement to lock desired ratio.",
                    parent="casing",
                    removable=True,
                    color_hex="#ffab00",
                    local_position=[0.6, 0.0, 0.0],
                    explosion_vector=[1.5, 0.0, 0.0],
                    explosion_distance=2.0
                )
            ]
        )

    def _create_smartphone_spec(self) -> ModelMetadata:
        """Electronics category: Modular Smartphone Assembly."""
        return ModelMetadata(
            id="smartphone",
            name="Quantum 16 Ultra Smartphone",
            category="Electronics",
            description="Ultra-thin flagship smartphone featuring layered modular electronics and thermal dissipation plates.",
            root_component_id="chassis",
            components=[
                ComponentMetadata(
                    id="chassis",
                    name="Titanium Mid-Frame Chassis",
                    category="Structure",
                    description="CNC-milled Grade 5 titanium exoskeleton frame.",
                    function="Structural foundation anchoring internal microelectronics and battery.",
                    removable=False,
                    color_hex="#263238",
                    local_position=[0.0, 0.0, 0.0]
                ),
                ComponentMetadata(
                    id="display_panel",
                    name="LTPO OLED Ultra-Retina Display",
                    category="Interface",
                    description="120Hz flexible ceramic glass front panel.",
                    function="Displays graphics and detects multi-touch input capacitance.",
                    parent="chassis",
                    removable=True,
                    color_hex="#00e5ff",
                    local_position=[0.0, 0.0, 0.2],
                    explosion_vector=[0.0, 0.0, 1.5],
                    explosion_distance=2.0
                ),
                ComponentMetadata(
                    id="battery",
                    name="High-Density Solid-State Battery",
                    category="Power",
                    description="5000mAh silicon-anode battery pack.",
                    function="Stores electrical chemical energy for mobile operation.",
                    parent="chassis",
                    removable=True,
                    color_hex="#00e676",
                    local_position=[0.0, -0.3, -0.1],
                    explosion_vector=[0.0, -0.8, -1.2],
                    explosion_distance=1.8
                ),
                ComponentMetadata(
                    id="logic_board",
                    name="Stacked Logic Motherboard",
                    category="Computing",
                    description="Multi-layer PCB with 3nm neural SoC, RAM, and flash storage.",
                    function="Executes system firmware, AI processing, and hardware bus scheduling.",
                    parent="chassis",
                    removable=True,
                    color_hex="#ff1744",
                    local_position=[0.0, 0.4, -0.1],
                    explosion_vector=[0.0, 0.8, -1.4],
                    explosion_distance=2.0
                ),
                ComponentMetadata(
                    id="camera_array",
                    name="Periscope Optical Camera System",
                    category="Optics",
                    description="Triple camera sensor module with optical image stabilization.",
                    function="Captures raw photon sensor data for computational photography.",
                    parent="logic_board",
                    removable=True,
                    color_hex="#ffd600",
                    local_position=[0.3, 0.5, -0.2],
                    explosion_vector=[0.8, 0.8, -1.8],
                    explosion_distance=2.4
                )
            ]
        )
