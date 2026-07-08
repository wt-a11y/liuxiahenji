from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


class PersonTracker:
    """给每个检测到的人分配稳定的 ID，并计算基础速度。"""

    def __init__(self, max_distance: float = 160.0, max_missing_frames: int = 5):
        self.max_distance = max_distance
        self.max_missing_frames = max_missing_frames
        self.active_tracks: Dict[int, Dict[str, object]] = {}
        self.next_id = 1

    def update(self, detections: List[Dict[str, object]], timestamp: float) -> List[Dict[str, object]]:
        if not detections:
            self._mark_missing_frames()
            return []

        matched_detection_indices = set()
        tracked_people: List[Dict[str, object]] = []

        for person_id in sorted(self.active_tracks.keys()):
            track = self.active_tracks[person_id]
            if int(track["missing_frames"]) > 0:
                continue

            best_index: Optional[int] = None
            best_distance: Optional[float] = None
            last_position = np.array(track["last_position"], dtype=float)
            for idx, detection in enumerate(detections):
                if idx in matched_detection_indices:
                    continue
                current_position = np.array(detection["position"], dtype=float)
                distance = float(np.linalg.norm(current_position - last_position))
                if best_distance is None or distance < best_distance:
                    best_index = idx
                    best_distance = distance

            if best_index is not None and best_distance is not None and best_distance <= self.max_distance:
                matched_detection_indices.add(best_index)
                detected_person = self._create_tracked_person(detections[best_index], person_id, timestamp, track)
                tracked_people.append(detected_person)
                track["missing_frames"] = 0
                track["last_position"] = detected_person["position"]
                track["last_timestamp"] = timestamp
            else:
                track["missing_frames"] = int(track["missing_frames"]) + 1

        for idx, detection in enumerate(detections):
            if idx in matched_detection_indices:
                continue
            person_id = self.next_id
            self.next_id += 1
            self.active_tracks[person_id] = {
                "person_id": person_id,
                "last_position": detection["position"],
                "last_timestamp": timestamp,
                "missing_frames": 0,
            }
            tracked_people.append(self._create_tracked_person(detection, person_id, timestamp, self.active_tracks[person_id]))

        self._remove_inactive_tracks()
        return tracked_people

    def _create_tracked_person(
        self,
        detection: Dict[str, object],
        person_id: int,
        timestamp: float,
        track: Dict[str, object],
    ) -> Dict[str, object]:
        current_position = np.array(detection["position"], dtype=float)
        last_position = np.array(track["last_position"], dtype=float)
        delta_time = timestamp - float(track["last_timestamp"])
        if delta_time <= 0:
            velocity = 0.0
        else:
            velocity = float(np.linalg.norm(current_position - last_position) / delta_time)

        tracked_person = dict(detection)
        tracked_person["person_id"] = person_id
        tracked_person["velocity"] = velocity
        return tracked_person

    def _mark_missing_frames(self) -> None:
        for track in self.active_tracks.values():
            track["missing_frames"] = int(track["missing_frames"]) + 1
        self._remove_inactive_tracks()

    def _remove_inactive_tracks(self) -> None:
        inactive_ids = [
            person_id for person_id, track in self.active_tracks.items() if int(track["missing_frames"]) > self.max_missing_frames
        ]
        for person_id in inactive_ids:
            del self.active_tracks[person_id]
