from typing import Dict, List, Optional, Tuple, Any
import cv2
import numpy as np
from ..models.metadata import ModelMetadata, ComponentMetadata

class Mesh3D:
    """3D Component Mesh with vertices, edges, and polygon faces for real-time projection."""
    def __init__(self, comp_id: str, name: str, vertices: np.ndarray, edges: List[Tuple[int, int]], faces: List[List[int]], color: Tuple[int, int, int]):
        self.comp_id = comp_id
        self.name = name
        self.base_vertices = vertices.astype(float) # (N, 3)
        self.edges = edges
        self.faces = faces
        self.base_color = color # BGR
        self.current_offset = np.array([0.0, 0.0, 0.0], dtype=float)
        self.manual_offset = np.array([0.0, 0.0, 0.0], dtype=float)
        self.is_grabbed = False
        self.is_selected = False

    def get_world_vertices(self, explosion_factor: float, exp_vector: np.ndarray, exp_dist: float) -> np.ndarray:
        offset = (exp_vector * (exp_dist * explosion_factor)) + self.manual_offset
        return self.base_vertices + offset

class Desktop3DRenderer:
    """High-performance 3D Spatial Laboratory Projection Engine for native OpenCV display."""

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2
        self.focal_length = 650.0

        # Orientation & Translation
        self.rot_x = 0.2
        self.rot_y = -0.4
        self.rot_z = 0.0
        self.trans_x = 0.0
        self.trans_y = 0.0
        self.trans_z = 3.5  # Camera distance in meters
        self.scale = 1.0

        self.explosion_factor = 0.0
        self.target_explosion_factor = 0.0

        # Meshes mapped by component_id
        self.meshes: Dict[str, Mesh3D] = {}
        self.current_model: Optional[ModelMetadata] = None
        self.selected_comp_id: Optional[str] = None
        self.hovered_comp_id: Optional[str] = None

        # Mechanical kinematics
        self.crank_angle = 0.0

    def load_model(self, model: ModelMetadata):
        """Builds procedural 3D geometric meshes for the model."""
        self.current_model = model
        self.meshes.clear()
        self.selected_comp_id = None
        self.hovered_comp_id = None
        self.explosion_factor = 0.0
        self.target_explosion_factor = 0.0

        for comp in model.components:
            mesh = self._create_component_mesh(comp)
            self.meshes[comp.id] = mesh

    def _create_component_mesh(self, comp: ComponentMetadata) -> Mesh3D:
        """Procedurally constructs 3D vertices and wireframe edges based on part type."""
        pos = np.array(comp.local_position, dtype=float)
        cid = comp.id
        color = self._hex_to_bgr(comp.color_hex)

        # 1. Wheels / Discs / Cylinders
        if "wheel" in cid:
            verts, edges, faces = self._gen_cylinder_mesh(pos, radius=0.6, height=0.25, segments=16, axis="z")
        elif "disc" in cid or "brakes" in cid:
            verts, edges, faces = self._gen_cylinder_mesh(pos, radius=0.42, height=0.08, segments=14, axis="z")
        elif "plug" in cid:
            verts, edges, faces = self._gen_cylinder_mesh(pos, radius=0.10, height=0.45, segments=8, axis="y")
        elif "piston" in cid:
            verts, edges, faces = self._gen_cylinder_mesh(pos, radius=0.35, height=0.45, segments=12, axis="y")
        elif "crankshaft" in cid:
            verts, edges, faces = self._gen_cylinder_mesh(pos, radius=0.18, height=1.1, segments=10, axis="x")
        elif "flywheel" in cid:
            verts, edges, faces = self._gen_cylinder_mesh(pos, radius=0.55, height=0.15, segments=16, axis="x")
        elif "suspension" in cid:
            verts, edges, faces = self._gen_box_mesh(pos, size=(0.25, 1.2, 0.2))
        elif "tank" in cid:
            verts, edges, faces = self._gen_box_mesh(pos, size=(0.6, 0.45, 0.9))
        elif "engine" in cid:
            verts, edges, faces = self._gen_box_mesh(pos, size=(0.85, 0.75, 0.7))
        elif "frame" in cid or "chassis" in cid:
            verts, edges, faces = self._gen_truss_mesh(pos, length=2.2, height=0.9, width=0.6)
        else:
            # Default box component
            verts, edges, faces = self._gen_box_mesh(pos, size=(0.45, 0.45, 0.45))

        return Mesh3D(comp.id, comp.name, verts, edges, faces, color)

    def _hex_to_bgr(self, hex_str: str) -> Tuple[int, int, int]:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) != 6:
            return (255, 240, 0) # Cyan
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (b, g, r)

    def _gen_box_mesh(self, center: np.ndarray, size: Tuple[float, float, float]):
        dx, dy, dz = size[0] / 2, size[1] / 2, size[2] / 2
        verts = center + np.array([
            [-dx, -dy, -dz], [dx, -dy, -dz], [dx, dy, -dz], [-dx, dy, -dz],
            [-dx, -dy,  dz], [dx, -dy,  dz], [dx, dy,  dz], [-dx, dy,  dz]
        ])
        edges = [
            (0,1), (1,2), (2,3), (3,0),
            (4,5), (5,6), (6,7), (7,4),
            (0,4), (1,5), (2,6), (3,7)
        ]
        faces = [
            [0, 1, 2, 3], [5, 4, 7, 6], [4, 0, 3, 7], [1, 5, 6, 2], [3, 2, 6, 7], [4, 5, 1, 0]
        ]
        return verts, edges, faces

    def _gen_cylinder_mesh(self, center: np.ndarray, radius: float, height: float, segments: int = 12, axis: str = "y"):
        verts = []
        half_h = height / 2.0
        angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

        for a in angles:
            ca, sa = np.cos(a) * radius, np.sin(a) * radius
            if axis == "y":
                verts.append([ca, -half_h, sa])
                verts.append([ca,  half_h, sa])
            elif axis == "x":
                verts.append([-half_h, ca, sa])
                verts.append([ half_h, ca, sa])
            else: # z
                verts.append([ca, sa, -half_h])
                verts.append([ca, sa,  half_h])

        verts = center + np.array(verts)
        edges = []
        faces = []
        for i in range(segments):
            b1 = i * 2
            t1 = b1 + 1
            b2 = ((i + 1) % segments) * 2
            t2 = b2 + 1
            edges.extend([(b1, b2), (t1, t2), (b1, t1)])
            faces.append([b1, b2, t2, t1])

        return verts, edges, faces

    def _gen_truss_mesh(self, center: np.ndarray, length: float, height: float, width: float):
        lx, hy, wz = length / 2, height / 2, width / 2
        verts = center + np.array([
            [-lx, -hy, -wz], [0, -hy, -wz], [lx, -hy, -wz],
            [-lx,  hy, -wz], [0,  hy, -wz], [lx,  hy, -wz],
            [-lx, -hy,  wz], [0, -hy,  wz], [lx, -hy,  wz],
            [-lx,  hy,  wz], [0,  hy,  wz], [lx,  hy,  wz],
        ])
        edges = [
            (0,1), (1,2), (3,4), (4,5), (0,3), (1,4), (2,5), (0,4), (1,5),
            (6,7), (7,8), (9,10), (10,11), (6,9), (7,10), (8,11), (6,10), (7,11),
            (0,6), (1,7), (2,8), (3,9), (4,10), (5,11)
        ]
        return verts, edges, []

    def update(self, dt: float = 0.016):
        """Updates animation curves and mechanical kinematics."""
        self.explosion_factor += (self.target_explosion_factor - self.explosion_factor) * 0.1
        self.crank_angle = (self.crank_angle + 0.08) % (2 * np.pi)

        # Animate piston reciprocating kinematics in 3D
        piston = self.meshes.get("piston")
        if piston and not piston.is_grabbed:
            stroke = 0.25 * np.cos(self.crank_angle)
            piston.manual_offset = np.array([0.0, stroke, 0.0])

    def render(self, frame: np.ndarray) -> np.ndarray:
        """Projects and renders 3D components onto the OpenCV laboratory canvas."""
        if not self.current_model or not self.meshes:
            return frame

        h, w, _ = frame.shape
        overlay = frame.copy()

        # 3D Rotation Matrix: Rx * Ry * Rz
        cx, sx = np.cos(self.rot_x), np.sin(self.rot_x)
        cy, sy = np.cos(self.rot_y), np.sin(self.rot_y)
        cz, sz = np.cos(self.rot_z), np.sin(self.rot_z)

        R = np.array([
            [cy * cz, -cy * sz, sy],
            [sx * sy * cz + cx * sz, -sx * sy * sz + cx * cz, -sx * cy],
            [-cx * sy * cz + sx * sz, cx * sy * sz + sx * cz, cx * cy]
        ])

        # Draw futuristic 3D floor grid
        self._render_grid(overlay, R)

        # Sort meshes by depth (Z-buffer painter's algorithm)
        mesh_depths = []
        for cid, mesh in self.meshes.items():
            comp_meta = next((c for c in self.current_model.components if c.id == cid), None)
            exp_vec = np.array(comp_meta.explosion_vector or [0, 1, 0], dtype=float) if comp_meta else np.array([0, 1, 0])
            exp_dist = comp_meta.explosion_distance if comp_meta else 1.5
            world_v = mesh.get_world_vertices(self.explosion_factor, exp_vec, exp_dist) * self.scale
            center_v = np.mean(world_v, axis=0)
            t_center = center_v @ R.T + np.array([self.trans_x, self.trans_y, self.trans_z])
            mesh_depths.append((t_center[2], cid, world_v, comp_meta))

        # Render farthest components first
        mesh_depths.sort(key=lambda x: x[0], reverse=True)

        for depth, cid, world_v, comp_meta in mesh_depths:
            # Transform vertices: (V * R.T) + Translation
            cam_v = world_v @ R.T + np.array([self.trans_x, self.trans_y, self.trans_z])

            # Perspective projection
            z = np.maximum(cam_v[:, 2], 0.2)
            px = (cam_v[:, 0] * self.focal_length / z) + self.cx
            py = (-cam_v[:, 1] * self.focal_length / z) + self.cy

            pts_2d = np.stack([px, py], axis=-1).astype(np.int32)

            mesh = self.meshes[cid]
            is_sel = (cid == self.selected_comp_id)
            is_hov = (cid == self.hovered_comp_id)

            # Colors and glow
            if is_sel:
                line_color = (0, 255, 255) # Bright Yellow/Cyan
                face_color = (40, 80, 100)
                thickness = 2
            elif is_hov:
                line_color = (255, 240, 0) # Neon Cyan
                face_color = (20, 50, 70)
                thickness = 2
            else:
                line_color = mesh.base_color
                face_color = (15, 25, 35)
                thickness = 1

            # Draw semi-transparent polygon faces
            for face in mesh.faces:
                poly = pts_2d[face]
                cv2.fillConvexPoly(overlay, poly, face_color)

            # Draw 3D wireframe edges
            for i1, i2 in mesh.edges:
                pt1 = (int(pts_2d[i1][0]), int(pts_2d[i1][1]))
                pt2 = (int(pts_2d[i2][0]), int(pts_2d[i2][1]))
                # Frustum clipping
                if 0 <= pt1[0] < w and 0 <= pt1[1] < h and 0 <= pt2[0] < w and 0 <= pt2[1] < h:
                    cv2.line(overlay, pt1, pt2, line_color, thickness, cv2.LINE_AA)

            # Draw 3D Floating Component Callout Label if selected or hovered
            if is_sel or is_hov:
                mean_pt = np.mean(pts_2d, axis=0).astype(int)
                mx, my = int(mean_pt[0]), int(mean_pt[1])
                callout_x = mx + 60
                callout_y = my - 40
                cv2.line(overlay, (mx, my), (callout_x, callout_y), (0, 240, 255), 1, cv2.LINE_AA)
                cv2.line(overlay, (callout_x, callout_y), (callout_x + 140, callout_y), (0, 240, 255), 1, cv2.LINE_AA)
                cv2.circle(overlay, (mx, my), 4, (0, 240, 255), -1)

                cv2.putText(overlay, mesh.name.upper(), (callout_x + 5, callout_y - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 255), 1, cv2.LINE_AA)
                if comp_meta:
                    cv2.putText(overlay, comp_meta.category.upper(), (callout_x + 5, callout_y + 16),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (160, 200, 220), 1, cv2.LINE_AA)

        # Alpha blend overlay onto frame
        return cv2.addWeighted(overlay, 0.88, frame, 0.12, 0)

    def _render_grid(self, frame: np.ndarray, R: np.ndarray):
        """Draws holographic laboratory floor grid in perspective."""
        grid_y = -1.2
        grid_size = 3.0
        grid_steps = 6
        coords = np.linspace(-grid_size, grid_size, grid_steps)
        grid_color = (25, 45, 60)

        for x in coords:
            p1 = np.array([x, grid_y, -grid_size]) @ R.T + np.array([self.trans_x, self.trans_y, self.trans_z])
            p2 = np.array([x, grid_y,  grid_size]) @ R.T + np.array([self.trans_x, self.trans_y, self.trans_z])
            self._draw_3d_line(frame, p1, p2, grid_color)

        for z in coords:
            p1 = np.array([-grid_size, grid_y, z]) @ R.T + np.array([self.trans_x, self.trans_y, self.trans_z])
            p2 = np.array([ grid_size, grid_y, z]) @ R.T + np.array([self.trans_x, self.trans_y, self.trans_z])
            self._draw_3d_line(frame, p1, p2, grid_color)

    def _draw_3d_line(self, frame: np.ndarray, p1: np.ndarray, p2: np.ndarray, color: Tuple[int, int, int]):
        if p1[2] < 0.2 or p2[2] < 0.2:
            return
        u1 = int((p1[0] * self.focal_length / p1[2]) + self.cx)
        v1 = int((-p1[1] * self.focal_length / p1[2]) + self.cy)
        u2 = int((p2[0] * self.focal_length / p2[2]) + self.cx)
        v2 = int((-p2[1] * self.focal_length / p2[2]) + self.cy)
        h, w, _ = frame.shape
        if 0 <= u1 < w and 0 <= v1 < h and 0 <= u2 < w and 0 <= v2 < h:
            cv2.line(frame, (u1, v1), (u2, v2), color, 1, cv2.LINE_AA)

    def explode(self):
        self.target_explosion_factor = 1.0

    def reassemble(self):
        self.target_explosion_factor = 0.0
        for m in self.meshes.values():
            m.manual_offset = np.array([0.0, 0.0, 0.0])
            m.is_grabbed = False
        self.selected_comp_id = None
