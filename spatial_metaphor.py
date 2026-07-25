"""
空间隐喻模块

实现两个空间隐喻：
- 安全距离圈：生命体周围的"个人空间"
- 引力场可视化：生命体对玩家手的吸引力

设计意图：让"距离"和"关系亲疏"变得可感知
"""

import pygame
import math
from typing import Tuple, Optional


class PersonalSpaceField:
    """
    个人空间场
    
    生命体周围有不同层次的"个人空间"：
    - 内圈（亲密距离）：< 80px
    - 中圈（社交距离）：80-200px
    - 外圈（公共距离）：> 200px
    
    不同的接近方式（速度、轨迹）会产生不同的反应
    """
    
    # 距离阈值（单位：屏幕像素，1280x720屏幕）
    INTIMATE_DISTANCE = 113     # 亲密距离（红圈边界，缩小为原 3/4）
    SOCIAL_DISTANCE = 210       # 社交距离（蓝圈边界，缩小为原 3/4）
    PERSONAL_RADIUS = 220       # 个人空间半径
    
    def __init__(self, target_x: float, target_y: float):
        self.center_x = target_x
        self.center_y = target_y
        self.pulse_phase = 0.0     # 脉冲动画
        self.breath_intensity = 0.3  # 呼吸强度
        
        # 边界状态
        self.boundary_intensity = 0.0  # 边界被侵入的程度
        self.boundary_color = (100, 180, 200)
        
        # 警告等级（0-2）
        self.warning_level = 0
        
    def update(self, dt: float, target_x: float, target_y: float,
               hand_x: Optional[float] = None, hand_y: Optional[float] = None,
               hand_speed: float = 0.0):
        """
        更新个人空间状态
        
        Args:
            dt: 时间增量
            target_x, target_y: 生命体位置
            hand_x, hand_y: 手部位置（None表示无手）
            hand_speed: 手部移动速度
        """
        self.center_x = target_x
        self.center_y = target_y
        self.pulse_phase += dt * 0.5  # 缓慢脉冲
        
        self.warning_level = 0
        self.boundary_intensity = 0.0
        
        if hand_x is not None and hand_y is not None:
            dx = hand_x - target_x
            dy = hand_y - target_y
            distance = math.hypot(dx, dy)
            
            if distance < self.INTIMATE_DISTANCE:
                # 进入亲密距离
                self.warning_level = 2
                self.boundary_intensity = 1.0 - distance / self.INTIMATE_DISTANCE
                if hand_speed > 5.0:
                    # 快速侵入亲密距离 → 红色警告
                    self.boundary_color = (220, 80, 80)
                else:
                    # 缓慢靠近 → 暖色
                    self.boundary_color = (220, 180, 130)
            elif distance < self.SOCIAL_DISTANCE:
                # 在社交距离内
                self.warning_level = 1
                self.boundary_intensity = 1.0 - (distance - self.INTIMATE_DISTANCE) / (
                    self.SOCIAL_DISTANCE - self.INTIMATE_DISTANCE
                )
                self.boundary_color = (180, 200, 220)
            else:
                # 在公共距离外
                self.warning_level = 0
                self.boundary_intensity = 0.0
                self.boundary_color = (120, 150, 170)
        else:
            # 无手 → 边界柔和
            self.boundary_color = (100, 150, 180)
    
    def draw(self, screen: pygame.Surface):
        """
        绘制个人空间边界
        
        使用虚线圆 + 呼吸效果
        """
        cx, cy = int(self.center_x), int(self.center_y)
        
        # 社交距离圈（最外）
        self._draw_dashed_circle(
            screen, cx, cy, self.SOCIAL_DISTANCE,
            (*self.boundary_color, 40),
            dash_length=12, gap_length=8
        )
        
        # 亲密距离圈（内）
        if self.warning_level > 0:
            inner_color = (*self.boundary_color, int(120 * (0.5 + self.boundary_intensity * 0.5)))
            self._draw_dashed_circle(
                screen, cx, cy, self.INTIMATE_DISTANCE,
                inner_color,
                dash_length=8, gap_length=4
            )
        
        # 警告光环（被侵入时显示）
        if self.warning_level == 2:
            warn_color = (220, 80, 80, int(150 + 100 * math.sin(self.pulse_phase * 4)))
            warn_radius = self.INTIMATE_DISTANCE + 15 + int(5 * math.sin(self.pulse_phase * 4))
            warn_surf = pygame.Surface((warn_radius * 2, warn_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(warn_surf, warn_color, (warn_radius, warn_radius), warn_radius, 2)
            screen.blit(warn_surf, (cx - warn_radius, cy - warn_radius))
    
    def _draw_dashed_circle(self, screen, cx, cy, radius, color, 
                            dash_length=10, gap_length=5, width=1):
        """绘制虚线圆"""
        # 采样圆上的点
        circumference = 2 * math.pi * radius
        num_dashes = int(circumference / (dash_length + gap_length))
        
        for i in range(num_dashes):
            start_angle = (i * (dash_length + gap_length)) / radius
            end_angle = start_angle + dash_length / radius
            
            # 计算起点和终点
            x1 = cx + radius * math.cos(start_angle)
            y1 = cy + radius * math.sin(start_angle)
            x2 = cx + radius * math.cos(end_angle)
            y2 = cy + radius * math.sin(end_angle)
            
            if len(color) == 4:
                line_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                pygame.draw.line(line_surf, color, (int(x1), int(y1)), (int(x2), int(y2)), width)
                screen.blit(line_surf, (0, 0))
            else:
                pygame.draw.line(screen, color, (int(x1), int(y1)), (int(x2), int(y2)), width)


class GravityField:
    """
    引力场可视化
    
    象征关系中的相互吸引：
    - 健康关系 → 引力柔和、双向
    - 受损关系 → 引力紊乱、单向
    - 死亡关系 → 引力消失
    """
    
    def __init__(self):
        self.field_points = []  # 场中的粒子
        self.field_strength = 0.5  # 场强度
        self.field_type = "calm"  # calm / turbulent / dead
        
    def update(self, dt: float, target_x: float, target_y: float,
               relationship_quality: float, hand_x: Optional[float] = None,
               hand_y: Optional[float] = None):
        """
        更新引力场
        
        Args:
            dt: 时间增量
            target_x, target_y: 生命体位置
            relationship_quality: 关系质量 [-1, 1]
            hand_x, hand_y: 手部位置
        """
        # 根据关系质量决定场类型
        if relationship_quality > 0.3:
            self.field_type = "calm"
            self.field_strength = 0.3 + relationship_quality * 0.4
        elif relationship_quality > -0.3:
            self.field_type = "neutral"
            self.field_strength = 0.2
        elif relationship_quality > -0.7:
            self.field_type = "turbulent"
            self.field_strength = 0.4 + abs(relationship_quality) * 0.3
        else:
            self.field_type = "dead"
            self.field_strength = 0.05
        
        # 更新粒子
        self._update_particles(dt, target_x, target_y, hand_x, hand_y)
    
    def _update_particles(self, dt: float, target_x: float, target_y: float,
                          hand_x, hand_y):
        """更新场粒子"""
        # 限制粒子数量
        max_particles = 20
        if len(self.field_points) > max_particles:
            self.field_points = self.field_points[-max_particles:]
        
        # 偶尔生成新粒子
        import random
        if random.random() < self.field_strength * 0.3:
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(60, 120)
            self.field_points.append({
                'x': target_x + r * math.cos(angle),
                'y': target_y + r * math.sin(angle),
                'angle': angle,
                'radius': r,
                'life': 1.0,
                'drift': random.uniform(-0.5, 0.5),
            })
        
        # 更新现有粒子
        for p in self.field_points:
            p['life'] -= dt * 0.3
            
            if self.field_type == "calm":
                # 顺时针缓慢漂移
                p['angle'] += dt * 0.3
            elif self.field_type == "turbulent":
                # 紊乱运动
                p['angle'] += dt * p['drift'] * 3
                p['radius'] += math.sin(p['angle'] * 5) * 2
            elif self.field_type == "dead":
                # 静止并衰减
                p['life'] -= dt * 0.2
            
            # 更新位置
            p['x'] = target_x + p['radius'] * math.cos(p['angle'])
            p['y'] = target_y + p['radius'] * math.sin(p['angle'])
        
        # 清除死亡粒子
        self.field_points = [p for p in self.field_points if p['life'] > 0]
    
    def draw(self, screen: pygame.Surface):
        """绘制引力场粒子"""
        if self.field_strength < 0.05:
            return
        
        color_map = {
            "calm": (180, 220, 200),
            "neutral": (150, 150, 160),
            "turbulent": (200, 100, 120),
            "dead": (80, 80, 90),
        }
        color = color_map.get(self.field_type, (150, 150, 150))
        
        for p in self.field_points:
            alpha = int(80 * p['life'] * self.field_strength)
            if alpha < 5:
                continue
            
            r = int(3 * p['life'])
            if r < 1:
                continue
            
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (r, r), r)
            screen.blit(surf, (int(p['x']) - r, int(p['y']) - r))


class StatusBar:
    """
    状态栏UI
    
    显示在屏幕底部，替代左上角的技术数据
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bar_height = 50
        self.y_offset = screen_height - self.bar_height
    
    def draw(self, screen: pygame.Surface, font, 
             emotional_state_desc: str,
             relationship_quality: float,
             cumulative_care: float, cumulative_harm: float,
             warning_active: bool = False, warning_message: str = ""):
        """
        绘制底部状态栏
        
        Args:
            screen: 主屏幕
            font: 字体
            emotional_state_desc: 情感状态描述
            relationship_quality: 关系质量 [-1, 1]
            cumulative_care, cumulative_harm: 累积数据
            warning_active: 是否显示预警
            warning_message: 预警消息
        """
        # 背景
        bar_rect = pygame.Rect(0, self.y_offset, self.screen_width, self.bar_height)
        bar_surf = pygame.Surface((self.screen_width, self.bar_height), pygame.SRCALPHA)
        bar_surf.fill((15, 12, 22, 220))
        screen.blit(bar_surf, (0, self.y_offset))
        
        # 顶部分割线
        pygame.draw.line(screen, (60, 50, 40), 
                         (0, self.y_offset), 
                         (self.screen_width, self.y_offset), 2)
        
        # 左侧：情感状态
        state_color = self._get_state_color(emotional_state_desc)
        state_text = font.render(f"生命体状态: {emotional_state_desc}", True, state_color)
        screen.blit(state_text, (20, self.y_offset + 15))
        
        # 中部：关系条
        rel_label = font.render("当前关系:", True, (180, 180, 190))
        screen.blit(rel_label, (280, self.y_offset + 15))
        
        bar_x = 400
        bar_w = 200
        bar_y = self.y_offset + 22
        
        # 背景条
        pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, 8), border_radius=4)
        
        # 关系指示
        center_x = bar_x + bar_w // 2
        if relationship_quality >= 0:
            fill_w = int(bar_w * 0.5 * relationship_quality)
            pygame.draw.rect(screen, (180, 220, 150), 
                             (center_x, bar_y, fill_w, 8), border_radius=4)
        else:
            fill_w = int(bar_w * 0.5 * abs(relationship_quality))
            pygame.draw.rect(screen, (220, 120, 100), 
                             (center_x - fill_w, bar_y, fill_w, 8), border_radius=4)
        
        # 中线
        pygame.draw.line(screen, (150, 150, 160),
                         (center_x, bar_y - 2), (center_x, bar_y + 10), 1)
        
        # 右侧：累积数据
        care_text = font.render(f"治愈 █ {cumulative_care:.1f}", True, (180, 220, 150))
        harm_text = font.render(f"伤害 █ {cumulative_harm:.1f}", True, (220, 120, 100))
        screen.blit(care_text, (self.screen_width - 320, self.y_offset + 15))
        screen.blit(harm_text, (self.screen_width - 160, self.y_offset + 15))
        
        # 预警提示（顶部）
        if warning_active and warning_message:
            warn_surf = font.render(f"⚠ {warning_message}", True, (255, 180, 100))
            warn_rect = warn_surf.get_rect(center=(self.screen_width // 2, 30))
            
            # 警告背景
            warn_bg = pygame.Surface((warn_rect.width + 40, warn_rect.height + 16), pygame.SRCALPHA)
            warn_bg.fill((60, 30, 20, 200))
            pygame.draw.rect(warn_bg, (255, 180, 100, 150), 
                             (0, 0, warn_rect.width + 40, warn_rect.height + 16), 2)
            screen.blit(warn_bg, (warn_rect.x - 20, warn_rect.y - 8))
            screen.blit(warn_surf, warn_rect)
    
    def _get_state_color(self, state_desc: str) -> Tuple[int, int, int]:
        """根据状态描述获取颜色"""
        color_map = {
            "平静": (150, 200, 180),
            "警觉": (255, 180, 100),
            "退缩": (130, 130, 180),
            "敞开": (255, 220, 150),
            "被忽视": (100, 100, 120),
        }
        return color_map.get(state_desc, (200, 200, 200))


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("空间隐喻模块测试")
    print("=" * 50)
    
    print("\n该模块提供：")
    print("1. PersonalSpaceField - 个人空间边界")
    print("2. GravityField - 引力场可视化")
    print("3. StatusBar - 状态栏UI")
    print("\n" + "=" * 50)
