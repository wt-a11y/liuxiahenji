"""
粒子系统模块

实现数字痕迹的视觉表现
动作结束后，轨迹重新出现形成数字痕迹
粒子沿轨迹移动，渐变消失，有运动感和残留感

可直接运行测试：python particle_system.py
"""

import pygame
import random
import math
from typing import List, Tuple, Optional


class Particle:
    """
    单个粒子
    
    沿轨迹路径移动，渐变消失
    """
    
    def __init__(self, trajectory: List[Tuple[int, int]], 
                 start_index: int = 0,
                 speed: float = 1.0,
                 lifetime: int = 100,
                 color: Tuple[int, int, int] = None,
                 size: float = 3.0):
        """
        初始化轨迹粒子
        
        Args:
            trajectory: 粒子沿此轨迹移动
            start_index: 起始位置索引
            speed: 移动速度（点/帧）
            lifetime: 生命周期（帧数）
            color: 粒子颜色
            size: 粒子大小
        """
        self.trajectory = trajectory
        self.current_index = start_index
        self.progress = 0.0  # 当前点内的进度 (0.0 - 1.0)
        self.speed = speed
        
        self.lifetime = lifetime
        self.age = 0
        
        # 颜色：蓝紫色调，带渐变
        if color is None:
            self.base_color = (
                random.randint(100, 150),  # R
                random.randint(150, 200),  # G
                random.randint(200, 255)   # B - 蓝色为主
            )
        else:
            self.base_color = color
        
        self.size = size
        self.initial_size = size
        
        # 当前位置
        self.x = 0.0
        self.y = 0.0
        self._update_position()
        
    def _update_position(self):
        """根据当前索引计算精确位置"""
        if not self.trajectory:
            return
        
        # 确保索引在有效范围内
        if self.current_index >= len(self.trajectory) - 1:
            self.current_index = len(self.trajectory) - 1
            self.x, self.y = self.trajectory[self.current_index]
            return
        
        # 在两点之间插值
        p1 = self.trajectory[self.current_index]
        p2 = self.trajectory[self.current_index + 1]
        
        self.x = p1[0] + (p2[0] - p1[0]) * self.progress
        self.y = p1[1] + (p2[1] - p1[1]) * self.progress
        
    def update(self):
        """更新粒子状态"""
        self.age += 1
        
        if self.trajectory and len(self.trajectory) > 1:
            # 沿轨迹移动
            self.progress += self.speed
            
            # 移动到下一个点
            while self.progress >= 1.0 and self.current_index < len(self.trajectory) - 1:
                self.progress -= 1.0
                self.current_index += 1
            
            # 更新位置
            self._update_position()
        
        # 大小随时间衰减（运动感）
        alpha = self.get_alpha()
        self.size = self.initial_size * (0.5 + 0.5 * alpha)  # 保留至少一半大小
        
    def is_alive(self) -> bool:
        """检查粒子是否存活"""
        # 生命周期结束，或轨迹走完
        return self.age < self.lifetime
    
    def get_alpha(self) -> float:
        """获取当前透明度比例（渐变消失）"""
        return max(0.0, 1.0 - (self.age / self.lifetime))
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前位置"""
        return (int(self.x), int(self.y))


class TrailParticle:
    """
    残留粒子
    
    在轨迹上留下短暂的光点，形成残留感
    """
    
    def __init__(self, x: float, y: float, lifetime: int = 30):
        """
        初始化残留粒子
        
        Args:
            x, y: 位置
            lifetime: 存活时间（帧数）
        """
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.age = 0
        self.size = random.uniform(2, 4)
        self.color = (
            random.randint(80, 120),
            random.randint(150, 200),
            random.randint(200, 255)
        )
        
    def update(self):
        """更新残留粒子"""
        self.age += 1
        
    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.age < self.lifetime
    
    def get_alpha(self) -> float:
        """获取透明度"""
        return 1.0 - (self.age / self.lifetime)


class TraceParticles:
    """
    轨迹粒子组
    
    代表一条轨迹上的所有粒子
    动作结束后，轨迹重新出现形成数字痕迹
    """
    
    def __init__(self, trajectory: List[Tuple[int, int]], 
                 particle_count: int = 10,
                 trace_lifetime: int = 180):
        """
        初始化轨迹粒子组
        
        Args:
            trajectory: 轨迹点列表
            particle_count: 粒子数量
            trace_lifetime: 痕迹整体生命周期（帧数）
        """
        self.trajectory = trajectory
        self.age = 0
        self.lifetime = trace_lifetime  # 约3秒 @ 60fps
        
        # 创建沿轨迹移动的粒子
        self.particles: List[Particle] = []
        self.trail_particles: List[TrailParticle] = []
        
        if len(trajectory) >= 2:
            # 粒子沿轨迹分布
            for i in range(particle_count):
                # 每个粒子从不同位置开始
                start_index = int((i / particle_count) * (len(trajectory) - 1))
                speed = random.uniform(0.3, 0.8)  # 不同速度，形成层次感
                
                particle = Particle(
                    trajectory=trajectory,
                    start_index=start_index,
                    speed=speed,
                    lifetime=random.randint(80, 150),
                    size=random.uniform(2.5, 5.0)
                )
                self.particles.append(particle)
        
        # 轨迹可见性
        self.visible = False
        self.appear_time = 30  # 动作结束后30帧开始出现
        
    def update(self):
        """更新轨迹粒子组"""
        self.age += 1
        
        # 动作结束后一段时间才开始出现（残留感）
        if self.age >= self.appear_time:
            self.visible = True
        
        # 更新所有粒子
        for particle in self.particles:
            if particle.is_alive():
                particle.update()
                
                # 粒子移动时留下残留光点
                if random.random() < 0.3:  # 30%概率留下残留
                    trail = TrailParticle(
                        particle.x, particle.y,
                        lifetime=random.randint(15, 25)
                    )
                    self.trail_particles.append(trail)
        
        # 更新残留粒子
        for trail in self.trail_particles:
            trail.update()
        
        # 移除死亡粒子
        self.particles = [p for p in self.particles if p.is_alive()]
        self.trail_particles = [t for t in self.trail_particles if t.is_alive()]
        
    def is_alive(self) -> bool:
        """检查痕迹是否仍然有效"""
        return self.age < self.lifetime
    
    def get_intensity(self) -> float:
        """获取当前强度"""
        return max(0.0, 1.0 - (self.age / self.lifetime))
    
    def draw(self, screen: pygame.Surface):
        """
        绘制轨迹粒子组
        
        Args:
            screen: Pygame屏幕表面
        """
        if not self.visible:
            return
        
        intensity = self.get_intensity()
        
        # 绘制残留粒子（残留感）
        for trail in self.trail_particles:
            alpha = trail.get_alpha() * intensity
            size = max(1, int(trail.size * alpha))
            color = tuple(int(c * (0.3 + 0.7 * alpha)) for c in trail.color)
            
            if size > 0:
                pygame.draw.circle(screen, color, (int(trail.x), int(trail.y)), size)
        
        # 绘制轨迹线（淡淡的连线）
        if self.trajectory and len(self.trajectory) >= 2 and intensity > 0.3:
            line_color = (
                int(60 * intensity),
                int(100 * intensity),
                int(150 * intensity)
            )
            pygame.draw.lines(screen, line_color, False, self.trajectory, 1)
        
        # 绘制移动粒子（运动感）
        for particle in self.particles:
            alpha = particle.get_alpha() * intensity
            size = max(1, int(particle.size * alpha))
            
            # 粒子发光效果
            color = tuple(int(c * (0.4 + 0.6 * alpha)) for c in particle.base_color)
            
            if size > 0:
                pos = particle.get_position()
                # 主粒子
                pygame.draw.circle(screen, color, pos, size)
                # 发光层（更大更淡）
                if size >= 2:
                    glow_color = tuple(min(255, int(c * 0.5)) for c in color)
                    pygame.draw.circle(screen, glow_color, pos, size + 2)


class ParticleSystem:
    """
    粒子系统
    
    管理所有轨迹粒子和残留效果
    """
    
    def __init__(self):
        """初始化粒子系统"""
        self.trace_particles: List[TraceParticles] = []  # 轨迹粒子组
        self.max_traces = 20  # 最大同时显示的痕迹数
        
    def create_trace_from_trajectory(self, trajectory: List[Tuple[int, int]]):
        """
        从轨迹创建数字痕迹
        
        动作结束后调用此方法，轨迹会重新出现形成粒子效果
        
        Args:
            trajectory: 轨迹点列表 [(x1, y1), (x2, y2), ...]
        """
        if len(trajectory) < 3:
            return
        
        # 粒子数量根据轨迹长度决定
        particle_count = min(15, max(5, len(trajectory) // 10))
        
        trace = TraceParticles(
            trajectory=trajectory,
            particle_count=particle_count,
            trace_lifetime=180  # 3秒
        )
        
        self.trace_particles.append(trace)
        
        # 限制痕迹数量
        if len(self.trace_particles) > self.max_traces:
            self.trace_particles.pop(0)
        
        print(f"创建数字痕迹: {len(trajectory)} 点, {particle_count} 粒子")
        
    def update(self):
        """更新所有粒子"""
        for trace in self.trace_particles:
            trace.update()
        
        # 移除过期痕迹
        self.trace_particles = [t for t in self.trace_particles if t.is_alive()]
    
    def draw(self, screen: pygame.Surface):
        """
        绘制所有粒子
        
        Args:
            screen: Pygame屏幕表面
        """
        for trace in self.trace_particles:
            trace.draw(screen)
    
    def clear(self):
        """清空所有粒子"""
        self.trace_particles.clear()
    
    def get_particle_count(self) -> int:
        """获取当前粒子总数"""
        total = 0
        for trace in self.trace_particles:
            total += len(trace.particles) + len(trace.trail_particles)
        return total
    
    def get_trace_count(self) -> int:
        """获取当前痕迹数量"""
        return len(self.trace_particles)


def main():
    """
    测试函数：测试粒子系统
    
    操作：
    - 移动鼠标绘制轨迹
    - 静止 0.8秒，轨迹变成数字痕迹
    - 按 'c' 清除
    - 按 'q' 退出
    """
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Particle System - 数字痕迹测试")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    particle_system = ParticleSystem()
    
    # 模拟轨迹记录
    trajectory: List[Tuple[int, int]] = []
    
    # 静止检测
    last_pos = None
    inactive_frames = 0
    inactive_threshold = 48  # 0.8秒 @ 60fps
    
    print("=" * 50)
    print("粒子系统测试 - 数字痕迹")
    print("=" * 50)
    print("移动鼠标绘制轨迹")
    print("静止 0.8秒后，轨迹变成数字痕迹")
    print("按 'c' 清除，按 'q' 退出")
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
                    trajectory.clear()
                    print("清除所有痕迹")
        
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        current_pos = (mouse_x, mouse_y)
        
        # 检测静止
        if last_pos is not None:
            dx = current_pos[0] - last_pos[0]
            dy = current_pos[1] - last_pos[1]
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance < 5:  # 静止阈值
                inactive_frames += 1
                
                if inactive_frames >= inactive_threshold:
                    # 静止超过0.8秒，动作结束
                    if len(trajectory) >= 10:
                        # 创建数字痕迹
                        particle_system.create_trace_from_trajectory(trajectory.copy())
                        trajectory.clear()
                    inactive_frames = 0
            else:
                inactive_frames = 0
        
        # 记录轨迹
        if len(trajectory) == 0 or distance > 5:
            trajectory.append(current_pos)
            if len(trajectory) > 100:
                trajectory.pop(0)
        
        last_pos = current_pos
        
        # 更新粒子系统
        particle_system.update()
        
        # 渲染
        screen.fill((10, 10, 20))
        
        # 绘制当前轨迹（实线）
        if len(trajectory) >= 2:
            pygame.draw.lines(screen, (100, 180, 255), False, trajectory, 2)
            pygame.draw.circle(screen, (150, 220, 255), trajectory[-1], 5)
        
        # 绘制粒子系统（数字痕迹）
        particle_system.draw(screen)
        
        # 显示信息
        info_lines = [
            f"轨迹点: {len(trajectory)}",
            f"数字痕迹: {particle_system.get_trace_count()}",
            f"粒子总数: {particle_system.get_particle_count()}",
            f"静止帧: {inactive_frames}/{inactive_threshold}"
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        # 操作提示
        hint_text = "移动鼠标 | 静止0.8秒生成痕迹 | 'c' 清除 | 'q' 退出"
        hint_surface = font.render(hint_text, True, (150, 150, 150))
        screen.blit(hint_surface, (10, screen.get_height() - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("测试结束")


if __name__ == "__main__":
    main()