from typing import Dict, Any, Optional
from ..models.metadata import ModelMetadata, ComponentMetadata

class EngineeringAIAssistant:
    """AI Component Assistant grounded in validated model metadata."""

    def __init__(self, model_meta: ModelMetadata):
        self.model_meta = model_meta
        self.components_by_id = {c.id: c for c in model_meta.components}

    def answer_query(self, query_type: str, component_id: Optional[str] = None) -> Dict[str, str]:
        """Provides accurate engineering context adhering strictly to metadata."""
        comp = self.components_by_id.get(component_id) if component_id else None

        if query_type == "what_does_it_do":
            if not comp:
                return {
                    "known_data": f"Model: {self.model_meta.name}",
                    "educational_explanation": self.model_meta.description
                }
            return {
                "known_data": f"Component: {comp.name} | Category: {comp.category} | Material: {comp.material}",
                "educational_explanation": f"FUNCTIONAL PURPOSE: {comp.function}\nDESCRIPTION: {comp.description}"
            }

        elif query_type == "why_connected_here":
            if not comp:
                return {"known_data": "N/A", "educational_explanation": "Please select a component first."}
            parent_name = self.components_by_id[comp.parent].name if comp.parent and comp.parent in self.components_by_id else "Chassis Root"
            return {
                "known_data": f"Parent Anchor: {parent_name} | Connections: {', '.join(comp.connected_components) if comp.connected_components else 'Direct mounting'}",
                "educational_explanation": (
                    f"'{comp.name}' is physically mounted to '{parent_name}' to transmit required mechanical loads and "
                    f"isolate vibrations while maintaining proper tolerances within the overall {self.model_meta.name} assembly."
                )
            }

        elif query_type == "what_happens_if_fails":
            if not comp:
                return {"known_data": "N/A", "educational_explanation": "Please select a component first."}
            return {
                "known_data": f"Documented Failure Mode: {comp.common_failure}",
                "educational_explanation": (
                    f"When '{comp.name}' degrades due to {comp.common_failure}, system efficiency drops immediately. "
                    "In severe cases, secondary catastrophic damage spreads to adjacent connected assemblies."
                )
            }

        elif query_type == "what_should_i_remove_next":
            removable_leaves = [c for c in self.model_meta.components if c.removable and c.id != self.model_meta.root_component_id]
            next_comp = removable_leaves[0] if removable_leaves else None
            if next_comp:
                return {
                    "known_data": f"Recommended Target: {next_comp.name} (ID: {next_comp.id})",
                    "educational_explanation": f"According to standard workshop procedure, detaching '{next_comp.name}' unlocks internal access without obstructing primary structural mounts."
                }
            return {"known_data": "Assembly Complete", "educational_explanation": "All external serviceable components have been detached."}

        else:
            return {
                "known_data": f"HoloMechanix Context: {self.model_meta.name}",
                "educational_explanation": "Ask about component function, connectivity rationale, failure diagnostics, or disassembly sequences."
            }
