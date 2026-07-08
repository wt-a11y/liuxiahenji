#!/usr/bin/env python
import sys
import time
import json
from pathlib import Path

# 添加 InvisibleNetwork 到路径
sys.path.insert(0, str(Path(__file__).parent / "InvisibleNetwork"))

from camera import CameraCapture
from pose_detection import PoseDetector
from tracking import PersonTracker
from data_logger import DataLogger

print("测试程序启动", flush=True)

try:
    # 初始化
    print("初始化摄像头...", flush=True)
    camera = CameraCapture(camera_index=1)
    camera.start()
    print("摄像头已启动", flush=True)
    
    detector = PoseDetector()
    tracker = PersonTracker()
    logger = DataLogger(output_path="output/pose_test.json")
    
    # 采集 3 秒内的帧（约 90 帧，如果是 30fps）
    print("开始采集数据...", flush=True)
    start_time = time.perf_counter()
    frame_count = 0
    
    while time.perf_counter() - start_time < 3:
        frame = camera.read_frame()
        frame_count += 1
        curr_time = time.perf_counter()
        
        detections = detector.detect_people(frame)
        tracked_people = tracker.update(detections, curr_time)
        
        for person in tracked_people:
            person["position"] = [float(person["position"][0]), float(person["position"][1])]
            person["orientation"] = float(person["orientation"])
            person["velocity"] = float(person["velocity"])
        
        logger.log_frame(frame_count, tracked_people)
        
        if frame_count % 30 == 0:
            print(f"已采集 {frame_count} 帧，检测到 {len(tracked_people)} 个人", flush=True)
    
    print(f"采集完成！总共 {frame_count} 帧", flush=True)
    
    # 分析数据
    with open("output/pose_test.json", "r") as f:
        data = json.load(f)
    
    print(f"\n数据分析:")
    print(f"总帧数: {len(data)}")
    
    if data:
        first = data[0]["persons"][0] if data[0]["persons"] else None
        last = data[-1]["persons"][0] if data[-1]["persons"] else None
        
        if first and last:
            print(f"第1帧位置: {first['position']}")
            print(f"最后1帧位置: {last['position']}")
            print(f"位置差: ({last['position'][0] - first['position'][0]:.1f}, {last['position'][1] - first['position'][1]:.1f})")
    
    camera.release()
    print("程序成功完成", flush=True)

except Exception as e:
    print(f"错误: {e}", flush=True)
    import traceback
    traceback.print_exc()
