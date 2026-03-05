"""Perception and edge inference pipeline tests."""
from __future__ import annotations

from app.perception.camera import SimulatedCamera
from app.perception.detection_store import DetectionStore
from app.perception.models.edge_model import EdgeDefectModel
from app.perception.pipeline import PerceptionEngine
from app.simulation.defects import DefectField
from app.simulation.drone import SimulatedDrone
from app.simulation.environment import SolarFarmEnvironment
from app.simulation.mission import GridInspectionMission


def _setup_scene(rows: int = 3, columns: int = 3):
    env = SolarFarmEnvironment(37.0, -122.0, rows=rows, columns=columns, panel_spacing_meters=6.0)
    mission = GridInspectionMission(env, inspection_altitude=26.0)
    waypoints = mission.generate_waypoints()
    drone = SimulatedDrone(
        latitude=waypoints[0].latitude,
        longitude=waypoints[0].longitude,
        altitude=waypoints[0].altitude,
        velocity_mps=5.0,
    )
    drone.set_mission(waypoints)
    defect_field = DefectField(environment=env, seed=11, defect_rate=0.6)
    env.defect_field = defect_field
    return env, drone, defect_field


def test_camera_sees_expected_panels() -> None:
    env, drone, _ = _setup_scene()
    camera = SimulatedCamera(drone=drone, fov_degrees=62.0, resolution=(640, 384))

    frame = camera.capture(env, drone.get_state())
    assert frame["frame_id"] == 1
    assert len(frame["visible_panels"]) > 0

    panel_ids = {p["panel_id"] for p in frame["visible_panels"]}
    assert "r0c0" in panel_ids


def test_detection_only_for_real_defects() -> None:
    env, drone, defect_field = _setup_scene()
    camera = SimulatedCamera(drone=drone)
    pipeline = PerceptionEngine(model_type="simulated")

    frame = camera.capture(env, drone.get_state())
    detections = pipeline.process_frame(frame)
    defect_panels = {f"r{d.panel_row}c{d.panel_col}" for d in defect_field.all_defects()}

    for det in detections:
        assert det["panel_id"] in defect_panels


def test_confidence_decreases_with_altitude() -> None:
    env, drone, _ = _setup_scene()
    camera = SimulatedCamera(drone=drone)
    model = EdgeDefectModel("simulated")
    model.load()

    low_state = drone.get_state()
    low_state["altitude"] = 18.0
    high_state = drone.get_state()
    high_state["altitude"] = 70.0

    low_frame = camera.capture(env, low_state)
    high_frame = camera.capture(env, high_state)

    low_dets = model.infer(low_frame)
    high_dets = model.infer(high_frame)

    if not low_dets or not high_dets:
        assert isinstance(low_dets, list)
        assert isinstance(high_dets, list)
        return

    low_max = max(d["confidence"] for d in low_dets)
    high_max = max(d["confidence"] for d in high_dets)
    assert high_max <= low_max


def test_duplicate_detection_confirmation_memory() -> None:
    store = DetectionStore(min_confirmations=2)
    detection = {
        "panel_id": "r1c1",
        "defect_type": "hotspot",
        "confidence": 0.8,
        "geo_location": {"latitude": 1.0, "longitude": 2.0},
    }

    first = store.update([detection, detection], "t1")
    second = store.update([detection], "t2")

    assert first == []
    assert len(second) == 1
    assert second[0]["confirmation_count"] == 2


def test_model_fallback_without_heavy_dependencies() -> None:
    model = EdgeDefectModel("onnx")
    runtime = model.load()
    assert runtime in {"onnx", "simulated"}

    output = model.infer(
        {
            "visible_panels": [],
            "defects_visible": [],
            "drone_position": {"altitude": 30.0},
            "camera": {"resolution": (640, 384), "mounting_angle_degrees": 90.0, "ground_footprint_m": 25.0},
        }
    )
    assert output == []
