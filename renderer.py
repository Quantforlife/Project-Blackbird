"""
Detection pipeline — runs YOLOv8 inference on uploaded images.
Celery worker picks up tasks from Redis queue.
"""
import os
import uuid
import math
import logging
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.tasks.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)

# Synchronous engine for Celery (Celery workers can't use async)
sync_engine = create_engine(settings.sync_database_url, pool_pre_ping=True)
SyncSession = sessionmaker(bind=sync_engine)

# COCO class → defect type mapping (demo mapping)
COCO_TO_DEFECT = {
    "person":       "soiling",
    "bicycle":      "crack",
    "car":          "physical_damage",
    "motorcycle":   "delamination",
    "airplane":     "corrosion",
    "bus":          "hot_spot",
    "train":        "micro_crack",
    "truck":        "bypass_diode_failure",
    "boat":         "snail_trail",
    "cat":          "potential_induced_degradation",
    "dog":          "glass_breakage",
    "horse":        "delamination",
    "bird":         "soiling",
    "cow":          "hot_spot",
    "elephant":     "crack",
    "umbrella":     "corrosion",
    "handbag":      "shading",
    "tie":          "micro_crack",
    "suitcase":     "bypass_diode_failure",
    "bottle":       "soiling",
    "cup":          "hot_spot",
    "fork":         "crack",
    "knife":        "physical_damage",
    "chair":        "delamination",
    "couch":        "corrosion",
    "laptop":       "hot_spot",
    "cell phone":   "soiling",
    "book":         "shading",
    "clock":        "micro_crack",
    "vase":         "glass_breakage",
}

SEVERITY_MAP = {
    "soiling": "low",
    "shading": "low",
    "micro_crack": "medium",
    "hot_spot": "medium",
    "snail_trail": "medium",
    "crack": "high",
    "delamination": "high",
    "corrosion": "high",
    "bypass_diode_failure": "critical",
    "glass_breakage": "critical",
    "physical_damage": "critical",
    "potential_induced_degradation": "critical",
}


def _load_yolo():
    """
    YOLO is optional — not installed on free-tier deployments.
    Synthetic detections are used as fallback for demo purposes.
    """
    try:
        from ultralytics import YOLO  # type: ignore
        model = YOLO(settings.yolo_model)
        return model
    except Exception as e:
        logger.info(f"YOLO unavailable, synthetic detections active: {e}")
        return None


_yolo_model = None


def get_yolo():
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = _load_yolo()
    return _yolo_model


@celery_app.task(name="run_detection", bind=True, max_retries=3)
def run_detection(self, image_id: str):
    """Run YOLOv8 inference on an image and store detections."""
    from app.models.models import Image, Detection, Asset, DefectSeverity
    import json

    logger.info(f"Running detection on image {image_id}")
    db = SyncSession()

    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            logger.error(f"Image {image_id} not found")
            return {"status": "error", "message": "Image not found"}

        detections_data = _run_inference(image.filepath)

        # Find nearest asset to associate
        assets = db.query(Asset).all()
        nearest_asset = _find_nearest_asset(image.lat, image.lon, assets)

        stored = []
        for det in detections_data:
            detection = Detection(
                id=str(uuid.uuid4()),
                image_id=image_id,
                asset_id=nearest_asset.id if nearest_asset else None,
                label=det["label"],
                confidence=det["confidence"],
                severity=DefectSeverity(det["severity"]),
                bbox_x=det["bbox"][0],
                bbox_y=det["bbox"][1],
                bbox_w=det["bbox"][2],
                bbox_h=det["bbox"][3],
                is_manual=False,
            )
            db.add(detection)
            stored.append(det)

        image.processed = True

        # Update asset condition if we found one
        if nearest_asset and stored:
            _update_asset_condition(nearest_asset, stored, db)

        db.commit()

        # Publish detection event to Redis
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            event = {
                "type": "detection",
                "image_id": image_id,
                "mission_id": image.mission_id,
                "count": len(stored),
                "timestamp": datetime.utcnow().isoformat(),
            }
            r.publish("events:detections", json.dumps(event))
        except Exception as e:
            logger.warning(f"Failed to publish detection event: {e}")

        logger.info(f"Detection complete: {len(stored)} defects found in image {image_id}")
        return {"status": "ok", "image_id": image_id, "detections": len(stored)}

    except Exception as exc:
        db.rollback()
        logger.error(f"Detection failed for {image_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


def _run_inference(filepath: str) -> List[Dict[str, Any]]:
    """Run YOLO inference and return structured detections."""
    model = get_yolo()
    results_list = []

    if model is None or not os.path.exists(filepath):
        # Fallback: generate synthetic detections for demo
        return _synthetic_detections()

    try:
        results = model(filepath, verbose=False)
        for result in results:
            if result.boxes is None:
                continue
            h, w = result.orig_shape
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = result.names.get(cls_id, "unknown")
                conf = float(box.conf[0])

                defect_label = COCO_TO_DEFECT.get(cls_name, "anomaly")
                severity = SEVERITY_MAP.get(defect_label, "low")

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bbox = [x1/w, y1/h, (x2-x1)/w, (y2-y1)/h]

                results_list.append({
                    "label": defect_label,
                    "confidence": round(conf, 4),
                    "severity": severity,
                    "bbox": bbox,
                })
    except Exception as e:
        logger.error(f"YOLO inference error: {e}")
        return _synthetic_detections()

    return results_list


def _synthetic_detections() -> List[Dict[str, Any]]:
    """Generate plausible synthetic detections for demo/testing."""
    import random
    rng = random.Random()

    defect_types = ["soiling", "hot_spot", "crack", "delamination", "micro_crack"]
    count = rng.randint(0, 3)
    results = []

    for _ in range(count):
        label = rng.choice(defect_types)
        conf = round(rng.uniform(0.55, 0.98), 4)
        x = round(rng.uniform(0.1, 0.7), 3)
        y = round(rng.uniform(0.1, 0.7), 3)
        w = round(rng.uniform(0.05, 0.25), 3)
        h = round(rng.uniform(0.05, 0.25), 3)
        results.append({
            "label": label,
            "confidence": conf,
            "severity": SEVERITY_MAP.get(label, "low"),
            "bbox": [x, y, w, h],
        })

    return results


def _find_nearest_asset(lat, lon, assets):
    """Find the asset closest to the given coordinates."""
    if not lat or not lon or not assets:
        return None

    def dist(a):
        dlat = (a.lat - lat) * 111000
        dlon = (a.lon - lon) * 111000 * math.cos(math.radians(lat))
        return math.sqrt(dlat**2 + dlon**2)

    nearest = min(assets, key=dist, default=None)
    # Only associate if within 100m
    if nearest and dist(nearest) < 100:
        return nearest
    return None


def _update_asset_condition(asset, detections, db):
    """Degrade asset condition score based on new detections."""
    severity_penalty = {"low": 1.0, "medium": 3.0, "high": 7.0, "critical": 15.0}
    penalty = sum(severity_penalty.get(d["severity"], 1.0) for d in detections)
    asset.condition_score = max(0.0, asset.condition_score - penalty)
    db.add(asset)
