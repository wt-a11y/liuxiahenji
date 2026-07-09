"""
粒子系统模块

记忆碎片系统 - 半透明、有机的记忆残留
行为痕迹以记忆碎片形式存在，沉积、漂移、渗透进入目标

可直接运行测试：python particle_system.py
"""

import pygame
import random
import math
from typing import List, Tuple, Optional, Dict
import time


class MemoryFragment:
    """
    记忆碎片
    
    代表行为痕迹的半透明有机残留
    不规则碎片形态，有旋转和残影效果
    """
    
    def __init__(self, x: float, y: float, 
                 intensity: float = 0.5,
                 behavior_speed: float = 0.0,
                 behavior_distance: float = 0.0):
        """
        初始化记忆碎片
        
        Args:
            x, y: 初始位置
            intensity: 碎片强度 (0.0 - 1.0)
            behavior_speed: 行为速度
            behavior_distance: 行为距离
        """
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        
        # 碎片属性
        self.intensity = intensity
        self.size = random.uniform(8, 15) * (0.5 + intensity * 0.5)
        
        # 不规则碎片形态
        self.num_vertices = random.randint(5, 7)  # 5-7个顶点
        self.vertex_angles = []  # 每个顶点的角度
        self.vertex_distances = []  # 每个顶点的距离
        
        # 初始化不规则形态
        base_angle = random.uniform(0, 2 * math.pi)
        for i in range(self.num_vertices):
            angle = base_angle + (i / self.num_vertices) * 2 * math.pi
            self.vertex_angles.append(angle)
            # 随机偏移，创造不规则形态
            distance_offset = random.uniform(0.6, 1.4)
            self.vertex_distances.append(distance_offset)
        
        # 旋转
        self.rotation_angle = 0
        self.rotation_speed = random.uniform(-0.03, 0.03)  # 缓慢旋转
        
        # 颜色 - 暖琥珀色，半透明
        self.base_color = (255, 183, 77)  # 琥珀色
        self.current_color = self.base_color
        self.base_transparency = 0.4 + intensity * 0.3
        self.transparency = self.base_transparency
        
        # 残影效果
        self.trail_positions: List[Tuple[float, float, float]] = []  # (x, y, alpha)
        self.max_trail_length = 5
        
        # 状态
        self.state = 'floating'  # floating, settling, drifting, penetrating
        self.state_start_time = time.time()
        
        # 沉积阶段（调整，让碎片位置更集中，更安静）
        self.settle_target_x = x + random.uniform(-20, 20)  # 减小偏移
        self.settle_target_y = y + random.uniform(15, 35)  # 减小偏移，向下沉积
        self.settle_speed = random.uniform(0.2, 0.4)  # 更慢的沉积速度
        
        # 漂移阶段（简化）
        self.drift_target = None
        self.drift_speed = 2.5  # 增加速度（从0.3改为2.5像素/帧）
        
        # 速度向量（确保有vx, vy）
        self.vx = 0.0
        self.vy = 0.0
        
        # 膜边界距离
        self.membrane_approach_range = 80  # 接近膜的距离（开始扰动）
        self.membrane_touch_range = 65  # 接触膜的边界（膜半径约60）
        self.membrane_penetration_range = 45  # 进入膜内部的深度（开始明显透明度变化）
        self.current_distance_to_target = 1000
        
        # 渗透阶段（进入内部，透明度变高）
        self.penetration_progress = 0.0
        # 3秒完成（180帧@60fps），透明度从100%渐变到0%
        self.penetration_speed = 1.0 / 180.0  # ≈ 0.00556
        # 碎片大小缩放（渗透阶段逐渐缩小）
        self.size_scale = 1.0
        self.is_touching_membrane = False  # 是否已经接触膜
        self.has_penetrated_membrane = False  # 是否已经进入膜内部
        
        # 生命周期
        self.birth_time = time.time()
        self.max_lifetime = 60
        
    def update(self, target_position: Optional[Tuple[float, float]] = None):
        """
        更新碎片状态
        
        Args:
            target_position: 目标对象位置，用于漂移阶段
        """
        current_time = time.time()
        state_duration = current_time - self.state_start_time
        
        # 更新旋转
        self.rotation_angle += self.rotation_speed
        
        # 记录残影位置（只在非渗透状态）
        if self.state in ['floating', 'settling', 'drifting']:
            self.trail_positions.append((self.x, self.y, self.transparency * 0.5))
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)
        
        # 状态机
        if self.state == 'floating':
            # 悬浮阶段 - 轻微摆动（更安静）
            # 减小摆动幅度
            self.x += math.sin(current_time * 1.5 + self.base_x) * 0.15  # 更小的摆动
            self.y += math.cos(current_time * 1.2 + self.base_y) * 0.1
            
            # 5秒后进入沉积阶段（延长时间）
            if state_duration > 5.0:
                self._transition_to('settling')
                
        elif self.state == 'settling':
            # 沉积阶段 - 缓慢移动到沉积位置
            dx = self.settle_target_x - self.x
            dy = self.settle_target_y - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance > 1:
                self.x += (dx / distance) * self.settle_speed
                self.y += (dy / distance) * self.settle_speed
            else:
                # 到达沉积位置，停留一段时间（延长）
                if state_duration > 12.0:  # 沉积8秒后开始漂移（更安静）
                    if target_position:
                        self._transition_to('drifting', target_position)
                    else:
                        # 没有目标，继续悬浮
                        self._transition_to('floating')
                        
        elif self.state == 'drifting':
            # 漂移阶段 - 向膜边界移动（使用速度向量）
            if target_position:
                # 计算到中心的距离
                dx = target_position[0] - self.x
                dy = target_position[1] - self.y
                self.current_distance_to_target = math.sqrt(dx ** 2 + dy ** 2)
                
                # 计算单位方向向量
                if self.current_distance_to_target > 0:
                    dir_x = dx / self.current_distance_to_target
                    dir_y = dy / self.current_distance_to_target
                else:
                    dir_x, dir_y = 0, 0
                
                # 根据距离调整速度
                if self.current_distance_to_target > self.membrane_touch_range:
                    # 还没接触膜，正常速度移动
                    current_speed = self.drift_speed
                    
                    # 当碎片靠近膜边界时（进入approach_range），标记为接近膜
                    if self.current_distance_to_target < self.membrane_approach_range:
                        self.is_touching_membrane = True
                elif self.current_distance_to_target > self.membrane_penetration_range:
                    # 已经接触膜，减速（从2.5降为1.5）
                    current_speed = self.drift_speed * 0.6
                    
                    # 标记已经接触膜
                    self.is_touching_membrane = True
                    self.has_penetrated_membrane = True
                    
                    # 透明度开始缓慢增加
                    self.transparency = self.base_transparency + (self.membrane_touch_range - self.current_distance_to_target) / (self.membrane_touch_range - self.membrane_penetration_range) * 0.15
                else:
                    # 已经进入膜内部，开始渗透
                    self.is_touching_membrane = False  # 已经进入内部，不再触发膜扰动
                    self._transition_to('penetrating')
                    current_speed = 0
                
                # 更新速度向量和位置
                self.vx = dir_x * current_speed
                self.vy = dir_y * current_speed
                self.x += self.vx
                self.y += self.vy
                        
        elif self.state == 'penetrating':
            # 渗透阶段 - 进入生命体内部
            # 进度累积，3秒完成（180帧@60fps）
            self.penetration_progress += self.penetration_speed
            
            # 碎片进入内部（向中心移动，极慢+强阻力感）
            if target_position:
                dx = target_position[0] - self.x
                dy = target_position[1] - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                
                # 缓慢向中心移动
                if dist > 8:  # 距离生命体中心还有一定距离
                    # 进度越深，阻力越大（移动越慢）
                    # 起始 1.0x 速度，结束时 0.2x 速度
                    resistance = 1.0 - self.penetration_progress * 0.8
                    move_factor = 0.04 * resistance
                    self.x += (dx / dist) * move_factor
                    self.y += (dy / dist) * move_factor
            
            # 透明度从当前值（drifting末态，约0.65）渐变到0（完全透明）
            # transparency语义：1.0=完全可见，0.0=完全透明
            # 保持连续性，从进入penetrating时的transparency开始渐变
            initial_transparency = getattr(self, '_initial_penetration_transparency', self.transparency)
            self.transparency = max(0.0, initial_transparency * (1.0 - self.penetration_progress))
            
            # 碎片大小逐渐缩小（暗示被生命体吸收）
            # 缩放系数从1.0逐渐减小到0.2
            self.size_scale = max(0.2, 1.0 - self.penetration_progress * 0.8)
            
            # 旋转速度变化（被吸收时旋转变慢）
            self.rotation_speed = 0.005 * (1.0 - self.penetration_progress * 0.7)
            
            # 渗透完成（进度达到1.0时移除）
            if self.penetration_progress >= 1.0:
                return True  # 碎片完全融入生命体
                
        return False  # 继续存活
    
    def _transition_to(self, new_state: str, target_position: Optional[Tuple[float, float]] = None):
        """状态转换（简化，去掉弯曲路径生成）"""
        self.state = new_state
        self.state_start_time = time.time()
        
        # 进入penetrating时记录初始透明度，保持视觉连续性
        if new_state == 'penetrating':
            self._initial_penetration_transparency = self.transparency
            self.penetration_progress = 0.0
        
        # 不再生成弯曲的漂移路径
        # 碎片直接缓慢直线移动到膜边界
    
    def get_polygon_points(self) -> List[Tuple[float, float]]:
        """
        获取多边形顶点（用于绘制不规则碎片）
        
        Returns:
            多边形顶点坐标列表
        """
        # 应用size_scale（渗透阶段碎片会缩小）
        size_scale = getattr(self, 'size_scale', 1.0)
        
        points = []
        for i in range(self.num_vertices):
            # 应用旋转
            angle = self.vertex_angles[i] + self.rotation_angle
            # 应用距离偏移（应用size_scale）
            distance = self.size * self.vertex_distances[i] * size_scale
            
            # 计算顶点位置
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            
            points.append((x, y))
        
        return points
    
    def get_current_color_with_alpha(self) -> Tuple[int, int, int, int]:
        """获取当前颜色（带透明度）"""
        alpha = int(255 * self.transparency)
        return (*self.current_color, alpha)
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        current_time = time.time()
        return (current_time - self.birth_time) < self.max_lifetime
    
    def get_state(self) -> str:
        """获取当前状态"""
        return self.state
    
    def get_penetration_data(self) -> Optional[Dict]:
        """
        获取渗透数据（用于影响目标对象）
        
        Returns:
            渗透数据字典，如果未进入渗透阶段则返回None
        """
        if self.state == 'penetrating' and self.penetration_progress > 0.5:
            return {
                'intensity': self.intensity,
                'position': (self.x, self.y),
                'progress': self.penetration_progress
            }
        return None


class MemoryCloud:
    """
    记忆碎片云
    
    管理一组记忆碎片
    """
    
    def __init__(self):
        """初始化记忆碎片云"""
        self.fragments: List[MemoryFragment] = []
        self.target_position: Optional[Tuple[float, float]] = None
        
    def add_fragments_from_trajectory(self, trajectory: List[Tuple[int, int]], 
                                     behavior_speed: float = 0.0,
                                     behavior_distance: float = 0.0):
        """
        从轨迹生成记忆碎片
        
        Args:
            trajectory: 轨迹点列表
            behavior_speed: 行为速度
            behavior_distance: 行为距离
        """
        if len(trajectory) < 3:
            return
        
        # 根据轨迹长度决定碎片数量
        num_fragments = min(8, max(3, len(trajectory) // 15))
        
        # 从轨迹中均匀采样点生成碎片
        step = len(trajectory) // num_fragments
        
        for i in range(num_fragments):
            idx = min(i * step, len(trajectory) - 1)
            x, y = trajectory[idx]
            
            # 强度根据轨迹特征计算
            intensity = min(1.0, (behavior_speed / 20.0) * 0.3 + 
                          (behavior_distance / 500.0) * 0.7)
            
            fragment = MemoryFragment(
                x=float(x), 
                y=float(y),
                intensity=intensity,
                behavior_speed=behavior_speed,
                behavior_distance=behavior_distance
            )
            self.fragments.append(fragment)
            
        print(f"生成 {num_fragments} 个记忆碎片")
        
    def set_target(self, target_position: Tuple[float, float]):
        """
        设置目标位置
        
        Args:
            target_position: 目标对象位置
        """
        self.target_position = target_position
        
    def get_fragments_data(self) -> List[Dict]:
        """
        获取所有碎片的状态数据（用于检查是否靠近膜边界）
        
        Returns:
            碎片数据列表
        """
        fragments_data = []
        for fragment in self.fragments:
            fragment_data = {
                'x': fragment.x,
                'y': fragment.y,
                'intensity': fragment.intensity,
                'is_touching_membrane': fragment.is_touching_membrane,
                'has_penetrated_membrane': fragment.has_penetrated_membrane,
                'distance_to_target': fragment.current_distance_to_target,
                'state': fragment.state
            }
            fragments_data.append(fragment_data)
        
        return fragments_data
    
    def update(self) -> List[Dict]:
        """
        更新所有碎片
        
        Returns:
            完成渗透的碎片数据列表
        """
        completed_penetrations = []
        
        for fragment in self.fragments:
            if fragment.is_alive():
                completed = fragment.update(self.target_position)
                if completed:
                    # 碎片渗透完成
                    penetration_data = fragment.get_penetration_data()
                    if penetration_data:
                        completed_penetrations.append(penetration_data)
                        
        # 移除死亡或完成的碎片
        self.fragments = [f for f in self.fragments 
                         if f.is_alive() and f.get_state() != 'penetrating_completed']
        
        return completed_penetrations
    
    def draw(self, screen: pygame.Surface):
        """
        绘制所有碎片
        
        Args:
            screen: Pygame屏幕表面
        """
        for fragment in self.fragments:
            if fragment.get_state() != 'penetrating':
                # 1. 绘制残影
                if fragment.trail_positions:
                    for i, (trail_x, trail_y, trail_alpha) in enumerate(fragment.trail_positions):
                        if trail_alpha > 0.05:
                            # 残影透明度递减
                            alpha_factor = (i + 1) / len(fragment.trail_positions)
                            trail_alpha_final = trail_alpha * alpha_factor * 0.3
                            
                            # 绘制残影（简化为圆形）
                            trail_size = fragment.size * 0.5
                            trail_color = (*fragment.base_color, int(255 * trail_alpha_final))
                            
                            trail_surf = pygame.Surface((int(trail_size * 2 + 4), int(trail_size * 2 + 4)), pygame.SRCALPHA)
                            pygame.draw.circle(trail_surf, trail_color, 
                                             (int(trail_size + 2), int(trail_size + 2)), int(trail_size))
                            screen.blit(trail_surf, (trail_x - trail_size - 2, trail_y - trail_size - 2))
                
                # 2. 绘制碎片主体
                points = fragment.get_polygon_points()
                
                if len(points) >= 3:
                    color_with_alpha = fragment.get_current_color_with_alpha()
                    
                    # 计算边界框
                    min_x = min(p[0] for p in points)
                    max_x = max(p[0] for p in points)
                    min_y = min(p[1] for p in points)
                    max_y = max(p[1] for p in points)
                    
                    width = int(max_x - min_x) + 20
                    height = int(max_y - min_y) + 20
                    
                    if width > 0 and height > 0:
                        # 创建临时表面
                        temp_surf = pygame.Surface((width, height), pygame.SRCALPHA)
                        
                        # 调整点坐标到临时表面坐标系
                        adjusted_points = [(p[0] - min_x + 10, p[1] - min_y + 10) for p in points]
                        
                        # 绘制多层（简单辉光效果）
                        # 外层（微弱辉光）
                        if fragment.intensity > 0.6:
                            glow_color = (*fragment.base_color, int(50 * fragment.transparency))
                            glow_points = [(p[0] - min_x + 10, p[1] - min_y + 10) for p in points]
                            pygame.draw.polygon(temp_surf, glow_color, glow_points)
                        
                        # 中层（主体）
                        pygame.draw.polygon(temp_surf, color_with_alpha, adjusted_points)
                        
                        # 内层（高亮中心）
                        if fragment.intensity > 0.5:
                            inner_size = fragment.size * 0.3
                            inner_color = (255, 220, 180, int(150 * fragment.transparency))
                            pygame.draw.circle(temp_surf, inner_color, 
                                             (int(width // 2), int(height // 2)), int(inner_size))
                        
                        # 绘制到屏幕
                        screen.blit(temp_surf, (min_x - 10, min_y - 10))
    
    def get_fragment_count(self) -> int:
        """获取当前碎片数量"""
        return len(self.fragments)
    
    def get_fragments_by_state(self, state: str) -> int:
        """获取特定状态的碎片数量"""
        return sum(1 for f in self.fragments if f.get_state() == state)
    
    def clear(self):
        """清除所有碎片"""
        self.fragments.clear()


class ParticleSystem:
    """
    粒子系统（主类，兼容旧接口）
    
    现在主要管理记忆碎片云
    """
    
    def __init__(self):
        """初始化粒子系统"""
        self.memory_cloud = MemoryCloud()
        self.target_position: Optional[Tuple[float, float]] = None
        
    def set_target(self, target_position: Tuple[float, float]):
        """
        设置目标位置
        
        Args:
            target_position: 目标对象位置
        """
        self.target_position = target_position
        self.memory_cloud.set_target(target_position)
        
    def create_trace_from_trajectory(self, trajectory: List[Tuple[int, int]],
                                    behavior_speed: float = 0.0,
                                    behavior_distance: float = 0.0):
        """
        从轨迹创建记忆碎片
        
        Args:
            trajectory: 轨迹点列表
            behavior_speed: 行为速度
            behavior_distance: 行为距离
        """
        self.memory_cloud.add_fragments_from_trajectory(
            trajectory, behavior_speed, behavior_distance
        )
        
    def update(self) -> List[Dict]:
        """
        更新粒子系统
        
        Returns:
            完成渗透的碎片数据列表
        """
        return self.memory_cloud.update()
    
    def get_fragments_data(self) -> List[Dict]:
        """
        获取所有碎片的状态数据（用于检查是否靠近膜边界）
        
        Returns:
            碎片数据列表
        """
        return self.memory_cloud.get_fragments_data()
    
    def draw(self, screen: pygame.Surface):
        """
        绘制粒子系统
        
        Args:
            screen: Pygame屏幕表面
        """
        self.memory_cloud.draw(screen)
        
    def get_particle_count(self) -> int:
        """获取当前粒子数量"""
        return self.memory_cloud.get_fragment_count()
    
    def clear(self):
        """清除所有粒子"""
        self.memory_cloud.clear()


def main():
    """
    测试函数：测试记忆碎片系统
    
    操作：
    - 鼠标移动生成轨迹
    - 静止 0.8秒生成记忆碎片
    - 碎片沉积 → 漂移 → 渗透
    - 'c' 清除
    - 'q' 退出
    """
    import time
    from behavior_analysis import BehaviorAnalyzer
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Memory Fragment Test - 记忆碎片系统")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    # 初始化系统
    particle_system = ParticleSystem()
    analyzer = BehaviorAnalyzer()
    
    # 设置目标位置（屏幕中央）
    target_pos = (640, 360)
    particle_system.set_target(target_pos)
    
    # 当前轨迹
    current_trajectory: List[Tuple[int, int]] = []
    
    print("=" * 50)
    print("记忆碎片系统测试")
    print("=" * 50)
    print("移动鼠标绘制轨迹")
    print("静止 0.8秒 → 生成记忆碎片 → 沉积 → 漂移 → 渗透")
    print("'c' - 清除")
    print("'q' - 退出")
    print("=" * 50)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_c:
                    particle_system.clear()
                    analyzer.clear()
                    current_trajectory.clear()
                    print("已清除")
        
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand_pos = {"x": mouse_x, "y": mouse_y}
        
        # 记录轨迹
        current_trajectory.append((mouse_x, mouse_y))
        if len(current_trajectory) > 150:
            current_trajectory.pop(0)
        
        # 更新行为分析器
        action = analyzer.update(hand_pos)
        
        if action:
            # 动作结束，生成记忆碎片
            action_dict = action.to_dict()
            particle_system.create_trace_from_trajectory(
                action_dict['trajectory'],
                action_dict['speed'],
                action_dict['distance']
            )
            current_trajectory.clear()
            print(f"生成记忆碎片: speed={action_dict['speed']:.2f}, distance={action_dict['distance']:.2f}")
        
        # 更新粒子系统（获取渗透数据）
        penetrations = particle_system.update()
        if penetrations:
            print(f"{len(penetrations)} 个碎片完成渗透")
        
        # 渲染
        screen.fill((15, 15, 25))  # 深色背景
        
        # 绘制目标位置（目标对象占位符）
        pygame.draw.circle(screen, (100, 150, 200, 100), target_pos, 50, 2)
        pygame.draw.circle(screen, (150, 180, 220, 50), target_pos, 30)
        
        # 绘制当前轨迹
        if len(current_trajectory) >= 2:
            pygame.draw.lines(screen, (80, 160, 220), False, current_trajectory, 2)
            if current_trajectory:
                pygame.draw.circle(screen, (120, 200, 255), current_trajectory[-1], 5)
        
        # 绘制记忆碎片
        particle_system.draw(screen)
        
        # 显示信息
        info_lines = [
            f"轨迹点: {len(current_trajectory)}",
            f"记忆碎片: {particle_system.get_particle_count()}",
            f"悬浮: {particle_system.memory_cloud.get_fragments_by_state('floating')}",
            f"沉积: {particle_system.memory_cloud.get_fragments_by_state('settling')}",
            f"漂移: {particle_system.memory_cloud.get_fragments_by_state('drifting')}",
            f"渗透: {particle_system.memory_cloud.get_fragments_by_state('penetrating')}",
            f"静止: {analyzer.get_inactive_duration():.2f}s / 0.8s",
            "",
            "移动鼠标 → 静止0.8秒 → 碎片飞向目标"
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("测试结束")


if __name__ == "__main__":
    main()