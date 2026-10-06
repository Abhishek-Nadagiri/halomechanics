import pytest
import numpy as np
from app.simulation.constraints import FixedConstraint, HingeConstraint, SliderConstraint, RotationalConstraint
from app.simulation.mechanisms import MechanicalSimulator

def test_fixed_constraint():
    fc = FixedConstraint()
    pos = np.array([1.0, 2.0, 3.0])
    delta = np.array([0.5, 0.5, 0.5])
    assert np.allclose(fc.apply_translation(pos, delta), pos)

def test_slider_constraint():
    sc = SliderConstraint(axis=(0.0, 1.0, 0.0), min_dist=-0.2, max_dist=0.2)
    pos = np.array([0.0, 0.0, 0.0])
    # Apply Y movement beyond limits
    res = sc.apply_translation(pos, np.array([0.0, 0.5, 0.0]))
    assert np.isclose(res[1], 0.2)

def test_mechanical_simulator():
    sim = MechanicalSimulator()
    state = sim.step(dt=0.016, is_running=True)
    assert "engine" in state
    assert "gearbox" in state
    assert state["engine"]["rpm"] > 0
    assert "piston_y" in state["engine"]
