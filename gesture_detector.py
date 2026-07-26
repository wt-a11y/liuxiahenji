"""
手势检测模块
============
纯 MediaPipe Hands 关键点数据驱动的轻量手势识别。

支持 2 个核心手势：
- 张开手掌（open_palm）：5 指全部伸展
- 握拳（closed_fist）：4 根手指弯曲 + 拇指收起

识别策略：
- 每帧基于 21 个关键点计算"伸出指头数"
- 用 N 帧连续判定（去抖）+ 持续时间触发（hold）
- 状态机：NONE → DETECTING → CONFIRMED（一次性事件）

返回：
- 实时识别结果 get_current_gesture() → 字符串
- 历史事件 consume_event() → ('open' 或 'close')
"""

import time
import math
from typing import Optional, List, Tuple
import mediapipe as mp


class GestureDetector:
    """
    手势检测器

    用法：
        detector = GestureDetector()
        # 每帧：把 MediaPipe 输出的 hand_landmarks 喂给它
        gesture = detector.update(hand_landmarks)
        # 周期性消费事件
        event = detector.consume_event()
    """

    # MediaPipe 关键点索引（21 个）
    # 0 = WRIST, 4 = THUMB_TIP, 8 = INDEX_TIP, 12 = MIDDLE_TIP, 16 = RING_TIP, 20 = PINKY_TIP
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    # MCP 关节（指根）
    THUMB_MCP = 2
    INDEX_MCP = 5
    MIDDLE_MCP = 9
    RING_MCP = 13
    PINKY_MCP = 17

    # PIP 关节（中间）
    INDEX_PIP = 6
    MIDDLE_PIP = 10
    RING_PIP = 14
    PINKY_PIP = 18

    def __init__(self,
                 open_hold_sec: float = 1.0,
                 close_hold_sec: float = 1.5,
                 debounce_frames: int = 3,
                 post_event_cooldown_sec: float = 1.2):
        """
        Args:
            open_hold_sec: 张开手掌持续多久触发"open"事件
            close_hold_sec: 握拳持续多久触发"close"事件
            debounce_frames: 去抖帧数（连续 N 帧都是同一手势才开始计时）
            post_event_cooldown_sec: 触发事件后多久内不接受新事件（让用户有反应时间）
        """
        self.open_hold_sec = open_hold_sec
        self.close_hold_sec = close_hold_sec
        self.debounce_frames = debounce_frames
        self.post_event_cooldown_sec = post_event_cooldown_sec

        # 状态
        self._current_gesture = 'unknown'  # 'open' / 'close' / 'unknown'
        self._same_gesture_count = 0       # 连续相同帧数
        self._hold_start_time = None       # 当前持续手势的开始时间
        self._event_queue: List[str] = []  # 待消费事件队列

        # 防滥用：上次事件后冷却（cooldown 用参数控制，默认 1.2s）
        self._last_event_time = 0.0
        self.cooldown_sec = post_event_cooldown_sec
        self._in_cooldown = False
        self._last_gesture_before_cooldown = None

    def _landmark_distance(self, lm_a, lm_b) -> float:
        """3D 距离"""
        dx = lm_a.x - lm_b.x
        dy = lm_a.y - lm_b.y
        dz = lm_a.z - lm_b.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def _is_finger_extended(self, landmarks, tip_id, pip_id, mcp_id) -> bool:
        """
        判断一根手指是否"伸展"
        启发式：指尖到 MCP 的距离 > PIP 到 MCP 的距离（伸直时指尖远离指根）
        """
        tip = landmarks[tip_id]
        pip = landmarks[pip_id]
        mcp = landmarks[mcp_id]
        # PIP 到 MCP 距离（弯曲时变短，伸直时变长）
        pip_to_mcp = self._landmark_distance(pip, mcp)
        # TIP 到 PIP 距离（伸直时变长）
        tip_to_pip = self._landmark_distance(tip, pip)
        # 伸直时：tip 应该比 pip 更"外延"
        # 用 tip-to-pip 与 mcp-to-pip 的比值
        # 经验阈值：伸直时 tip 到 pip > 0.9 * (mcp 到 pip)
        return tip_to_pip > pip_to_mcp * 0.85

    def _is_thumb_extended(self, landmarks) -> bool:
        """
        拇指是否伸展（特殊判断：横向）
        比较拇指尖到小指 MCP 的距离 vs 拇指 MCP 到小指 MCP 的距离
        """
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        pinky_mcp = landmarks[self.PINKY_MCP]
        tip_to_pinky_mcp = self._landmark_distance(thumb_tip, pinky_mcp)
        mcp_to_pinky_mcp = self._landmark_distance(thumb_mcp, pinky_mcp)
        # 伸展时：拇指离掌心较远
        return tip_to_pinky_mcp > mcp_to_pinky_mcp * 1.1

    def classify(self, hand_landmarks) -> str:
        """
        分类当前帧的手势

        Args:
            hand_landmarks: MediaPipe hand_landmarks 对象，含 .landmark[i] 关键点

        Returns:
            'open' / 'close' / 'unknown'
        """
        if hand_landmarks is None:
            return 'unknown'
        lm = hand_landmarks.landmark
        # 检查 4 根手指（拇指单独判断）
        index_ext = self._is_finger_extended(lm, self.INDEX_TIP, self.INDEX_PIP, self.INDEX_MCP)
        middle_ext = self._is_finger_extended(lm, self.MIDDLE_TIP, self.MIDDLE_PIP, self.MIDDLE_MCP)
        ring_ext = self._is_finger_extended(lm, self.RING_TIP, self.RING_PIP, self.RING_MCP)
        pinky_ext = self._is_finger_extended(lm, self.PINKY_TIP, self.PINKY_PIP, self.PINKY_MCP)
        thumb_ext = self._is_thumb_extended(lm)

        extended_count = sum([index_ext, middle_ext, ring_ext, pinky_ext, thumb_ext])

        # open: 全部 5 指伸展
        if extended_count >= 4 and thumb_ext:
            return 'open'
        # close: 4 指弯曲 + 拇指收起（不伸展）
        if extended_count == 0 or (not thumb_ext and extended_count <= 1):
            return 'close'
        return 'unknown'

    def update(self, hand_landmarks) -> str:
        """
        每帧调用一次，喂新的 hand_landmarks

        Returns:
            当前手势（'open' / 'close' / 'unknown'）
        """
        detected = self.classify(hand_landmarks)

        # 防抖：连续 N 帧相同
        if detected == self._current_gesture and detected != 'unknown':
            self._same_gesture_count += 1
        else:
            self._same_gesture_count = 0
            self._hold_start_time = None
            # 从一个手势切换到另一个时，标记"上一次的持续状态结束"
            if detected != self._current_gesture:
                self._current_gesture = detected
                if detected != 'unknown':
                    self._hold_start_time = time.time()
                return detected
            self._current_gesture = detected

        # 检查持续时间
        if detected != 'unknown' and self._same_gesture_count >= self.debounce_frames:
            if self._hold_start_time is None:
                self._hold_start_time = time.time()
            held_for = time.time() - self._hold_start_time
            target_hold = self.open_hold_sec if detected == 'open' else self.close_hold_sec
            # close 是高优先级动作（退出），不受 cooldown 限制
            # open 是常规动作（翻页/暂停反思），需要 cooldown 让用户有反应时间
            can_trigger = (time.time() - self._last_event_time) > self.cooldown_sec
            is_high_priority = (detected == 'close')
            if held_for >= target_hold and (can_trigger or is_high_priority):
                # 触发事件（一次性）
                self._event_queue.append(detected)
                self._last_event_time = time.time()
                # 触发后立即进入冷却期：
                # 强制把当前手势置为 unknown（让 UI 不再显示 100%）
                # 直到用户松开手势（hand_landmarks 消失或换成 other）
                self._current_gesture = 'unknown'
                self._same_gesture_count = 0
                self._hold_start_time = None
                self._in_cooldown = not is_high_priority  # close 退出程序后不需要冷却

        # 冷却期：冷却时间到立刻退出（不再要求用户切换手势）
        if getattr(self, '_in_cooldown', False):
            if (time.time() - self._last_event_time) >= self.post_event_cooldown_sec:
                self._in_cooldown = False
                self._last_gesture_before_cooldown = None
                self._hold_start_time = None
                self._same_gesture_count = 0
            else:
                return 'unknown'
        self._last_gesture_before_cooldown = detected

        return self._current_gesture

    def get_current_gesture(self) -> str:
        """获取当前手势（仅查询，不消费）"""
        return self._current_gesture

    def get_hold_progress(self) -> float:
        """
        获取当前手势的持续进度（0.0-1.0）

        用于 UI 显示进度条：
        - 0.0 = 刚开始计时
        - 1.0 = 即将触发事件
        """
        if self._current_gesture == 'unknown' or self._hold_start_time is None:
            return 0.0
        held = time.time() - self._hold_start_time
        target = self.open_hold_sec if self._current_gesture == 'open' else self.close_hold_sec
        return min(1.0, held / target)

    def consume_event(self) -> Optional[str]:
        """消费一个事件（'open' / 'close' / None）"""
        if self._event_queue:
            return self._event_queue.pop(0)
        return None
