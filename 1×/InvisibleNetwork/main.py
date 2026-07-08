from __future__ import annotations

import argparse
import time
from typing import List, Dict

import cv2
import numpy as np

from camera import CameraCapture
from data_logger import DataLogger
from pose_detection import PoseDetector
from tracking import PersonTracker


def draw_overlay(frame, tracked_people: List[Dict[str, object]]) -> np.ndarray:
    display_frame = frame.copy()
    for person in tracked_people:
        landmarks = person["landmarks"]
        person_id = person["person_id"]
        position = person["position"]

        for start_name, end_name in [
            ("left_shoulder", "left_elbow"),
            ("left_elbow", "left_wrist"),
            ("right_shoulder", "right_elbow"),
            ("right_elbow", "right_wrist"),
            ("left_shoulder", "left_hip"),
            ("right_shoulder", "right_hip"),
            ("left_hip", "left_knee"),
            ("left_knee", "left_ankle"),
            ("right_hip", "right_knee"),
            ("right_knee", "right_ankle"),
        ]:
            if start_name in landmarks and end_name in landmarks:
                start = tuple(map(int, landmarks[start_name]))
                end = tuple(map(int, landmarks[end_name]))
                cv2.line(display_frame, start, end, (0, 255, 0), 2)

        for landmark_name, coordinate in landmarks.items():
            x, y = int(coordinate[0]), int(coordinate[1])
            cv2.circle(display_frame, (x, y), 4, (255, 0, 0), -1)

        cv2.putText(
            display_frame,
            f"P{person_id}",
            (int(position[0]) - 10, int(position[1]) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

    return display_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invisible Network - 人体姿态数据采集原型")
    parser.add_argument("--camera-index", type=int, default=0, help="摄像头编号")
    parser.add_argument("--output", default="output/pose_data.json", help="输出 JSON 文件路径")
    parser.add_argument("--no-display", action="store_true", help="不显示实时窗口，只保存数据")
    return parser.parse_args()


def main() -> None:
    print("程序已启动", flush=True)
    args = parse_args()
    print(f"摄像头编号: {args.camera_index}", flush=True)

    camera = CameraCapture(camera_index=args.camera_index)
    print("正在初始化摄像头...", flush=True)
    detector = PoseDetector()
    print("正在初始化姿态检测器...", flush=True)
    tracker = PersonTracker()
    print("正在初始化人体追踪...", flush=True)
    logger = DataLogger(output_path=args.output)
    print("正在初始化数据记录器...", flush=True)

    camera.start()
    print("摄像头已启动", flush=True)
    frame_index = 0
    start_program_time = time.perf_counter()
    # 显式创建并定位窗口，帮助在多显示器或后台会话中更容易看到
    window_name = "Invisible Network - Pose Capture"
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.moveWindow(window_name, 50, 50)
        # 尝试设置窗口置顶（非所有平台都支持）
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            pass
    except Exception:
        window_name = "Invisible Network - Pose Capture"

    try:
        while True:
            frame = camera.read_frame()
            frame_index += 1
            start_time = time.perf_counter()

            detections = detector.detect_people(frame)
            tracked_people = tracker.update(detections, start_time)

            for person in tracked_people:
                person["position"] = [float(person["position"][0]), float(person["position"][1])]
                person["orientation"] = float(person["orientation"])
                person["velocity"] = float(person["velocity"])

            logger.log_frame(frame_index, tracked_people)

            display_frame = draw_overlay(frame, tracked_people)
            if not args.no_display:
                cv2.imshow(window_name, display_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                if frame_index % 30 == 0:
                    print(f"已采集第 {frame_index} 帧，当前检测到 {len(tracked_people)} 个人", flush=True)
    finally:
        camera.release()
        if not args.no_display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
