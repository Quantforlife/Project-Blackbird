"""Detection memory store with multi-seen confirmation."""
from __future__ import annotations


class DetectionStore:
    """Track detections and confirm after repeated observations."""

    def __init__(self, min_confirmations: int = 2) -> None:
        if min_confirmations <= 0:
            raise ValueError("min_confirmations must be positive")
        self.min_confirmations = min_confirmations
        self._records: dict[str, dict[str, object]] = {}

    @staticmethod
    def _key(panel_id: str, defect_type: str) -> str:
        return f"{panel_id}:{defect_type}"

    def _record_to_output(self, rec: dict[str, object]) -> dict[str, object]:
        return {
            "panel_id": rec["panel_id"],
            "defect_type": rec["defect_type"],
            "first_seen_timestamp": rec["first_seen_timestamp"],
            "confirmation_count": rec["confirmation_count"],
            "average_confidence": round(float(rec["average_confidence"]), 4),
            "geo_location": rec["latest_detection"]["geo_location"],
        }

    def update(
        self,
        detections: list[dict[str, object]],
        timestamp: str,
    ) -> list[dict[str, object]]:
        """Update store with frame detections and return newly confirmed records."""
        newly_confirmed: list[dict[str, object]] = []
        seen_keys: set[str] = set()

        for detection in detections:
            panel_id = str(detection["panel_id"])
            defect_type = str(detection["defect_type"])
            key = self._key(panel_id, defect_type)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            confidence = float(detection["confidence"])
            if key not in self._records:
                self._records[key] = {
                    "panel_id": panel_id,
                    "defect_type": defect_type,
                    "first_seen_timestamp": timestamp,
                    "last_seen_timestamp": timestamp,
                    "confirmation_count": 1,
                    "average_confidence": confidence,
                    "latest_detection": detection,
                    "confirmed": False,
                }
            else:
                rec = self._records[key]
                count = int(rec["confirmation_count"]) + 1
                old_avg = float(rec["average_confidence"])
                new_avg = ((old_avg * (count - 1)) + confidence) / count
                rec["confirmation_count"] = count
                rec["average_confidence"] = new_avg
                rec["last_seen_timestamp"] = timestamp
                rec["latest_detection"] = detection

            rec = self._records[key]
            if (
                int(rec["confirmation_count"]) >= self.min_confirmations
                and not bool(rec["confirmed"])
            ):
                rec["confirmed"] = True
                newly_confirmed.append(self._record_to_output(rec))

        return newly_confirmed

    def confirmed_detections(self) -> list[dict[str, object]]:
        """Return all detections that reached confirmation threshold."""
        output: list[dict[str, object]] = []
        for rec in self._records.values():
            if bool(rec.get("confirmed", False)):
                output.append(self._record_to_output(rec))
        return output
