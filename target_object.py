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
        
    def update(self, center_x: float, center_y: float, is_influenced: bool):
        """
        更新纹理状态
        
        Args:
            center_x, center_y: 生命体中心位置
            is_influenced: 是否被影响
        """
        # 流动效果
        self.flow_phase += self.flow_speed
        self.current_angle = self.base_angle + self.flow_phase * 0.1
        
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
            
            # 最终距离
            final_distance = base_distance + wave_offset + deformation_offset + perturbation_offset + permanent_offset
            
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
        self.num_flow_textures = random.randint(5, 8)
        self.flow_textures: List[FlowTexture] = []
        
        for i in range(self.num_flow_textures):
            texture = FlowTexture(x, y, i)
            self.flow_textures.append(texture)
        
        # 永久纹理层（被影响后新增的纹理）
        self.permanent_texture_layers: List[PermanentTextureLayer] = []
        
        # 状态
        self.age = 0
        self.cumulative_influence = 0.0
        self.impact_level = 0.0  # 0.0-1.0 累积影响水平（用于视觉反馈）
        self.absorbed_count = 0  # 实际进入生命体的碎片数量（用于颜色分阶段）
        self.fragment_count = 0  # 累计吸收的碎片数量（核心颜色变化依据，不衰减）
        
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
        
        # 计算当前color_progress（基于fragment_count，但更平滑的分段）
        new_progress = self._calculate_color_progress(self.fragment_count)
        
        # 计算目标颜色（基于color_progress在5个关键色之间插值）
        target_color = self._calculate_target_color_from_progress(new_progress)
        
        # 调试输出：每次碎片进入时打印
        print(f"Fragment absorbed: count = {self.fragment_count}")
        print(f"  color_progress = {new_progress:.3f}")
        print(f"  target_color   = {tuple(int(c) for c in target_color)}")
        print(f"  current_color  = {tuple(int(c) for c in self.current_color)}")
        
        # 标记为被影响状态
        self.is_currently_influenced = True
        
        # 如果有来源位置，添加局部扰动和新增永久纹理层
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
            
            # 新增永久纹理层（在影响点周围）
            # 限制总层数，避免性能问题
            if len(self.permanent_texture_layers) < 8:
                impact_position = (fragment_x, fragment_y)
                permanent_layer = PermanentTextureLayer(self.x, self.y, impact_position, value)
                self.permanent_texture_layers.append(permanent_layer)
            
            # 新增一条新的FlowTexture（表达生命体记住了痕迹）
            # 限制总纹理数量，避免性能问题
            if len(self.flow_textures) < 15:
                new_texture = FlowTexture(self.x, self.y, len(self.flow_textures))
                # 让新纹理与影响角度相关
                new_texture.base_angle = angle
                new_texture.base_radius = 15 + value * 20
                new_texture.base_intensity = 0.4 + value * 0.3
                new_texture.current_intensity = new_texture.base_intensity
                self.flow_textures.append(new_texture)
            
            # 改变原有纹理的速度（受新影响改变）- 限制最大速度
            for texture in self.flow_textures[:-1]:  # 不包括刚加的
                texture.flow_speed = min(0.15, texture.flow_speed * (1.0 + value * 0.1))
            
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
            
        print(f"生命体受到记忆渗透: 强度={value:.2f}, 新增永久纹理层={len(self.permanent_texture_layers)}, 累积={self.cumulative_influence:.2f}")
    
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
        
        # 1. 根据fragment_count更新color_progress（0.0-1.0）
        self.color_progress = self._calculate_color_progress(self.fragment_count)
        
        # 2. 根据color_progress计算目标颜色（在5个关键色之间连续插值）
        target_color = self._calculate_target_color_from_progress(self.color_progress)
        
        # 3. 当前颜色向目标颜色缓慢插值（生命体慢慢适应）
        # 每帧只移动1%差距，需要约100帧(1.7秒)接近目标
        for i in range(3):
            self.current_color[i] += (target_color[i] - self.current_color[i]) * self.color_transition_speed
        
        # 4. 同步当前颜色到membrane（实际显示颜色）
        self.membrane._current_display_color = tuple(self.current_color)
        
        # 更新外膜
        self.membrane.update(self.x, self.y, self.is_currently_influenced)
        
        # 更新流动纹理
        for texture in self.flow_textures:
            texture.update(self.x, self.y, self.is_currently_influenced)
        
        # 更新永久纹理层
        for layer in self.permanent_texture_layers:
            layer.update(self.x, self.y)
        
        # 检查是否所有纹理都恢复平静
        all_calm = all(texture.influence_intensity < 0.05 for texture in self.flow_textures)
        if all_calm and self.membrane.deformation_factor < 0.05:
            self.is_currently_influenced = False
    
    def draw(self, screen: pygame.Surface):
        """
        绘制生命体（三层叠加）
        
        1. 内部流动纹理（最底层）
        2. 多层半透明有机膜（最外层）
        
        永久影响通过对生命体自身（膜形态、内部纹理）的作用来表达
        不再绘制独立的永久纹理层
        
        Args:
            screen: Pygame屏幕表面
        """
        # 1. 绘制内部流动纹理（最底层）
        self._draw_flow_textures(screen)
        
        # 2. 绘制多层半透明有机膜（最外层）
        self._draw_membrane_layers(screen)
    
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
        颜色随impact_level变化
        
        Args:
            screen: Pygame屏幕表面
        """
        # 根据impact_level计算纹理颜色
        # 基础：冷青色
        r0, g0, b0 = 200, 220, 240
        # 大量影响：暖琥珀色
        r1, g1, b1 = 255, 200, 150
        
        t = self.impact_level
        r = int(r0 + (r1 - r0) * t)
        g = int(g0 + (g1 - g0) * t)
        b = int(b0 + (b1 - b0) * t)
        
        for texture in self.flow_textures:
            points = texture.get_points()
            
            if len(points) >= 2:
                # 纹理强度
                intensity = texture.get_intensity()
                
                # 纹理颜色（半透明，强度影响透明度）
                alpha = int(80 * intensity)
                color = (r, g, b, alpha)
                
                # 计算边界框
                min_x = min(p[0] for p in points)
                max_x = max(p[0] for p in points)
                min_y = min(p[1] for p in points)
                max_y = max(p[1] for p in points)
                
                width = int(max_x - min_x) + 10
                height = int(max_y - min_y) + 10
                
                if width > 0 and height > 0:
                    texture_surf = pygame.Surface((width, height), pygame.SRCALPHA)
                    
                    # 调整点坐标
                    adjusted_points = [(p[0] - min_x + 5, p[1] - min_y + 5) for p in points]
                    
                    # 绘制曲线（线条）
                    pygame.draw.lines(texture_surf, color, False, adjusted_points, 2)
                    
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
        
        # 清空永久纹理层
        self.permanent_texture_layers.clear()
        
        self.cumulative_influence = 0.0
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