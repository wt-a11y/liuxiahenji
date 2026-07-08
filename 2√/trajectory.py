"""
轨迹管理模块

记录手部运动轨迹
保存最近5秒的手部运动数据
将完成的动作转化为数字痕迹

可直接运行测试：python trajectory.py
"""

from typing import List, Tuple, Optional, Dict
from collections import deque
import pygame
import math
import time


class Trace:
    """
    数字痕迹类
    
    代表一次手部动作完成后留下的痕迹
    具有位置、强度、生命周期等属性
    """
    
    def __init__(self, points: List[Tuple[int, int]]):
        """
        初始化痕迹
        
        Args:
            points: 轨迹点列表
        """
        self.points = points.copy()
        self.intensity = 1.0       # 强度，随时间衰减
        self.lifetime = 300        # 生命周期（帧数，约5秒@60fps）
        self.age = 0
        self.center = self._calculate_center()  # 痕迹中心点
        
    def _calculate_center(self) -> Tuple[float, float]:
        """计算痕迹中心点"""
        if not self.points:
            return (0.0, 0.0)
        avg_x = sum(p[0] for p in self.points) / len(self.points)
        avg_y = sum(p[1] for p in self.points) / len(self.points)
        return (avg_x, avg_y)
        
    def update(self):
        """更新痕迹状态"""
        self.age += 1
        # 强度随时间衰减
        self.intensity = max(0, 1.0 - (self.age / self.lifetime))
        
    def is_alive(self) -> bool:
        """检查痕迹是否仍然有效"""
        return self.age < self.lifetime
    
    def get_length(self) -> float:
        """计算痕迹总长度"""
        if len(self.points) < 2:
            return 0.0
        length = 0.0
        for i in range(1, len(self.points)):
            dx = self.points[i][0] - self.points[i-1][0]
            dy = self.points[i][1] - self.points[i-1][1]
            length += math.sqrt(dx ** 2 + dy ** 2)
        return length


class TrajectoryManager:
    """
    轨迹管理器
    
    实时记录手部位置，保存最近5秒的轨迹数据
    当动作结束时，将轨迹转化为痕迹
    """
    
    def __init__(self):
        """初始化轨迹管理器"""
        # 当前正在记录的轨迹点（带时间戳）
        # 格式: deque([(x, y, timestamp), ...])
        self.trajectory_with_time: deque = deque()
        
        # 当前轨迹点列表（供外部访问）
        self.current_points: List[Tuple[int, int]] = []
        
        # 已完成的痕迹列表
        self.traces: List[Trace] = []
        
        # 时间限制：保存最近5秒的轨迹
        self.time_limit = 5.0  # 秒
        
        # 运动检测参数
        self.movement_threshold = 5      # 运动检测阈值（像素）
        self.inactive_frames = 0         # 静止帧计数
        self.inactive_threshold = 15     # 静止阈值（帧数），超过则认为动作结束
        self.min_trace_length = 20       # 最小痕迹长度（像素）
        
    def update(self, hand_position: Optional[Dict[str, int]]):
        """
        更新轨迹
        
        Args:
            hand_position: 当前手部位置，格式 {"x": int, "y": int}，None表示未检测到手
        """
        current_time = time.time()
        
        # 将字典转换为元组
        pos = None
        if hand_position is not None:
            pos = (hand_position["x"], hand_position["y"])
        
        if pos is None:
            # 手消失，结束当前轨迹
            self._finalize_current_trajectory()
            return
        
        # 添加新点到带时间戳的队列
        self.trajectory_with_time.append((pos[0], pos[1], current_time))
        
        # 移除超过5秒的旧点
        cutoff_time = current_time - self.time_limit
        while self.trajectory_with_time and self.trajectory_with_time[0][2] < cutoff_time:
            self.trajectory_with_time.popleft()
        
        # 更新当前轨迹点列表（去除时间戳）
        self.current_points = [(p[0], p[1]) for p in self.trajectory_with_time]
        
        # 检测运动状态
        if len(self.trajectory_with_time) >= 2:
            # 获取最近两个点
            points_list = list(self.trajectory_with_time)
            last_pos = (points_list[-1][0], points_list[-1][1])
            prev_pos = (points_list[-2][0], points_list[-2][1])
            
            # 计算移动距离
            dx = last_pos[0] - prev_pos[0]
            dy = last_pos[1] - prev_pos[1]
            distance = math.sqrt(dx ** 2 + dy ** 2)
            
            if distance > self.movement_threshold:
                # 有显著移动
                self.inactive_frames = 0
            else:
                # 静止
                self.inactive_frames += 1
                
                if self.inactive_frames >= self.inactive_threshold:
                    # 静止过久，结束当前轨迹，生成痕迹
                    self._finalize_current_trajectory()
        
        # 更新所有痕迹
        for trace in self.traces:
            trace.update()
        
        # 移除过期痕迹
        self.traces = [t for t in self.traces if t.is_alive()]
    
    def _finalize_current_trajectory(self):
        """将当前轨迹转化为痕迹"""
        if len(self.current_points) >= 3:
            # 计算轨迹长度
            trace_length = 0.0
            for i in range(1, len(self.current_points)):
                dx = self.current_points[i][0] - self.current_points[i-1][0]
                dy = self.current_points[i][1] - self.current_points[i-1][1]
                trace_length += math.sqrt(dx ** 2 + dy ** 2)
            
            # 只有足够长的轨迹才转化为痕迹
            if trace_length >= self.min_trace_length:
                trace = Trace(self.current_points.copy())
                self.traces.append(trace)
                print(f"生成痕迹: {len(self.current_points)} 点, 长度 {trace_length:.1f} px")
    
    def get_current_trajectory(self) -> List[Tuple[int, int]]:
        """
        获取当前正在记录的轨迹（最近5秒）
        
        Returns:
            trajectory: [(x1, y1), (x2, y2), ...]
        """
        return self.current_points.copy()
    
    def get_traces(self) -> List[Trace]:
        """获取所有活跃的痕迹"""
        return self.traces
    
    def clear_traces(self):
        """清除所有痕迹和轨迹"""
        self.traces.clear()
        self.current_points.clear()
        self.trajectory_with_time.clear()
    
    def draw(self, screen: pygame.Surface):
        """
        绘制轨迹和痕迹
        
        Args:
            screen: Pygame屏幕表面
        """
        # 绘制当前轨迹（实线，较亮）
        if len(self.current_points) >= 2:
            pygame.draw.lines(
                screen,
                (100, 180, 255),  # 亮蓝色
                False,
                self.current_points,
                3  # 线宽
            )
            
            # 绘制当前点（最新位置）
            if self.current_points:
                pygame.draw.circle(
                    screen,
                    (150, 220, 255),
                    self.current_points[-1],
                    6
                )
        
        # 绘制痕迹（随时间衰减）
        for trace in self.traces:
            if len(trace.points) >= 2:
                # 根据强度调整透明度
                intensity = trace.intensity
                color = (
                    int(100 + 50 * intensity),
                    int(150 + 50 * intensity),
                    int(200 + 55 * intensity)
                )
                
                pygame.draw.lines(
                    screen,
                    color,
                    False,
                    trace.points,
                    max(1, int(3 * intensity))  # 线宽随强度减小
                )
                
                # 绘制痕迹中心点
                center = (int(trace.center[0]), int(trace.center[1]))
                pygame.draw.circle(
                    screen,
                    (200, 200, 255),
                    center,
                    max(2, int(6 * intensity)),
                    1  # 空心圆
                )


def main():
    """
    测试函数：模拟手部移动测试轨迹记录
    
    按 'q' 键退出，按 'c' 键清除痕迹
    """
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Trajectory Test - 最近5秒轨迹")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    manager = TrajectoryManager()
    
    print("=" * 50)
    print("轨迹管理器测试")
    print("=" * 50)
    print("移动鼠标模拟手部移动")
    print("轨迹自动保存最近5秒的数据")
    print("静止超过 0.25 秒会生成痕迹")
    print("按 'q' 退出，按 'c' 清除痕迹")
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
                    manager.clear_traces()
                    print("痕迹已清除")
        
        # 获取鼠标位置作为模拟手部位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand_pos = {"x": mouse_x, "y": mouse_y}
        
        # 更新轨迹管理器
        manager.update(hand_pos)
        
        # 渲染
        screen.fill((20, 20, 30))  # 深色背景
        
        # 绘制轨迹和痕迹
        manager.draw(screen)
        
        # 显示信息
        trajectory = manager.get_current_trajectory()
        info_lines = [
            f"轨迹点数: {len(trajectory)} (最近5秒)",
            f"痕迹数: {len(manager.get_traces())}",
            f"静止帧: {manager.inactive_frames}/{manager.inactive_threshold}"
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        # 显示操作提示
        hint_text = "移动鼠标 | 静止生成痕迹 | 'c' 清除 | 'q' 退出"
        hint_surface = font.render(hint_text, True, (150, 150, 150))
        screen.blit(hint_surface, (10, screen.get_height() - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("测试结束")


if __name__ == "__main__":
    main()