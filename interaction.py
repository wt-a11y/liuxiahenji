"""
交互模块

实现行为痕迹影响目标对象

流程：
动作结束 → 生成记忆碎片 → 碎片沉积 → 漂移 → 渗透 → 改变目标内部结构

影响强度根据 movement_speed 和 movement_distance 计算
不判断正面/负面影响，只表现行为产生影响

可直接运行测试：python interaction.py
"""

import math
import random
from typing import List, Dict, Optional, Tuple
import time


class InteractionManager:
    """
    交互管理器
    
    管理记忆碎片与目标对象的交互
    实现：动作结束 → 生成碎片 → 碎片渗透 → 改变目标内部结构
    """
    
    def __init__(self):
        """初始化交互管理器"""
        # 目标对象引用
        self.target: Optional[any] = None  # TargetObject
        
        # 渗透记录
        self.penetration_history: List[Dict] = []
        
    def set_target(self, target):
        """
        设置目标对象
        
        Args:
            target: TargetObject 实例
        """
        self.target = target
    
    def check_membrane_approach(self, fragment_data: Dict):
        """
        检查碎片是否靠近膜边界，触发膜的扰动（收缩）
        
        只在碎片靠近膜边界时触发扰动
        碎片进入膜内部后不再触发扰动
        
        Args:
            fragment_data: 碎片数据 {x, y, intensity, is_touching_membrane, has_penetrated_membrane, distance_to_target}
        """
        if not self.target:
            return
        
        # 检查碎片是否靠近膜边界（但还未进入内部）
        is_touching = fragment_data.get('is_touching_membrane', False)
        has_penetrated = fragment_data.get('has_penetrated_membrane', False)
        
        # 只有在碎片靠近膜且还未进入内部时才触发扰动
        if is_touching and not has_penetrated:
            fragment_x = fragment_data.get('x', 0)
            fragment_y = fragment_data.get('y', 0)
            intensity = fragment_data.get('intensity', 0.5)
            
            # 计算fragment相对于生命体中心的角度
            dx = fragment_x - self.target.x
            dy = fragment_y - self.target.y
            angle = math.atan2(dy, dx)
            
            # 在接触点添加扰动（强度与fragment强度相关）
            self.target.membrane.add_perturbation(angle, intensity=intensity)
            
            # 记录接触位置（用于内部纹理变化）
            self.target.fragment_contact_positions.append((fragment_x, fragment_y))
            if len(self.target.fragment_contact_positions) > 3:
                self.target.fragment_contact_positions.pop(0)
    
    def process_penetrations(self, penetrations: List[Dict]):
        """
        处理完成的渗透
        
        碎片缓慢融入生命体边界，进入内部后改变结构
        
        Args:
            penetrations: 完成渗透的碎片数据列表
        """
        if not self.target:
            return
        
        for penetration in penetrations:
            # 提取渗透数据
            intensity = penetration.get('intensity', 0.0)
            position = penetration.get('position', (0, 0))
            progress = penetration.get('progress', 0.0)
            
            # 计算影响值（基于渗透进度）
            impact_value = self._calculate_impact_value(intensity, progress)
            
            # 调用目标对象的 receive_impact()
            # 碎片进入内部，改变生命体的结构和形态
            source_pos = {'x': position[0], 'y': position[1]}
            self.target.receive_impact(
                value=impact_value,
                source_position=source_pos,
                impact_type='memory'
            )
            
            # 记录渗透历史
            penetration_record = {
                'time': time.time(),
                'intensity': intensity,
                'impact_value': impact_value,
                'position': position,
                'progress': progress
            }
            self.penetration_history.append(penetration_record)
            
            print(f"记忆碎片渗透进入生命体: 强度={intensity:.2f}, 影响值={impact_value:.2f}, 进度={progress:.2f}")
    
    def _calculate_impact_value(self, intensity: float, progress: float) -> float:
        """
        计算影响值
        
        Args:
            intensity: 碎片强度
            progress: 渗透进度
            
        Returns:
            影响值 (0.0 - 1.0)
        """
        # 基础影响值
        base_impact = intensity * 0.5
        
        # 渗透进度加成
        progress_bonus = progress * 0.3
        
        # 随机波动（模拟不确定性）
        random_factor = random.uniform(-0.1, 0.1)
        
        impact_value = base_impact + progress_bonus + random_factor
        
        # 限制在 0.0 - 1.0 范围内
        return min(1.0, max(0.05, impact_value))
    
    def get_penetration_count(self) -> int:
        """获取渗透历史数量"""
        return len(self.penetration_history)
    
    def clear(self):
        """清除渗透历史"""
        self.penetration_history.clear()


def main():
    """
    测试函数：测试交互系统
    
    操作：
    - 移动鼠标绘制轨迹
    - 静止 0.8秒动作结束
    - 记忆碎片生成并渗透
    - 渗透完成后影响目标对象
    
    按 'c' 清除
    按 'q' 退出
    """
    import pygame
    from target_object import TargetObject
    from behavior_analysis import BehaviorAnalyzer
    from particle_system import ParticleSystem
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Interaction Test - 记忆渗透系统")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    # 初始化模块
    target = TargetObject()
    analyzer = BehaviorAnalyzer()
    particle_system = ParticleSystem()
    interaction = InteractionManager()
    
    # 设置目标
    interaction.set_target(target)
    particle_system.set_target(target.get_position())
    
    print("=" * 50)
    print("交互系统测试 - 记忆渗透")
    print("=" * 50)
    print("移动鼠标绘制轨迹")
    print("静止 0.8秒 → 生成记忆碎片 → 沉积 → 漂移 → 渗透 → 改变目标")
    print("'c' - 清除")
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
                    particle_system.clear()
                    current_trajectory.clear()
                    print("已清除")
        
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand_pos = {"x": mouse_x, "y": mouse_y}
        
        # 记录轨迹点
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
        
        # 处理渗透
        if penetrations:
            interaction.process_penetrations(penetrations)
        
        # 更新目标对象
        target.update()
        
        # 更新目标位置（目标可能移动）
        particle_system.set_target(target.get_position())
        
        # 渲染
        screen.fill((15, 15, 25))
        
        # 绘制当前轨迹
        if len(current_trajectory) >= 2:
            pygame.draw.lines(screen, (80, 160, 220), False, current_trajectory, 2)
            if current_trajectory:
                pygame.draw.circle(screen, (120, 200, 255), current_trajectory[-1], 5)
        
        # 绘制记忆碎片
        particle_system.draw(screen)
        
        # 绘制目标对象
        target.draw(screen)
        
        # 显示信息
        structure_info = target.get_structure_info()
        info_lines = [
            f"轨迹点: {len(current_trajectory)}",
            f"记忆碎片: {particle_system.get_particle_count()}",
            f"渗透历史: {interaction.get_penetration_count()}",
            f"目标位置: ({target.x:.1f}, {target.y:.1f})",
            f"累积影响: {target.get_cumulative_influence():.2f}",
            f"影响历史: {target.get_history_length()}",
            f"节点数: {structure_info['node_count']}",
            f"连接数: {structure_info['connection_count']}",
            f"受影响的节点: {structure_info['influenced_count']}",
            f"静止: {analyzer.get_inactive_duration():.2f}s / 0.8s",
            "",
            "移动鼠标 → 静止0.8秒 → 碎片渗透 → 改变目标"
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
