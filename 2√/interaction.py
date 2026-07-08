"""
交互模块

实现行为痕迹影响目标对象

流程：
动作结束 → 生成痕迹 → 痕迹移动到目标对象 → 触碰目标 → 调用 receive_impact()

影响强度根据 movement_speed 和 movement_distance 计算
不判断正面/负面影响，只表现行为产生影响

可直接运行测试：python interaction.py
"""

import math
import random
from typing import List, Dict, Optional, Tuple
import time


class TraceProjectile:
    """
    痕迹投射物
    
    代表一个正在移动的痕迹
    从轨迹位置移动到目标对象
    """
    
    def __init__(self, start_x: float, start_y: float,
                 target_x: float, target_y: float,
                 speed: float, distance: float, trajectory: List[Tuple[int, int]]):
        """
        初始化痕迹投射物
        
        Args:
            start_x, start_y: 痕迹起始位置（轨迹中心）
            target_x, target_y: 目标位置
            speed: 动作速度（用于计算影响强度）
            distance: 动作距离（用于计算影响强度）
            trajectory: 原始轨迹点
        """
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y
        
        self.target_x = target_x
        self.target_y = target_y
        
        # 计算移动方向
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        
        if dist > 0:
            self.vx = (dx / dist) * 3  # 固定速度：3像素/帧
            self.vy = (dy / dist) * 3
        else:
            self.vx = 0
            self.vy = 0
        
        # 影响参数
        self.movement_speed = speed
        self.movement_distance = distance
        self.trajectory = trajectory
        
        # 状态
        self.alive = True
        self.has_impacted = False
        
        # 视觉参数
        self.size = 8
        self.color = (180, 150, 200)  # 淡紫色
        self.trail: List[Tuple[float, float]] = []  # 移动轨迹
        
    def update(self, target_x: float, target_y: float):
        """
        更新投射物位置
        
        Args:
            target_x, target_y: 当前目标位置（目标可能移动）
        """
        # 更新目标位置
        self.target_x = target_x
        self.target_y = target_y
        
        # 重新计算方向
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        
        if dist > 0:
            self.vx = (dx / dist) * 3
            self.vy = (dy / dist) * 3
        
        # 移动
        self.x += self.vx
        self.y += self.vy
        
        # 记录轨迹
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)
        
        # 检查是否到达目标
        if dist < 50:  # 距离小于50像素视为触碰
            self.has_impacted = True
            self.alive = False
    
    def calculate_impact_value(self) -> float:
        """
        计算影响强度
        
        根据 movement_speed 和 movement_distance
        
        Returns:
            影响强度 (0.0 - 1.0)
        """
        # 速度影响：速度越快，影响越大（但有上限）
        speed_factor = min(1.0, self.movement_speed / 20.0)  # 20px/frame为最大速度
        
        # 距离影响：距离越长，影响越大（但有上限）
        distance_factor = min(1.0, self.movement_distance / 500.0)  # 500px为最大距离
        
        # 综合影响值
        impact_value = (speed_factor * 0.4 + distance_factor * 0.6)
        
        # 确保在 0.0 - 1.0 范围内
        return min(1.0, max(0.1, impact_value))
    
    def get_source_position(self) -> Dict[str, float]:
        """获取来源位置"""
        return {'x': self.start_x, 'y': self.start_y}
    
    def is_alive(self) -> bool:
        """是否存活"""
        return self.alive
    
    def has_reached_target(self) -> bool:
        """是否已到达目标"""
        return self.has_impacted


class InteractionManager:
    """
    交互管理器
    
    管理痕迹与目标对象的交互
    实现：动作结束 → 生成痕迹 → 痕迹移动到目标 → 触碰 → receive_impact()
    """
    
    def __init__(self):
        """初始化交互管理器"""
        # 痕迹投射物列表
        self.projectiles: List[TraceProjectile] = []
        
        # 目标对象引用
        self.target: Optional[any] = None  # TargetObject
        
        # 参数
        self.max_projectiles = 10  # 最大同时存在的投射物数量
        
    def set_target(self, target):
        """
        设置目标对象
        
        Args:
            target: TargetObject 实例
        """
        self.target = target
    
    def process_action_end(self, action_data: Dict):
        """
        处理动作结束
        
        动作结束后，创建痕迹投射物，向目标移动
        
        Args:
            action_data: 动作数据 {
                'speed': float,
                'distance': float,
                'duration': float,
                'trajectory': List[Tuple[int, int]]
            }
        """
        if not action_data or not action_data.get('trajectory'):
            return
        
        trajectory = action_data['trajectory']
        
        if len(trajectory) < 3:
            return
        
        if not self.target:
            print("警告：未设置目标对象")
            return
        
        # 计算轨迹中心作为痕迹起始位置
        center_x = sum(p[0] for p in trajectory) / len(trajectory)
        center_y = sum(p[1] for p in trajectory) / len(trajectory)
        
        # 获取目标位置
        target_pos = self.target.position
        target_x = target_pos['x']
        target_y = target_pos['y']
        
        # 获取动作参数
        speed = action_data.get('speed', 0)
        distance = action_data.get('distance', 0)
        
        # 创建痕迹投射物
        projectile = TraceProjectile(
            start_x=center_x,
            start_y=center_y,
            target_x=target_x,
            target_y=target_y,
            speed=speed,
            distance=distance,
            trajectory=trajectory
        )
        
        self.projectiles.append(projectile)
        
        # 限制投射物数量
        if len(self.projectiles) > self.max_projectiles:
            self.projectiles.pop(0)
        
        print(f"创建痕迹投射物: speed={speed:.2f}, distance={distance:.2f}, 中心({center_x:.1f}, {center_y:.1f})")
    
    def update(self):
        """
        更新所有投射物
        
        移动投射物，检查是否到达目标，触发 receive_impact()
        """
        if not self.target:
            return
        
        # 获取目标当前位置
        target_pos = self.target.position
        target_x = target_pos['x']
        target_y = target_pos['y']
        
        # 更新每个投射物
        for projectile in self.projectiles:
            if projectile.is_alive():
                projectile.update(target_x, target_y)
                
                # 检查是否到达目标
                if projectile.has_reached_target():
                    # 计算影响强度
                    impact_value = projectile.calculate_impact_value()
                    
                    # 获取来源位置
                    source_pos = projectile.get_source_position()
                    
                    # 调用目标对象的 receive_impact()
                    # 不判断正面/负面影响，只传递 'attract' 作为默认类型
                    self.target.receive_impact(
                        value=impact_value,
                        source_position=source_pos,
                        impact_type='attract'
                    )
                    
                    print(f"痕迹触碰目标: impact_value={impact_value:.2f}")
        
        # 移除已完成的投射物
        self.projectiles = [p for p in self.projectiles if p.is_alive()]
    
    def draw(self, screen):
        """
        绘制所有投射物
        
        Args:
            screen: Pygame 屏幕表面
        """
        import pygame
        
        for projectile in self.projectiles:
            # 绘制移动轨迹（淡紫色线条）
            if len(projectile.trail) >= 2:
                trail_points = [(int(p[0]), int(p[1])) for p in projectile.trail]
                
                # 轨迹渐变效果
                for i in range(len(trail_points) - 1):
                    alpha = (i + 1) / len(trail_points)
                    color = tuple(int(c * (0.3 + 0.7 * alpha)) for c in projectile.color)
                    pygame.draw.line(screen, color, trail_points[i], trail_points[i + 1], 2)
            
            # 绘制投射物主体
            pos = (int(projectile.x), int(projectile.y))
            
            # 发光效果
            glow_color = tuple(int(c * 0.5) for c in projectile.color)
            pygame.draw.circle(screen, glow_color, pos, projectile.size + 4)
            
            # 主体
            pygame.draw.circle(screen, projectile.color, pos, projectile.size)
            
            # 中心亮点
            pygame.draw.circle(screen, (255, 255, 255), pos, 3)
    
    def get_projectile_count(self) -> int:
        """获取当前投射物数量"""
        return len(self.projectiles)
    
    def clear(self):
        """清除所有投射物"""
        self.projectiles.clear()


def main():
    """
    测试函数：测试交互系统
    
    操作：
    - 移动鼠标绘制轨迹
    - 静止 0.8秒动作结束
    - 痕迹向目标移动
    - 触碰目标产生效果
    
    按 'c' 清除
    按 's' 重置目标位置
    按 'q' 退出
    """
    import pygame
    from target_object import TargetObject
    from behavior_analysis import BehaviorAnalyzer
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Interaction Test - 痕迹影响目标")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    # 初始化模块
    target = TargetObject()
    analyzer = BehaviorAnalyzer()
    interaction = InteractionManager()
    
    # 设置目标
    interaction.set_target(target)
    
    print("=" * 50)
    print("交互系统测试 - 痕迹影响目标")
    print("=" * 50)
    print("移动鼠标绘制轨迹")
    print("静止 0.8秒 → 动作结束 → 痕迹向目标移动 → 触碰产生效果")
    print("'c' - 清除")
    print("'s' - 重置目标")
    print("'q' - 退出")
    print("=" * 50)
    
    # 轨迹可视化
    current_trajectory: List[Tuple[int, int]] = []
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_c:
                    interaction.clear()
                    analyzer.clear()
                    current_trajectory.clear()
                    print("已清除")
                elif event.key == pygame.K_s:
                    target.reset_position()
                    print("目标已重置")
        
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand_pos = {"x": mouse_x, "y": mouse_y}
        
        # 记录轨迹点
        current_trajectory.append((mouse_x, mouse_y))
        if len(current_trajectory) > 100:
            current_trajectory.pop(0)
        
        # 更新行为分析器
        action = analyzer.update(hand_pos)
        
        if action:
            # 动作结束，处理交互
            action_data = action.to_dict()
            interaction.process_action_end(action_data)
            current_trajectory.clear()
        
        # 更新交互管理器
        interaction.update()
        
        # 更新目标对象
        target.update()
        
        # 渲染
        screen.fill((15, 15, 25))
        
        # 绘制当前轨迹
        if len(current_trajectory) >= 2:
            pygame.draw.lines(screen, (100, 180, 255), False, current_trajectory, 2)
            pygame.draw.circle(screen, (150, 220, 255), current_trajectory[-1], 5)
        
        # 绘制目标对象
        target.draw(screen)
        
        # 绘制投射物
        interaction.draw(screen)
        
        # 显示信息
        info_lines = [
            f"轨迹点: {len(current_trajectory)}",
            f"投射物: {interaction.get_projectile_count()}",
            f"目标位置: ({target.position['x']:.1f}, {target.position['y']:.1f})",
            f"目标状态: {target.state}",
            f"影响值: {target.impact_value:.2f}",
            f"静止帧: {analyzer.get_inactive_duration():.2f}s / 0.8s",
            "",
            "移动鼠标 → 静止0.8秒 → 痕迹飞向目标"
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