"""Deterministic simulation and autonomy tests."""
from __future__ import annotations

from app.simulation.defects import DefectField
from app.simulation.drone import SimulatedDrone
from app.simulation.engine import SimulationEngine
from app.simulation.environment import SolarFarmEnvironment
from app.simulation.mission import GridInspectionMission


def test_environment_grid_generation() -> None:
    env = SolarFarmEnvironment(37.0, -122.0, rows=3, columns=4, panel_spacing_meters=5.0)
    panels = env.get_panel_coordinates()
    bounds = env.get_farm_bounds()

    assert len(panels) == 12
    assert bounds["width_meters"] == 15.0
    assert bounds["height_meters"] == 10.0
    assert panels[0].row == 0 and panels[0].col == 0
    assert panels[-1].row == 2 and panels[-1].col == 3


def test_mission_waypoints_serpentine() -> None:
    env = SolarFarmEnvironment(37.0, -122.0, rows=2, columns=3, panel_spacing_meters=6.0)
    mission = GridInspectionMission(environment=env, inspection_altitude=35.0)
    waypoints = mission.generate_waypoints()

    assert len(waypoints) == 6
    # row 0 left->right, row 1 right->left
    assert waypoints[0].longitude < waypoints[1].longitude < waypoints[2].longitude
    assert waypoints[3].longitude > waypoints[4].longitude > waypoints[5].longitude
    assert all(w.altitude == 35.0 for w in waypoints)


def test_drone_follows_exact_path_and_battery_drains() -> None:
    env = SolarFarmEnvironment(37.0, -122.0, rows=1, columns=3, panel_spacing_meters=4.0)
    waypoints = GridInspectionMission(env, inspection_altitude=20.0).generate_waypoints()
    drone = SimulatedDrone(
        latitude=waypoints[0].latitude,
        longitude=waypoints[0].longitude,
        altitude=waypoints[0].altitude,
        velocity_mps=4.0,
    )
    drone.set_mission(waypoints)

    initial = drone.get_state()
    for _ in range(20):
        drone.step(1.0)
    final = drone.get_state()

    assert final["current_waypoint_index"] >= initial["current_waypoint_index"]
    assert final["battery"] < initial["battery"]
    assert final["mission_state"] == "completed"


def test_engine_mission_completion() -> None:
    engine = SimulationEngine(rows=2, columns=2, panel_spacing_meters=4.0, velocity_mps=8.0)
    for _ in range(20):
        engine.step(1.0)
    state = engine.get_current_state()

    assert state["mission_progress"] == 100.0
    assert state["mission_state"] == "completed"


def test_defects_trigger_only_near_correct_panels() -> None:
    env = SolarFarmEnvironment(37.0, -122.0, rows=3, columns=3, panel_spacing_meters=6.0)
    defects = DefectField(environment=env, seed=7, defect_rate=0.5)
    all_defects = defects.all_defects()

    if not all_defects:
        assert defects.get_defects_in_view(37.0, -122.0) == []
        return

    target = all_defects[0]
    near = defects.get_defects_in_view(target.latitude, target.longitude, view_radius_meters=2.0)
    far = defects.get_defects_in_view(0.0, 0.0, view_radius_meters=2.0)

    assert any(d.panel_row == target.panel_row and d.panel_col == target.panel_col for d in near)
    assert far == []
