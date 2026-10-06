import pytest
from app.models.registry import ModelRegistry
from app.models.hierarchy import ModelHierarchy

def test_model_registry_discovery():
    registry = ModelRegistry()
    models = registry.list_models()
    assert len(models) >= 4

    ids = [m["id"] for m in models]
    assert "sports_bike" in ids
    assert "combustion_engine" in ids
    assert "mechanical_gearbox" in ids
    assert "smartphone" in ids

def test_model_hierarchy_and_explosion():
    registry = ModelRegistry()
    bike = registry.get_model("sports_bike")
    assert bike is not None

    hierarchy = ModelHierarchy(bike)
    assert hierarchy.root is not None
    assert hierarchy.root.data.id == "frame"

    # Exploded view offsets
    offsets = hierarchy.compute_explosion_offsets(1.0)
    assert "engine" in offsets
    assert offsets["frame"] == [0.0, 0.0, 0.0]  # Root remains anchored
    assert offsets["engine"] != [0.0, 0.0, 0.0]
