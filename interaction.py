"""
交互模块

实现行为痕迹影响目标对象

5阶段状态机流程：
动作结束 → 生成记忆碎片 → 碎片沉积 → APPROACHING → CONTACT →
ABSORBING → INTEGRATING → COMPLETED → 改变目标内部结构

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
    实现：动作结束 → 生成碎片 → 吸收 → 改变目标内部结构

    5阶段状态机：
    - APPROACHING: 碎片漂浮靠近生命体
    - CONTACT: 碎片接触生命膜，短暂停留
    - ABSORBING: 碎片被生命体吞噬（边缘模糊/晶体瓦解/颜色扩散）
    - INTEGRATING: 整合过渡
    - COMPLETED: 碎片完全融入，影响继续存在
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

        根据碎片状态变化触发 TargetObject 的不同响应：
        - approaching → contact: 触发膜接触扰动（凹陷+涟漪）
        - contact → absorbing: 启动吸收响应（收缩+流动偏置）
        - absorbing 持续期间: 更新吸收进度
        - absorbing → integrating/completed: 结束吸收响应

        Args:
            fragment_data: 碎片数据 {id, x, y, intensity, state, previous_state,
                              state_changed, is_touching_membrane, ...}
        """
        if not self.target:
            return

        fragment_id = fragment_data.get('id')
        state = fragment_data.get('state', '')
        prev_state = fragment_data.get('previous_state')
        state_changed = fragment_data.get('state_changed', False)
        is_touching = fragment_data.get('is_touching_membrane', False)
        has_penetrated = fragment_data.get('has_penetrated_membrane', False)
        intensity = fragment_data.get('intensity', 0.5)
        absorption_progress = fragment_data.get('absorption_progress', 0.0)

        fragment_x = fragment_data.get('x', 0)
        fragment_y = fragment_data.get('y', 0)

        # === 触发膜接触扰动（state 变化：approaching → contact） ===
        if state_changed and state == 'contact' and prev_state == 'approaching':
            dx = fragment_x - self.target.x
            dy = fragment_y - self.target.y
            angle = math.atan2(dy, dx)
            self.target.on_fragment_contact(fragment_id, angle, intensity)

        # === 启动吸收响应（state 变化：contact → absorbing） ===
        elif state_changed and state == 'absorbing' and prev_state == 'contact':
            dx = fragment_x - self.target.x
            dy = fragment_y - self.target.y
            angle = math.atan2(dy, dx)
            self.target.on_absorption_start(fragment_id, angle, intensity)

        # === 吸收过程中：每帧更新进度 ===
        elif state == 'absorbing' and fragment_id is not None:
            self.target.on_absorption_progress(fragment_id, absorption_progress)

        # === 结束吸收响应（state 变化：absorbing → integrating 或 completed） ===
        elif state_changed and prev_state == 'absorbing' and state in ('integrating', 'completed'):
            self.target.on_absorption_complete(fragment_id)

        # === 兼容旧 API：approaching 状态靠近膜边界时触发扰动（保留旧有 membrane.add_perturbation 行为） ===
        is_touching = fragment_data.get('is_touching_membrane', False)
        has_penetrated = fragment_data.get('has_penetrated_membrane', False)

        # 只有在碎片靠近膜且还未进入内部时才触发扰动
        if is_touching and not has_penetrated:
            fragment_x = fragment_data.get('x', 0)
            fragment_y = fragment_data.get('y', 0)
            intensity = fragment_data.get('intensity', 0.5)

            dx = fragment_x - self.target.x
            dy = fragment_y - self.target.y
            angle = math.atan2(dy, dx)

            self.target.membrane.add_perturbation(angle, intensity=intensity)

            self.target.fragment_contact_positions.append((fragment_x, fragment_y))
            if len(self.target.fragment_contact_positions) > 3:
                self.target.fragment_contact_positions.pop(0)

    def process_penetrations(self, penetrations: List[Dict]):
        """
        处理完成的吸收（COMPLETED 状态）

        碎片完全融入生命体后，改变生命体的内部结构

        新状态机：碎片在完成 absorbing + integrating 后返回，
        携带 intensity / position / progress / diffusion_intensity 等数据。

        Args:
            penetrations: 完成吸收的碎片数据列表
        """
        if not self.target:
            return

        for penetration in penetrations:
            intensity = penetration.get('intensity', 0.0)
            position = penetration.get('position', (0, 0))
            progress = penetration.get('progress', 1.0)
            diffusion = penetration.get('diffusion_intensity', 1.0)

            # 影响值 = 强度 × 进度 × 扩散质量
            impact_value = self._calculate_impact_value(
                intensity, progress, diffusion
            )

            source_pos = {'x': position[0], 'y': position[1]}
            self.target.receive_impact(
                value=impact_value,
                source_position=source_pos,
                impact_type='memory'
            )

            penetration_record = {
                'time': time.time(),
                'intensity': intensity,
                'impact_value': impact_value,
                'position': position,
                'progress': progress,
                'diffusion_intensity': diffusion,
            }
            self.penetration_history.append(penetration_record)

            print(f"记忆碎片被吸收: 强度={intensity:.2f}, 影响值={impact_value:.2f}, "
                  f"进度={progress:.2f}, 扩散={diffusion:.2f}")

    def _calculate_impact_value(self, intensity: float, progress: float,
                                 diffusion: float = 1.0) -> float:
        """
        计算影响值

        5阶段状态机下，影响值综合考虑：
        - 碎片原始强度
        - 吸收进度（progress=1.0 表示完全吸收）
        - 颜色扩散质量（diffusion=1.0 表示颜色完全扩散进入生命体）

        Args:
            intensity: 碎片强度
            progress: 吸收进度 (0.0 - 1.0)
            diffusion: 颜色扩散强度 (0.0 - 1.0)

        Returns:
            影响值 (0.0 - 1.0)
        """
        # 基础影响值
        base_impact = intensity * 0.5

        # 吸收进度加成（最高 0.3）
        progress_bonus = progress * 0.3

        # 扩散质量加成（最高 0.2） - 颜色扩散越充分，影响越深入
        diffusion_bonus = diffusion * 0.2

        # 随机波动
        random_factor = random.uniform(-0.1, 0.1)

        impact_value = base_impact + progress_bonus + diffusion_bonus + random_factor

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
