"""
行为分析模块

分析手部动作数据
判断动作何时结束
不进行情绪分析，只分析运动数据

可直接运行测试：python behavior_analysis.py
"""

from typing import List, Tuple, Dict, Optional
import math
import time


class ActionData:
    """
    动作数据类
    
    描述一次手部动作的运动数据
    """
    
    def __init__(self):
        self.speed: float = 0.0          # 当前速度（像素/帧）
        self.distance: float = 0.0       # 总移动距离（像素）
        self.duration: float = 0.0       # 持续时间（秒）
        self.trajectory: List[Tuple[int, int]] = []  # 轨迹点列表
        
    def to_dict(self) -> Dict:
        """
        输出为字典格式
        
        Returns:
            {"speed": float, "distance": float, "duration": float, "trajectory": list}
        """
        return {
            "speed": self.speed,
            "distance": self.distance,
            "duration": self.duration,
            "trajectory": self.trajectory.copy()
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"ActionData(\n"
            f"  speed={self.speed:.2f} px/frame,\n"
            f"  distance={self.distance:.2f} px,\n"
            f"  duration={self.duration:.2f} s,\n"
            f"  trajectory_points={len(self.trajectory)}\n"
            f")"
        )


class BehaviorAnalyzer:
    """
    行为分析器
    
    判断手部动作何时结束
    规则：速度低于阈值并持续0.8秒 → 动作结束
    """
    
    def __init__(self):
        """初始化行为分析器"""
        # 动作结束判断参数
        self.speed_threshold = 5.0              # 速度阈值（像素/帧），低于此认为静止
        self.inactive_duration_threshold = 0.8   # 静止持续时间阈值（秒）
        
        # 内部状态
        self.inactive_start_time: Optional[float] = None  # 静止开始时间
        self.is_action_ended = False                  # 动作是否已结束
        
        # 轨迹记录（带时间戳）
        self.trajectory_with_time: List[Tuple[int, int, float]] = []
        
        # 当前动作数据
        self.current_action = ActionData()
        
        # 历史动作列表
        self.completed_actions: List[ActionData] = []
        
    def update(self, hand_position: Optional[Dict[str, int]]) -> Optional[ActionData]:
        """
        更新分析器状态
        
        Args:
            hand_position: 手部位置 {"x": int, "y": int} 或 None
            
        Returns:
            如果动作结束，返回 ActionData；否则返回 None
        """
        current_time = time.time()
        
        # 处理手消失的情况
        if hand_position is None:
            if self.trajectory_with_time:
                # 手消失，认为动作结束
                return self._finalize_action()
            return None
        
        # 提取位置
        pos = (hand_position["x"], hand_position["y"])
        
        # 添加到轨迹
        self.trajectory_with_time.append((pos[0], pos[1], current_time))
        
        # 计算当前速度
        speed = self._calculate_current_speed()
        self.current_action.speed = speed
        
        # 判断动作是否结束
        action_ended = self._check_action_end(speed, current_time)
        
        if action_ended:
            return self._finalize_action()
        
        return None
    
    def _calculate_current_speed(self) -> float:
        """
        计算当前速度
        
        Returns:
            当前速度（像素/帧）
        """
        if len(self.trajectory_with_time) < 2:
            return 0.0
        
        # 使用最近几帧计算平均速度，更稳定
        recent_points = self.trajectory_with_time[-5:]  # 最近5帧
        
        total_dist = 0.0
        for i in range(1, len(recent_points)):
            dx = recent_points[i][0] - recent_points[i-1][0]
            dy = recent_points[i][1] - recent_points[i-1][1]
            total_dist += math.sqrt(dx ** 2 + dy ** 2)
        
        # 平均速度（像素/帧）
        avg_speed = total_dist / (len(recent_points) - 1) if len(recent_points) > 1 else 0.0
        
        return avg_speed
    
    def _check_action_end(self, speed: float, current_time: float) -> bool:
        """
        检查动作是否结束
        
        规则：速度低于阈值并持续0.8秒
        
        Args:
            speed: 当前速度
            current_time: 当前时间
            
        Returns:
            True 如果动作结束
        """
        if speed < self.speed_threshold:
            # 速度低于阈值
            if self.inactive_start_time is None:
                # 开始静止
                self.inactive_start_time = current_time
                print(f"开始静止: speed={speed:.2f}")
            else:
                # 检查静止持续时间
                inactive_duration = current_time - self.inactive_start_time
                print(f"静止持续时间: {inactive_duration:.2f}s (阈值: {self.inactive_duration_threshold}s)")
                
                if inactive_duration >= self.inactive_duration_threshold:
                    # 静止超过0.8秒，动作结束
                    self.is_action_ended = True
                    return True
        else:
            # 速度高于阈值，重置静止状态
            if self.inactive_start_time is not None:
                print(f"静止中断: speed={speed:.2f} > {self.speed_threshold}")
            self.inactive_start_time = None
            self.is_action_ended = False
        
        return False
    
    def _finalize_action(self) -> ActionData:
        """
        完成动作，计算最终数据
        
        Returns:
            ActionData 对象
        """
        action = ActionData()
        
        if not self.trajectory_with_time:
            return action
        
        # 计算轨迹数据
        trajectory = [(p[0], p[1]) for p in self.trajectory_with_time]
        action.trajectory = trajectory
        
        # 计算总距离
        total_distance = 0.0
        for i in range(1, len(trajectory)):
            dx = trajectory[i][0] - trajectory[i-1][0]
            dy = trajectory[i][1] - trajectory[i-1][1]
            total_distance += math.sqrt(dx ** 2 + dy ** 2)
        action.distance = total_distance
        
        # 计算持续时间
        start_time = self.trajectory_with_time[0][2]
        end_time = self.trajectory_with_time[-1][2]
        action.duration = end_time - start_time
        
        # 计算平均速度
        if action.duration > 0:
            action.speed = total_distance / (action.duration * 60)  # 转换为像素/帧（假设60fps）
        else:
            action.speed = 0.0
        
        # 保存到历史
        self.completed_actions.append(action)
        
        # 重置状态
        self.trajectory_with_time.clear()
        self.inactive_start_time = None
        self.is_action_ended = False
        
        print(f"动作结束: {action}")
        
        return action
    
    def analyze(self, trajectory: List[Tuple[int, int]]) -> Optional[ActionData]:
        """
        分析轨迹（兼容旧接口）
        
        Args:
            trajectory: 轨迹点列表
            
        Returns:
            ActionData 对象
        """
        if len(trajectory) < 2:
            return None
        
        action = ActionData()
        action.trajectory = trajectory.copy()
        
        # 计算总距离
        total_distance = 0.0
        for i in range(1, len(trajectory)):
            dx = trajectory[i][0] - trajectory[i-1][0]
            dy = trajectory[i][1] - trajectory[i-1][1]
            total_distance += math.sqrt(dx ** 2 + dy ** 2)
        action.distance = total_distance
        
        # 持续时间（帧数转换为秒，假设60fps）
        action.duration = len(trajectory) / 60.0
        
        # 平均速度
        if len(trajectory) > 1:
            action.speed = total_distance / (len(trajectory) - 1)
        
        return action
    
    def get_current_action(self) -> ActionData:
        """获取当前正在进行的动作数据"""
        return self.current_action
    
    def get_completed_actions(self) -> List[ActionData]:
        """获取已完成的历史动作列表"""
        return self.completed_actions
    
    def clear(self):
        """清除所有状态和数据"""
        self.trajectory_with_time.clear()
        self.inactive_start_time = None
        self.is_action_ended = False
        self.current_action = ActionData()
        self.completed_actions.clear()
    
    def is_inactive(self) -> bool:
        """判断当前是否静止"""
        return self.inactive_start_time is not None
    
    def get_inactive_duration(self) -> float:
        """获取当前静止持续时间"""
        if self.inactive_start_time is None:
            return 0.0
        return time.time() - self.inactive_start_time


def main():
    """
    测试函数：使用鼠标模拟手部移动测试动作结束判断
    
    按 'q' 键退出
    """
    import pygame
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Behavior Analysis Test - 动作结束判断")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    analyzer = BehaviorAnalyzer()
    
    print("=" * 50)
    print("行为分析器测试")
    print("=" * 50)
    print("移动鼠标模拟手部动作")
    print("速度低于阈值并持续0.8秒 → 动作结束")
    print(f"速度阈值: {analyzer.speed_threshold} px/frame")
    print(f"静止时间阈值: {analyzer.inactive_duration_threshold} 秒")
    print("按 'q' 退出")
    print("=" * 50)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
        
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand_pos = {"x": mouse_x, "y": mouse_y}
        
        # 更新分析器
        action = analyzer.update(hand_pos)
        
        if action:
            # 动作结束，打印数据
            print(f"\n动作数据输出: {action.to_dict()}")
        
        # 渲染
        screen.fill((20, 20, 30))
        
        # 显示状态信息
        info_lines = [
            f"当前速度: {analyzer.current_action.speed:.2f} px/frame",
            f"速度阈值: {analyzer.speed_threshold} px/frame",
            f"静止状态: {'是' if analyzer.is_inactive() else '否'}",
            f"静止时间: {analyzer.get_inactive_duration():.2f} s / {analyzer.inactive_duration_threshold} s",
            f"已完成动作: {len(analyzer.completed_actions)} 次"
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 30
        
        # 绘制当前轨迹
        trajectory = [(p[0], p[1]) for p in analyzer.trajectory_with_time]
        if len(trajectory) >= 2:
            pygame.draw.lines(screen, (100, 180, 255), False, trajectory, 2)
        
        # 绘制当前位置
        if trajectory:
            pygame.draw.circle(screen, (150, 220, 255), trajectory[-1], 8)
        
        # 操作提示
        hint_text = "移动鼠标 | 静止0.8秒生成动作数据 | 'q' 退出"
        hint_surface = font.render(hint_text, True, (150, 150, 150))
        screen.blit(hint_surface, (10, screen.get_height() - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    
    # 打印所有完成的动作
    print("\n" + "=" * 50)
    print("测试完成，共记录 {} 次动作".format(len(analyzer.completed_actions)))
    for i, action in enumerate(analyzer.completed_actions):
        print(f"\n动作 {i+1}:")
        print(action.to_dict())
    print("=" * 50)


if __name__ == "__main__":
    main()