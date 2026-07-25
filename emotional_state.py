"""
情感状态模块

实现生命体的情绪状态系统，让"他人"的反应可视化

核心概念：
- 生命体不是被动接受影响，而是有情绪反应的"他人"
- 情绪状态影响视觉表现和交互反馈
- 情绪会随时间缓慢恢复，但严重伤害会留下持久影响
"""

from enum import Enum, auto
from typing import Dict, Tuple, Optional, List
import math
import time


class EmotionalState(Enum):
    """生命体的情绪状态"""
    CALM = "calm"           # 平静 - 正常状态
    ALERT = "alert"         # 警觉 - 被惊扰，快速接近或粗暴动作
    WITHDRAWN = "withdrawn" # 退缩 - 受到伤害后的防御状态
    OPEN = "open"           # 敞开 - 被温柔对待后的信任状态
    NEGLECTED = "neglected" # 被忽视 - 长时间无互动


class EmotionalCore:
    """
    生命体的情感核心
    
    管理情绪状态转换、情绪强度、恢复过程
    """
    
    # 状态持续时间（秒）
    STATE_DURATIONS = {
        EmotionalState.ALERT: 2.5,      # 警觉2.5秒后尝试恢复（原3秒，缩短以加快响应）
        EmotionalState.WITHDRAWN: 4.0,  # 退缩4秒后缓慢恢复（原5秒）
        EmotionalState.OPEN: 3.0,       # 敞开3秒后回归平静（原4秒）
        EmotionalState.NEGLECTED: 8.0,  # 被忽视8秒后尝试恢复（之前是inf）
    }
    
    # 忽视判定时间（秒）
    NEGLECT_THRESHOLD = 10.0
    
    def __init__(self):
        self.current_state = EmotionalState.CALM
        self.state_intensity = 0.0  # 当前状态强度 [0, 1]
        self.state_timer = 0.0      # 当前状态持续时间
        self.last_interaction_time = time.time()
        self.cumulative_harm = 0.0   # 累积伤害
        self.cumulative_care = 0.0   # 累积关怀
        
        # 视觉反馈参数
        self.breath_rate = 1.0       # 呼吸速率倍率（1.0 = 正常）
        self.size_scale = 1.0        # 体型缩放（退缩时缩小）
        self.opacity = 1.0           # 透明度（被忽视时降低）
        self.glow_intensity = 0.0    # 光晕强度
        
        # 状态切换回调
        self.on_state_change = None

        # 警觉锁定：进入个人空间时强制锁定，优先级最高
        # 锁定期间只能被更高的优先级（WITHDRAWN=伤害）覆盖，不能被 OPEN/平静 覆盖
        self.alert_locked = False
        
    def update(self, dt: float, interaction_data: Optional[Dict] = None):
        """
        更新情感状态
        
        Args:
            dt: 时间增量（秒）
            interaction_data: 交互数据，包含动作类型、强度等
        """
        current_time = time.time()
        
        # 处理新的交互
        if interaction_data:
            self.last_interaction_time = current_time
            self._process_interaction(interaction_data)
        
        # 检查是否被忽视
        time_since_interaction = current_time - self.last_interaction_time
        if time_since_interaction > self.NEGLECT_THRESHOLD:
            if self.current_state != EmotionalState.NEGLECTED:
                self._transition_to(EmotionalState.NEGLECTED)
        
        # 更新状态计时器
        self.state_timer += dt
        
        # 检查状态自动恢复
        if self.current_state in self.STATE_DURATIONS:
            max_duration = self.STATE_DURATIONS[self.current_state]
            if self.state_timer > max_duration:
                self._attempt_recovery()
        
        # 更新视觉参数
        self._update_visual_params(dt)
        
    def _process_interaction(self, data: Dict):
        """处理交互事件，可能导致状态转换"""
        action_type = data.get('type', 'neutral')  # 'gentle', 'violent', 'approach', 'retreat'
        intensity = data.get('intensity', 0.5)  # [0, 1]

        # 优先级规则：
        # WITHDRAWN（伤害/退缩） > ALERT（警觉） > OPEN（敞开） > CALM/NEGLECTED
        # 警觉被锁定时：除 WITHDRAWN 外，其他状态都被屏蔽
        if self.alert_locked and self.current_state == EmotionalState.ALERT:
            if action_type == 'violent' and intensity >= 0.85:
                # 强烈伤害可以触发 WITHDRAWN，覆盖警觉
                self._transition_to(EmotionalState.WITHDRAWN, intensity)
                return
            if action_type == 'approach' or action_type == 'approach_violent':
                # 持续警觉中，重新进入红圈：增强强度
                self.state_intensity = min(1.0, max(self.state_intensity, intensity))
                self.state_timer = 0.0
                return
            # 其他（gentle 等）不改变警觉状态
            return

        if action_type == 'violent':
            self.cumulative_harm += intensity
            # 现在 violent 动作的 intensity 范围是 0.7-1.0
            # intensity > 0.85 触发 WITHDRAWN（退缩）
            # 0.7-0.85 触发 ALERT（警觉）
            if intensity >= 0.85:
                self._transition_to(EmotionalState.WITHDRAWN, intensity)
            else:
                self._transition_to(EmotionalState.ALERT, intensity)

        elif action_type == 'gentle':
            self.cumulative_care += intensity
            # 如果是从退缩状态被治愈
            if self.current_state == EmotionalState.WITHDRAWN:
                if self.cumulative_care > self.cumulative_harm * 0.5:
                    self._transition_to(EmotionalState.OPEN, intensity)
            else:
                self._transition_to(EmotionalState.OPEN, intensity)

        elif action_type == 'approach':
            # 接近触发警觉（不再要求 intensity > 0.6 才有反应）
            # 任何接近都会引发不同程度的警觉
            self._transition_to(EmotionalState.ALERT, max(0.3, intensity))

        elif action_type == 'approach_violent':
            # 快速/粗暴接近 → 强烈警觉
            self._transition_to(EmotionalState.ALERT, max(0.6, intensity))

        elif action_type == 'retreat':
            # 突然远离可能加剧被忽视感
            if self.current_state == EmotionalState.OPEN:
                self._transition_to(EmotionalState.CALM)

    def trigger_approach(self, intensity: float = 0.5, violent: bool = False):
        """
        外部调用：直接触发"被接近"反应
        当手进入个人空间时由 spatial_metaphor 调用
        """
        action_type = 'approach_violent' if violent else 'approach'
        self._process_interaction({
            'type': action_type,
            'intensity': intensity
        })
    
    def _transition_to(self, new_state: EmotionalState, intensity: float = 0.5):
        """转换到新的情绪状态"""
        if new_state != self.current_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_timer = 0.0
            self.state_intensity = min(1.0, intensity)

            if self.on_state_change:
                self.on_state_change(old_state, new_state)

    def set_alert_lock(self, locked: bool):
        """设置警觉锁定状态（在/不在个人空间内）"""
        self.alert_locked = bool(locked)

    def force_alert(self, intensity: float = 0.5):
        """
        强制设置为警觉状态（不重置 timer，保持连贯）
        用于：手只要在红圈内就持续警觉，离开红圈才解锁
        """
        if self.current_state == EmotionalState.WITHDRAWN:
            # 退缩优先：不覆盖
            return
        intensity = max(0.3, min(1.0, intensity))
        if self.current_state != EmotionalState.ALERT:
            # 进入警觉
            self._transition_to(EmotionalState.ALERT, intensity)
        else:
            # 已经在警觉：只更新强度，不重置 timer（保留恢复节奏）
            self.state_intensity = max(self.state_intensity, intensity)
        # 锁定开启
        self.alert_locked = True

    def _attempt_recovery(self):
        """尝试从当前状态恢复"""
        # 警觉锁定时不恢复（保持警觉）
        if self.alert_locked and self.current_state == EmotionalState.ALERT:
            return

        recovery_map = {
            EmotionalState.ALERT: EmotionalState.CALM,
            EmotionalState.WITHDRAWN: EmotionalState.CALM,
            EmotionalState.OPEN: EmotionalState.CALM,
        }

        if self.current_state in recovery_map:
            # 根据累积伤害/关怀决定恢复后的状态
            # 只在伤害严重超过关怀时才保持警觉，避免反复横跳
            if self.cumulative_harm > self.cumulative_care * 3 and self.cumulative_harm > 5.0:
                # 伤害严重，保持警觉
                self._transition_to(EmotionalState.ALERT, 0.3)
            else:
                # 正常恢复到平静
                self._transition_to(recovery_map[self.current_state])
    
    def _update_visual_params(self, dt: float):
        """更新视觉反馈参数"""
        target_breath = 1.0
        target_size = 1.0
        target_opacity = 1.0
        target_glow = 0.0
        
        if self.current_state == EmotionalState.CALM:
            target_breath = 1.0
            target_size = 1.0
            target_glow = 0.1
            
        elif self.current_state == EmotionalState.ALERT:
            target_breath = 1.5 + self.state_intensity * 0.5  # 呼吸急促
            target_size = 1.0 - self.state_intensity * 0.1   # 微微收缩
            target_glow = 0.3
            
        elif self.current_state == EmotionalState.WITHDRAWN:
            target_breath = 0.6  # 呼吸放缓（压抑）
            target_size = 0.7 - self.state_intensity * 0.15  # 明显缩小
            target_opacity = 0.8
            target_glow = 0.0
            
        elif self.current_state == EmotionalState.OPEN:
            target_breath = 0.8  # 呼吸深缓
            target_size = 1.05 + self.state_intensity * 0.1  # 舒展
            target_glow = 0.4 + self.state_intensity * 0.3   # 柔和光晕
            
        elif self.current_state == EmotionalState.NEGLECTED:
            target_breath = 0.5  # 呼吸微弱
            target_size = 0.85
            target_opacity = 0.5 + 0.3 * (1.0 - min(1.0, self.state_timer / 10.0))  # 逐渐变淡
            target_glow = 0.0
        
        # 平滑过渡 - 提高响应速度
        # 原 2.0 * dt ≈ 0.033/帧，需要约 1.5 秒达到目标（太慢）
        # 现 8.0 * dt ≈ 0.13/帧，约 0.15 秒达到目标（快速响应）
        lerp_speed = min(1.0, 8.0 * dt)
        self.breath_rate += (target_breath - self.breath_rate) * lerp_speed
        self.size_scale += (target_size - self.size_scale) * lerp_speed
        self.opacity += (target_opacity - self.opacity) * lerp_speed
        self.glow_intensity += (target_glow - self.glow_intensity) * lerp_speed
    
    def get_state_description(self) -> str:
        """获取当前状态的中文描述"""
        descriptions = {
            EmotionalState.CALM: "平静",
            EmotionalState.ALERT: "警觉",
            EmotionalState.WITHDRAWN: "退缩",
            EmotionalState.OPEN: "敞开",
            EmotionalState.NEGLECTED: "被忽视",
        }
        return descriptions.get(self.current_state, "未知")

    def get_monologue(self) -> str:
        """
        获取生命体当前状态的"内心独白"
        短句/省略号/呼吸感
        根据强度变化，让独白有细微差异
        """
        # 平静：多版本，按强度/伤害累积选择
        if self.current_state == EmotionalState.CALM:
            if self.cumulative_harm > self.cumulative_care * 1.5:
                return "……（还在恢复）"
            return "……嗯"

        # 警觉：被接近
        if self.current_state == EmotionalState.ALERT:
            if self.state_intensity > 0.7:
                return "你……靠得太近了"
            if self.alert_locked:
                return "请……再慢一点"
            return "嗯？……"

        # 退缩：受伤害
        if self.current_state == EmotionalState.WITHDRAWN:
            if self.cumulative_harm > 5.0:
                return "……我需要空间"
            return "……别这样"

        # 敞开：被温柔对待
        if self.current_state == EmotionalState.OPEN:
            if self.cumulative_care > 3.0:
                return "我愿意靠近你"
            return "嗯……这样就很好"

        # 被忽视
        if self.current_state == EmotionalState.NEGLECTED:
            if self.state_timer > 15.0:
                return "……你还在吗？"
            return "……"

        return ""
    
    def get_relationship_quality(self) -> float:
        """
        获取关系质量 [-1, 1]
        -1 = 严重受损, 0 = 中性, 1 = 良好
        """
        total = self.cumulative_care + self.cumulative_harm
        if total == 0:
            return 0.0
        return (self.cumulative_care - self.cumulative_harm) / total
    
    def to_dict(self) -> Dict:
        """导出状态数据"""
        return {
            'state': self.current_state.value,
            'state_desc': self.get_state_description(),
            'intensity': round(self.state_intensity, 2),
            'breath_rate': round(self.breath_rate, 2),
            'size_scale': round(self.size_scale, 2),
            'opacity': round(self.opacity, 2),
            'glow': round(self.glow_intensity, 2),
            'cumulative_harm': round(self.cumulative_harm, 2),
            'cumulative_care': round(self.cumulative_care, 2),
            'relationship': round(self.get_relationship_quality(), 2),
        }


class ConsequenceManager:
    """
    后果管理器
    
    实现"控制与后果的显性化"：
    - 意图预警
    - 后果延迟
    - 修复成本
    - 累积效应
    """
    
    def __init__(self):
        # 意图预警
        self.warning_active = False
        self.warning_intensity = 0.0  # 预警强度 [0, 1]
        self.warning_cooldown = 0.0
        
        # 延迟后果队列
        self.pending_consequences = []  # [(trigger_time, consequence_data), ...]
        
        # 累积效应
        self.recent_actions = []  # 最近的动作记录
        self.cumulative_window = 10.0  # 累积窗口（秒）
        
    def check_intention(self, action_data: Dict) -> Dict:
        """
        检查意图，返回预警信息
        
        Returns:
            {'warning': bool, 'intensity': float, 'message': str}
        """
        speed = action_data.get('speed', 0)
        acceleration = action_data.get('acceleration', 0)
        
        # 预警阈值（达到剧烈动作的80%触发预警）
        warning_speed_threshold = 18.0 * 0.8  # POSITIVE_MAX_PEAK_SPEED * 0.8
        warning_accel_threshold = 60.0 * 0.8
        
        intensity = 0.0
        message = ""
        
        if speed > warning_speed_threshold:
            intensity = (speed - warning_speed_threshold) / (warning_speed_threshold * 0.25)
            message = "你的手正在快速接近..."
            
        if acceleration > warning_accel_threshold:
            accel_intensity = (acceleration - warning_accel_threshold) / (warning_accel_threshold * 0.25)
            intensity = max(intensity, accel_intensity)
            message = "动作变得急促..."
        
        self.warning_active = intensity > 0
        self.warning_intensity = min(1.0, intensity)
        
        return {
            'warning': self.warning_active,
            'intensity': self.warning_intensity,
            'message': message,
        }
    
    def queue_consequence(self, consequence_type: str, delay: float, data: Dict):
        """
        将后果加入延迟队列
        
        Args:
            consequence_type: 'harm', 'heal', 'alert' 等
            delay: 延迟时间（秒）
            data: 后果数据
        """
        trigger_time = time.time() + delay
        self.pending_consequences.append({
            'trigger_time': trigger_time,
            'type': consequence_type,
            'data': data,
        })
    
    def update(self, dt: float) -> List[Dict]:
        """
        更新后果队列，返回到期的后果
        
        Returns:
            到期的后果列表
        """
        current_time = time.time()
        triggered = []
        remaining = []
        
        for consequence in self.pending_consequences:
            if current_time >= consequence['trigger_time']:
                triggered.append(consequence)
            else:
                remaining.append(consequence)
        
        self.pending_consequences = remaining
        
        # 更新预警冷却
        if self.warning_cooldown > 0:
            self.warning_cooldown -= dt
            if self.warning_cooldown <= 0:
                self.warning_active = False
        
        return triggered
    
    def record_action(self, action_data: Dict):
        """记录动作用于累积效应计算"""
        current_time = time.time()
        self.recent_actions.append({
            'time': current_time,
            'data': action_data,
        })
        
        # 清理过期记录
        self.recent_actions = [
            a for a in self.recent_actions
            if current_time - a['time'] < self.cumulative_window
        ]
    
    def get_cumulative_effect(self) -> Dict:
        """
        计算累积效应
        
        Returns:
            {'harm_level': float, 'care_level': float, 'trend': str}
        """
        harm_count = sum(1 for a in self.recent_actions 
                        if a['data'].get('classification') == 'negative')
        care_count = sum(1 for a in self.recent_actions 
                        if a['data'].get('classification') == 'positive')
        
        total = len(self.recent_actions)
        if total == 0:
            return {'harm_level': 0, 'care_level': 0, 'trend': 'neutral'}
        
        harm_level = harm_count / total
        care_level = care_count / total
        
        # 判断趋势
        if harm_count >= 3:
            trend = 'escalating_harm'
        elif care_count >= 3:
            trend = 'building_trust'
        else:
            trend = 'mixed'
        
        return {
            'harm_level': round(harm_level, 2),
            'care_level': round(care_level, 2),
            'trend': trend,
            'recent_count': total,
        }


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("情感状态模块测试")
    print("=" * 50)
    
    # 测试情感核心
    core = EmotionalCore()
    print(f"\n初始状态: {core.get_state_description()}")
    
    # 模拟被伤害
    print("\n模拟粗暴动作...")
    core.update(0.1, {'type': 'violent', 'intensity': 0.8})
    print(f"状态: {core.get_state_description()}, 强度: {core.state_intensity}")
    
    # 模拟时间流逝
    for i in range(60):
        core.update(0.1)
    print(f"5秒后: {core.get_state_description()}")
    
    # 模拟被治愈
    print("\n模拟温柔动作...")
    core.update(0.1, {'type': 'gentle', 'intensity': 0.7})
    print(f"状态: {core.get_state_description()}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
