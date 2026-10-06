from typing import Dict, List, Optional, Tuple
import numpy as np
from .metadata import ComponentMetadata, ModelMetadata

class ComponentNode:
    """Tree node representing a component and its sub-assemblies."""
    def __init__(self, data: ComponentMetadata):
        self.data = data
        self.parent: Optional['ComponentNode'] = None
        self.children: List['ComponentNode'] = []
        self.is_dismantled: bool = False
        self.current_offset: np.ndarray = np.array([0.0, 0.0, 0.0], dtype=float)
        self.explosion_vector: np.ndarray = self._compute_default_explosion_vector()

    def _compute_default_explosion_vector(self) -> np.ndarray:
        if self.data.explosion_vector is not None:
            vec = np.array(self.data.explosion_vector, dtype=float)
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 1e-4 else np.array([0.0, 1.0, 0.0])
        
        # Calculate outward from local position relative to origin
        pos = np.array(self.data.local_position, dtype=float)
        norm = np.linalg.norm(pos)
        if norm > 1e-3:
            return pos / norm
        return np.array(self.data.movement_axis, dtype=float)

    def add_child(self, child: 'ComponentNode'):
        child.parent = self
        self.children.append(child)


class ModelHierarchy:
    """Manages the semantic assembly hierarchy and explosion geometry of a 3D model."""

    def __init__(self, model_meta: ModelMetadata):
        self.model_meta = model_meta
        self.nodes: Dict[str, ComponentNode] = {}
        self.root: Optional[ComponentNode] = None
        self._build_tree()

    def _build_tree(self):
        # 1. Instantiate all nodes
        for comp in self.model_meta.components:
            self.nodes[comp.id] = ComponentNode(comp)

        # 2. Link parents and children
        for comp in self.model_meta.components:
            node = self.nodes[comp.id]
            if comp.parent and comp.parent in self.nodes:
                self.nodes[comp.parent].add_child(node)
            else:
                if self.root is None or comp.id == self.model_meta.root_component_id:
                    self.root = node

    def get_node(self, comp_id: str) -> Optional[ComponentNode]:
        return self.nodes.get(comp_id)

    def get_all_components(self) -> List[ComponentMetadata]:
        return [node.data for node in self.nodes.values()]

    def compute_explosion_offsets(self, explosion_factor: float) -> Dict[str, List[float]]:
        """Calculates interpolated outward translation vectors for every component.
        explosion_factor ranges from 0.0 (compact) to 1.0 (fully exploded).
        """
        offsets = {}
        for comp_id, node in self.nodes.items():
            if node == self.root:
                offsets[comp_id] = [0.0, 0.0, 0.0]
                continue

            dist = node.data.explosion_distance * explosion_factor
            target_vec = node.explosion_vector * dist
            offsets[comp_id] = [round(float(c), 4) for c in target_vec]

        return offsets

    def reset_assembly(self):
        """Reassembles all components to original baseline positions."""
        for node in self.nodes.values():
            node.is_dismantled = False
            node.current_offset = np.array([0.0, 0.0, 0.0], dtype=float)
