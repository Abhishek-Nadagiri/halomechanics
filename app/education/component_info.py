from typing import Dict, Any, Optional
from ..models.metadata import ComponentMetadata

class ComponentInfoService:
    """Formats engineering metadata into high-tech HUD cards."""

    @staticmethod
    def format_card(comp: ComponentMetadata) -> Dict[str, Any]:
        return {
            "id": comp.id,
            "title": f"COMPONENT // {comp.name.upper()}",
            "name": comp.name,
            "category": comp.category,
            "function": comp.function,
            "connected_components": comp.connected_components or [comp.parent] if comp.parent else ["Chassis Mount"],
            "material": comp.material,
            "common_failure": comp.common_failure,
            "educational_level": comp.educational_level,
            "removable": comp.removable,
            "description": comp.description
        }
