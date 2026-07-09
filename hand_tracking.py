"""
手部追踪模块

使用 MediaPipe Hands 检测手部关键点
获取手腕和食指指尖坐标

可直接运行测试：python hand_tracking.py
"""

import cv2
import mediapipe as mp
from typing import Optional, Dict, Tuple


class HandTracker:
    """
    手部追踪器
    
    封装 MediaPipe Hands，提供手部关键点检测接口
    """
    
    def __init__(self):
        """初始化手部追踪器"""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles
        
    def get_hand_position(self, frame) -> Optional[Dict[str, int]]:
        """
        获取手部关键点位置
        
        Args:
            frame: OpenCV 图像帧 (BGR格式)
            
        Returns:
            包含 x, y 坐标的字典，未检测到手时返回 None
            {
                "x": int,  # 食指指尖 x 坐标
                "y": int   # 食指指尖 y 坐标
            }
        """
        # 转换颜色空间
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 处理图像
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            # 获取第一只手的 landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # 获取图像尺寸
            h, w, _ = frame.shape
            
            # 获取食指指尖坐标 (landmark 8)
            index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            x = int(index_tip.x * w)
            y = int(index_tip.y * h)
            
            return {"x": x, "y": y}
        
        return None
    
    def get_wrist_and_index_tip(self, frame) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取手腕和食指指尖坐标
        
        Args:
            frame: OpenCV 图像帧
            
        Returns:
            (wrist_pos, index_tip_pos) 元组，未检测到手时返回 None
            wrist_pos: (x, y) 手腕坐标
            index_tip_pos: (x, y) 食指指尖坐标
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            h, w, _ = frame.shape
            
            # 获取手腕坐标 (landmark 0)
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            wrist_pos = (int(wrist.x * w), int(wrist.y * h))
            
            # 获取食指指尖坐标 (landmark 8)
            index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            index_tip_pos = (int(index_tip.x * w), int(index_tip.y * h))
            
            return (wrist_pos, index_tip_pos)
        
        return None
    
    def draw_landmarks(self, frame, highlight_wrist: bool = True, highlight_index_tip: bool = True) -> None:
        """
        在图像上绘制手部关键点
        
        Args:
            frame: OpenCV 图像帧
            highlight_wrist: 是否高亮显示手腕
            highlight_index_tip: 是否高亮显示食指指尖
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            h, w, _ = frame.shape
            
            # 绘制所有关键点
            self.mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_styles.get_default_hand_landmarks_style(),
                self.mp_styles.get_default_hand_connections_style()
            )
            
            # 高亮手腕
            if highlight_wrist:
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                wrist_pos = (int(wrist.x * w), int(wrist.y * h))
                cv2.circle(frame, wrist_pos, 10, (0, 0, 255), -1)  # 红色实心圆
                cv2.putText(frame, "Wrist", (wrist_pos[0] + 15, wrist_pos[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 高亮食指指尖
            if highlight_index_tip:
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                tip_pos = (int(index_tip.x * w), int(index_tip.y * h))
                cv2.circle(frame, tip_pos, 10, (0, 255, 0), -1)  # 绿色实心圆
                cv2.putText(frame, "Index Tip", (tip_pos[0] + 15, tip_pos[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    def release(self):
        """释放资源"""
        self.hands.close()


def main():
    """
    测试函数：直接运行此文件进行手部追踪测试
    
    按 'q' 键退出
    """
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("错误：无法打开摄像头")
        return
    
    # 初始化手部追踪器
    tracker = HandTracker()
    
    print("手部追踪已启动")
    print("按 'q' 键退出")
    
    while True:
        # 读取帧
        ret, frame = cap.read()
        if not ret:
            print("错误：无法读取摄像头画面")
            break
        
        # 镜像翻转，符合自然交互习惯
        frame = cv2.flip(frame, 1)
        
        # 获取手部位置
        hand_pos = tracker.get_hand_position(frame)
        
        # 获取手腕和食指指尖
        wrist_and_tip = tracker.get_wrist_and_index_tip(frame)
        
        # 绘制手部关键点
        tracker.draw_landmarks(frame)
        
        # 显示坐标信息
        if hand_pos:
            info_text = f"Index Tip: ({hand_pos['x']}, {hand_pos['y']})"
            cv2.putText(frame, info_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if wrist_and_tip:
            wrist_pos, tip_pos = wrist_and_tip
            wrist_text = f"Wrist: ({wrist_pos[0]}, {wrist_pos[1]})"
            cv2.putText(frame, wrist_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 显示状态
        status = "Hand Detected" if hand_pos else "No Hand"
        color = (0, 255, 0) if hand_pos else (0, 0, 255)
        cv2.putText(frame, status, (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # 显示画面
        cv2.imshow("Hand Tracking - Press 'q' to exit", frame)
        
        # 检测按键
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 释放资源
    tracker.release()
    cap.release()
    cv2.destroyAllWindows()
    print("程序已退出")


if __name__ == "__main__":
    main()
