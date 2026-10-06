// HoloMechanix 3D Spatial Scene Engine powered by Three.js
class HoloScene {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Scene Graph Objects
    this.modelRoot = new THREE.Group();
    this.componentMeshes = new Map(); // id -> THREE.Object3D
    this.originalTransforms = new Map(); // id -> { pos, rot }
    this.explosionOffsets = new Map(); // id -> THREE.Vector3

    // State
    this.currentModelId = 'sports_bike';
    this.currentModelData = null;
    this.hoveredComponentId = null;
    this.selectedComponentId = null;
    this.grabbedComponentId = null;
    this.grabOffset = new THREE.Vector3();

    // Animation & Kinematics
    this.explosionFactor = 0.0;
    this.targetExplosionFactor = 0.0;
    this.rotationEuler = new THREE.Euler(0, 0, 0);
    this.targetRotation = new THREE.Euler(0, 0, 0);
    this.targetPosition = new THREE.Vector3(0, 0, 0);
    this.targetScale = 1.0;

    // Simulation angles
    this.engineAngle = 0.0;
    this.gearAngle = 0.0;
    this.wheelAngle = 0.0;
    this.isMechanicalSimActive = true;

    this._init();
  }

  _init() {
    // 1. Scene & Dark Engineering Environment
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x060913);
    this.scene.fog = new THREE.FogExp2(0x060913, 0.08);

    // 2. Camera
    const aspect = window.innerWidth / window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100);
    this.camera.position.set(0, 1.2, 4.5);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // 4. Laboratory Lighting
    const ambientLight = new THREE.AmbientLight(0x1a2638, 1.5);
    this.scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x00f0ff, 2.0);
    dirLight1.position.set(5, 8, 5);
    dirLight1.castShadow = true;
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xffaa00, 1.2);
    dirLight2.position.set(-5, -3, -5);
    this.scene.add(dirLight2);

    const rimLight = new THREE.PointLight(0x00f0ff, 2.5, 10);
    rimLight.position.set(0, 3, -2);
    this.scene.add(rimLight);

    // 5. Cyber Grid Ground Plane
    const grid = new THREE.GridHelper(20, 40, 0x00f0ff, 0x162438);
    grid.position.y = -1.2;
    this.scene.add(grid);

    // 6. Floating Hologram Dust Particles
    this._createParticleField();

    // 7. Add root model group
    this.scene.add(this.modelRoot);

    // Event listeners
    window.addEventListener('resize', () => this._onResize());
    this._setupMouseControls();

    // Start render loop
    this._animate();
  }

  _createParticleField() {
    const pCount = 300;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(pCount * 3);
    for (let i = 0; i < pCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 15;
      positions[i + 1] = (Math.random() - 0.5) * 10;
      positions[i + 2] = (Math.random() - 0.5) * 15;
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: 0x00f0ff,
      size: 0.04,
      transparent: true,
      opacity: 0.4
    });
    const particles = new THREE.Points(geometry, material);
    this.scene.add(particles);
  }

  _onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  _setupMouseControls() {
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    window.addEventListener('mousedown', (e) => {
      if (e.target.closest('.interactive-panel') || e.target.closest('.modal-content')) return;
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    });

    window.addEventListener('mousemove', (e) => {
      // Update normalized mouse coordinates
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

      if (isDragging) {
        const deltaX = (e.clientX - prevMouseX) * 0.008;
        const deltaY = (e.clientY - prevMouseY) * 0.008;
        this.targetRotation.y += deltaX;
        this.targetRotation.x += deltaY;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      } else {
        // Raycast hover test
        this._checkRaycast();
      }
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });

    window.addEventListener('wheel', (e) => {
      if (e.target.closest('.interactive-panel') || e.target.closest('.modal-content')) return;
      this.targetScale = Math.max(0.4, Math.min(2.8, this.targetScale - e.deltaY * 0.0015));
    });

    window.addEventListener('click', (e) => {
      if (e.target.closest('.interactive-panel') || e.target.closest('.modal-content')) return;
      if (this.hoveredComponentId) {
        this.selectComponent(this.hoveredComponentId);
        if (window.soundFX) window.soundFX.playGrab();
      }
    });
  }

  _checkRaycast() {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const meshes = Array.from(this.componentMeshes.values());
    const intersects = this.raycaster.intersectObjects(meshes, true);

    if (intersects.length > 0) {
      // Walk up parents to find named component
      let hit = intersects[0].object;
      while (hit && !hit.userData.componentId && hit.parent !== this.modelRoot) {
        hit = hit.parent;
      }
      if (hit && hit.userData.componentId) {
        if (this.hoveredComponentId !== hit.userData.componentId) {
          this.hoveredComponentId = hit.userData.componentId;
          document.body.style.cursor = 'pointer';
        }
        return;
      }
    }
    this.hoveredComponentId = null;
    document.body.style.cursor = 'default';
  }

  // Load and generate procedural 3D model with realistic geometry
  loadModel(modelMeta) {
    this.currentModelId = modelMeta.id;
    this.currentModelData = modelMeta;
    this.hoveredComponentId = null;
    this.selectedComponentId = null;
    this.grabbedComponentId = null;
    this.targetExplosionFactor = 0.0;
    this.explosionFactor = 0.0;

    // Clear previous model objects
    while (this.modelRoot.children.length > 0) {
      const obj = this.modelRoot.children[0];
      this.modelRoot.remove(obj);
    }
    this.componentMeshes.clear();
    this.originalTransforms.clear();
    this.explosionOffsets.clear();

    // Reset root orientation
    this.modelRoot.rotation.set(0, 0, 0);
    this.targetRotation.set(0, 0, 0);
    this.modelRoot.scale.set(1, 1, 1);
    this.targetScale = 1.0;

    // Construct procedural components
    if (modelMeta.id === 'sports_bike') {
      this._buildSportsBike(modelMeta);
    } else if (modelMeta.id === 'combustion_engine') {
      this._buildCombustionEngine(modelMeta);
    } else if (modelMeta.id === 'mechanical_gearbox') {
      this._buildGearbox(modelMeta);
    } else if (modelMeta.id === 'smartphone') {
      this._buildSmartphone(modelMeta);
    } else {
      this._buildGenericAssembly(modelMeta);
    }

    // Cache explosion offsets and baseline transforms
    modelMeta.components.forEach((c) => {
      const mesh = this.componentMeshes.get(c.id);
      if (mesh) {
        this.originalTransforms.set(c.id, {
          pos: mesh.position.clone(),
          rot: mesh.rotation.clone()
        });
        const expVec = c.explosion_vector || [0, 1, 0];
        const dist = c.explosion_distance || 1.5;
        this.explosionOffsets.set(c.id, new THREE.Vector3(expVec[0] * dist, expVec[1] * dist, expVec[2] * dist));
      }
    });

    if (window.soundFX) window.soundFX.playBlip();
  }

  // Helper Material Generator
  _createCyberMaterial(colorHex, isAccent = false) {
    return new THREE.MeshStandardMaterial({
      color: new THREE.Color(colorHex),
      metalness: 0.85,
      roughness: 0.25,
      emissive: isAccent ? new THREE.Color(colorHex) : new THREE.Color(0x000000),
      emissiveIntensity: isAccent ? 0.35 : 0.0
    });
  }

  _registerComponent(id, group) {
    group.userData.componentId = id;
    this.componentMeshes.set(id, group);
    this.modelRoot.add(group);
  }

  // Model 1: 2025 Sports Motorcycle (Phase 53)
  _buildSportsBike(meta) {
    // 1. Trellis Frame
    const frameGrp = new THREE.Group();
    const frameMat = this._createCyberMaterial(0x2a3b4c);
    const pipeGeom = new THREE.CylinderGeometry(0.04, 0.04, 1.8, 16);
    const p1 = new THREE.Mesh(pipeGeom, frameMat);
    p1.rotation.z = Math.PI / 4;
    p1.position.set(-0.2, 0.2, 0);
    const p2 = p1.clone();
    p2.position.set(0.2, 0.2, 0);
    p2.rotation.z = -Math.PI / 4;
    frameGrp.add(p1, p2);
    this._registerComponent('frame', frameGrp);

    // 2. Engine Block
    const engGrp = new THREE.Group();
    const engMat = this._createCyberMaterial(0x00e5ff);
    const block = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.6, 0.5), engMat);
    const fins = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.1, 0.55), this._createCyberMaterial(0x1a2638));
    fins.position.y = 0.15;
    engGrp.add(block, fins);
    engGrp.position.set(0, -0.2, 0);
    this._registerComponent('engine', engGrp);

    // 3. Fuel Tank
    const tankGrp = new THREE.Group();
    const tankMat = this._createCyberMaterial(0xff1744);
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.35, 0.9, 16), tankMat);
    tank.rotation.x = Math.PI / 2;
    tank.position.set(0, 0.65, 0.2);
    tankGrp.add(tank);
    this._registerComponent('fuel_tank', tankGrp);

    // 4. Lithium Battery
    const batGrp = new THREE.Group();
    const batMat = this._createCyberMaterial(0xffea00);
    const bat = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.25, 0.22), batMat);
    batGrp.add(bat);
    batGrp.position.set(-0.35, 0.2, -0.1);
    this._registerComponent('battery', batGrp);

    // 5. Air Filter
    const filterGrp = new THREE.Group();
    const filterMat = this._createCyberMaterial(0x76ff03);
    const filter = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.4, 16), filterMat);
    filter.rotation.z = Math.PI / 2;
    filterGrp.add(filter);
    filterGrp.position.set(0, 0.3, 0.35);
    this._registerComponent('air_filter', filterGrp);

    // 6. Spark Plug
    const plugGrp = new THREE.Group();
    const plugMat = this._createCyberMaterial(0x00b0ff);
    const ceramic = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 0.3, 12), plugMat);
    const hexNut = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.08, 6), this._createCyberMaterial(0x888888));
    plugGrp.add(ceramic, hexNut);
    plugGrp.position.set(0.25, 0.1, 0.1);
    this._registerComponent('spark_plug', plugGrp);

    // 7. Exhaust Header & Muffler
    const exhGrp = new THREE.Group();
    const exhMat = this._createCyberMaterial(0xffd600);
    const pipe = new THREE.Mesh(new THREE.TorusGeometry(0.4, 0.06, 8, 24, Math.PI), exhMat);
    pipe.rotation.y = Math.PI / 2;
    const can = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.8, 16), exhMat);
    can.position.set(0.3, -0.4, -0.7);
    can.rotation.x = Math.PI / 3;
    exhGrp.add(pipe, can);
    this._registerComponent('exhaust', exhGrp);

    // 8. Front Wheel
    const fwGrp = new THREE.Group();
    const tireMat = this._createCyberMaterial(0x1a1a1a);
    const rimMat = this._createCyberMaterial(0x2979ff);
    const fTire = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.12, 16, 32), tireMat);
    const fRim = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.15, 16), rimMat);
    fRim.rotation.x = Math.PI / 2;
    fwGrp.add(fTire, fRim);
    fwGrp.position.set(0, -0.5, 1.4);
    this._registerComponent('front_wheel', fwGrp);

    // 9. Rear Wheel
    const rwGrp = new THREE.Group();
    const rTire = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.16, 16, 32), tireMat);
    const rRim = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.22, 16), rimMat);
    rRim.rotation.x = Math.PI / 2;
    rwGrp.add(rTire, rRim);
    rwGrp.position.set(0, -0.5, -1.4);
    this._registerComponent('rear_wheel', rwGrp);

    // 10. Brakes
    const brkGrp = new THREE.Group();
    const discMat = this._createCyberMaterial(0xff3d00);
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.02, 24), discMat);
    disc.rotation.x = Math.PI / 2;
    const caliper = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.18, 0.1), this._createCyberMaterial(0xff1744));
    caliper.position.set(0.2, 0.2, 0);
    brkGrp.add(disc, caliper);
    brkGrp.position.set(0.15, -0.5, 1.4);
    this._registerComponent('brakes', brkGrp);

    // 11. Suspension Forks
    const suspGrp = new THREE.Group();
    const suspMat = this._createCyberMaterial(0xc51162);
    const forkL = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 1.3, 16), suspMat);
    forkL.position.set(-0.15, 0.1, 1.1);
    forkL.rotation.x = -Math.PI / 6;
    const forkR = forkL.clone();
    forkR.position.x = 0.15;
    suspGrp.add(forkL, forkR);
    this._registerComponent('suspension', suspGrp);
  }

  // Model 2: Four-Stroke Engine Assembly (Phase 8 & 12)
  _buildCombustionEngine(meta) {
    // 1. Engine Block
    const blockGrp = new THREE.Group();
    const block = new THREE.Mesh(new THREE.BoxGeometry(1.0, 1.2, 0.8), this._createCyberMaterial(0x455a64));
    blockGrp.add(block);
    this._registerComponent('engine_block', blockGrp);

    // 2. Cylinder Head
    const headGrp = new THREE.Group();
    const head = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.5, 0.85), this._createCyberMaterial(0x00bcd4));
    headGrp.add(head);
    headGrp.position.set(0, 0.85, 0);
    this._registerComponent('cylinder_head', headGrp);

    // 3. Spark Plug
    const plugGrp = new THREE.Group();
    const plug = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.45, 16), this._createCyberMaterial(0xff9100));
    plugGrp.add(plug);
    plugGrp.position.set(0, 1.35, 0);
    this._registerComponent('spark_plug', plugGrp);

    // 4. Piston
    const pistonGrp = new THREE.Group();
    const piston = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.45, 24), this._createCyberMaterial(0x00e676));
    pistonGrp.add(piston);
    pistonGrp.position.set(0, 0.25, 0);
    this._registerComponent('piston', pistonGrp);

    // 5. Connecting Rod
    const rodGrp = new THREE.Group();
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.7, 16), this._createCyberMaterial(0xffd600));
    rodGrp.add(rod);
    rodGrp.position.set(0, -0.35, 0);
    this._registerComponent('connecting_rod', rodGrp);

    // 6. Crankshaft
    const crankGrp = new THREE.Group();
    const crankMat = this._createCyberMaterial(0xe040fb);
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 1.1, 16), crankMat);
    shaft.rotation.z = Math.PI / 2;
    const counterweight = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.2, 0.3), crankMat);
    counterweight.position.y = -0.15;
    crankGrp.add(shaft, counterweight);
    crankGrp.position.set(0, -0.75, 0);
    this._registerComponent('crankshaft', crankGrp);

    // 7. Flywheel
    const flyGrp = new THREE.Group();
    const fly = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.12, 32), this._createCyberMaterial(0xff5252));
    fly.rotation.z = Math.PI / 2;
    flyGrp.add(fly);
    flyGrp.position.set(-0.7, -0.75, 0);
    this._registerComponent('flywheel', flyGrp);
  }

  // Model 3: Mechanical Gearbox (Phase 8)
  _buildGearbox(meta) {
    const caseGrp = new THREE.Group();
    const casing = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.1, 0.9), this._createCyberMaterial(0x37474f));
    caseGrp.add(casing);
    this._registerComponent('casing', caseGrp);

    // Input Shaft with Gear
    const inGrp = new THREE.Group();
    const inShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.3, 16), this._createCyberMaterial(0x00e5ff));
    inShaft.rotation.z = Math.PI / 2;
    const gear1 = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.18, 20), this._createCyberMaterial(0x00bcd4));
    gear1.rotation.z = Math.PI / 2;
    inGrp.add(inShaft, gear1);
    inGrp.position.set(0, 0.35, 0);
    this._registerComponent('input_shaft', inGrp);

    // Output Shaft with Meshing Gear
    const outGrp = new THREE.Group();
    const outShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.3, 16), this._createCyberMaterial(0x76ff03));
    outShaft.rotation.z = Math.PI / 2;
    const gear2 = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.18, 26), this._createCyberMaterial(0x00e676));
    gear2.rotation.z = Math.PI / 2;
    outGrp.add(outShaft, gear2);
    outGrp.position.set(0, -0.35, 0);
    this._registerComponent('output_shaft', outGrp);

    // Selector Fork
    const forkGrp = new THREE.Group();
    const fork = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.06, 8, 16, Math.PI), this._createCyberMaterial(0xffab00));
    fork.rotation.y = Math.PI / 2;
    forkGrp.add(fork);
    forkGrp.position.set(0.4, 0, 0);
    this._registerComponent('selector_fork', forkGrp);
  }

  // Model 4: Modular Smartphone
  _buildSmartphone(meta) {
    const chassisGrp = new THREE.Group();
    const chassis = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.8, 0.08), this._createCyberMaterial(0x263238));
    chassisGrp.add(chassis);
    this._registerComponent('chassis', chassisGrp);

    const dispGrp = new THREE.Group();
    const disp = new THREE.Mesh(new THREE.BoxGeometry(0.85, 1.75, 0.02), this._createCyberMaterial(0x00e5ff, true));
    dispGrp.add(disp);
    dispGrp.position.set(0, 0, 0.06);
    this._registerComponent('display_panel', dispGrp);

    const batGrp = new THREE.Group();
    const bat = new THREE.Mesh(new THREE.BoxGeometry(0.75, 1.0, 0.04), this._createCyberMaterial(0x00e676));
    batGrp.add(bat);
    batGrp.position.set(0, -0.25, -0.06);
    this._registerComponent('battery', batGrp);

    const logicGrp = new THREE.Group();
    const board = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.55, 0.03), this._createCyberMaterial(0xff1744));
    logicGrp.add(board);
    logicGrp.position.set(0, 0.5, -0.06);
    this._registerComponent('logic_board', logicGrp);

    const camGrp = new THREE.Group();
    const camMat = this._createCyberMaterial(0xffd600);
    const c1 = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.05, 16), camMat);
    c1.rotation.x = Math.PI / 2;
    camGrp.add(c1);
    camGrp.position.set(0.2, 0.6, -0.1);
    this._registerComponent('camera_array', camGrp);
  }

  _buildGenericAssembly(meta) {
    meta.components.forEach((c) => {
      const grp = new THREE.Group();
      const geom = new THREE.BoxGeometry(0.5, 0.5, 0.5);
      const mesh = new THREE.Mesh(geom, this._createCyberMaterial(c.color_hex || 0x00e5ff));
      grp.add(mesh);
      const pos = c.local_position || [0, 0, 0];
      grp.position.set(pos[0], pos[1], pos[2]);
      this._registerComponent(c.id, grp);
    });
  }

  // Component Selection & Highlighting (Phase 10 & 11)
  selectComponent(compId) {
    this.selectedComponentId = compId;
    this.componentMeshes.forEach((mesh, id) => {
      const isSelected = id === compId;
      mesh.traverse((child) => {
        if (child.isMesh) {
          if (isSelected) {
            child.material.emissive = new THREE.Color(0x00f0ff);
            child.material.emissiveIntensity = 0.8;
          } else if (compId) {
            child.material.emissive = new THREE.Color(0x000000);
            child.material.emissiveIntensity = 0.0;
            child.material.opacity = 0.45;
            child.material.transparent = true;
          } else {
            child.material.emissive = new THREE.Color(0x000000);
            child.material.emissiveIntensity = 0.0;
            child.material.opacity = 1.0;
            child.material.transparent = false;
          }
        }
      });
    });

    // Notify UI
    if (window.onComponentSelected) {
      window.onComponentSelected(compId);
    }
  }

  // Exploded View Trigger (Phase 16)
  explode() {
    this.targetExplosionFactor = 1.0;
    if (window.soundFX) window.soundFX.playExplode();
  }

  // Reassembly Trigger (Phase 20)
  reassemble() {
    this.targetExplosionFactor = 0.0;
    this.componentMeshes.forEach((mesh, id) => {
      const orig = this.originalTransforms.get(id);
      if (orig) {
        mesh.userData.manualOffset = null;
      }
    });
    this.selectComponent(null);
    if (window.soundFX) window.soundFX.playReassemble();
  }

  // Main Render and Kinematics Loop (Phase 19 & 32)
  _animate() {
    requestAnimationFrame(() => this._animate());

    // 1. Smoothly interpolate model orientation, position & scale
    this.modelRoot.rotation.x += (this.targetRotation.x - this.modelRoot.rotation.x) * 0.1;
    this.modelRoot.rotation.y += (this.targetRotation.y - this.modelRoot.rotation.y) * 0.1;
    this.modelRoot.position.x += (this.targetPosition.x - this.modelRoot.position.x) * 0.12;
    this.modelRoot.position.y += (this.targetPosition.y - this.modelRoot.position.y) * 0.12;
    this.modelRoot.position.z += (this.targetPosition.z - this.modelRoot.position.z) * 0.12;
    const curScale = this.modelRoot.scale.x;
    const newScale = curScale + (this.targetScale - curScale) * 0.1;
    this.modelRoot.scale.set(newScale, newScale, newScale);

    // 2. Smoothly interpolate explosion factor (Lerp)
    this.explosionFactor += (this.targetExplosionFactor - this.explosionFactor) * 0.08;

    // 3. Update component positions based on explosion offsets
    this.componentMeshes.forEach((mesh, id) => {
      const orig = this.originalTransforms.get(id);
      const offset = this.explosionOffsets.get(id);
      if (orig && offset) {
        if (!mesh.userData.manualOffset) {
          mesh.position.x = orig.pos.x + offset.x * this.explosionFactor;
          mesh.position.y = orig.pos.y + offset.y * this.explosionFactor;
          mesh.position.z = orig.pos.z + offset.z * this.explosionFactor;
        }
      }
    });

    // 4. Mechanical Simulation Kinematics (Phase 19)
    if (this.isMechanicalSimActive && this.explosionFactor < 0.2) {
      this.engineAngle += 0.06;
      this.gearAngle += 0.04;
      this.wheelAngle += 0.05;

      // Piston reciprocating motion
      const pistonMesh = this.componentMeshes.get('piston');
      const rodMesh = this.componentMeshes.get('connecting_rod');
      const crankMesh = this.componentMeshes.get('crankshaft');
      const flyMesh = this.componentMeshes.get('flywheel');

      if (pistonMesh && crankMesh) {
        crankMesh.rotation.x = this.engineAngle;
        if (flyMesh) flyMesh.rotation.x = this.engineAngle;
        const r = 0.25;
        const l = 0.70;
        const strokeY = r * Math.cos(this.engineAngle);
        pistonMesh.position.y = 0.25 + strokeY;
        if (rodMesh) {
          rodMesh.position.y = -0.35 + strokeY * 0.5;
          rodMesh.rotation.z = Math.sin(this.engineAngle) * 0.25;
        }
      }

      // Wheel and Brake Disc rotation
      const fw = this.componentMeshes.get('front_wheel');
      const rw = this.componentMeshes.get('rear_wheel');
      const brk = this.componentMeshes.get('brakes');
      if (fw) fw.rotation.x = this.wheelAngle;
      if (rw) rw.rotation.x = this.wheelAngle;
      if (brk) brk.rotation.x = this.wheelAngle;
    }

    this.renderer.render(this.scene, this.camera);
  }
}

window.HoloScene = HoloScene;
