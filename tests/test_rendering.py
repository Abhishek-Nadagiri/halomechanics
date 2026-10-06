import pytest
import numpy as np
from app.models.registry import ModelRegistry
from app.rendering.desktop_renderer import Desktop3DRenderer

def test_desktop_3d_renderer():
    registry = ModelRegistry()
    bike = registry.get_model("sports_bike")
    assert bike is not None

    renderer = Desktop3DRenderer(width=640, height=480)
    renderer.load_model(bike)
    assert len(renderer.meshes) > 0
    assert "frame" in renderer.meshes

    # Test update and kinematics
    renderer.update(0.016)
    renderer.explode()
    assert renderer.target_explosion_factor == 1.0

    # Test frame projection
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    rendered = renderer.render(dummy_frame)
    assert rendered is not None
    assert rendered.shape == (480, 640, 3)
