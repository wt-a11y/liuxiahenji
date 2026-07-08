"""
目标对象模块

创建一个抽象对象
代表受到行为影响的另一个存在

可直接运行测试：python target_object.py
"""

import pygame
import math
import random
from typing import Tuple, Dict, List


class InternalParticle:
    """
    内部粒子
    
    构成目标对象形态的小粒子
    让对象看起来有机、有生命
    """
    
    def __init__(self, angle: float, distance: float):
        """
        初始化内部粒子
        
        Args:
            angle: 相对中心的角度
            distance: 相对中心的距离
        """
        self.base_angle = angle
        self.base_distance = distance
        
        # 当前状态
        self.angle = angle
        self.distance = distance
        
        # 动态参数
        self.oscillation_offset = random.uniform(0, 2 * math.pi)
        self.oscillation_speed = random.uniform(0.02, 0.05)
        
        # 大小
        self.size = random.uniform(2, 4)
        
    def update(self, impact_intensity: float = 0.0):
        """
        更新粒子位置
        
        Args:
            impact_intensity: 受到影响的强度 (0.0 - 1.0)
        """
        # 振荡运动
        self.oscillation_offset += self.oscillation_speed
        
        # 角度和距离的微小变化
        angle_variation = math.sin(self.oscillation_offset) * 0.1
        distance_variation = math.sin(self.oscillation_offset * 2) * 3
        
        # 受影响时的额外变化
        if impact_intensity > 0:
            angle_variation += random.uniform(-0.2, 0.2) * impact_intensity
            distance_variation += random.uniform(-5, 5) * impact_intensity
        
        self.angle = self.base_angle + angle_variation
        self.distance = self.base_distance + distance_variation
        
    def get_position(self, center_x: float, center_y: float) -> Tuple[float, float]:
        """
        计算粒子实际位置
        
        Args:
            center_x, center_y: 中心位置
            
        Returns:
            (x, y) 粒子位置
        """
        x = center_x + math.cos(self.angle) * self.distance
        y = center_y + math.sin(self.angle) * self.distance
        return (x, y)


class TargetObject:
    """
    目标对象类
    
    一个抽象的、有机的存在
    受到痕迹的影响而产生变化
    
    属性：
    - position: 位置
    - size: 大小
    - brightness: 亮度
    - state: 状态 (idle, impacted, recovering)
    """
    
    def __init__(self, x: float = 640, y: float = 360):
        """
        初始化目标对象
        
        Args:
            x, y: 初始位置（默认屏幕中心）
        """
        # 基本属性
        self.position = {'x': x, 'y': y}
        self.size = 40.0          # 基础大小
        self.brightness = 0.6     # 亮度 (0.0 - 1.0)
        self.state = 'idle'       # 状态
        
        # 物理属性
        self.vx = 0.0             # 速度 x
        self.vy = 0.0             # 速度 y
        self.target_x = x         # 目标位置 x
        self.target_y = y         # 目标位置 y
        
        # 影响相关
        self.impact_value = 0.0   # 当前影响值
        self.impact_decay = 0.02  # 影响衰减速度
        
        # 视觉参数
        self.pulse_phase = 0      # 脉动相位
        self.base_color = (180, 120, 160)  # 基础颜色（淡紫色）
        
        # 内部粒子（构成有机形态）
        self.internal_particles: List[InternalParticle] = []
        self._create_internal_particles()
        
        # 外部粒子（受影响时产生）
        self.external_particles: List[Dict] = []
        
    def _create_internal_particles(self):
        """创建内部粒子结构"""
        num_particles = 25
        
        for i in range(num_particles):
            angle = (i / num_particles) * 2 * math.pi
            distance = random.uniform(15, 35)
            
            particle = InternalParticle(angle, distance)
            self.internal_particles.append(particle)
    
    def receive_impact(self, value: float, 
                       source_position: Dict = None,
                       impact_type: str = 'attract'):
        """
        接受痕迹影响
        
        Args:
            value: 影响强度 (0.0 - 1.0)
            source_position: 痕迹来源位置 {'x': float, 'y': float}
            impact_type: 影响类型 ('attract', 'repel', 'disturb')
        """
        self.impact_value = min(1.0, max(0.0, value))
        self.state = 'impacted'
        
        # 根据来源位置计算影响方向
        if source_position is not None:
            dx = source_position['x'] - self.position['x']
            dy = source_position['y'] - self.position['y']
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance > 0:
                # 影响力随距离衰减
                force = value * 30 / (distance + 50)
                
                # 标准化方向
                nx = dx / distance
                ny = dy / distance
                
                if impact_type == 'attract':
                    # 吸引：向来源移动
                    self.vx += nx * force
                    self.vy += ny * force
                elif impact_type == 'repel':
                    # 排斥：远离来源
                    self.vx -= nx * force
                    self.vy -= ny * force
                else:
                    # 扰动：随机方向
                    self.vx += random.uniform(-force, force)
                    self.vy += random.uniform(-force, force)
        
        # 产生外部粒子（视觉反馈）
        self._spawn_external_particles(int(value * 10))
        
        # 大小和亮度受影响
        self.size += value * 5
        self.brightness = min(1.0, self.brightness + value * 0.3)
        
        print(f"目标对象受影响: value={value:.2f}, type={impact_type}, state={self.state}")
        
    def _spawn_external_particles(self, count: int):
        """
        产生外部粒子（受影响时的视觉效果）
        
        Args:
            count: 粒子数量
        """
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            
            particle = {
                'x': self.position['x'],
                'y': self.position['y'],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': random.randint(20, 40),
                'age': 0,
                'size': random.uniform(2, 4),
                'color': (
                    random.randint(150, 200),
                    random.randint(100, 150),
                    random.randint(180, 230)
                )
            }
            self.external_particles.append(particle)
    
    def update(self):
        """更新目标对象状态"""
        # 更新脉动相位
        self.pulse_phase += 0.03
        
        # 应用速度
        self.position['x'] += self.vx
        self.position['y'] += self.vy
        
        # 速度衰减
        self.vx *= 0.92
        self.vy *= 0.92
        
        # 边界软约束
        width, height = 1280, 720
        margin = 80
        
        if self.position['x'] < margin:
            self.vx += 0.5
        elif self.position['x'] > width - margin:
            self.vx -= 0.5
            
        if self.position['y'] < margin:
            self.vy += 0.5
        elif self.position['y'] > height - margin:
            self.vy -= 0.5
        
        # 影响值衰减
        if self.impact_value > 0:
            self.impact_value -= self.impact_decay
            
            if self.impact_value <= 0:
                self.impact_value = 0
                self.state = 'recovering'
        
        # 恢复状态
        if self.state == 'recovering':
            # 大小和亮度逐渐恢复
            self.size = max(40.0, self.size - 0.5)
            self.brightness = max(0.6, self.brightness - 0.01)
            
            if self.size <= 40.0 and self.brightness <= 0.6:
                self.state = 'idle'
        
        # 更新内部粒子
        for particle in self.internal_particles:
            particle.update(self.impact_value)
        
        # 更新外部粒子
        for particle in self.external_particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vx'] *= 0.95
            particle['vy'] *= 0.95
            particle['age'] += 1
        
        # 移除死亡的外部粒子
        self.external_particles = [
            p for p in self.external_particles 
            if p['age'] < p['lifetime']
        ]
    
    def get_current_size(self) -> float:
        """
        获取当前大小（包含脉动效果）
        
        Returns:
            当前大小
        """
        # 脉动效果
        pulse = math.sin(self.pulse_phase) * 3
        
        # 影响效果
        impact_effect = self.impact_value * 8
        
        return self.size + pulse + impact_effect
    
    def get_current_color(self) -> Tuple[int, int, int]:
        """
        获取当前颜色（根据状态变化）
        
        Returns:
            RGB 颜色值
        """
        # 根据状态调整颜色
        if self.state == 'impacted':
            # 受影响时：更亮、更蓝
            r = int(self.base_color[0] * 0.7 + 60 * self.brightness)
            g = int(self.base_color[1] * 0.7 + 100 * self.brightness)
            b = int(self.base_color[2] * 0.5 + 150 * self.brightness)
        elif self.state == 'recovering':
            # 恢复时：淡紫色
            r = int(self.base_color[0] * self.brightness)
            g = int(self.base_color[1] * self.brightness)
            b = int(self.base_color[2] * self.brightness)
        else:
            # 静止时：暗淡
            r = int(self.base_color[0] * 0.8)
            g = int(self.base_color[1] * 0.8)
            b = int(self.base_color[2] * 0.8)
        
        return (min(255, r), min(255, g), min(255, b))
    
    def get_position_tuple(self) -> Tuple[int, int]:
        """获取位置元组"""
        return (int(self.position['x']), int(self.position['y']))
    
    def reset_position(self, x: float = 640, y: float = 360):
        """
        重置位置
        
        Args:
            x, y: 新位置（默认屏幕中心）
        """
        self.position['x'] = x
        self.position['y'] = y
        self.vx = 0.0
        self.vy = 0.0
        self.state = 'idle'
        self.impact_value = 0.0
        self.size = 40.0
        self.brightness = 0.6
    
    def draw(self, screen: pygame.Surface):
        """
        绘制目标对象
        
        Args:
            screen: Pygame 屏幕表面
        """
        x = int(self.position['x'])
        y = int(self.position['y'])
        
        color = self.get_current_color()
        size = self.get_current_size()
        
        # 绘制发光效果（多层）
        for i in range(3, 0, -1):
            glow_radius = size + i * 10
            glow_intensity = 0.3 / i
            glow_color = tuple(int(c * glow_intensity) for c in color)
            pygame.draw.circle(screen, glow_color, (x, y), int(glow_radius))
        
        # 绘制外部粒子
        for particle in self.external_particles:
            alpha = 1.0 - (particle['age'] / particle['lifetime'])
            p_size = max(1, int(particle['size'] * alpha))
            p_color = tuple(int(c * (0.4 + 0.6 * alpha)) for c in particle['color'])
            pygame.draw.circle(
                screen, p_color,
                (int(particle['x']), int(particle['y'])),
                p_size
            )
        
        # 绘制内部粒子
        for internal_p in self.internal_particles:
            px, py = internal_p.get_position(self.position['x'], self.position['y'])
            
            # 内部粒子颜色（比主体亮）
            p_color = tuple(min(255, c + 50) for c in color)
            pygame.draw.circle(screen, p_color, (int(px), int(py)), int(internal_p.size))
        
        # 绘制主体
        pygame.draw.circle(screen, color, (x, y), int(size))
        
        # 绘制中心点（白色核心）
        core_size = max(3, int(5 * self.brightness))
        pygame.draw.circle(screen, (255, 255, 255), (x, y), core_size)
        
        # 状态指示（外轮廓）
        if self.state != 'idle':
            outline_size = size + 8
            pygame.draw.circle(screen, color, (x, y), int(outline_size), 2)


def main():
    """
    测试函数：测试目标对象
    
    操作：
    - 'a' 吸引效果
    - 'r' 排斥效果
    - 'd' 扰动效果
    - 's' 重置位置
    - 'q' 退出
    - 鼠标点击在点击位置产生效果
    """
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Target Object Test - 抽象存在")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    target = TargetObject()
    
    print("=" * 50)
    print("目标对象测试 - 抽象存在")
    print("=" * 50)
    print("'a' - 吸引效果")
    print("'r' - 排斥效果")
    print("'d' - 扰动效果")
    print("'s' - 重置位置")
    print("鼠标点击 - 在点击位置产生效果")
    print("'q' - 退出")
    print("=" * 50)
    
    impact_type = "attract"
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_a:
                    impact_type = "attract"
                    print("选择: 吸引效果")
                elif event.key == pygame.K_r:
                    impact_type = "repel"
                    print("选择: 排斥效果")
                elif event.key == pygame.K_d:
                    impact_type = "disturb"
                    print("选择: 扰动效果")
                elif event.key == pygame.K_s:
                    target.reset_position()
                    print("位置已重置")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 在点击位置产生效果
                mx, my = event.pos
                source = {'x': mx, 'y': my}
                target.receive_impact(0.8, source, impact_type)
        
        # 更新目标对象
        target.update()
        
        # 渲染
        screen.fill((15, 15, 25))  # 深色背景
        
        # 绘制目标对象
        target.draw(screen)
        
        # 显示信息
        info_lines = [
            f"Position: ({target.position['x']:.1f}, {target.position['y']:.1f})",
            f"Size: {target.size:.1f}",
            f"Brightness: {target.brightness:.2f}",
            f"State: {target.state}",
            f"Impact value: {target.impact_value:.2f}",
            f"Effect type: {impact_type}",
            "",
            "Keys: 'a'=attract, 'r'=repel, 'd'=disturb, 's'=reset, 'q'=quit"
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