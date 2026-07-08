from __future__ import annotations

import cv2
import time


class CameraCapture:
    """封装摄像头读取逻辑，方便后续切换输入设备。"""

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None

    def start(self) -> None:
        # 尝试多个 backend
        backends = [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]
        self.cap = None
        
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(self.camera_index, backend)
                if self.cap is None or not self.cap.isOpened():
                    if self.cap is not None:
                        self.cap.release()
                    continue
                
                # 尝试读取一帧来验证
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    break
                else:
                    self.cap.release()
                    self.cap = None
            except Exception:
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                continue
        
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError("无法打开摄像头，请确认设备连接正常。")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read_frame(self):
        if self.cap is None:
            raise RuntimeError("摄像头尚未启动。")

        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("读取视频帧失败。")
        return frame

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
