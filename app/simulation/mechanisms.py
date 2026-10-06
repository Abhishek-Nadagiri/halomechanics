from typing import Dict, Any, Tuple
import numpy as np

class MechanicalSimulator:
    """Simulates real-time mechanical linkages and kinematic couplings."""

    def __init__(self):
        self.crankshaft_angle = 0.0      # Radians
        self.gear_angle = 0.0            # Radians
        self.wheel_angle = 0.0           # Radians
        self.suspension_compression = 0.0 # Meters
        self.engine_rpm = 1200.0         # Default idle RPM

        # Engine geometry (piston slider-crank mechanism)
        self.crank_radius = 0.25         # meters (r)
        self.rod_length = 0.70           # meters (l)

    def step(self, dt: float, is_running: bool = True) -> Dict[str, Any]:
        """Advances mechanical simulation by delta time dt."""
        if is_running:
            d_theta = (self.engine_rpm * 2.0 * np.pi / 60.0) * dt
            self.crankshaft_angle = (self.crankshaft_angle + d_theta) % (2 * np.pi)
            self.gear_angle = (self.gear_angle + d_theta * 0.5) % (2 * np.pi)
            self.wheel_angle = (self.wheel_angle + d_theta * 0.25) % (2 * np.pi)

        # 1. Slider-crank kinematics for piston displacement:
        # y(theta) = r * cos(theta) + sqrt(l^2 - r^2 * sin^2(theta))
        r = self.crank_radius
        l = self.rod_length
        theta = self.crankshaft_angle
        piston_y = r * np.cos(theta) + np.sqrt(max(1e-4, l**2 - (r * np.sin(theta))**2))
        rod_angle = float(np.arcsin(np.clip((r * np.sin(theta)) / l, -1.0, 1.0)))

        # Gearbox kinematics
        # Pinion drives Counter Gear at 2:1 reduction in reverse direction
        pinion_rot = self.gear_angle
        driven_rot = -0.5 * self.gear_angle

        return {
            "engine": {
                "crankshaft_angle_rad": round(float(self.crankshaft_angle), 4),
                "piston_y": round(float(piston_y), 4),
                "rod_angle_rad": round(float(rod_angle), 4),
                "rpm": self.engine_rpm
            },
            "gearbox": {
                "drive_gear_angle_rad": round(float(pinion_rot), 4),
                "driven_gear_angle_rad": round(float(driven_rot), 4),
            },
            "wheel_assembly": {
                "wheel_angle_rad": round(float(self.wheel_angle), 4),
                "brake_disc_angle_rad": round(float(self.wheel_angle), 4),
            },
            "suspension": {
                "compression_m": round(float(self.suspension_compression), 4)
            }
        }
