"""
《留下的痕迹》
The Trace We Leave

主程序入口

负责：
1. 初始化摄像头
2. 获取手部数据
3. 记录轨迹
4. 判断动作结束
5. 生成记忆碎片
6. 碎片渗透影响目标对象

运行：py -3.11 main.py
"""

import cv2
import pygame
import sys
import os
import math

from hand_tracking import HandTracker
from behavior_analysis import BehaviorAnalyzer
from particle_system import ParticleSystem
from target_object import TargetObject
from interaction import InteractionManager
from visual_effects import TrailSurface, BackgroundNoiseField, apply_post_processing
from emotional_state import EmotionalCore, ConsequenceManager
from reflection import ReflectionSystem, draw_pause_overlay, draw_choice_dialog, draw_ending_screen
from spatial_metaphor import PersonalSpaceField, GravityField, StatusBar


def main():
    try:
        _main_loop()
    except Exception as e:
        import traceback
        print("\n" + "=" * 50)
        print("程序异常退出：")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50)
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(1)


def _main_loop():
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
    print("正在初始化 Pygame...")
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("The Trace We Leave")
    print("Pygame 窗口已创建")
    clock = pygame.time.Clock()
    pygame.font.init()
    # 中文字体（如系统无中文字体，会回退到默认字体，但中文可能显示为方块）
    _cjk_candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    font_path = None
    for _p in _cjk_candidates:
        if os.path.exists(_p):
            font_path = _p
            break
    if font_path:
        font = pygame.font.Font(font_path, 28)
        font_large = pygame.font.Font(font_path, 52)
        font_medium = pygame.font.Font(font_path, 34)
    else:
        font = pygame.font.Font(None, 28)
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 40)

    # 2.5 显示启动引导界面
    print("显示启动引导界面...")
    _show_intro_screen(screen, font_large, font_medium, font)
    print("用户已确认，继续初始化...")

    # 2.6 视觉特效初始化
    screen_w, screen_h = screen.get_size()
    trail = TrailSurface(screen_w, screen_h, decay=0.06)
    bg_noise = BackgroundNoiseField(screen_w, screen_h, resolution=16, seed=42)

    # 2.7 主题化系统初始化
    emotional_core = EmotionalCore()                    # 情感核心
    consequence_manager = ConsequenceManager()         # 后果管理
    reflection_system = ReflectionSystem(screen_w, screen_h)  # 反思系统
    target_pos = (640, 360)  # 生命体默认位置
    personal_space = PersonalSpaceField(target_pos[0], target_pos[1])  # 个人空间
    gravity_field = GravityField()                      # 引力场
    status_bar = StatusBar(screen_w, screen_h)         # 状态栏

    # 3. 初始化所有模块
    hand_tracker = HandTracker()           # 手部追踪
    behavior_analyzer = BehaviorAnalyzer() # 行为分析
    particle_system = ParticleSystem()     # 记忆碎片系统
    target_object = TargetObject()         # 有机体目标对象
    interaction_manager = InteractionManager()  # 交互管理

    # 设置交互管理器的目标对象
    interaction_manager.set_target(target_object)
    # 设置记忆碎片的目标位置
    particle_system.set_target(target_object.get_position())
    
    print("所有模块已初始化")
    print("=" * 50)
    print("操作说明：")
    print("  - 移动手部绘制轨迹")
    print("  - 静止 0.8秒 → 动作结束 → 生成记忆碎片")
    print("  - 碎片沉积 → 漂移 → 渗透 → 改变目标内部结构")
    print("  - ESC: 退出")
    print("  - C: 清除")
    print("=" * 50)
    
    # 当前轨迹可视化
    current_trajectory = []
    max_trajectory_points = 500
    frame_count = 0

    running = True
    while running:
        # 计算帧时间
        dt = clock.tick(60) / 1000.0

        # 处理 Pygame 事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # 空格键：触发暂停反思
                    if not reflection_system.is_paused:
                        personal_space_snapshot = screen.copy()
                        reflection_system.trigger_pause(screen)
                    else:
                        reflection_system.end_pause()
                elif event.key == pygame.K_r:
                    # R键：手动触发选择时刻
                    # 若处于暂停状态，先结束暂停
                    if reflection_system.is_paused:
                        reflection_system.end_pause()
                    reflection_system.choice_pending = True
                    reflection_system.time_since_last_choice = 0.0
                    print(">>> R键按下，触发选择时刻")

        # ESC 键：退出（仅由 Pygame 事件处理，移除 OpenCV waitKey 提升 FPS）

        # === 处理暂停反思 ===
        if reflection_system.is_paused:
            draw_pause_overlay(
                screen, target_object, emotional_core,
                font_medium, font, 0.0
            )
            pygame.display.flip()
            continue

        # === 处理选择时刻 ===
        if reflection_system.choice_pending:
            # 记录当前数据用于生成有意义的提示
            reflection_system.record_current_stats(emotional_core)
            choice_result = _handle_choice_dialog(
                screen, reflection_system, font_large, font_medium, font
            )
            if choice_result is not None:
                reflection_system.choice_pending = False
                if choice_result == 1:  # 选择"尝试改变"
                    # 应用"改变"的具体效果
                    reflection_system.apply_change_choice(
                        emotional_core, particle_system, target_object
                    )
                    print(">>> 你选择了改变——生命体正在向你敞开")
            else:
                pygame.display.flip()
                continue

        # === 初始化主循环状态变量（首次） ===
        if not hasattr(_main_loop, '_frame_w'):
            _main_loop._frame_w = 1280
            _main_loop._frame_h = 720
        if not hasattr(_main_loop, '_last_hand_pos'):
            _main_loop._last_hand_pos = None
            _main_loop._hand_missing_count = 0
            _main_loop._hand_lost = False
            _main_loop._last_hand_time = 0.0
        if not hasattr(_main_loop, '_last_rt_class'):
            _main_loop._last_rt_class = None
            _main_loop._last_rt_intensity = 0.0

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
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 60)
            ret, frame = cap.read()
            if not ret:
                print("警告：摄像头暂时不可用")
                continue

        # 镜像翻转（符合自然交互）
        frame = cv2.flip(frame, 1)

        # 获取手部位置（不再在 OpenCV 上绘制，状态信息迁移到 Pygame）
        hand_position = hand_tracker.get_hand_position(frame)

        # 记录轨迹点（按 frame 实际大小缩放到屏幕坐标）
        frame_h_now, frame_w_now = frame.shape[:2]
        _main_loop._frame_h = frame_h_now
        _main_loop._frame_w = frame_w_now
        fw = max(frame_w_now, 1)
        fh = max(frame_h_now, 1)
        if hand_position:
            sx = hand_position['x'] * screen_w / fw
            sy = hand_position['y'] * screen_h / fh
            current_trajectory.append((sx, sy))
            if len(current_trajectory) > max_trajectory_points:
                current_trajectory.pop(0)
        else:
            # 手彻底离开：清除轨迹
            if _main_loop._hand_lost:
                current_trajectory.clear()

        # 5. 更新行为分析器（判断动作结束）
        action_data = behavior_analyzer.update(hand_position)

        if action_data:
            # 动作结束！
            action_dict = action_data.to_dict()
            print(f"\n动作结束: speed={action_dict['speed']:.2f}, distance={action_dict['distance']:.2f}")

            # === 主题化：动作结果反馈到情感系统 ===
            classification = action_dict.get('classification', 'neutral')
            intensity = action_dict.get('intensity', 0.5)

            if classification == 'negative':
                emotional_core.update(0, {
                    'type': 'violent',
                    'intensity': intensity
                })
                # 后果延迟：3秒后显示伤害效果
                consequence_manager.queue_consequence(
                    'harm', 3.0,
                    {'intensity': intensity, 'location': target_object.get_position()}
                )
            elif classification == 'positive':
                emotional_core.update(0, {
                    'type': 'gentle',
                    'intensity': intensity
                })

            # 记录到后果管理器
            consequence_manager.record_action(action_dict)

            # 意图检查
            warning_info = consequence_manager.check_intention(action_dict)

            # 6. 生成记忆碎片
            if action_dict['trajectory'] and len(action_dict['trajectory']) >= 5:
                particle_system.create_trace_from_trajectory(
                    action_dict['trajectory'],
                    action_dict['speed'],
                    action_dict['distance']
                )

            # 清空当前轨迹可视化
            current_trajectory.clear()

        # === 实时速度反馈：每帧根据手部速度更新情感（方案 A - 精简版） ===
        # 关键：让生命体状态对手部速度"实时"反应
        # 节流：分类变化或 intensity 变化 > 0.4 时才更新，避免震荡和卡顿
        if hand_position and len(current_trajectory) >= 3:
            # 快速速度估计：仅看最后 2 个点（不遍历窗口）
            p1 = current_trajectory[-2]
            p2 = current_trajectory[-1]
            speed_2pt = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

            # 归一化：20 像素/帧 ≈ 快速（30 fps 下 600 px/s）
            real_time_intensity = min(1.0, speed_2pt / 20.0)

            # 分类
            if real_time_intensity >= 0.7:
                new_class = 'negative'
            elif real_time_intensity >= 0.2:
                new_class = 'positive'
            else:
                new_class = 'neutral'

            # 节流：仅在分类变化或强度变化 > 0.4 时触发
            if (new_class != _main_loop._last_rt_class or
                abs(real_time_intensity - _main_loop._last_rt_intensity) > 0.4):
                if new_class == 'negative':
                    emotional_core.update(0, {'type': 'violent', 'intensity': real_time_intensity})
                elif new_class == 'positive':
                    emotional_core.update(0, {'type': 'gentle', 'intensity': real_time_intensity})
                _main_loop._last_rt_class = new_class
                _main_loop._last_rt_intensity = real_time_intensity

        # === 更新主题化系统 ===
        emotional_core.update(dt)
        triggered_consequences = consequence_manager.update(dt)

        # 碎片颜色根据生命体当前状态调整（只在状态变化时调用，避免每帧遍历）
        state_tint_map = {
            '平静': 'warm',
            '警觉': 'tense',
            '退缩': 'sad',
            '敞开': 'healing',
            '被忽视': 'cold',
        }
        current_tint = state_tint_map.get(emotional_core.get_state_description())
        if not hasattr(main, '_last_tint'):
            main._last_tint = None
        if current_tint != main._last_tint:
            particle_system.set_emotional_tint(current_tint)
            main._last_tint = current_tint

        # 应用延迟后果
        for cons in triggered_consequences:
            if cons['type'] == 'harm':
                # 延迟的伤害效果：可在目标上添加疤痕
                pass  # 由particle系统自然产生

        # 反思时刻检查
        reflection_event = reflection_system.update(dt)

        # 更新个人空间和引力场
        hand_screen_x = None
        hand_screen_y = None
        hand_speed = 0.0

        # 记录 frame 实际大小（hand_position 是基于此坐标系）
        _main_loop._frame_h, _main_loop._frame_w = frame.shape[:2]

        if hand_position:
            # 转换摄像头坐标到屏幕坐标（按 frame 实际大小）
            frame_w = max(_main_loop._frame_w, 1)
            frame_h = max(_main_loop._frame_h, 1)
            hand_screen_x = hand_position['x'] * screen_w / frame_w
            hand_screen_y = hand_position['y'] * screen_h / frame_h
            if len(current_trajectory) >= 2:
                dx = current_trajectory[-1][0] - current_trajectory[-2][0]
                dy = current_trajectory[-1][1] - current_trajectory[-2][1]
                hand_speed = math.hypot(dx, dy)

        personal_space.update(
            dt, target_object.x, target_object.y,
            hand_screen_x, hand_screen_y, hand_speed
        )

        # === 个人空间 → 情感状态联动 ===
        # 规则：手在红圈内 → 强制警觉（优先级最高）
        #      手离开红圈 → 解锁，让状态自然恢复
        current_level = personal_space.warning_level
        prev_level = getattr(personal_space, '_prev_warning_level', 0)

        if current_level == 2 and hand_screen_x is not None:
            # 在亲密距离（红圈）内：每帧强制警觉
            violent = hand_speed > 8.0
            intensity = max(0.5, personal_space.boundary_intensity)
            if violent:
                intensity = max(intensity, 0.8)
            emotional_core.force_alert(intensity=intensity)
        elif current_level < 2:
            # 离开红圈：解锁警觉（恢复计时器继续）
            if getattr(personal_space, '_prev_warning_level', 0) == 2:
                # 刚离开红圈，解锁
                emotional_core.set_alert_lock(False)
            # 注意：current_level == 1（社交距离）不主动干预，让警觉自然恢复

        personal_space._prev_warning_level = current_level

        gravity_field.update(
            dt, target_object.x, target_object.y,
            emotional_core.get_relationship_quality(),
            hand_screen_x, hand_screen_y
        )
        
        # 更新所有模块
        # 更新粒子系统（获取渗透数据）
        penetrations = particle_system.update()
        
        # 检查碎片是否靠近膜边界（触发膜的扰动）
        fragments_data = particle_system.get_fragments_data()
        for fragment_data in fragments_data:
            interaction_manager.check_membrane_approach(fragment_data)
        
        # 7. 处理渗透（改变目标内部结构）
        if penetrations:
            interaction_manager.process_penetrations(penetrations)
        
        # 更新目标对象
        target_object.update()
        
        # 更新目标位置（目标可能移动）
        particle_system.set_target(target_object.get_position())
        
        # 渲染 Pygame 窗口
        # === 背景：noise 场（缓慢流动的深蓝→深紫渐变） ===
        bg_noise.update()
        bg_noise.draw(screen)

        # === 引力场：生命体周围的粒子场 ===
        gravity_field.draw(screen)

        # === 残影拖尾：衰减上一帧，准备绘制新帧 ===
        trail.begin_frame()

        # 绘制当前轨迹（实时跟踪线）→ 画到 trail surface
        if len(current_trajectory) >= 2:
            pygame.draw.lines(trail.surface, (80, 160, 220), False, current_trajectory, 2)
            if current_trajectory:
                pygame.draw.circle(trail.surface, (120, 200, 255), current_trajectory[-1], 6)

        # 绘制记忆碎片 → 画到 trail surface
        particle_system.draw(trail.surface)

        # 绘制目标对象（有机体）→ 画到 trail surface
        target_object.draw(trail.surface)

        # === 将 trail 残影叠加到 screen ===
        trail.apply_to(screen)

        # === 个人空间边界（绘制在生命体周围） ===
        personal_space.draw(screen)

        # === 后期处理：每 4 帧做一次轻量模糊（模拟柔焦） ===
        if frame_count % 4 == 0:
            screen.blit(
                apply_post_processing(screen, blur_radius=1, blur_passes=1, sharpen=0.05),
                (0, 0),
            )

        # === 状态栏（底部）===
        warning_info = consequence_manager.check_intention({'speed': 0, 'acceleration': 0})
        status_bar.draw(
            screen, font,
            emotional_core.get_state_description(),
            emotional_core.get_relationship_quality(),
            emotional_core.cumulative_care,
            emotional_core.cumulative_harm,
            consequence_manager.warning_active,
            warning_info.get('message', '')
        )

        # === 顶部提示 ===
        top_hint = font.render(
            "空格: 暂停反思  R: 选择时刻  ESC: 退出",
            True, (120, 120, 130)
        )
        screen.blit(top_hint, (10, 10))

        # === 手部状态显示（替代 OpenCV 窗口） ===
        if hand_position:
            # 手部检测成功
            hand_status = font.render(
                "Hand Detected!",
                True, (0, 200, 100)
            )
            screen.blit(hand_status, (10, 35))

            # 在 Pygame 上画指尖标记（按 frame 实际大小缩放）
            frame_w = max(getattr(_main_loop, '_frame_w', 1280), 1)
            frame_h = max(getattr(_main_loop, '_frame_h', 720), 1)
            tip_screen_x = hand_position['x'] * screen_w / frame_w
            tip_screen_y = hand_position['y'] * screen_h / frame_h
            pygame.draw.circle(
                screen, (255, 255, 100),
                (int(tip_screen_x), int(tip_screen_y)), 15, 3
            )
        else:
            # 未检测到手
            hand_status = font.render(
                "No Hand Detected",
                True, (220, 80, 80)
            )
            screen.blit(hand_status, (10, 35))

        # === FPS 显示（每 30 帧更新一次）===
        if not hasattr(_main_loop, '_fps_counter'):
            _main_loop._fps_counter = 0
            _main_loop._fps_last_time = pygame.time.get_ticks()
            _main_loop._fps_value = 0
        _main_loop._fps_counter += 1
        if _main_loop._fps_counter % 30 == 0:
            now = pygame.time.get_ticks()
            elapsed = (now - _main_loop._fps_last_time) / 1000.0
            _main_loop._fps_value = 30.0 / max(elapsed, 0.001)
            _main_loop._fps_last_time = now
        fps_text = font.render(f"FPS: {_main_loop._fps_value:.1f}", True, (200, 200, 200))
        screen.blit(fps_text, (1280 - 100, 10))

        pygame.display.flip()
        frame_count += 1

    # === 退出前：显示反思界面 ===
    try:
        _show_reflection_screen(
            screen,
            font_large, font_medium, font,
            positive_count=target_object.positive_count,
            negative_count=target_object.negative_count,
            fragment_count=len(particle_system.fragments) + target_object.fragment_count,
        )
    except Exception as e:
        print(f"反思界面显示失败：{e}")

    # 清理资源
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()

    print("=" * 50)
    print("程序已退出")
    print("=" * 50)
    sys.exit()


def _handle_choice_dialog(screen, reflection_system, font_large, font_medium, font):
    """
    处理选择时刻对话框

    Returns:
        0 = 选择"继续当前方式"
        1 = 选择"尝试改变"
        None = 仍在选择中
    """
    selected = 0
    clock = pygame.time.Clock()
    choosing = True

    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 0  # 跳过选择
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = 1
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return selected

        message = reflection_system.get_choice_message(reflection_system.choice_count)
        draw_choice_dialog(
            screen, message,
            font_large, font_medium, font,
            selected
        )
        pygame.display.flip()
        clock.tick(60)


def _draw_text_lines(screen, lines, font, color, center_x, start_y, line_spacing=None):
    """居中绘制多行文字，返回最终 y 坐标"""
    if line_spacing is None:
        line_spacing = font.get_linesize() + 6
    y = start_y
    for line in lines:
        if line == "":
            y += line_spacing // 2
            continue
        surf = font.render(line, True, color)
        rect = surf.get_rect(center=(center_x, y + surf.get_height() // 2))
        screen.blit(surf, rect)
        y += line_spacing
    return y


def _show_intro_screen(screen, font_large, font_medium, font):
    """
    启动引导界面：明确传达作品观点，等待用户按键进入
    """
    clock = pygame.time.Clock()
    waiting = True
    blink = 0

    # 确保窗口获得焦点
    pygame.event.clear()
    pygame.display.flip()

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            # 同时检测 KEYDOWN 和 MOUSEBUTTONDOWN
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit(0)
                waiting = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

        screen.fill((18, 16, 22))

        # 顶部主标题（中文）
        title_lines = [
            "留下的痕迹",
        ]
        _draw_text_lines(
            screen, title_lines, font_large,
            (232, 188, 132),
            screen.get_width() // 2, 90, line_spacing=70,
        )

        # 引导正文（中文）
        body_lines = [
            "在人与人的相处中，我们的行为会影响他人。",
            "",
            "轻柔   =   治愈",
            "剧烈   =   伤害",
            "",
            "那么——",
            "在这样的前提下，应该怎样控制自己的行为？",
        ]
        _draw_text_lines(
            screen, body_lines, font_medium,
            (220, 215, 205),
            screen.get_width() // 2, 230, line_spacing=42,
        )

        # 闪烁提示
        blink = (blink + 1) % 60
        if blink < 40:
            hint = font.render("点击或按任意键开始", True, (160, 160, 170))
            rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 60))
            screen.blit(hint, rect)

        pygame.display.flip()
        clock.tick(60)


def _show_reflection_screen(screen, font_large, font_medium, font,
                             positive_count, negative_count, fragment_count):
    """
    结束反思界面：根据用户本次交互的正/负向比例，给出反思文字
    """
    clock = pygame.time.Clock()
    waiting = True
    blink = 0
    total = positive_count + negative_count
    if total == 0:
        ratio_label = "未交互"
        ratio_value = 0.0
    else:
        ratio_value = positive_count / total
        if ratio_value >= 0.75:
            ratio_label = "温柔"
        elif ratio_value >= 0.5:
            ratio_label = "平和"
        elif ratio_value >= 0.25:
            ratio_label = "急躁"
        else:
            ratio_label = "粗暴"

    # 选择反思文案
    if total == 0:
        reflection_lines = [
            "你没有与它互动。",
            "",
            "但现实中，沉默与回避，",
            "也常常是一种回应。",
            "",
            "下次面对他人时，",
            "愿你选择走近，而不是漠视。",
        ]
    elif ratio_value >= 0.6:
        reflection_lines = [
            f"这一次，你以 {ratio_label} 为主。",
            f"  治愈动作 {positive_count} 次，伤害动作 {negative_count} 次。",
            "",
            "它的身体渐渐舒展，",
            "暗色也正在褪去。",
            "",
            "你证明了一件事：",
            "温柔，是有回响的。",
        ]
    elif ratio_value >= 0.4:
        reflection_lines = [
            f"这一次，你的动作在 {ratio_label} 与粗暴之间摇摆。",
            f"  治愈动作 {positive_count} 次，伤害动作 {negative_count} 次。",
            "",
            "它的身上既有柔软的记忆，",
            "也留下了清晰的暗色疤痕。",
            "",
            "我们常常以为自己的言行无关紧要，",
            "但其实，痕迹正在累积。",
        ]
    else:
        reflection_lines = [
            f"这一次，你的动作以 {ratio_label} 为主。",
            f"  治愈动作 {positive_count} 次，伤害动作 {negative_count} 次。",
            "",
            "它的身上布满了暗色疤痕，",
            "原本的颜色几乎被掩盖。",
            "",
            "也许这并不是你的本意，",
            "但语言与动作的重量，",
            "比我们以为的要大得多。",
            "",
            "请记得，",
            "在看不见的地方，",
            "痕迹依然存在。",
        ]

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            if event.type == pygame.KEYDOWN:
                waiting = False

        screen.fill((14, 12, 18))

        # 标题
        _draw_text_lines(
            screen, ["《留下的痕迹》", "—— 反思 ——"],
            font_large,
            (232, 188, 132),
            screen.get_width() // 2, 60, line_spacing=66,
        )

        # 统计数据
        stats_lines = [
            f"本次共生成 {fragment_count} 个记忆碎片",
            f"  治愈（轻柔）：{positive_count}    伤害（剧烈）：{negative_count}",
            f"  总体倾向：{ratio_label}",
            "",
        ]
        _draw_text_lines(
            screen, stats_lines, font_medium,
            (200, 200, 210),
            screen.get_width() // 2, 200, line_spacing=40,
        )

        # 反思正文
        _draw_text_lines(
            screen, reflection_lines, font_medium,
            (220, 215, 205),
            screen.get_width() // 2, 360, line_spacing=42,
        )

        # 闪烁提示
        blink = (blink + 1) % 60
        if blink < 40:
            hint = font.render("按 任意键  退出", True, (160, 160, 170))
            rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))
            screen.blit(hint, rect)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
