"""
手部追踪模块

使用 MediaPipe Hands 检测手部关键点
获取手腕和食指指尖坐标

可直接运行测试：python hand_tracking.py
"""

import cv2
import mediapipe as mp
import time
import math
from typing import Optional, Dict, Tuple


class HandTracker:
    """
    手部追踪器

    封装 MediaPipe Hands，提供手部关键点检测接口
    优化：缩放检测、跳帧、EMA 滤波、速度外推、多点平均
    """

    # 类常量
    DETECT_WIDTH = 640               # 检测帧宽度
    DETECT_HEIGHT = 360              # 检测帧高度
    DETECT_EVERY_N_FRAMES = 2        # 每 N 帧检测一次
    MAX_INTERPOLATE_FRAMES = 3       # 最多外推帧数
    EMA_ALPHA = 0.5                  # 位置 EMA（0.5=平衡，0.3=强滤波，0.7=少滤波）
    DEAD_ZONE = 6.0                  # 死区：变化 < 此值不更新（防抖）- 加大
    STATIC_SMOOTH_THRESHOLD = 8.0    # 平滑位置变化 < 此值认为静止 - 放宽
    STATIC_FREEZE_FRAMES = 4         # 连续 N 帧静止后完全冻结
    FAST_MOVE_VEL_THRESHOLD = 30.0   # 速度 > 此值时检测失败仍外推
    CROP_RATIO = 1.0                # 中央裁剪比例（1.0=不裁剪，全画面识别）

    def __init__(self):
        """初始化手部追踪器"""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,                # 轻量模型
            min_detection_confidence=0.3,      # 降低检测阈值
            min_tracking_confidence=0.3        # 降低跟踪阈值
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        # 状态变量
        self._frame_count = 0
        self._last_pos = None                # 上次检测到的原始位置
        self._smooth_pos = None              # EMA 平滑后的位置
        self._last_velocity = (0.0, 0.0)     # 估计速度 (vx, vy)
        self._last_detect_time = None        # 上次检测时间
        self._missing_count = 0              # 连续失败帧数
        self._scale = 1.0                    # 检测到原图的缩放比例
        self._x_start = 0                    # 裁剪起始 x
        self._y_start = 0                    # 裁剪起始 y
        self._crop_w = 1280                  # 裁剪宽度（默认）
        self._crop_h = 720                   # 裁剪高度（默认）
        self._static_frame_count = 0         # 连续静止帧数（达到阈值后冻结）

    def get_hand_position(self, frame) -> Optional[Dict[str, int]]:
        """
        获取手部关键点位置（指尖位置，含优化）

        Returns:
            {"x": int, "y": int} 或 None
        """
        now = time.time()
        self._frame_count += 1
        h_orig, w_orig = frame.shape[:2]

        # === 计算中央裁剪范围 ===
        if self._crop_w != w_orig or self._crop_h != h_orig:
            self._crop_w = w_orig
            self._crop_h = h_orig
            self._x_start = int(w_orig * (1 - self.CROP_RATIO) / 2)
            self._y_start = int(h_orig * (1 - self.CROP_RATIO) / 2)
            crop_w = int(w_orig * self.CROP_RATIO)
            crop_h = int(h_orig * self.CROP_RATIO)
        else:
            crop_w = int(w_orig * self.CROP_RATIO)
            crop_h = int(h_orig * self.CROP_RATIO)

        # === 跳帧策略 ===
        should_detect = (self._frame_count % self.DETECT_EVERY_N_FRAMES == 0) or self._smooth_pos is None

        if not should_detect:
            # 跳帧：用速度外推
            if self._smooth_pos is not None and self._last_detect_time is not None:
                dt = now - self._last_detect_time
                vx, vy = self._last_velocity
                # 速度衰减（避免无限外推）
                vx *= 0.85
                vy *= 0.85
                new_x = self._smooth_pos[0] + vx * dt
                new_y = self._smooth_pos[1] + vy * dt
                # 边界裁剪
                new_x = max(0, min(w_orig - 1, new_x))
                new_y = max(0, min(h_orig - 1, new_y))
                self._smooth_pos = (new_x, new_y)
                self._last_detect_time = now
                return {"x": int(new_x), "y": int(new_y)}
            return None

        # === 真实检测 ===
        # 中央裁剪
        cropped = frame[self._y_start:self._y_start + crop_h,
                        self._x_start:self._x_start + crop_w]

        # 缩放
        small = cv2.resize(cropped, (self.DETECT_WIDTH, self.DETECT_HEIGHT))
        # 颜色转换
        rgb_frame = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        # MediaPipe 处理
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            # === 多点平均（指尖 + 手腕 + 中指 MCP） ===
            tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]

            # 平均坐标（在缩放后的坐标系，归一化 0-1）
            avg_x_small = (tip.x + wrist.x + mcp.x) / 3.0
            avg_y_small = (tip.y + wrist.y + mcp.y) / 3.0

            # 缩放还原：small(归一化) → cropped → original
            # 关键：乘 cropped 尺寸（不是 DETECT_WIDTH，那是缩放前的小图）
            avg_x_crop = avg_x_small * crop_w
            avg_y_crop = avg_y_small * crop_h

            # 裁剪还原：cropped → original（加裁剪偏移）
            raw_x = avg_x_crop + self._x_start
            raw_y = avg_y_crop + self._y_start

            # 边界
            raw_x = max(0, min(w_orig - 1, raw_x))
            raw_y = max(0, min(h_orig - 1, raw_y))

            # === EMA 滤波 + 死区 + 静止检测 ===
            if self._smooth_pos is None:
                # 首次：直接初始化
                self._smooth_pos = (raw_x, raw_y)
                self._last_pos = (raw_x, raw_y)
                self._last_velocity = (0.0, 0.0)
                self._missing_count = 0
                self._last_detect_time = now
                return {"x": int(raw_x), "y": int(raw_y)}

            # 计算与平滑位置的偏差
            dx_from_smooth = raw_x - self._smooth_pos[0]
            dy_from_smooth = raw_y - self._smooth_pos[1]
            dist_from_smooth = math.hypot(dx_from_smooth, dy_from_smooth)

            if dist_from_smooth < self.STATIC_SMOOTH_THRESHOLD:
                # 偏差小：可能静止，也可能小幅移动
                self._static_frame_count += 1

                if self._static_frame_count >= self.STATIC_FREEZE_FRAMES:
                    # 连续静止 → 完全冻结位置（消除所有微抖动）
                    self._last_velocity = (0.0, 0.0)
                    self._missing_count = 0
                    self._last_detect_time = now
                    self._last_pos = (raw_x, raw_y)
                    return {"x": int(self._smooth_pos[0]), "y": int(self._smooth_pos[1])}

                # 静止初期：用 EMA 缓慢更新（不会漂移）
                new_smooth_x = self.EMA_ALPHA * raw_x + (1 - self.EMA_ALPHA) * self._smooth_pos[0]
                new_smooth_y = self.EMA_ALPHA * raw_y + (1 - self.EMA_ALPHA) * self._smooth_pos[1]

                # 死区检查：变化 < DEAD_ZONE 不更新
                actual_dx = new_smooth_x - self._smooth_pos[0]
                actual_dy = new_smooth_y - self._smooth_pos[1]
                if abs(actual_dx) < self.DEAD_ZONE * 0.5 and abs(actual_dy) < self.DEAD_ZONE * 0.5:
                    # 微小变化：保持
                    pass
                else:
                    self._smooth_pos = (new_smooth_x, new_smooth_y)

                # 速度衰减（静止时）
                self._last_velocity = (self._last_velocity[0] * 0.3, self._last_velocity[1] * 0.3)
                self._last_pos = (raw_x, raw_y)
                self._missing_count = 0
                self._last_detect_time = now
                return {"x": int(self._smooth_pos[0]), "y": int(self._smooth_pos[1])}

            # 偏差大：手在动 → 重置静止计数
            self._static_frame_count = 0

            # 偏差大：手在动
            # 速度估计
            if self._last_pos is not None and self._last_detect_time is not None:
                dt_real = max(now - self._last_detect_time, 1e-6)
                vx_new = (raw_x - self._last_pos[0]) / dt_real
                vy_new = (raw_y - self._last_pos[1]) / dt_real

                # 速度更激进：取新值（如果它更大）
                vx_final = vx_new if abs(vx_new) > abs(self._last_velocity[0]) else (
                    0.6 * vx_new + 0.4 * self._last_velocity[0]
                )
                vy_final = vy_new if abs(vy_new) > abs(self._last_velocity[1]) else (
                    0.6 * vy_new + 0.4 * self._last_velocity[1]
                )
                self._last_velocity = (vx_final, vy_final)

            # EMA 更新平滑位置
            new_smooth_x = self.EMA_ALPHA * raw_x + (1 - self.EMA_ALPHA) * self._smooth_pos[0]
            new_smooth_y = self.EMA_ALPHA * raw_y + (1 - self.EMA_ALPHA) * self._smooth_pos[1]
            self._smooth_pos = (new_smooth_x, new_smooth_y)
            self._last_pos = (raw_x, raw_y)
            self._missing_count = 0
            self._last_detect_time = now
            return {"x": int(self._smooth_pos[0]), "y": int(self._smooth_pos[1])}

        # === MediaPipe 检测失败 ===
        speed = math.hypot(self._last_velocity[0], self._last_velocity[1])
        if speed < self.FAST_MOVE_VEL_THRESHOLD:
            # 速度小：真的没手
            self._last_velocity = (0.0, 0.0)
            self._smooth_pos = None
            self._last_pos = None
            return None

        # 快速运动中：尝试外推
        self._missing_count += 1
        if self._missing_count > self.MAX_INTERPOLATE_FRAMES:
            self._last_velocity = (0.0, 0.0)
            self._smooth_pos = None
            self._last_pos = None
            return None

        if self._smooth_pos is not None and self._last_detect_time is not None:
            dt = now - self._last_detect_time
            vx, vy = self._last_velocity
            vx *= 0.6
            vy *= 0.6
            self._last_velocity = (vx, vy)
            new_x = self._smooth_pos[0] + vx * dt
            new_y = self._smooth_pos[1] + vy * dt
            new_x = max(0, min(w_orig - 1, new_x))
            new_y = max(0, min(h_orig - 1, new_y))
            self._smooth_pos = (new_x, new_y)
            self._last_detect_time = now
            return {"x": int(new_x), "y": int(new_y)}

        return None

    def get_wrist_and_index_tip(self, frame) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取手腕和食指指尖坐标（含优化）

        Returns:
            (wrist_pos, index_tip_pos) 或 None
        """
        h_orig, w_orig = frame.shape[:2]

        # 中央裁剪
        crop_w = int(w_orig * self.CROP_RATIO)
        crop_h = int(h_orig * self.CROP_RATIO)
        x_start = int(w_orig * (1 - self.CROP_RATIO) / 2)
        y_start = int(h_orig * (1 - self.CROP_RATIO) / 2)
        cropped = frame[y_start:y_start + crop_h, x_start:x_start + crop_w]

        # 缩放
        small = cv2.resize(cropped, (self.DETECT_WIDTH, self.DETECT_HEIGHT))
        rgb_frame = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            wrist_pos = (int(wrist.x * self.DETECT_WIDTH + x_start),
                        int(wrist.y * self.DETECT_HEIGHT + y_start))

            index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            index_tip_pos = (int(index_tip.x * self.DETECT_WIDTH + x_start),
                            int(index_tip.y * self.DETECT_HEIGHT + y_start))

            return (wrist_pos, index_tip_pos)

        return None

    def draw_landmarks(self, frame, highlight_wrist: bool = True, highlight_index_tip: bool = True) -> None:
        """在图像上绘制手部关键点"""
        h_orig, w_orig = frame.shape[:2]

        crop_w = int(w_orig * self.CROP_RATIO)
        crop_h = int(h_orig * self.CROP_RATIO)
        x_start = int(w_orig * (1 - self.CROP_RATIO) / 2)
        y_start = int(h_orig * (1 - self.CROP_RATIO) / 2)
        cropped = frame[y_start:y_start + crop_h, x_start:x_start + crop_w]
        small = cv2.resize(cropped, (self.DETECT_WIDTH, self.DETECT_HEIGHT))
        rgb_frame = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            # 绘制（在 small 坐标系）
            annotated = small.copy()
            self.mp_draw.draw_landmarks(
                annotated,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_styles.get_default_hand_landmarks_style(),
                self.mp_styles.get_default_hand_connections_style()
            )
            # 还原到原图大小
            annotated_full = cv2.resize(annotated, (crop_w, crop_h))
            frame[y_start:y_start + crop_h, x_start:x_start + crop_w] = annotated_full

            h, w = self.DETECT_HEIGHT, self.DETECT_WIDTH

            if highlight_wrist:
                wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                wrist_pos = (int(wrist.x * w + x_start), int(wrist.y * h + y_start))
                cv2.circle(frame, wrist_pos, 10, (0, 0, 255), -1)
                cv2.putText(frame, "Wrist", (wrist_pos[0] + 15, wrist_pos[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            if highlight_index_tip:
                index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                tip_pos = (int(index_tip.x * w + x_start), int(index_tip.y * h + y_start))
                cv2.circle(frame, tip_pos, 10, (0, 255, 0), -1)
                cv2.putText(frame, "Index Tip", (tip_pos[0] + 15, tip_pos[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def release(self):
        """释放资源"""
        self.hands.close()


def main():
    """测试函数"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("错误：无法打开摄像头")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)

    tracker = HandTracker()
    print("手部追踪已启动（含优化）")
    print("按 'q' 键退出")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        hand_pos = tracker.get_hand_position(frame)

        if hand_pos:
            cv2.putText(frame, f"Tip: ({hand_pos['x']}, {hand_pos['y']})", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            status = "Hand Detected"
            color = (0, 255, 0)
        else:
            status = "No Hand"
            color = (0, 0, 255)

        cv2.putText(frame, status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow("Hand Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    tracker.release()
    cap.release()
    cv2.destroyAllWindows()
