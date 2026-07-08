from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
except ImportError:  # pragma: no cover - depends on runtime environment
    mp = None


if mp is not None and hasattr(mp, "solutions"):
    LANDMARK_NAMES = {
        "nose": mp.solutions.pose.PoseLandmark.NOSE,
        "left_shoulder": mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
        "right_shoulder": mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
        "left_elbow": mp.solutions.pose.PoseLandmark.LEFT_ELBOW,
        "right_elbow": mp.solutions.pose.PoseLandmark.RIGHT_ELBOW,
        "left_wrist": mp.solutions.pose.PoseLandmark.LEFT_WRIST,
        "right_wrist": mp.solutions.pose.PoseLandmark.RIGHT_WRIST,
        "left_hip": mp.solutions.pose.PoseLandmark.LEFT_HIP,
        "right_hip": mp.solutions.pose.PoseLandmark.RIGHT_HIP,
        "left_knee": mp.solutions.pose.PoseLandmark.LEFT_KNEE,
        "right_knee": mp.solutions.pose.PoseLandmark.RIGHT_KNEE,
        "left_ankle": mp.solutions.pose.PoseLandmark.LEFT_ANKLE,
        "right_ankle": mp.solutions.pose.PoseLandmark.RIGHT_ANKLE,
    }
else:
    LANDMARK_NAMES = {}


class PoseDetector:
    """使用 MediaPipe Pose 检测人体关键点，并尝试处理多人场景。"""

    def __init__(self, detection_confidence: float = 0.5, tracking_confidence: float = 0.5):
        self.mp_available = mp is not None and hasattr(mp, "solutions")
        self.pose = None
        if self.mp_available:
            self.pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                enable_segmentation=False,
                min_detection_confidence=detection_confidence,
                min_tracking_confidence=tracking_confidence,
            )
        self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_fullbody.xml")
        if self.body_cascade.empty():
            self.body_cascade = None

    def detect_people(self, frame) -> List[Dict[str, object]]:
        """返回一帧中所有检测到的人的基础特征。"""
        height, width = frame.shape[:2]
        candidate_boxes = self._get_candidate_boxes(frame)

        detected_people: List[Dict[str, object]] = []
        for x, y, w, h in candidate_boxes[:5]:
            if w < 40 or h < 80:
                continue
            x1 = max(0, x - 20)
            y1 = max(0, y - 30)
            x2 = min(width, x + w + 20)
            y2 = min(height, y + h + 30)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            if self.mp_available and self.pose is not None:
                rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb_crop)
                if not results.pose_landmarks:
                    continue

                landmarks = self._extract_landmarks(results.pose_landmarks, x1, y1, crop.shape[1], crop.shape[0])
                person_record = self._build_person_record(landmarks)
                if person_record is not None:
                    detected_people.append(person_record)
            else:
                landmarks = self._build_fallback_landmarks(x1, y1, w, h)
                person_record = self._build_person_record(landmarks)
                if person_record is not None:
                    detected_people.append(person_record)

        if not detected_people and self.mp_available and self.pose is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)
            if results.pose_landmarks:
                landmarks = self._extract_landmarks(results.pose_landmarks, 0, 0, width, height)
                person_record = self._build_person_record(landmarks)
                if person_record is not None:
                    detected_people.append(person_record)

        return detected_people[:5]

    def _get_candidate_boxes(self, frame) -> List[Tuple[int, int, int, int]]:
        height, width = frame.shape[:2]
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.body_cascade is None:
            return [(0, 0, width, height)]

        detections = self.body_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(80, 160),
        )
        if len(detections) == 0:
            return [(0, 0, width, height)]

        boxes = []
        for x, y, w, h in detections:
            boxes.append((int(x), int(y), int(w), int(h)))
        return boxes

    def _extract_landmarks(
        self,
        pose_landmarks,
        offset_x: int,
        offset_y: int,
        crop_width: int,
        crop_height: int,
    ) -> Dict[str, List[float]]:
        landmarks: Dict[str, List[float]] = {}
        for name, landmark_index in LANDMARK_NAMES.items():
            landmark = pose_landmarks.landmark[landmark_index]
            x = int(landmark.x * crop_width + offset_x)
            y = int(landmark.y * crop_height + offset_y)
            landmarks[name] = [x, y]
        return landmarks

    def _build_fallback_landmarks(self, x: int, y: int, w: int, h: int) -> Dict[str, List[float]]:
        return {
            "nose": [int(x + w * 0.5), int(y + h * 0.18)],
            "left_shoulder": [int(x + w * 0.35), int(y + h * 0.25)],
            "right_shoulder": [int(x + w * 0.65), int(y + h * 0.25)],
            "left_elbow": [int(x + w * 0.30), int(y + h * 0.42)],
            "right_elbow": [int(x + w * 0.70), int(y + h * 0.42)],
            "left_wrist": [int(x + w * 0.28), int(y + h * 0.60)],
            "right_wrist": [int(x + w * 0.72), int(y + h * 0.60)],
            "left_hip": [int(x + w * 0.38), int(y + h * 0.58)],
            "right_hip": [int(x + w * 0.62), int(y + h * 0.58)],
            "left_knee": [int(x + w * 0.40), int(y + h * 0.78)],
            "right_knee": [int(x + w * 0.60), int(y + h * 0.78)],
            "left_ankle": [int(x + w * 0.42), int(y + h * 0.95)],
            "right_ankle": [int(x + w * 0.58), int(y + h * 0.95)],
        }

    def _build_person_record(self, landmarks: Dict[str, List[float]]) -> Optional[Dict[str, object]]:
        required_keys = ["left_hip", "right_hip", "left_shoulder", "right_shoulder"]
        if any(key not in landmarks for key in required_keys):
            return None

        left_hip = np.array(landmarks["left_hip"], dtype=float)
        right_hip = np.array(landmarks["right_hip"], dtype=float)
        left_shoulder = np.array(landmarks["left_shoulder"], dtype=float)
        right_shoulder = np.array(landmarks["right_shoulder"], dtype=float)

        position = [float((left_hip[0] + right_hip[0]) / 2.0), float((left_hip[1] + right_hip[1]) / 2.0)]
        orientation = self._compute_orientation(left_shoulder, right_shoulder)

        return {
            "landmarks": landmarks,
            "position": position,
            "orientation": orientation,
        }

    def _compute_orientation(self, left_shoulder: np.ndarray, right_shoulder: np.ndarray) -> float:
        dx = float(right_shoulder[0] - left_shoulder[0])
        dy = float(right_shoulder[1] - left_shoulder[1])
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            return 0.0
        angle = math.degrees(math.atan2(dy, dx))
        return float((angle + 360.0) % 360.0)
