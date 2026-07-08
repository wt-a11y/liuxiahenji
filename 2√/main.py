"""
《留下的痕迹》
The Trace We Leave

主程序入口

负责：
1. 初始化摄像头
2. 获取手部数据
3. 记录轨迹
4. 判断动作结束
5. 生成痕迹
6. 影响目标对象

运行：py -3.11 main.py
"""

import cv2
import pygame
import sys

from hand_tracking import HandTracker
from behavior_analysis import BehaviorAnalyzer
from particle_system import ParticleSystem
from target_object import TargetObject
from interaction import InteractionManager


def main():
    """主函数"""
    print("=" * 50)
    print("《留下的痕迹》 The Trace We Leave")
    print("=" * 50)
    print("正在初始化...")
    
    # 1. 初始化摄像头
    print("正在初始化摄像头...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("错误：无法打开摄像头")
        print("请检查摄像头是否已连接")
        print("如果摄像头正被其他程序使用，请先关闭")
        return
    
    # 设置摄像头分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # 预热摄像头（等待摄像头准备好）
    print("摄像头预热...")
    for i in range(5):
        ret, _ = cap.read()
        if ret:
            print(f"摄像头预热成功 (尝试 {i+1}/5)")
            break
        pygame.time.wait(100)
    
    if not ret:
        print("警告：摄像头预热失败，但程序将继续运行")
        print("如果画面无法显示，请检查摄像头连接")
    
    # 2. 初始化Pygame
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("The Trace We Leave")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    # 3. 初始化所有模块
    hand_tracker = HandTracker()           # 手部追踪
    behavior_analyzer = BehaviorAnalyzer() # 行为分析
    particle_system = ParticleSystem()     # 粒子系统
    target_object = TargetObject()         # 目标对象
    interaction_manager = InteractionManager()  # 交互管理
    
    # 设置交互管理器的目标对象
    interaction_manager.set_target(target_object)
    
    print("所有模块已初始化")
    print("=" * 50)
    print("操作说明：")
    print("  - 移动手部绘制轨迹")
    print("  - 静止 0.8秒 → 动作结束 → 痕迹飞向目标")
    print("  - ESC: 退出")
    print("  - C: 清除")
    print("=" * 50)
    
    # 当前轨迹可视化
    current_trajectory = []
    max_trajectory_points = 150
    
    running = True
    while running:
        # 处理 Pygame 事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    # 清除所有状态
                    behavior_analyzer.clear()
                    particle_system.clear()
                    interaction_manager.clear()
                    target_object.reset_position()
                    current_trajectory.clear()
                    print("已清除所有痕迹")
        
        # 检查 OpenCV 窗口事件
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC 键
            running = False
        
        # 4. 获取手部数据
        ret, frame = cap.read()
        if not ret:
            # 摄像头读取失败，尝试重新初始化
            cap.release()
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("警告：无法读取摄像头画面，正在重试...")
                pygame.time.wait(100)  # 等待100ms
                continue
            ret, frame = cap.read()
            if not ret:
                print("警告：摄像头暂时不可用")
                continue
        
        # 镜像翻转（符合自然交互）
        frame = cv2.flip(frame, 1)
        
        # 获取手部位置
        hand_position = hand_tracker.get_hand_position(frame)
        
        # 绘制手部关键点
        hand_tracker.draw_landmarks(frame)
        
        # 在摄像头画面显示状态
        if hand_position:
            # 手部检测成功
            cv2.putText(frame, "Hand Detected!", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(frame, f"Pos: ({hand_position['x']}, {hand_position['y']})", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 绘制指尖标记
            cv2.circle(frame, (hand_position['x'], hand_position['y']), 15, (0, 255, 255), 3)
            
            # 记录轨迹点（用于可视化）
            current_trajectory.append((hand_position['x'], hand_position['y']))
            if len(current_trajectory) > max_trajectory_points:
                current_trajectory.pop(0)
        else:
            # 未检测到手
            cv2.putText(frame, "No Hand Detected", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            cv2.putText(frame, "Show your hand to camera", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # 清空当前轨迹
            current_trajectory.clear()
        
        # 显示操作提示
        cv2.putText(frame, "ESC: Exit", (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # 显示摄像头画面
        cv2.imshow("Camera", frame)
        
        # 5. 更新行为分析器（判断动作结束）
        action_data = behavior_analyzer.update(hand_position)
        
        if action_data:
            # 动作结束！
            action_dict = action_data.to_dict()
            print(f"\n动作结束: speed={action_dict['speed']:.2f}, distance={action_dict['distance']:.2f}")
            
            # 6. 生成痕迹（粒子效果）
            if action_dict['trajectory'] and len(action_dict['trajectory']) >= 5:
                particle_system.create_trace_from_trajectory(action_dict['trajectory'])
            
            # 7. 影响目标对象（痕迹投射物）
            interaction_manager.process_action_end(action_dict)
            
            # 清空当前轨迹可视化
            current_trajectory.clear()
        
        # 更新所有模块
        particle_system.update()
        interaction_manager.update()
        target_object.update()
        
        # 渲染 Pygame 窗口
        screen.fill((15, 15, 25))  # 深色背景
        
        # 绘制当前轨迹（实时跟踪线）
        if len(current_trajectory) >= 2:
            pygame.draw.lines(screen, (80, 160, 220), False, current_trajectory, 2)
            if current_trajectory:
                pygame.draw.circle(screen, (120, 200, 255), current_trajectory[-1], 6)
        
        # 绘制粒子系统（数字痕迹）
        particle_system.draw(screen)
        
        # 绘制交互投射物（飞向目标）
        interaction_manager.draw(screen)
        
        # 绘制目标对象
        target_object.draw(screen)
        
        # 显示状态信息
        info_lines = [
            f"Hand: {'Detected' if hand_position else 'None'}",
            f"Trajectory: {len(current_trajectory)} points",
            f"Particles: {particle_system.get_particle_count()}",
            f"Projectiles: {interaction_manager.get_projectile_count()}",
            f"Target: {target_object.state} (impact: {target_object.impact_value:.2f})",
            f"Inactive: {behavior_analyzer.get_inactive_duration():.2f}s / 0.8s"
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        # 操作提示
        hint_text = "Move hand -> Stop 0.8s -> Trace flies to target | ESC: Exit | C: Clear"
        hint_surface = font.render(hint_text, True, (120, 120, 120))
        screen.blit(hint_surface, (10, screen.get_height() - 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    # 清理资源
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    
    print("=" * 50)
    print("程序已退出")
    print("=" * 50)
    sys.exit()


if __name__ == "__main__":
    main()