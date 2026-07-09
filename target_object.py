"""
目标对象模块

有机生命体 - 半透明、不规则形态的生命体抽象
行为痕迹会渗透进入内部，改变其结构和形态

核心概念：
- 不是数据节点，而是有机生命体
- 半透明外膜，内部有连续流动纹理
- 被影响时产生永久结构变化（新增纹理层）

视觉：
- 半透明有机膜（不规则边界）
- 内部连续流动纹理（曲线、涟漪）
- 影响后新增纹理层（留下永久变化）

动态反馈（membrane_disturbance）：
- Fragment接触膜：局部凹陷+涟漪（类似水滴进入水面）
- 吸收过程中：外膜收缩+内部纹理向碎片方向流动
- 完成吸收：恢复平静，但内部结构已改变

可直接运行测试：python target_object.py
"""

import pygame
import math
import random
from typing import List, Tuple, Dict, Optional


class FlowTexture:
    """
    流动纹理
    
    代表生命体内部的能量流动
    使用连续曲线，而不是离散光点
    
    特点：
    - 流动的曲线纹理
    - 动态波动
    - 被影响时增强纹理强度
    """
    
    def __init__(self, center_x: float, center_y: float, texture_id: int):
        """
        初始化流动纹理
        
        Args:
            center_x, center_y: 生命体中心位置
            texture_id: 纹理ID
        """
        self.id = texture_id
        
        # 纹理类型（不同形态）
        self.texture_type = random.choice(['wave', 'spiral', 'ripple'])
        
        # 基础参数
        self.base_angle = random.uniform(0, 2 * math.pi)
        self.base_radius = random.uniform(20, 40)  # 纹理半径范围
        self.current_angle = self.base_angle
        
        # 流动参数
        self.flow_speed = random.uniform(0.02, 0.05)
        self.flow_phase = random.uniform(0, 2 * math.pi)
        self.wave_frequency = random.uniform(2, 4)  # 波动频率
        
        # 纹理强度
        self.base_intensity = random.uniform(0.2, 0.4)
        self.current_intensity = self.base_intensity
        
        # 位置
        self.x = center_x
        self.y = center_y

        # 影响状态
        self.is_influenced = False
        self.influence_intensity = 0.0

        # === 内部纹理"脉络"系统 ===
        # memory_level 增加时，在现有曲线上叠加琥珀色脉络
        # 代表"外部经历融入"生命体的视觉
        # - 脉络仅是高亮部分曲线，不创建新的曲线/粒子
        # - 不覆盖原有纹理（基础曲线始终完整绘制）
        # - 脉络位置缓慢漂移，呈现生命感
        self.vein_phase_a = random.uniform(0, 1)  # 1st vein position on curve (0-1)
        self.vein_phase_b = random.uniform(0, 1)  # 2nd vein position (L3+ 才使用)
        self.vein_drift_speed = random.uniform(0.0008, 0.0022)  # 脉络漂移速度
        
    def update(self, center_x: float, center_y: float, is_influenced: bool,
               flow_bias_angle: float = None, flow_bias_intensity: float = 0.0):
        """
        更新纹理状态

        Args:
            center_x, center_y: 生命体中心位置
            is_influenced: 是否被影响
            flow_bias_angle: 流动偏置方向（外部扰动导致内部纹理向此方向流动）
            flow_bias_intensity: 流动偏置强度 (0.0 - 1.0)
        """
        # 流动效果
        self.flow_phase += self.flow_speed
        self.current_angle = self.base_angle + self.flow_phase * 0.1

        # 应用流动偏置（吸收阶段：内部纹理向碎片方向流动）
        if flow_bias_angle is not None and flow_bias_intensity > 0:
            # 计算从纹理到偏置方向的角度差
            angle_diff = flow_bias_angle - self.base_angle
            # 归一化到 [-pi, pi]
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            # 偏置方向加成（限制在最大偏置角度内）
            max_bias = 0.6 * flow_bias_intensity  # 最大偏置角度
            bias_offset = angle_diff * flow_bias_intensity * 0.15
            self.current_angle += max(-max_bias, min(max_bias, bias_offset))

            # 偏置越强，流动越快
            self.flow_phase += flow_bias_intensity * 0.02

        # 更新位置
        self.x = center_x
        self.y = center_y

        # 被影响时的变化
        if is_influenced:
            self.is_influenced = True
            self.influence_intensity = min(1.0, self.influence_intensity + 0.05)
            self.current_intensity = min(0.8, self.base_intensity + self.influence_intensity * 0.3)
    
    def get_points(self) -> List[Tuple[float, float]]:
        """
        获取纹理曲线点
        
        Returns:
            曲线点列表
        """
        points = []
        
        if self.texture_type == 'wave':
            # 波动纹理（半透明曲线，缓慢旋转）
            num_points = 20
            for i in range(num_points):
                t = i / (num_points - 1)
                
                # 基础半径
                radius = self.base_radius
                
                # 波动偏移（明显的曲线感）
                wave_offset = math.sin(t * self.wave_frequency * math.pi + self.flow_phase) * 12
                
                # 角度偏移
                angle_offset = t * 2.0 - 1.0
                
                # 计算点位置
                angle = self.current_angle + angle_offset
                r = radius + wave_offset
                
                x = self.x + math.cos(angle) * r
                y = self.y + math.sin(angle) * r
                
                points.append((x, y))
                
        elif self.texture_type == 'spiral':
            # 螺旋纹理（旋转的曲线）
            num_points = 24
            for i in range(num_points):
                t = i / (num_points - 1)
                
                # 螺旋半径
                radius = self.base_radius * (0.2 + t * 0.8)
                
                # 螺旋角度（更明显的旋转）
                angle = self.current_angle + t * 4 * math.pi
                
                # 波动偏移
                wave_offset = math.sin(t * self.wave_frequency * math.pi + self.flow_phase) * 6
                
                r = radius + wave_offset
                
                x = self.x + math.cos(angle) * r
                y = self.y + math.sin(angle) * r
                
                points.append((x, y))
                
        elif self.texture_type == 'ripple':
            # 涟漪纹理（动态变化的同心圆）
            num_points = 16
            for i in range(num_points):
                angle = i / num_points * 2 * math.pi
                
                # 涟漪半径（随时间变化）
                radius = self.base_radius + math.sin(self.flow_phase * 1.5 + angle * 2) * 12
                
                x = self.x + math.cos(angle) * radius
                y = self.y + math.sin(angle) * radius
                
                points.append((x, y))
        
        return points
    
    def get_intensity(self) -> float:
        """
        获取纹理强度
        
        Returns:
            纹理强度
        """
        return self.current_intensity


class PermanentTextureLayer:
    """
    永久纹理层
    
    被影响后新增的纹理层，留下永久结构变化
    
    特点：
    - 在影响点周围生成
    - 永久存在（不衰减）
    - 强度随累积影响增加
    """
    
    def __init__(self, center_x: float, center_y: float, impact_position: Tuple[float, float], intensity: float):
        """
        初始化永久纹理层
        
        Args:
            center_x, center_y: 生命体中心位置
            impact_position: 影响点位置
            intensity: 影响强度
        """
        # 影响点位置
        self.impact_x = impact_position[0]
        self.impact_y = impact_position[1]
        
        # 纹理参数
        self.base_radius = 15 + intensity * 10  # 纹理大小
        self.current_radius = self.base_radius
        
        # 纹理形态（类似涟漪，但更复杂）
        self.num_ripples = random.randint(2, 4)  # 多层涟漪
        self.ripple_offsets = [random.uniform(0, 2 * math.pi) for _ in range(self.num_ripples)]
        
        # 纹理强度
        self.intensity = intensity
        self.current_intensity = intensity
        
        # 动态参数
        self.flow_phase = random.uniform(0, 2 * math.pi)
        self.flow_speed = random.uniform(0.01, 0.02)
        
        # 位置
        self.center_x = center_x
        self.center_y = center_y
        
    def update(self, center_x: float, center_y: float):
        """
        更新纹理层
        
        Args:
            center_x, center_y: 生命体中心位置
        """
        # 流动效果（轻微波动）
        self.flow_phase += self.flow_speed
        
        # 更新位置
        self.center_x = center_x
        self.center_y = center_y
        
        # 纹理强度保持不变（永久存在）
    
    def get_points(self) -> List[List[Tuple[float, float]]]:
        """
        获取纹理层曲线点（多层涟漪）
        
        Returns:
            多层曲线点列表
        """
        all_layer_points = []
        
        # 计算相对于中心的位置
        dx = self.impact_x - self.center_x
        dy = self.impact_y - self.center_y
        
        # 多层涟漪
        for layer_idx in range(self.num_ripples):
            layer_points = []
            
            # 涟漪半径（从内到外）
            radius_offset = layer_idx * 8
            radius = self.current_radius + radius_offset
            
            # 涟漪点数
            num_points = 10
            
            for i in range(num_points):
                angle = i / num_points * 2 * math.pi
                
                # 添加波动
                wave_offset = math.sin(self.flow_phase + angle + self.ripple_offsets[layer_idx]) * 3
                
                r = radius + wave_offset
                
                # 计算点位置（相对于影响点）
                x = self.impact_x + math.cos(angle) * r
                y = self.impact_y + math.sin(angle) * r
                
                layer_points.append((x, y))

            all_layer_points.append(layer_points)

        return all_layer_points

    def get_intensity(self) -> float:
        """
        获取纹理强度

        Returns:
            纹理强度
        """
        return self.current_intensity


class MemoryLayer:
    """
    记忆层 - 一次吸收后生命体内部的永久变化

    核心设计：碎片消失后留下的是生命体内部的改变，不是残影。

    阶段表现（根据 layer_index）：
    - 1st (layer_index=0)：新增一条新纹理（吸收方向延伸的曲线）
    - 2nd (layer_index=1)：与已有纹理发生交叉，改写流动方向
    - 3rd (layer_index=2)：形成结构变化 - 局部亮度增加 + 纹理分支
    - 4th+ (layer_index>=3)：与最早的记忆层共振，强化已有结构

    关键约束：
    - 不是黄色多边形残影
    - 不会被无限堆叠（最大层数限制）
    - 通过改变生命体自身的绘制状态来表达
    """

    def __init__(self, center_x: float, center_y: float,
                 impact_angle: float, intensity: float, layer_index: int):
        """
        初始化记忆层

        Args:
            center_x, center_y: 生命体中心
            impact_angle: 碎片进入的方向（弧度）
            intensity: 影响强度 (0.0 - 1.0)
            layer_index: 该层是第几次吸收（0-based）
        """
        self.center_x = center_x
        self.center_y = center_y
        self.impact_angle = impact_angle
        self.intensity = intensity
        self.layer_index = layer_index

        # 渐入生长 (0.0 → 1.0)，避免突然出现
        self.growth = 0.0
        self.target_growth = 1.0

        # 个体特征 - 让每个记忆层有微妙的差异
        self.local_phase = random.uniform(0, 2 * math.pi)
        self.flow_rate = random.uniform(0.005, 0.012)

        # 阶段 3+ 的"结构变化"参数
        self.is_structure = (layer_index >= 2)  # 第3次起为结构变化
        self.branch_intensity = 0.0  # 渐入

        # 阶段 4+ 的"共振"参数
        self.resonance_target = None  # 与之共振的早期记忆层

    def update(self, center_x: float, center_y: float, dt: float = 1.0 / 60.0):
        """
        更新记忆层状态

        Args:
            center_x, center_y: 生命体中心
            dt: 时间步长
        """
        self.center_x = center_x
        self.center_y = center_y
        self.local_phase += self.flow_rate
        # 缓慢生长（避免突然出现）
        self.growth += (self.target_growth - self.growth) * 0.006
        # 结构变化时分支强度也增长
        if self.is_structure:
            self.branch_intensity = min(1.0, self.growth)

    def get_curve_points(self) -> List[Tuple[float, float]]:
        """
        获取记忆层曲线点（用于绘制）

        不是封闭多边形，而是开放曲线。
        曲线从中心向 impact_angle 方向延伸，带波动。

        Returns:
            曲线点列表
        """
        points = []

        # 曲线长度 - 受 growth 和 intensity 影响
        base_length = 25 + self.intensity * 25
        length = base_length * self.growth

        num_points = 18

        # 基础方向 - 沿 impact_angle
        # 但根据 layer_index 产生分支（阶段 3+）
        if self.is_structure and self.branch_intensity > 0.1:
            # 结构变化：产生 2-3 条分支
            branch_angles = [
                -0.4, 0.0, 0.4
            ]
            for branch_offset in branch_angles:
                branch_angle = self.impact_angle + branch_offset
                for i in range(num_points):
                    t = i / (num_points - 1)
                    r = length * t
                    # 波动
                    wave = math.sin(t * 3.0 * math.pi + self.local_phase) * (4 + self.intensity * 4)
                    r += wave
                    x = self.center_x + math.cos(branch_angle) * r
                    y = self.center_y + math.sin(branch_angle) * r
                    points.append((x, y))
                # 分支之间留空隙
                points.append(None)  # 标记分段
            # 移除最后的 None
            if points and points[-1] is None:
                points.pop()
        else:
            # 普通纹理：单条曲线
            for i in range(num_points):
                t = i / (num_points - 1)
                r = length * t
                # 沿 impact_angle 方向的曲线
                wave = math.sin(t * 2.5 * math.pi + self.local_phase) * (5 + self.intensity * 5)
                angle = self.impact_angle + wave * 0.05
                x = self.center_x + math.cos(angle) * r
                y = self.center_y + math.sin(angle) * r
                points.append((x, y))

        return points

    def get_intensity(self) -> float:
        """
        获取记忆层当前强度

        Returns:
            强度（考虑 growth 和原始 intensity）
        """
        return self.intensity * self.growth

    def is_fully_grown(self) -> bool:
        """判断记忆层是否已完全生长"""
        return self.growth > 0.95



class MembraneDisturbance:
    """
    膜扰动系统

    表现生命膜受到外部碎片影响的动态反馈

    三个阶段：
    1. CONTACT（接触）：局部凹陷 + 涟漪（像水滴进入水面）
       - 接触点处产生深度凹陷
       - 凹陷有自然回弹（轻微过冲）
       - 同心圆涟漪从接触点向外扩散
       - 边界扰动（凹陷附近的膜顶点产生明显形变）

    2. ABSORBING（吸收中）：整体收缩 + 流动偏置
       - 膜整体轻微收缩（半径减小）
       - 内部纹理向碎片方向流动（flow_bias）
       - 凹陷持续但变浅

    3. COMPLETED（完成）：恢复平静
       - 收缩释放，膜恢复
       - 流动偏置衰减
       - 但内部结构已永久改变（由 PermanentTextureLayer / 新增 FlowTexture 表达）

    约束：
    - 不重新设计生命体
    - 只在原有 membrane 渲染基础上叠加扰动偏移
    - 不影响现有 color/membrane 状态机
    """

    def __init__(self, center_x: float, center_y: float):
        """
        初始化膜扰动系统

        Args:
            center_x, center_y: 生命体中心位置
        """
        self.center_x = center_x
        self.center_y = center_y

        # === 接触凹陷（CONTACT 阶段） ===
        # 每个凹陷有独立的生命周期：下沉 → 恢复（可有过冲）
        self.contact_indents: List[Dict] = []
        self.max_contact_indents = 5

        # === 涟漪（CONTACT 阶段） ===
        # 从接触点向外扩散的同心圆波
        self.ripples: List[Dict] = []
        self.max_ripples = 6

        # === 吸收收缩（ABSORBING 阶段） ===
        # 膜整体轻微收缩（负值=向内收缩）
        self.absorption_contraction = 0.0  # 0-1
        self.absorption_contraction_target = 0.0  # 目标值

        # === 流动偏置（ABSORBING 阶段） ===
        # 内部纹理向此方向流动
        self.flow_bias_angle: Optional[float] = None
        self.flow_bias_intensity = 0.0  # 0-1
        self.flow_bias_target = 0.0

        # 内部时钟
        self.disturbance_time = 0.0

    def trigger_contact(self, angle: float, intensity: float = 0.5):
        """
        触发接触扰动

        在 CONTACT 阶段被调用：
        - 添加一个新的凹陷（局部深度下沉）
        - 生成 1-2 个涟漪（从接触点向外扩散）
        - 凹陷会有自然的回弹过程（不是瞬间消失）

        Args:
            angle: 接触点角度
            intensity: 扰动强度 (0.0 - 1.0)
        """
        # 凹陷参数
        max_depth = 6.0 + intensity * 6.0  # 6-12 像素
        max_age = 0.9 + intensity * 0.4  # 0.9-1.3 秒

        self.contact_indents.append({
            'angle': angle,
            'max_depth': max_depth,
            'current_depth': 0.0,  # 当前深度（动态变化）
            'radius': 0.35 + intensity * 0.1,  # 影响半径（角度范围）
            'age': 0.0,
            'max_age': max_age,
            'phase': random.uniform(0, math.pi),  # 涟漪相位
            'intensity': intensity,
        })

        # 限制凹陷数量
        if len(self.contact_indents) > self.max_contact_indents:
            self.contact_indents.pop(0)

        # 涟漪参数（向外扩散的同心波）
        num_ripples = 1 if intensity < 0.5 else 2
        for i in range(num_ripples):
            self.ripples.append({
                'angle': angle,
                'current_radius': 0.0,  # 当前扩散半径
                'spread_speed': 35.0 + intensity * 15.0,  # 扩散速度
                'intensity': intensity * (1.0 - i * 0.3),  # 第二圈涟漪稍弱
                'age': 0.0,
                'max_age': 1.4 + i * 0.3,
                'phase': self.disturbance_time * 5.0 + i * 1.5,
                'width': 0.25 + i * 0.1,  # 涟漪宽度（角度范围）
            })

        # 限制涟漪数量
        if len(self.ripples) > self.max_ripples:
            self.ripples.pop(0)

    def start_absorption(self, angle: float, intensity: float = 0.5):
        """
        启动吸收响应

        在 ABSORBING 阶段被调用：
        - 膜整体轻微收缩
        - 内部纹理向碎片方向流动
        - 不立即重置 contact 凹陷（让它自然衰减）

        Args:
            angle: 碎片相对生命体中心的角度
            intensity: 吸收强度 (0.0 - 1.0)
        """
        self.absorption_contraction_target = min(1.0, 0.4 + intensity * 0.5)
        self.flow_bias_angle = angle
        self.flow_bias_target = min(1.0, 0.5 + intensity * 0.4)

    def end_absorption(self):
        """
        结束吸收响应

        在 COMPLETED 阶段被调用：
        - 释放收缩
        - 释放流动偏置（但内部纹理已永久改变）
        - 凹陷和涟漪继续自然衰减
        """
        self.absorption_contraction_target = 0.0
        self.flow_bias_target = 0.0

    def update(self, dt: float = 1.0 / 60.0):
        """
        更新扰动系统

        Args:
            dt: 时间步长
        """
        self.disturbance_time += dt

        # === 更新接触凹陷的生命周期 ===
        # 凹陷轨迹：快速下沉 → 短暂稳定 → 回弹（轻微过冲）→ 恢复平静
        alive_indents = []
        for indent in self.contact_indents:
            indent['age'] += dt
            t = indent['age'] / indent['max_age']

            if t < 1.0:
                # 凹陷深度曲线：开始时快速下沉，0.3 达到最深，然后回弹（过冲），最后恢复
                if t < 0.15:
                    # 快速下沉阶段
                    depth_factor = t / 0.15
                elif t < 0.4:
                    # 短暂稳定在最深
                    depth_factor = 1.0
                elif t < 0.7:
                    # 回弹（轻微过冲 - 微微凸起）
                    rebound = (t - 0.4) / 0.3
                    depth_factor = 1.0 - rebound * 1.3  # 过冲到 -0.3
                else:
                    # 恢复平静
                    settle = (t - 0.7) / 0.3
                    depth_factor = -0.3 * (1.0 - settle)

                indent['current_depth'] = indent['max_depth'] * depth_factor
                alive_indents.append(indent)
            # else: 自然消亡

        self.contact_indents = alive_indents

        # === 更新涟漪的扩散和衰减 ===
        alive_ripples = []
        for ripple in self.ripples:
            ripple['age'] += dt
            ripple['current_radius'] += ripple['spread_speed'] * dt
            # 强度衰减
            ripple['intensity'] *= (1.0 - dt * 0.7)

            if ripple['age'] < ripple['max_age'] and ripple['intensity'] > 0.04:
                alive_ripples.append(ripple)
        self.ripples = alive_ripples

        # === 平滑过渡收缩和流动偏置 ===
        transition_speed = 0.05  # 缓慢过渡
        self.absorption_contraction += (
            (self.absorption_contraction_target - self.absorption_contraction) * transition_speed
        )
        self.flow_bias_intensity += (
            (self.flow_bias_target - self.flow_bias_intensity) * transition_speed
        )

        # 收缩到很小值时直接归零（避免长期微小残留）
        if self.absorption_contraction < 0.005:
            self.absorption_contraction = 0.0
        if self.flow_bias_intensity < 0.005:
            self.flow_bias_intensity = 0.0

    def get_membrane_offset(self, vertex_angle: float) -> float:
        """
        获取膜上某角度顶点因扰动产生的径向偏移

        Args:
            vertex_angle: 顶点角度

        Returns:
            径向偏移（负=向内凹陷，正=向外凸起）
        """
        offset = 0.0

        # === 凹陷偏移 ===
        for indent in self.contact_indents:
            angle_diff = abs(vertex_angle - indent['angle'])
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            if angle_diff < indent['radius']:
                # 高斯衰减：中心深，边缘浅
                gaussian = math.exp(-(angle_diff ** 2) * (8.0 / (indent['radius'] ** 2)))
                offset += indent['current_depth'] * gaussian

        # === 涟漪偏移（扩散的正弦波） ===
        for ripple in self.ripples:
            # 涟漪位置：在 current_radius 处
            # 但我们要在 vertex_angle 上找涟漪效应
            # 简化：把 current_radius 视为角度距离（已扩散的范围）
            angle_diff = abs(vertex_angle - ripple['angle'])
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # 涟漪的"环宽"
            if angle_diff < ripple['current_radius'] + ripple['width']:
                # 涟漪在扩散前沿最明显
                front = ripple['current_radius']
                # 该顶点到涟漪中心的角度距离
                dist = angle_diff
                # 涟漪在 front 处振幅最大
                # 简化：高斯包络 + 正弦波
                envelope = math.exp(-((dist - front) ** 2) * 30.0)
                wave = math.sin(ripple['age'] * 6.0 - front * 0.3 + ripple['phase'])
                ripple_effect = envelope * wave * ripple['intensity'] * 4.0
                offset += ripple_effect

        # === 整体收缩偏移（向内） ===
        if self.absorption_contraction > 0.01:
            # 收缩：所有顶点均匀向内
            offset -= self.absorption_contraction * 4.0

        return offset

    def get_flow_bias(self) -> Tuple[Optional[float], float]:
        """
        获取当前流动偏置

        Returns:
            (angle, intensity) - angle 可能为 None 当未激活
        """
        return (self.flow_bias_angle, self.flow_bias_intensity)

    def is_active(self) -> bool:
        """
        检查扰动系统是否处于活跃状态

        Returns:
            是否有任何活跃的扰动
        """
        return (len(self.contact_indents) > 0 or
                len(self.ripples) > 0 or
                self.absorption_contraction > 0.01 or
                self.flow_bias_intensity > 0.01)


# 删除InternalLight类，改用FlowTexture和PermanentTextureLayer


class OrganicMembrane:
    """
    有机外膜 - Multi-Layer Translucent Blob
    
    生命体的边界，由多个半透明blob叠加而成
    像水母/细胞，而不是硬轮廓
    
    特点：
    - 多层半透明blob叠加（不是单个polygon）
    - 强烈呼吸效果（整体扩张和收缩）
    - 每层blob独立波动
    - 局部扰动（被fragment接触时产生涟漪）
    - 半透明叠加产生柔和边缘
    """
    
    def __init__(self, center_x: float, center_y: float):
        """
        初始化有机外膜
        
        Args:
            center_x, center_y: 中心位置
        """
        self.center_x = center_x
        self.center_y = center_y
        
        # 基础半径
        self.base_radius = 60
        self.current_radius = self.base_radius
        
        # 呼吸效果（基础值）
        self.breathing_phase = 0
        self.base_breathing_speed = 0.012
        self.base_breathing_amplitude = 10
        self.breathing_speed = self.base_breathing_speed
        self.breathing_amplitude = self.base_breathing_amplitude
        
        # 影响累积（0.0-1.0，永久累积）
        self.impact_level = 0.0
        self.pulse_intensity = 0.0  # 影响瞬间的脉冲强度（会衰减）
        
        # 永久形状变化（来自影响位置）
        self.permanent_vertex_shifts: List[Tuple[float, float]] = []  # (angle, shift_amount)
        
        # 多层blob（3-4层叠加产生柔和效果）
        self.num_layers = 4
        self.layers = []
        
        for layer_idx in range(self.num_layers):
            layer = {
                'radius_offset': layer_idx * 4,  # 每层半径递增
                'phase_offset': layer_idx * 1.7,  # 每层相位不同
                'speed_offset': random.uniform(0.005, 0.015),  # 每层速度不同
                'alpha': 0.25 - layer_idx * 0.05,  # 外层更透明
                'num_vertices': 18 + layer_idx * 4,  # 每层顶点数量不同
                'vertex_angles': [],
                'vertex_base_distances': [],
                'vertex_current_distances': [],
            }
            
            # 初始化每层的顶点
            num_v = layer['num_vertices']
            for i in range(num_v):
                angle = (i / num_v) * 2 * math.pi
                layer['vertex_angles'].append(angle)
                
                # 基础偏移（创造不规则）
                base_offset = random.uniform(-12, 12)
                layer['vertex_base_distances'].append(base_offset)
                layer['vertex_current_distances'].append(base_offset)
            
            self.layers.append(layer)
        
        # 局部扰动（涟漪）
        self.perturbations: List[Dict] = []
        self.max_perturbations = 6
        self.perturbation_decay_rate = 0.88
        
        # 表面波动
        self.surface_wave_phase = 0
        self.surface_wave_speed = 0.018
        
        # 形态变化（被影响时）
        self.deformation_factor = 0.0
        self.deformation_target = 0.0

        # === 膜扰动系统（membrane_disturbance） ===
        # 表现生命体被碎片影响时的动态反馈
        # - 接触时：局部凹陷+涟漪
        # - 吸收时：整体收缩
        # - 完成后：恢复平静
        self.disturbance = MembraneDisturbance(center_x, center_y)
        
    def update(self, center_x: float, center_y: float, is_influenced: bool):
        """
        更新外膜状态
        
        Args:
            center_x, center_y: 中心位置
            is_influenced: 是否被影响
        """
        self.center_x = center_x
        self.center_y = center_y
        
        # 1. 呼吸效果 - 随impact_level增强（更慢更微妙）
        # 影响越大，呼吸越快、振幅越大
        self.breathing_speed = self.base_breathing_speed * (1.0 + self.impact_level * 0.8)
        self.breathing_amplitude = self.base_breathing_amplitude * (1.0 + self.impact_level * 0.4)
        
        # 影响瞬间的脉冲反馈（更柔和）
        pulse_amplitude = self.pulse_intensity * 5  # 脉冲时温和收缩/扩张
        pulse_phase = self.pulse_intensity * 0.5  # 脉冲相位偏移
        
        self.breathing_phase += self.breathing_speed
        breathing_offset = math.sin(self.breathing_phase + pulse_phase) * (self.breathing_amplitude + pulse_amplitude)
        self.current_radius = self.base_radius + breathing_offset
        
        # 脉冲强度衰减（更慢）
        self.pulse_intensity *= 0.96
        if self.pulse_intensity < 0.01:
            self.pulse_intensity = 0.0
        
        # 2. 表面波动
        self.surface_wave_phase += self.surface_wave_speed
        
        # 3. 更新每层blob的顶点
        for layer in self.layers:
            num_v = layer['num_vertices']
            layer_phase = self.surface_wave_phase + layer['phase_offset']
            
            for i in range(num_v):
                # 每个顶点独立波动
                target = layer['vertex_base_distances'][i] + math.sin(layer_phase + i * 0.4) * 6
                layer['vertex_current_distances'][i] += (target - layer['vertex_current_distances'][i]) * 0.06
        
        # 4. 更新扰动（涟漪衰减）
        for perturbation in self.perturbations:
            perturbation['intensity'] *= self.perturbation_decay_rate
            perturbation['radius'] += 0.5  # 涟漪扩散
        
        self.perturbations = [p for p in self.perturbations if p['intensity'] > 0.05]
        
        # 5. 被影响时的整体形态变化 - 随impact_level缓慢增强
        if is_influenced:
            self.deformation_target = 0.1 + self.impact_level * 0.15
        else:
            self.deformation_target = max(0.0, self.deformation_target - 0.005)
        
        self.deformation_factor += (self.deformation_target - self.deformation_factor) * 0.08

        # 6. 更新膜扰动系统（membrane_disturbance）
        self.disturbance.center_x = center_x
        self.disturbance.center_y = center_y
        self.disturbance.update()
    
    def receive_impact(self, value: float, impact_angle: float):
        """
        接收影响（累积影响系统）
        
        Args:
            value: 影响强度 (0.0 - 1.0)
            impact_angle: 影响方向（角度）
        """
        # 累积影响水平（永久）
        self.impact_level = min(1.0, self.impact_level + value * 0.2)
        
        # 影响瞬间产生脉冲
        self.pulse_intensity = min(1.0, self.pulse_intensity + value)
        
        # 在影响方向添加永久顶点位移
        shift_amount = 2 + value * 4  # 基础位移2-6像素（更微妙）
        self.permanent_vertex_shifts.append((impact_angle, shift_amount))
        
        # 限制永久位移数量，避免性能问题和数值爆炸
        if len(self.permanent_vertex_shifts) > 30:
            # 合并最早的位移
            self.permanent_vertex_shifts.pop(0)
        
    def add_perturbation(self, angle: float, intensity: float = 1.0):
        """
        在特定角度添加局部扰动（涟漪）
        
        Args:
            angle: 扰动角度
            intensity: 扰动强度
        """
        if len(self.perturbations) < self.max_perturbations:
            perturbation = {
                'angle': angle,
                'intensity': intensity,
                'radius': 0.0,  # 涟漪扩散半径
                'decay': self.perturbation_decay_rate
            }
            self.perturbations.append(perturbation)
    
    def get_layer_points(self, layer_idx: int) -> List[Tuple[float, float]]:
        """
        获取指定层的blob顶点
        
        Args:
            layer_idx: 层索引
            
        Returns:
            顶点坐标列表
        """
        layer = self.layers[layer_idx]
        points = []
        
        # 该层的基础半径
        layer_radius = self.current_radius + layer['radius_offset']
        
        for i in range(layer['num_vertices']):
            base_angle = layer['vertex_angles'][i]
            
            # 基础距离（呼吸 + 不规则偏移）
            base_distance = layer_radius + layer['vertex_current_distances'][i]
            
            # 表面波动
            wave_offset = math.sin(self.surface_wave_phase + layer['phase_offset'] + i * 0.4) * 3
            
            # 形态变化（整体变形）
            deformation_offset = math.sin(base_angle * 2) * self.deformation_factor * 6
            
            # 局部扰动（涟漪效果，扩散的圆形波）
            perturbation_offset = 0
            for perturbation in self.perturbations:
                # 计算角度差异
                angle_diff = abs(base_angle - perturbation['angle'])
                if angle_diff < math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                
                if angle_diff < 1.0:  # 涟漪影响范围
                    # 涟漪在扰动点扩散（正弦波效果）
                    ripple = math.sin(perturbation['radius'] * 0.3 - angle_diff * 3) * perturbation['intensity'] * 3
                    perturbation_offset += ripple
            
            # 永久顶点位移（来自历史影响）
            permanent_offset = 0
            for shift_angle, shift_amount in self.permanent_vertex_shifts:
                angle_diff = abs(base_angle - shift_angle)
                if angle_diff < math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                # 高斯衰减：影响点附近位移大，远处小
                if angle_diff < 1.5:
                    gaussian = math.exp(-(angle_diff ** 2) * 2.0)
                    permanent_offset += shift_amount * gaussian

            # === 膜扰动偏移（membrane_disturbance）===
            # 接触凹陷 + 涟漪扩散 + 整体收缩
            # 这是生命体对碎片影响的主动反馈，独立于永久影响
            disturbance_offset = self.disturbance.get_membrane_offset(base_angle)

            # 最终距离
            final_distance = (base_distance + wave_offset + deformation_offset
                              + perturbation_offset + permanent_offset
                              + disturbance_offset)
            
            # 计算顶点位置
            x = self.center_x + math.cos(base_angle) * final_distance
            y = self.center_y + math.sin(base_angle) * final_distance
            
            points.append((x, y))
        
        return points
    
    def get_color(self, layer_idx: int) -> Tuple[int, int, int, int]:
        """获取颜色（带透明度）- 使用TargetObject同步的当前显示颜色"""
        # 使用_current_display_color（由TargetObject.update缓慢插值得到）
        # 这是基于fragment_count的目标颜色，经过color_transition_speed的平滑过渡
        display_color = getattr(self, '_current_display_color', (160, 200, 230))
        
        r = display_color[0]
        g = display_color[1]
        b = display_color[2]
        
        # 加入脉冲效果（影响瞬间）- 微妙
        if self.pulse_intensity > 0:
            pulse = self.pulse_intensity
            r = min(255, r + pulse * 15)
            g = min(255, g + pulse * 10)
            b = min(255, b + pulse * 5)
        
        r = int(r)
        g = int(g)
        b = int(b)
        
        # 透明度（外层更透明）
        alpha = int(255 * self.layers[layer_idx]['alpha'])
        
        return (r, g, b, alpha)


class TargetObject:
    """
    目标对象类 - Organic Blob
    
    半透明、果冻般的有机生命体
    行为痕迹会渗透进入内部，改变其结构和形态
    
    视觉特征：
    - 不规则边界（动态变化）
    - 明显呼吸效果
    - 内部连续流动纹理（不是离散光点）
    - Fragment接触时局部扰动
    - 被影响后新增永久纹理层（留下永久变化）
    """
    
    def __init__(self, x: float = 640, y: float = 360):
        """
        初始化目标对象
        
        Args:
            x, y: 初始位置（默认屏幕中心）
        """
        # 位置
        self.x = x
        self.y = y
        
        # 有机外膜
        self.membrane = OrganicMembrane(x, y)
        
        # 内部流动纹理（5-8条连续纹理曲线）
        # 注意：这些是生命体本身的"基础纹理"，不随碎片吸收而增加
        # 吸收效果通过 memory_layers 表达
        self.num_flow_textures = random.randint(5, 8)
        self.flow_textures: List[FlowTexture] = []

        for i in range(self.num_flow_textures):
            texture = FlowTexture(x, y, i)
            self.flow_textures.append(texture)

        # === 长期影响系统：碎片消失后留下的是生命体的改变 ===
        # 不再使用 permanent_texture_layers（会产生黄色多边形残影）
        # 改为 memory_layers 表达内部纹理改变
        self.memory_layers: List[MemoryLayer] = []
        self.max_memory_layers = 6  # 最多6层记忆（避免无限堆叠）

        # 结构变化计数（第3次吸收起开始累积）
        self.structure_changes = 0  # 内部结构改变次数
        # 内部痕迹计数（每层记忆贡献的痕迹数）
        self.internal_traces = 0  # 当前活跃的内部痕迹数量

        # 永久纹理层（旧系统，保留字段以防外部引用，但不绘制）
        # 新设计不再使用此列表 - 仅保留用于兼容性
        self.permanent_texture_layers: List[PermanentTextureLayer] = []
        
        # 状态
        self.age = 0
        self.cumulative_influence = 0.0
        self.impact_level = 0.0  # 0.0-1.0 累积影响水平（用于视觉反馈）
        self.absorbed_count = 0  # 实际进入生命体的碎片数量（用于颜色分阶段）
        self.fragment_count = 0  # 累计吸收的碎片数量（核心颜色变化依据，不衰减）

        # === 记忆等级系统 ===
        # 根据累计吸收的碎片数量计算生命状态等级（5级：0-4）
        # 当前等级（不修改任何绘制/颜色效果，仅作为状态标签）
        self.memory_level = 0
        # 上一次记录的等级（用于检测等级变化并输出日志）
        self._last_logged_level = 0

        # === 记忆等级颜色系统 ===
        # 5个等级的核心颜色锚点（用于生命体主色 / 外膜）
        # 设计：每级之间有清晰可辨的色调过渡，让"经历"成为可读的故事
        # L0: 冷蓝 → L1: 薄荷绿 → L2: 青绿 → L3: 琥珀 → L4: 暖橙
        # 注意：L1/L2 故意与 L0 拉开差距，避免"看不出中间状态"
        self._memory_level_core_stops = [
            (160, 200, 230),  # Level 0: 冷蓝（原始）
            (130, 220, 195),  # Level 1: 薄荷绿（明显比 L0 绿）
            (170, 215, 170),  # Level 2: 青绿（明显的青绿）
            (200, 185, 160),  # Level 3: 琥珀
            (215, 170, 135),  # Level 4: 暖橙
        ]
        # 5个等级的内部纹理颜色锚点（内部纹理线条，更鲜明一些）
        self._memory_level_texture_stops = [
            (200, 220, 240),  # Level 0: 冷蓝
            (160, 235, 195),  # Level 1: 鲜明薄荷绿
            (195, 230, 165),  # Level 2: 黄绿
            (225, 195, 140),  # Level 3: 琥珀
            (240, 175, 115),  # Level 4: 暖橙
        ]
        # 当前实际显示的核心/纹理颜色（每帧缓慢插值）
        self._current_core_color = [160.0, 200.0, 230.0]
        self._current_texture_color = [200.0, 220.0, 240.0]
        # 等级颜色过渡速度（比主颜色更慢，避免"升级感"）
        # 0.002 ≈ 30秒才接近目标（让每级有足够时间沉淀）
        # 之前 0.005 时用户感觉"颜色追着等级跑"，现在大幅放慢
        self._memory_color_speed = 0.002

        # === 内部纹理"脉络"颜色系统 ===
        # 在基础纹理曲线之上叠加暖色脉络（记忆融入视觉）
        # 设计：脉络色与基底纹理同色系渐进变化
        # L0：冷蓝（与基底一致）
        # L1：浅暖绿（与 L1 薄荷绿基底呼应）
        # L2：暖绿（连接绿与琥珀）
        # L3：琥珀色
        # L4：稳定暖橙
        self._memory_level_vein_stops = [
            (185, 210, 225),  # Level 0: 冷蓝（与基底冷色一致，不可见）
            (170, 230, 190),  # Level 1: 浅暖绿（呼应 L1 薄荷绿）
            (215, 220, 170),  # Level 2: 暖绿（连接绿与琥珀）
            (230, 180, 135),  # Level 3: 琥珀
            (240, 165, 100),  # Level 4: 稳定暖橙
        ]
        self._current_vein_color = [185.0, 210.0, 225.0]
        # 脉络强度（控制覆盖比例 + 不透明度）
        # L0=0, L1=0.15 (极弱), L2=0.40 (显形), L3=0.65 (建立), L4=0.85 (主导)
        # 调低 L1 强度以避免"第一次吸收就明显跳变"
        self._memory_level_vein_strength = [0.0, 0.15, 0.40, 0.65, 0.85]
        
        # 当前实际显示颜色（用于平滑过渡）
        # 初始冷蓝色 (160, 200, 230)
        self.current_color = [160, 200, 230]
        # 颜色过渡速度（每帧插值比例）
        # 0.005 时约200帧(3.3秒)接近目标；0.01 时约100帧(1.7秒)
        self.color_transition_speed = 0.008  # 缓慢过渡，让每个阶段停留明显
        
        # 颜色变化进度（0.0-1.0）
        # 由fragment_count经过分段映射得到
        self.color_progress = 0.0
        self.max_fragments_for_color = 40  # 达到40个碎片时color_progress=1.0（接近金色）
        
        # 影响历史
        self.influence_history: List[Dict] = []
        
        # 当前是否被影响
        self.is_currently_influenced = False
        
        # Fragment接触位置（用于局部扰动）
        self.fragment_contact_positions: List[Tuple[float, float]] = []

        # === 主动吸收响应状态 ===
        # 用于追踪当前是否有碎片正在被吸收
        # - absorbing_fragments: 正在吸收中的碎片（key=id, value={'angle', 'intensity', 'progress'}）
        # - last_contact_time: 上次接触时间（避免重复触发）
        self.absorbing_fragments: Dict[int, Dict] = {}
        self.last_contact_trigger_time = 0.0

    def on_fragment_contact(self, fragment_id: int, angle: float, intensity: float):
        """
        Fragment 进入 CONTACT 状态 - 触发膜接触扰动

        调用时机：碎片首次接触生命膜的瞬间
        效果：
        - 局部凹陷（接触点）
        - 涟漪从接触点向外扩散
        - 类似水滴进入水面

        Args:
            fragment_id: 碎片唯一标识
            angle: 接触角度（相对生命体中心）
            intensity: 扰动强度 (0.0 - 1.0)
        """
        self.membrane.disturbance.trigger_contact(angle, intensity)
        self.last_contact_trigger_time = self.age

    def on_absorption_start(self, fragment_id: int, angle: float, intensity: float):
        """
        Fragment 进入 ABSORBING 状态 - 启动吸收响应

        调用时机：碎片开始被吸收的瞬间
        效果：
        - 膜整体轻微收缩
        - 内部纹理向碎片方向流动（flow_bias）
        - 凹陷持续但变浅

        Args:
            fragment_id: 碎片唯一标识
            angle: 碎片相对生命体中心的角度
            intensity: 吸收强度 (0.0 - 1.0)
        """
        self.absorbing_fragments[fragment_id] = {
            'angle': angle,
            'intensity': intensity,
            'progress': 0.0,
        }
        self.membrane.disturbance.start_absorption(angle, intensity)

    def on_absorption_progress(self, fragment_id: int, progress: float):
        """
        Fragment 吸收进度更新

        调用时机：吸收过程中每帧调用
        用于更新内部流动偏置的强度（随进度变化）

        Args:
            fragment_id: 碎片唯一标识
            progress: 当前吸收进度 (0.0 - 1.0)
        """
        if fragment_id in self.absorbing_fragments:
            self.absorbing_fragments[fragment_id]['progress'] = progress

    def on_absorption_complete(self, fragment_id: int):
        """
        Fragment 吸收完成 - 结束吸收响应

        调用时机：碎片完全融入生命体
        效果：
        - 释放收缩（膜恢复）
        - 释放流动偏置（但内部纹理已永久改变）
        - 凹陷和涟漪继续自然衰减

        Args:
            fragment_id: 碎片唯一标识
        """
        if fragment_id in self.absorbing_fragments:
            del self.absorbing_fragments[fragment_id]

        # 当所有吸收完成时，释放扰动
        if not self.absorbing_fragments:
            self.membrane.disturbance.end_absorption()

    def receive_impact(self, value: float,
                      source_position: Dict = None,
                      impact_type: str = 'memory'):
        """
        接受行为影响

        被影响后新增永久纹理层，留下永久结构变化

        Args:
            value: 影响强度 (0.0 - 1.0)
            source_position: 来源位置
            impact_type: 影响类型
        """
        # 记录影响历史
        impact_record = {
            'time': self.age,
            'value': value,
            'source': source_position.copy() if source_position else None
        }
        self.influence_history.append(impact_record)
        
        # 更新累积影响
        self.cumulative_influence = min(1.0, self.cumulative_influence + value * 0.1)
        
        # 累积影响水平（用于视觉反馈，永久）
        self.impact_level = min(1.0, self.impact_level + value * 0.05)
        
        # 实际进入的碎片数量+1（用于颜色分阶段判定）
        self.absorbed_count += 1
        # 累计吸收的碎片数量（核心颜色变化依据，不衰减）
        self.fragment_count += 1

        # === 更新记忆等级（不修改任何绘制/颜色效果）===
        new_level = self.calculate_memory_level()
        leveled_up = new_level != self.memory_level
        self.memory_level = new_level

        # 计算当前color_progress（基于fragment_count，但更平滑的分段）
        new_progress = self._calculate_color_progress(self.fragment_count)

        # 计算目标颜色（基于color_progress在5个关键色之间插值）
        target_color = self._calculate_target_color_from_progress(new_progress)

        # 调试输出：每次碎片进入时打印
        print(f"Fragment absorbed: count = {self.fragment_count}")
        print(f"  color_progress = {new_progress:.3f}")
        print(f"  target_color   = {tuple(int(c) for c in target_color)}")
        print(f"  current_color  = {tuple(int(c) for c in self.current_color)}")
        # 记忆等级日志：仅在等级变化时输出，便于测试
        if leveled_up:
            print(f"  >>> memory_level UP: {self._last_logged_level} -> {self.memory_level}  "
                  f"(fragment_count = {self.fragment_count})")
            self._last_logged_level = self.memory_level
        
        # 标记为被影响状态
        self.is_currently_influenced = True
        
        # 如果有来源位置，添加记忆层和内部变化
        if source_position:
            fragment_x = source_position.get('x', self.x)
            fragment_y = source_position.get('y', self.y)

            # 计算fragment相对于生命体中心的角度
            dx = fragment_x - self.x
            dy = fragment_y - self.y
            angle = math.atan2(dy, dx)

            # 在接触点添加扰动（强度与影响值相关）
            self.membrane.add_perturbation(angle, intensity=value)

            # 调用膜的receive_impact（影响脉冲、永久形状变化）
            self.membrane.receive_impact(value, angle)

            # === 长期影响：新增 memory_layer（不是残影多边形）===
            # 第1次吸收：新增一条内部纹理
            # 第2次吸收：与已有纹理交叉，改写方向
            # 第3次+：形成结构变化
            # 第4次+：与最早记忆层共振
            self._absorb_into_memory(angle, value)

            # 改变原有基础纹理的方向（让内部纹理向影响方向微微偏转）
            # 偏转量较小，不会破坏生命体本身的设计
            for texture in self.flow_textures:
                # 计算从纹理到影响方向的角度差
                angle_diff = angle - texture.base_angle
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                # 累积影响越大，偏转越明显
                rotate_amount = angle_diff * 0.04 * (0.5 + value * 0.5)
                texture.base_angle += rotate_amount
                # 限制最大速度
                texture.flow_speed = min(0.15, texture.flow_speed * (1.0 + value * 0.04))

            # 记录接触位置
            self.fragment_contact_positions.append((fragment_x, fragment_y))
            if len(self.fragment_contact_positions) > 3:
                self.fragment_contact_positions.pop(0)

        # 增强流动纹理的强度（被影响时）
        num_to_influence = max(1, int(value * 3))
        textures_to_influence = random.sample(self.flow_textures,
                                             min(num_to_influence, len(self.flow_textures)))

        for texture in textures_to_influence:
            texture.is_influenced = True

        print(f"生命体受到记忆渗透: 强度={value:.2f}, 记忆层数={len(self.memory_layers)}, "
              f"结构变化={self.structure_changes}, 内部痕迹={self.internal_traces}, "
              f"累积={self.cumulative_influence:.2f}")

    def _absorb_into_memory(self, angle: float, intensity: float):
        """
        吸收转化为记忆层（核心：碎片消失，生命体已不同）

        阶段表现：
        - 1st: 新增一条新纹理
        - 2nd: 与已有纹理交叉，改写方向
        - 3rd+: 形成新的内部结构（分支、亮度提升）
        - 4th+: 与最早记忆层共振

        Args:
            angle: 吸收方向
            intensity: 吸收强度
        """
        if len(self.memory_layers) < self.max_memory_layers:
            # 添加新的记忆层
            layer_index = len(self.memory_layers)
            new_layer = MemoryLayer(self.x, self.y, angle, intensity, layer_index)
            self.memory_layers.append(new_layer)
            self.internal_traces += 1
            # 第3次吸收起记录结构变化
            if layer_index >= 2:
                self.structure_changes += 1
        else:
            # 已达到最大层数 → 与最早记忆层共振
            oldest = self.memory_layers[0]
            # 强化最早的纹理：让它的方向向新方向偏转
            angle_diff = angle - oldest.impact_angle
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            # 偏转最早记忆层的方向（累积共振）
            oldest.impact_angle += angle_diff * 0.3
            # 增强最早记忆层的强度
            oldest.intensity = min(1.0, oldest.intensity + intensity * 0.15)
            self.structure_changes += 1
    
    def calculate_memory_level(self) -> int:
        """
        根据当前 fragment_count 计算记忆等级 (0 - 4)

        等级映射（已大幅扩展阈值，让每级停留足够久）：
        - Level 0: 0 个碎片                （原始状态）
        - Level 1: 1-8 个碎片              （首次注入绿色）
        - Level 2: 9-25 个碎片             （青绿 + 暖色融合）
        - Level 3: 26-55 个碎片            （琥珀色已建立）
        - Level 4: 56 个及以上              （稳定暖橙）

        设计原因：让每级有"沉淀时间"，颜色能稳定显示一段时间后再过渡到下一级。
        配合 _memory_color_speed = 0.002（约30s达到90%目标），
        即使持续吸收碎片，颜色也不会"追着等级跑"。

        注意：
        - 该函数只计算等级，不修改任何绘制/颜色效果
        - 不修改 fragment 动画
        - 保留现有吞噬逻辑
        - 通过 self.memory_level 暴露当前等级，供后续逻辑使用

        Returns:
            等级值 (0-4)
        """
        count = self.fragment_count

        if count <= 0:
            return 0
        elif count <= 8:
            return 1
        elif count <= 25:
            return 2
        elif count <= 55:
            return 3
        else:
            return 4

    def calculate_memory_level_colors(self, level: int) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        根据记忆等级计算核心色 + 内部纹理色（在相邻等级之间 smoothstep 插值）

        即使 level 是整数，相邻等级之间也做插值（保持函数对将来小数值兼容），
        当前整数 level 下输出 = stops[level]

        设计原则：
        - 保留生命体冷色基调
        - 不直接切换颜色（通过 _current_core_color / _current_texture_color 缓慢插值）
        - 核心色变化小（外膜感受），纹理色变化大（内部明显）
        - 不出现纯黄色（保持有机感）

        Args:
            level: 记忆等级（0-4；超出范围自动 clamp）

        Returns:
            (core_rgb, texture_rgb) - 两组 RGB 浮点元组
        """
        lv = max(0.0, min(4.0, float(level)))
        lower = int(math.floor(lv))
        upper = min(4, lower + 1)
        frac = lv - lower

        # smoothstep 缓动 - 等级过渡更自然
        smooth = frac * frac * (3.0 - 2.0 * frac)

        # 核心色插值
        c_a = self._memory_level_core_stops[lower]
        c_b = self._memory_level_core_stops[upper]
        core = (
            c_a[0] + (c_b[0] - c_a[0]) * smooth,
            c_a[1] + (c_b[1] - c_a[1]) * smooth,
            c_a[2] + (c_b[2] - c_a[2]) * smooth,
        )

        # 内部纹理色插值
        t_a = self._memory_level_texture_stops[lower]
        t_b = self._memory_level_texture_stops[upper]
        texture = (
            t_a[0] + (t_b[0] - t_a[0]) * smooth,
            t_a[1] + (t_b[1] - t_a[1]) * smooth,
            t_a[2] + (t_b[2] - t_a[2]) * smooth,
        )

        return core, texture

    def calculate_memory_level_vein_color(self, level: int) -> Tuple[float, float, float]:
        """
        根据记忆等级计算内部纹理"脉络"颜色（暖琥珀色）

        脉络色与核心/纹理色不同：它是"经历融入"的高亮色，
        即使在 L4 暖橙基底上，脉络色也会更饱和的橙色，
        强化"新结构"视觉。

        Returns:
            脉络 RGB 浮点元组
        """
        lv = max(0.0, min(4.0, float(level)))
        lower = int(math.floor(lv))
        upper = min(4, lower + 1)
        frac = lv - lower
        smooth = frac * frac * (3.0 - 2.0 * frac)

        v_a = self._memory_level_vein_stops[lower]
        v_b = self._memory_level_vein_stops[upper]
        return (
            v_a[0] + (v_b[0] - v_a[0]) * smooth,
            v_a[1] + (v_b[1] - v_a[1]) * smooth,
            v_a[2] + (v_b[2] - v_a[2]) * smooth,
        )

    def get_memory_level_vein_strength(self, level: int) -> float:
        """
        根据记忆等级获取脉络强度 (0.0 - 0.90)

        L0=0, L1=0.25, L2=0.45, L3=0.70, L4=0.90
        离散等级直接读取；外部若传入小数值可被 smoothstep 平滑
        """
        lv = max(0, min(4, int(level)))
        return self._memory_level_vein_strength[lv]

    def _calculate_color_progress(self, fragment_count: int) -> float:
        """
        根据累计碎片数量计算颜色变化进度 (0.0 - 1.0)
        
        分段映射让每个阶段都有明显的颜色停留：
        - 0个碎片:   0.0   (蓝色起点)
        - 1-5个:     0.0-0.20 (蓝色→蓝紫色)
        - 6-15个:    0.20-0.45 (蓝紫→紫色)
        - 16-30个:   0.45-0.80 (紫色→紫金色)
        - 30+个:     0.80-1.0 (紫金→金色)
        
        Returns:
            color_progress (0.0 - 1.0)
        """
        max_n = self.max_fragments_for_color
        
        # 分段阈值
        if fragment_count <= 0:
            return 0.0
        elif fragment_count <= 5:
            # 0-5: 0.0-0.20
            return 0.20 * (fragment_count / 5.0)
        elif fragment_count <= 15:
            # 6-15: 0.20-0.45
            return 0.20 + 0.25 * ((fragment_count - 5) / 10.0)
        elif fragment_count <= 30:
            # 16-30: 0.45-0.80
            return 0.45 + 0.35 * ((fragment_count - 15) / 15.0)
        else:
            # 30+: 0.80-1.0
            progress = 0.80 + 0.20 * min(1.0, (fragment_count - 30) / (max_n - 30))
            return min(1.0, progress)
    
    def _calculate_target_color_from_progress(self, progress: float) -> Tuple[float, float, float]:
        """
        根据color_progress (0.0-1.0) 在5个关键颜色之间连续插值
        
        5个关键颜色锚点：
        - 0.0:  蓝色      (160, 200, 230)
        - 0.25: 蓝紫色    (175, 180, 225)
        - 0.50: 紫色      (200, 165, 200)
        - 0.75: 紫金色    (225, 175, 165)
        - 1.00: 金色      (240, 185, 130)
        
        Returns:
            (R, G, B) 目标颜色（0-255）
        """
        # 5个关键颜色锚点
        color_stops = [
            (0.00, (160, 200, 230)),  # 蓝色
            (0.25, (175, 180, 225)),  # 蓝紫色
            (0.50, (200, 165, 200)),  # 紫色
            (0.75, (225, 175, 165)),  # 紫金色
            (1.00, (240, 185, 130)),  # 金色
        ]
        
        p = max(0.0, min(1.0, progress))
        
        # 找到所在的颜色区间
        for i in range(len(color_stops) - 1):
            p_start, c_start = color_stops[i]
            p_end, c_end = color_stops[i + 1]
            
            if p_start <= p <= p_end:
                # 在区间内插值
                if p_end == p_start:
                    return c_start
                seg_progress = (p - p_start) / (p_end - p_start)
                # smoothstep 缓动让过渡更自然
                smooth = seg_progress * seg_progress * (3 - 2 * seg_progress)
                
                r = c_start[0] + (c_end[0] - c_start[0]) * smooth
                g = c_start[1] + (c_end[1] - c_start[1]) * smooth
                b = c_start[2] + (c_end[2] - c_start[2]) * smooth
                return (r, g, b)
        
        return color_stops[-1][1]
    
    def update(self):
        """更新生命体状态"""
        self.age += 1

        # 同步impact_level和absorbed_count到membrane
        self.membrane.impact_level = self.impact_level
        self.membrane._target_absorbed_count = self.absorbed_count

        # 同步fragment_count到membrane
        self.membrane._target_fragment_count = self.fragment_count

        # === 记忆等级颜色（替换原 fragment_count-based 颜色系统）===
        # 根据 memory_level 计算核心/纹理目标颜色
        core_target, tex_target = self.calculate_memory_level_colors(self.memory_level)
        # 脉络目标颜色
        vein_target = self.calculate_memory_level_vein_color(self.memory_level)

        # 缓慢插值（避免直接切换，每帧仅移动约 0.5% 差距）
        for i in range(3):
            self._current_core_color[i] += (core_target[i] - self._current_core_color[i]) * self._memory_color_speed
            self._current_texture_color[i] += (tex_target[i] - self._current_texture_color[i]) * self._memory_color_speed
            self._current_vein_color[i] += (vein_target[i] - self._current_vein_color[i]) * self._memory_color_speed

        # 同步到 current_color（保持向后兼容：membrane 仍通过 _current_display_color 读取）
        for i in range(3):
            self.current_color[i] = int(self._current_core_color[i])

        # 4. 同步当前颜色到membrane（实际显示颜色）
        self.membrane._current_display_color = tuple(self.current_color)

        # 更新外膜
        self.membrane.update(self.x, self.y, self.is_currently_influenced)

        # === 流动偏置（membrane_disturbance） ===
        # 吸收阶段让内部纹理向碎片方向流动
        flow_bias_angle, flow_bias_intensity = self.membrane.disturbance.get_flow_bias()

        # 更新流动纹理
        for texture in self.flow_textures:
            texture.update(
                self.x, self.y,
                self.is_currently_influenced,
                flow_bias_angle=flow_bias_angle,
                flow_bias_intensity=flow_bias_intensity,
            )

        # 更新永久纹理层（兼容旧字段，不再创建新对象）
        # for layer in self.permanent_texture_layers:
        #     layer.update(self.x, self.y)

        # 更新记忆层（长期影响 - 碎片消失后的内部改变）
        for layer in self.memory_layers:
            layer.update(self.x, self.y)

        # 检查是否所有纹理都恢复平静
        all_calm = all(texture.influence_intensity < 0.05 for texture in self.flow_textures)
        if all_calm and self.membrane.deformation_factor < 0.05:
            self.is_currently_influenced = False
    
    def draw(self, screen: pygame.Surface):
        """
        绘制生命体（多层叠加）

        1. 基础内部流动纹理（生命体本身的纹理）
        2. 记忆层（吸收后的内部改变 - 内部纹理的一部分）
        3. 多层半透明有机膜（最外层）

        长期影响通过 memory_layers 表达，融入基础纹理系统
        不是独立的残影/多边形层

        Args:
            screen: Pygame屏幕表面
        """
        # 1. 绘制基础内部流动纹理（最底层）
        self._draw_flow_textures(screen)

        # 2. 绘制记忆层（吸收后的永久改变 - 融入内部纹理）
        self._draw_memory_layers(screen)

        # 3. 绘制多层半透明有机膜（最外层）
        self._draw_membrane_layers(screen)

    def _draw_memory_layers(self, screen: pygame.Surface):
        """
        绘制记忆层（吸收后的内部改变）

        不是残影多边形，而是融入生命体内部的新纹理结构。
        阶段表现：
        - 1-2层：单条曲线（内部新纹理）
        - 3+层：多分支（结构变化）
        - 亮度随 impact_level 提升
        """
        if not self.memory_layers:
            return

        # 内部颜色 - 与基础纹理色系一致（由 memory_level 缓慢插值）
        r = int(self._current_texture_color[0])
        g = int(self._current_texture_color[1])
        b = int(self._current_texture_color[2])

        for layer in self.memory_layers:
            if layer.growth < 0.05:
                continue  # 还未生长完成

            intensity = layer.get_intensity()
            if intensity < 0.05:
                continue

            # 透明度由 growth 和 intensity 共同决定
            # 结构变化层（layer_index >= 2）有更高的基础透明度
            base_alpha = 70 if not layer.is_structure else 90
            alpha = int(base_alpha * intensity)
            color = (r, g, b, alpha)

            # 获取曲线点（带 None 分隔的多段）
            raw_points = layer.get_curve_points()

            # 按 None 分段绘制
            current_segment: List[Tuple[float, float]] = []
            for pt in raw_points:
                if pt is None:
                    # 分段结束 - 绘制当前段
                    self._draw_curve_segment(screen, current_segment, color, layer)
                    current_segment = []
                else:
                    current_segment.append(pt)
            # 绘制最后一段
            if current_segment:
                self._draw_curve_segment(screen, current_segment, color, layer)

    def _draw_curve_segment(self, screen, points, color, layer):
        """
        绘制一段曲线（记忆层的一段）

        使用 pygame.draw.lines 但通过独立 Surface 渲染以支持 alpha
        """
        if len(points) < 2:
            return

        # 计算边界框
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        width = int(max_x - min_x) + 10
        height = int(max_y - min_y) + 10

        if width <= 0 or height <= 0:
            return

        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        adjusted_points = [(p[0] - min_x + 5, p[1] - min_y + 5) for p in points]

        # 结构变化层使用更粗的线
        line_width = 2 if not layer.is_structure else 3
        pygame.draw.lines(surf, color, False, adjusted_points, line_width)

        screen.blit(surf, (min_x - 5, min_y - 5))
    
    def _draw_membrane_layers(self, screen: pygame.Surface):
        """
        绘制多层半透明有机膜
        
        多层blob叠加产生柔和、有机的边缘
        避免硬轮廓，看起来像水母/细胞
        """
        # 从外到内绘制（外层先画）
        for layer_idx in range(self.membrane.num_layers - 1, -1, -1):
            points = self.membrane.get_layer_points(layer_idx)
            
            if len(points) < 3:
                continue
            
            color = self.membrane.get_color(layer_idx)
            
            # 计算边界框
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)
            
            width = int(max_x - min_x) + 20
            height = int(max_y - min_y) + 20
            
            if width <= 0 or height <= 0:
                continue
            
            # 创建临时表面
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            
            # 调整点坐标
            adjusted_points = [(p[0] - min_x + 10, p[1] - min_y + 10) for p in points]
            
            # 绘制填充的多边形
            pygame.draw.polygon(surf, color, adjusted_points)
            
            # 绘制到屏幕
            screen.blit(surf, (min_x - 10, min_y - 10))
    
    def _draw_flow_textures(self, screen: pygame.Surface):
        """
        绘制内部流动纹理

        连续的曲线纹理，不是离散光点
        基础颜色由 memory_level 缓慢插值得到（保留原有冷色基调）
        在 L1+ 叠加琥珀色"脉络"高亮，模拟"经历融入"生命体

        Args:
            screen: Pygame屏幕表面
        """
        # === 基础纹理颜色：由 memory_level 缓慢插值得到（替换原 impact_level 计算）===
        r = int(self._current_texture_color[0])
        g = int(self._current_texture_color[1])
        b = int(self._current_texture_color[2])

        # === 脉络颜色 + 强度（仅 L1+ 显示）===
        vein_r = int(self._current_vein_color[0])
        vein_g = int(self._current_vein_color[1])
        vein_b = int(self._current_vein_color[2])
        vein_strength = self.get_memory_level_vein_strength(self.memory_level)

        for texture in self.flow_textures:
            points = texture.get_points()

            if len(points) < 2:
                continue

            # 纹理强度
            intensity = texture.get_intensity()
            if intensity <= 0.05:
                continue

            # 计算边界框
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            width = int(max_x - min_x) + 10
            height = int(max_y - min_y) + 10

            if width <= 0 or height <= 0:
                continue

            texture_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            adjusted_points = [(p[0] - min_x + 5, p[1] - min_y + 5) for p in points]

            # 1) 基础纹理曲线（始终完整绘制，不被覆盖）
            base_alpha = int(80 * intensity)
            base_color = (r, g, b, base_alpha)
            pygame.draw.lines(texture_surf, base_color, False, adjusted_points, 2)

            # 2) 脉络高亮（L1+ 出现） - 在原曲线之上叠加琥珀色片段
            #    脉络位置缓慢漂移，覆盖比例随 memory_level 增加
            #    2nd vein 仅 L3+ 出现，模拟"新结构"形成
            if vein_strength > 0.02:
                # 漂移脉络位置（每次绘制都移动一点点）
                texture.vein_phase_a = (texture.vein_phase_a + texture.vein_drift_speed) % 1.0
                texture.vein_phase_b = (texture.vein_phase_b + texture.vein_drift_speed * 0.73) % 1.0

                n = len(adjusted_points)
                # 防御性 clamp（边界情况下保护 pygame.draw）
                intensity = max(0.0, min(1.0, intensity))
                # 脉络覆盖比例：0.20 (L1) → 0.45 (L4)
                vein_width_pts = max(2, min(n - 1, int((0.20 + 0.25 * vein_strength) * n)))
                # 脉络不透明度：80 (L1) → 160 (L4)；clamp 到 [0, 255]
                vein_alpha = max(0, min(255, int((90 + 90 * vein_strength) * intensity)))

                # 1st vein
                start_a = int(texture.vein_phase_a * n) - vein_width_pts // 2
                start_a = max(0, start_a)
                end_a = min(n, start_a + vein_width_pts)
                if end_a - start_a >= 2:
                    vein_color_a = (vein_r, vein_g, vein_b, vein_alpha)
                    pygame.draw.lines(texture_surf, vein_color_a, False,
                                      adjusted_points[start_a:end_a], 2)

                # 2nd vein（L3+ 新结构出现）
                if self.memory_level >= 3:
                    start_b = int(texture.vein_phase_b * n) - vein_width_pts // 2
                    start_b = max(0, start_b)
                    end_b = min(n, start_b + vein_width_pts)
                    # 避免两条脉络完全重叠
                    if end_b - start_b >= 2 and abs(start_b - start_a) > vein_width_pts // 2:
                        vein_color_b = (vein_r, vein_g, vein_b, int(vein_alpha * 0.85))
                        pygame.draw.lines(texture_surf, vein_color_b, False,
                                          adjusted_points[start_b:end_b], 2)

            # 绘制到屏幕
            screen.blit(texture_surf, (min_x - 5, min_y - 5))
    
    def get_position(self) -> Tuple[float, float]:
        """获取生命体位置"""
        return (self.x, self.y)
    
    def get_cumulative_influence(self) -> float:
        """获取累积影响值"""
        return self.cumulative_influence
    
    def get_history_length(self) -> int:
        """获取影响历史长度"""
        return len(self.influence_history)
    
    def reset_position(self):
        """重置位置和状态"""
        self.x = 640
        self.y = 360
        self.membrane = OrganicMembrane(self.x, self.y)
        
        # 重置流动纹理
        self.flow_textures.clear()
        for i in range(self.num_flow_textures):
            texture = FlowTexture(self.x, self.y, i)
            self.flow_textures.append(texture)

        # 清空记忆层（长期影响重置）
        self.memory_layers.clear()
        self.structure_changes = 0
        self.internal_traces = 0

        # 清空永久纹理层（旧系统，保留兼容）
        self.permanent_texture_layers.clear()

        self.cumulative_influence = 0.0
        self.impact_level = 0.0
        self.absorbed_count = 0
        self.fragment_count = 0
        # 重置记忆等级
        self.memory_level = 0
        self._last_logged_level = 0
        # 重置记忆等级颜色（回到 Level 0 冷色起点）
        self._current_core_color = [160.0, 200.0, 230.0]
        self._current_texture_color = [200.0, 220.0, 240.0]
        self._current_vein_color = [185.0, 210.0, 225.0]
        self.is_currently_influenced = False


# 测试代码（如果直接运行此文件）
if __name__ == "__main__":
    import sys
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("有机生命体测试 - 连续流动纹理")
    clock = pygame.time.Clock()
    
    # 创建生命体
    target = TargetObject(640, 360)
    
    print("测试有机生命体（连续流动纹理版本）")
    print("按ESC退出，按空格键模拟影响")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # 模拟影响
                    impact_pos = {'x': target.x + random.randint(-50, 50), 
                                  'y': target.y + random.randint(-50, 50)}
                    target.receive_impact(value=0.5, source_position=impact_pos)
        
        # 更新
        target.update()
        
        # 绘制
        screen.fill((15, 15, 25))
        target.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()