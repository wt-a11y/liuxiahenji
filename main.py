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
import time

from hand_tracking import HandTracker
from behavior_analysis import BehaviorAnalyzer
from particle_system import ParticleSystem
from target_object import TargetObject
from interaction import InteractionManager
from visual_effects import TrailSurface, BackgroundNoiseField, apply_post_processing
from emotional_state import EmotionalCore, ConsequenceManager
from reflection import ReflectionSystem, draw_pause_overlay, draw_ending_screen
from spatial_metaphor import PersonalSpaceField, GravityField, StatusBar
from data_export import DataExporter
from intro_tutorial import show_tutorial
from audio import init_audio, get_audio


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

    # 2.2 初始化音效（在 pygame.init() 之后立即初始化，让 mixer 准备好）
    audio_manager = init_audio()

    # 2.3 提前初始化 hand_tracker（必须先于 show_tutorial，否则引导界面无法追踪手）
    hand_tracker = HandTracker()

    # 2.4 初始化手势检测器（必须先于 show_tutorial，否则引导界面无法驱动摄像头+手势识别）
    from gesture_detector import GestureDetector
    gesture_detector = GestureDetector(
        open_hold_sec=1.5,    # 张开手掌 1.5 秒 = 翻页 / 暂停反思（更宽容）
        close_hold_sec=2.0,   # 握拳 2.0 秒 = 退出（更宽容，避免误触）
        debounce_frames=3,
        post_event_cooldown_sec=1.0,
    )

    # 2.5 显示新手引导（8 张引导卡，含数据导出说明）
    print("显示新手引导界面...")
    show_tutorial(screen, font_large, font_medium, font,
                gesture_detector=gesture_detector, hand_tracker=hand_tracker, cap=cap)
    print("用户已确认，继续初始化...")

    # 2.6 视觉特效初始化
    screen_w, screen_h = screen.get_size()
    trail = TrailSurface(screen_w, screen_h, decay=0.06)
    bg_noise = BackgroundNoiseField(screen_w, screen_h, resolution=16, seed=42)

    # 2.7 主题化系统初始化
    # 数据导出器必须先初始化，因为 emotional_core.on_state_change 要绑定它
    data_exporter = DataExporter()
    emotional_core = EmotionalCore()                    # 情感核心
    consequence_manager = ConsequenceManager()         # 后果管理

    # 状态切换回调链：先数据导出，后音效
    def _on_state_change_with_audio(old_state, new_state):
        # 1. 数据导出
        data_exporter.on_state_change(old_state, new_state)
        # 2. 音效：只在新状态触发时播放（实时反馈）
        if audio_manager and audio_manager.is_available():
            new_name = new_state.value if hasattr(new_state, 'value') else str(new_state)
            # 警觉音效门控：必须在红圈内才播
            in_red_zone = False
            try:
                in_red_zone = personal_space.warning_level == 2
            except Exception:
                in_red_zone = False
            if new_name == 'alert':
                # 警觉只在红圈内有效——红圈外的"假警觉"不播音
                if in_red_zone:
                    audio_manager.play('enter_red')      # 警觉 → 高频警告音
            elif new_name == 'withdrawn':
                audio_manager.play('state_withdrawn') # 退缩 → 高频
            elif new_name == 'open':
                audio_manager.play('state_open')      # 敞开 → 低频
            elif new_name == 'calm':
                # 平静状态无专属音（柔和 + 静静陪伴）
                pass
            elif new_name == 'neglected':
                # 被忽视状态无专属音（安静反而是表达）
                pass

    emotional_core.on_state_change = _on_state_change_with_audio
    reflection_system = ReflectionSystem(screen_w, screen_h)  # 反思系统
    target_pos = (640, 360)  # 生命体默认位置
    personal_space = PersonalSpaceField(target_pos[0], target_pos[1])  # 个人空间
    gravity_field = GravityField()                      # 引力场
    status_bar = StatusBar(screen_w, screen_h)         # 状态栏

    # 警觉 → 行为时间线标记为"重"在主循环中持续处理
    # （见 personal_space 警觉联动处：只要在红圈内每 1.2s 追加一条"重"）

    # 3. 初始化所有模块
    # hand_tracker 与 gesture_detector 已在 #2.3/#2.4 创建（早于 show_tutorial 调用），此处不再重复创建
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

    # === 行为时间线（最近 8 个动作） ===
    # 每个元素: {'classification': 'positive'/'negative'/'neutral', 'intensity': float, 'time': float}
    recent_actions = []
    max_recent_actions = 8
    _last_monologue = ""           # 上次显示的独白
    _monologue_alpha = 0.0         # 独白淡入淡出 alpha

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
                # R 键：选择时刻已移除，无操作
                elif event.key == pygame.K_m:
                    # M键：切换静音
                    if audio_manager and audio_manager.is_available():
                        muted = audio_manager.toggle_mute()
                        print(f">>> 音效 {'已静音' if muted else '已开启'}")

        # ESC 键：退出（仅由 Pygame 事件处理，移除 OpenCV waitKey 提升 FPS）

        # 选择时刻环节已移除（reflection_system.choice_pending 不再被触发）

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

        # === 手势识别（每帧喂入 landmarks）===
        landmarks_now = hand_tracker.get_landmarks()
        current_gesture = gesture_detector.update(landmarks_now)
        # 消费所有事件（优先取最新；close 优先级最高）
        gesture_event = None
        all_events = []
        while True:
            e = gesture_detector.consume_event()
            if e is None:
                break
            all_events.append(e)
        if 'close' in all_events:
            gesture_event = 'close'  # close 优先级最高
        elif 'open' in all_events:
            gesture_event = 'open'

        # 记录轨迹点（按 frame 实际大小缩放到屏幕坐标）
        frame_h_now, frame_w_now = frame.shape[:2]
        _main_loop._frame_h = frame_h_now
        _main_loop._frame_w = frame_w_now
        fw = max(frame_w_now, 1)

        # === 手势事件响应 ===
        if gesture_event == 'open':
            # 张开手掌持续 1 秒 → 暂停 / 继续反思
            if not reflection_system.is_paused:
                personal_space_snapshot = screen.copy()
                reflection_system.trigger_pause(screen)
            else:
                reflection_system.end_pause()
        elif gesture_event == 'close':
            # 握拳持续 1.5 秒 → 退出程序（保留 ESC 兜底）
            print(">>> 握拳手势触发，退出程序")
            running = False
        fh = max(frame_h_now, 1)
        if hand_position and not reflection_system.is_paused:
            sx = hand_position['x'] * screen_w / fw
            sy = hand_position['y'] * screen_h / fh
            current_trajectory.append((sx, sy))
            if len(current_trajectory) > max_trajectory_points:
                current_trajectory.pop(0)

            # === 过程中生成碎片（按当时情感状态染色 + 间距增大） ===
            # 每 0.35s（约 21 帧）生成 1 个小碎片（之前 0.15s 太密）
            # 警觉 tint 仅在红圈内生效——红圈外的"伪警觉"改回 warm
            if not hasattr(main, '_last_inline_emit'):
                main._last_inline_emit = 0.0
            now = pygame.time.get_ticks() / 1000.0
            if now - main._last_inline_emit >= 0.35:
                main._last_inline_emit = now
                # 当前时刻的情感状态 → tint
                cur_state_inline = emotional_core.get_state_description()
                in_red_zone_inline = False
                try:
                    in_red_zone_inline = personal_space.warning_level == 2
                except Exception:
                    in_red_zone_inline = False
                # 警觉 tint 门控：红圈外不能用 tense（避免外面出现橙红"假警觉"）
                if cur_state_inline == '警觉' and not in_red_zone_inline:
                    tint_for_fragment = 'warm'  # 降级为基础色
                else:
                    tint_for_fragment = {
                        '平静': 'warm',
                        '警觉': 'tense',
                        '退缩': 'sad',
                        '敞开': 'healing',
                        '被忽视': 'cold',
                    }.get(cur_state_inline, 'warm')
                # 用单点 trajectory 创建碎片（只 1 个）
                inline_traj = [(sx, sy)]
                particle_system.create_trace_from_trajectory(
                    inline_traj,
                    behavior_speed=abs(hand_position.get('speed', 0.0)),
                    behavior_distance=0.0,
                    classification='neutral',
                    emotional_tint=tint_for_fragment,
                )
        else:
            # 手彻底离开：清除轨迹
            if _main_loop._hand_lost:
                current_trajectory.clear()

        # 5. 更新行为分析器（判断动作结束）
        action_data = behavior_analyzer.update(hand_position)

        if action_data and not reflection_system.is_paused:
            # 动作结束！
            action_dict = action_data.to_dict()
            print(f"\n动作结束: speed={action_dict['speed']:.2f}, distance={action_dict['distance']:.2f}")

            # === 主题化：动作结果反馈到情感系统 ===
            classification = action_dict.get('classification', 'neutral')
            intensity = action_dict.get('intensity', 0.5)

            # === 记录到行为时间线 ===
            # impact: 该行为在生命体上留下的"影响程度"（不被时间衰减）
            recent_actions.append({
                'classification': classification,
                'intensity': intensity,        # 瞬时强度
                'impact': intensity,           # 持续影响（与强度同源，但语义不同）
                'time': time.time(),
            })
            if len(recent_actions) > max_recent_actions:
                recent_actions.pop(0)

            # === 数据导出：记录动作前的状态 + 是否在个人空间内 ===
            state_before = emotional_core.current_state.value
            inside_ps = False
            if hand_position:
                hand_screen_x_now = hand_position.get('x', 0) * screen_w / max(getattr(_main_loop, '_frame_w', 1280), 1)
                hand_screen_y_now = hand_position.get('y', 0) * screen_h / max(getattr(_main_loop, '_frame_h', 720), 1)
                dx = hand_screen_x_now - target_pos[0]
                dy = hand_screen_y_now - target_pos[1]
                dist_to_target = (dx * dx + dy * dy) ** 0.5
                # 用 PersonalSpaceField.INTIMATE_DISTANCE 作为"在红圈内"的判定阈值
                inside_ps = dist_to_target < PersonalSpaceField.INTIMATE_DISTANCE

            if classification == 'negative':
                # 红圈门控：仅在红圈内的 violent 才可能触发警觉
                red_zone_now = False
                try:
                    red_zone_now = personal_space.warning_level == 2
                except Exception:
                    red_zone_now = False
                emotional_core.update(0, {
                    'type': 'violent',
                    'intensity': intensity,
                    'in_red_zone': red_zone_now,
                })
                # 后果延迟：3秒后显示伤害效果
                consequence_manager.queue_consequence(
                    'harm', 3.0,
                    {'intensity': intensity, 'location': target_object.get_position()}
                )
                # 音效：剧烈画线 → 失谐双音（即时动作反馈）
                # 与状态切换回调播放的 state_withdrawn/state_alert 不同，这是"动作力度"反馈
                if audio_manager and audio_manager.is_available():
                    audio_manager.play('violent')
            elif classification == 'positive':
                # 红圈门控：gentle 不影响警觉（这里只为一致性记录）
                red_zone_now = False
                try:
                    red_zone_now = personal_space.warning_level == 2
                except Exception:
                    red_zone_now = False
                emotional_core.update(0, {
                    'type': 'gentle',
                    'intensity': intensity,
                    'in_red_zone': red_zone_now,
                })
                # 音效：轻柔画线 → 和弦琶音（即时动作反馈）
                # 与状态切换回调播放的 state_open 不同，这是"动作温柔"反馈
                if audio_manager and audio_manager.is_available():
                    audio_manager.play('gentle')

            # 记录动作后的状态
            state_after = emotional_core.current_state.value

            # === 累计正/负向交互次数（用于结算界面判定结局） ===
            # 注意：粒子系统的 create_trace_from_trajectory 用的是 'neutral' 分类，
            # 不会触发 target_object.receive_impact 的计数逻辑——这里显式补一次
            if classification in ('positive', 'negative'):
                try:
                    # target_object 类的方法实际叫 receive_impact，不是 apply_influence
                    if hasattr(target_object, 'receive_impact'):
                        hand_xy = None
                        if hand_position:
                            hand_xy = (sx, sy) if 'sx' in dir() else None
                        # receive_impact 接受 source_position: Dict (含 x/y) 或 None
                        src_dict = None
                        if hand_xy is not None:
                            src_dict = {'x': hand_xy[0], 'y': hand_xy[1]}
                        target_object.receive_impact(
                            value=intensity,
                            source_position=src_dict,
                            impact_type='touch',
                            classification=classification,
                            intensity_raw=intensity,
                        )
                except Exception as e:
                    # 不阻断主流程，仅记录
                    print(f"[warning] target_object.receive_impact 失败: {e}")

            # === 数据导出：记录到 CSV ===
            data_exporter.log_action(
                action_dict,
                state_before=state_before,
                state_after=state_after,
                inside_personal_space=inside_ps
            )

            # 记录到后果管理器
            consequence_manager.record_action(action_dict)

            # 意图检查
            warning_info = consequence_manager.check_intention(action_dict)

            # 6. 画线结束时，不再批量生成碎片
            # 碎片已在画线过程中按当时情感状态实时生成（多色、自然）
            # 这样长线下多个碎片可能是不同颜色（取决于画线过程状态切换）

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
                # 红圈门控（实时反馈路径）
                red_zone_rt = False
                try:
                    red_zone_rt = personal_space.warning_level == 2
                except Exception:
                    red_zone_rt = False
                if new_class == 'negative':
                    emotional_core.update(0, {
                        'type': 'violent',
                        'intensity': real_time_intensity,
                        'in_red_zone': red_zone_rt,
                    })
                elif new_class == 'positive':
                    emotional_core.update(0, {
                        'type': 'gentle',
                        'intensity': real_time_intensity,
                        'in_red_zone': red_zone_rt,
                    })
                _main_loop._last_rt_class = new_class
                _main_loop._last_rt_intensity = real_time_intensity

        # === 更新主题化系统 ===
        # 每帧情感推进（传入当前红圈状态用于任何路径的警觉门控）
        red_zone_tick = False
        try:
            red_zone_tick = personal_space.warning_level == 2
        except Exception:
            red_zone_tick = False
        emotional_core.update(dt, in_red_zone=red_zone_tick)
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

        # === 持续状态监测：停留过久时强化音频提示 ===
        # 检测生命体在同一状态停留时间
        if not hasattr(main, '_state_hold_start'):
            main._state_hold_start = time.time()
            main._state_hold_last_state = emotional_core.current_state.value
            main._state_hold_played = set()  # 已播放的强化音（在状态切换时清空）
        if main._state_hold_last_state != emotional_core.current_state.value:
            main._state_hold_start = time.time()
            main._state_hold_last_state = emotional_core.current_state.value
            main._state_hold_played.clear()
        # 持续 N 秒未变化 → 播放强化音（每状态最多 1 次，需切状态重置）
        hold_threshold_sec = 6.0  # 6 秒阈值
        if (audio_manager and audio_manager.is_available()
                and not audio_manager.is_muted()
                and emotional_core.current_state.value not in main._state_hold_played):
            hold_time = time.time() - main._state_hold_start
            cur_state = emotional_core.current_state.value
            if hold_time >= hold_threshold_sec:
                # 持续警示：play with low vol？
                # 警觉强化音门控（红圈外不播）
                in_red_zone_hold = False
                try:
                    in_red_zone_hold = personal_space.warning_level == 2
                except Exception:
                    in_red_zone_hold = False
                if cur_state == 'withdrawn':
                    # 持续退缩：再播一次高频警示
                    audio_manager.play('state_withdrawn')
                elif cur_state == 'alert':
                    if in_red_zone_hold:
                        audio_manager.play('enter_red')
                elif cur_state == 'open':
                    audio_manager.play('state_open')
                elif cur_state == 'neglected':
                    # 被忽视时可以使用 enter_red 提醒？
                    pass
                main._state_hold_played.add(cur_state)

        # 应用延迟后果
        for cons in triggered_consequences:
            if cons['type'] == 'harm':
                # 延迟的伤害效果：可在目标上添加疤痕
                # 音效：3秒延迟后播放伤害冲击音
                if audio_manager and audio_manager.is_available():
                    audio_manager.play('harm')
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

            # 音效：从外圈刚进入红圈时（prev_level != 2）播放警告音
            if prev_level != 2 and audio_manager and audio_manager.is_available():
                audio_manager.play('enter_red')

            # === 在红圈内持续追加"重"到时间线 ===
            # 每 1.2s 追加一条，让用户感受到"持续侵入"
            if not hasattr(_main_loop, '_last_alert_record_time'):
                _main_loop._last_alert_record_time = 0.0
            now_t = time.time()
            if now_t - _main_loop._last_alert_record_time >= 1.2:
                _main_loop._last_alert_record_time = now_t
                recent_actions.append({
                    'classification': 'negative',
                    'intensity': max(0.6, emotional_core.state_intensity),
                    'impact': max(0.7, emotional_core.state_intensity),  # 持续警觉影响（≥0.7 表示持续惊扰）
                    'time': now_t,
                    'reason': 'alert',  # 标记：因在红圈内持续
                })
                if len(recent_actions) > 8:
                    recent_actions.pop(0)
        elif current_level < 2:
            # 离开红圈：解锁警觉（恢复计时器继续）
            if getattr(personal_space, '_prev_warning_level', 0) == 2:
                # 刚离开红圈，解锁
                emotional_core.set_alert_lock(False)
                # 重置红圈记录节流，以便下次进入时立即记录
                if hasattr(_main_loop, '_last_alert_record_time'):
                    _main_loop._last_alert_record_time = 0.0
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

        # === P0-1: 生命体内心独白（绘制在生命体上方） ===
        current_monologue = emotional_core.get_monologue()
        if current_monologue != _last_monologue:
            # 独白变化时，重置 alpha 触发淡入
            _monologue_alpha = 0.0
            _last_monologue = current_monologue
        # 缓慢淡入
        _monologue_alpha = min(1.0, _monologue_alpha + dt * 1.5)
        if current_monologue and _monologue_alpha > 0.05:
            mono_color = status_bar._get_state_color(
                emotional_core.get_state_description()
            )
            mono_surf = font_medium.render(current_monologue, True, mono_color)
            mono_surf.set_alpha(int(220 * _monologue_alpha))
            mono_rect = mono_surf.get_rect(
                center=(int(target_object.x), int(target_object.y) - 110)
            )
            # 描边（让文字在背景上清晰）
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                edge = font_medium.render(current_monologue, True, (20, 18, 28))
                edge.set_alpha(int(180 * _monologue_alpha))
                edge_rect = edge.get_rect(
                    center=(int(target_object.x) + dx, int(target_object.y) - 110 + dy)
                )
                screen.blit(edge, edge_rect)
            screen.blit(mono_surf, mono_rect)

        # === P0-2: 行为时间线（状态栏上方） ===
        # 用"动作块"显示：每块含文字标签（轻/重/中）+ 颜色 + 强度条
        # 配合右侧图例，明白易懂
        # 上移避免被状态栏进度条遮挡（块高 28 + 图例行 ≈ 50，状态栏顶 670）
        tl_y = screen_h - status_bar.bar_height - 60
        tl_x_start = 20

        # === 主标题 ===
        title_surf = font.render("你的行为:", True, (170, 170, 180))
        screen.blit(title_surf, (tl_x_start, tl_y))
        block_x = tl_x_start + 110

        now = time.time()
        block_w = 36
        block_h = 28  # 加高 4 像素，让强度条放块内
        gap = 4
        for act in recent_actions[-8:]:
            # === 分类 → 文字 + 颜色 ===
            if act['classification'] == 'positive':
                text = "轻"
                bg_color = (90, 130, 80)         # 深绿底
                edge_color = (180, 220, 150)     # 亮绿描边
                text_color = (220, 240, 200)
                bar_color = (180, 220, 150)
            elif act['classification'] == 'negative':
                text = "重"
                bg_color = (130, 70, 60)         # 深红底
                edge_color = (240, 140, 110)     # 亮红描边
                text_color = (250, 200, 180)
                bar_color = (240, 140, 110)
            else:
                text = "中"
                bg_color = (70, 70, 80)
                edge_color = (150, 150, 160)
                text_color = (200, 200, 210)
                bar_color = (150, 150, 160)

            # === 透明度（按时间衰减） ===
            age = now - act['time']
            alpha = max(50, int(255 * (1.0 - age / 15.0)))

            # === 块背景（半透明圆角矩形） ===
            block_surf = pygame.Surface((block_w, block_h), pygame.SRCALPHA)
            pygame.draw.rect(
                block_surf, (*bg_color, alpha),
                (0, 0, block_w, block_h - 4), border_radius=4
            )
            pygame.draw.rect(
                block_surf, (*edge_color, min(255, alpha + 30)),
                (0, 0, block_w, block_h - 4), width=1, border_radius=4
            )

            # === 文字 ===
            text_surf = font.render(text, True, text_color)
            text_surf.set_alpha(alpha)
            text_rect = text_surf.get_rect(center=(block_w // 2, (block_h - 4) // 2))
            block_surf.blit(text_surf, text_rect)

            # === 强度条（块内部底部，固定长度，深浅=持续影响 impact） ===
            # 色条深浅 = impact 强度 × 时间衰减因子（与块整体同步衰减）
            # 含义：行为造成的影响会随时间慢慢变淡
            bar_w = block_w - 4  # 固定长度
            bar_h = 2
            # 影响强度（base_alpha） + 时间衰减（time_factor）
            impact = act.get('impact', act.get('intensity', 0.5))
            base_alpha = 30 + 225 * min(1.0, impact)
            # 与块整体同步衰减（15s 完全衰减，最低保留 30% 让痕迹一直可见）
            time_factor = max(0.3, 1.0 - (age / 15.0)) if 'age' in dir() else 1.0
            # 单独计算时间因子（避免依赖 age 局部变量）
            age_now = time.time() - act['time']
            time_factor = max(0.3, 1.0 - age_now / 15.0)
            bar_alpha = int(base_alpha * time_factor)
            pygame.draw.rect(
                block_surf, (*bar_color, bar_alpha),
                (2, block_h - 5, bar_w, bar_h), border_radius=1
            )

            screen.blit(block_surf, (block_x, tl_y))
            block_x += block_w + gap

        # === 图例（时间线块的上方一行，右对齐，分两行） ===
        if recent_actions:
            legend_items = [
                ("轻", (180, 220, 150)),
                ("重", (240, 140, 110)),
                ("中", (150, 150, 160)),
            ]
            # 估算每图例项宽度：24(块) + 6 + 30(字) = 60
            # 标题"图例: " 约 56 像素
            # 间距 10 像素
            total_w = 56 + len(legend_items) * 60 + 10
            # 右对齐（屏幕右边 20px 保护）
            legend_x = max(20, screen_w - total_w - 20)
            # 向上移动：时间线块上方 30px
            legend_y = tl_y - 30

            # 第一行：图例 + 三个色块（轻/重/中）
            tip_surf = font.render("图例:", True, (130, 130, 140))
            screen.blit(tip_surf, (legend_x, legend_y))
            lx = legend_x + 56
            for txt, col in legend_items:
                # 小色块
                chip = pygame.Surface((18, 14), pygame.SRCALPHA)
                pygame.draw.rect(chip, (*col, 200), (0, 0, 18, 14), border_radius=2)
                screen.blit(chip, (lx, legend_y + 4))
                lx += 24
                # 文字
                ts = font.render(txt, True, col)
                screen.blit(ts, (lx, legend_y))
                lx += 30

            # 第二行：色条深浅=影响（在第一行下方 28px = 20 + 8）
            intensity_hint = font.render("色条深浅=影响", True, (110, 110, 120))
            screen.blit(intensity_hint, (legend_x, legend_y + 28))

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
            "空格: 暂停反思  ESC: 退出",
            True, (120, 120, 130)
        )
        screen.blit(top_hint, (10, 10))

        # === 手部状态显示（替代 OpenCV 窗口，放在手势指示下方） ===
        if hand_position:
            # 手部检测成功
            hand_status = font.render(
                "Hand Detected!",
                True, (0, 200, 100)
            )
            screen.blit(hand_status, (10, 62))

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
            screen.blit(hand_status, (10, 62))

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

        # === 右上角：手势状态（替代 FPS 显示） ===
        cur_g_top = gesture_detector.get_current_gesture()
        if cur_g_top != 'unknown':
            # 手势识别中：显示名称 + 进度
            progress_top = gesture_detector.get_hold_progress()
            g_label_top = '✋ 张开手掌' if cur_g_top == 'open' else '✊ 握拳'
            color_top = (140, 200, 160) if cur_g_top == 'open' else (200, 130, 130)
            text_top = f"{g_label_top}  {progress_top * 100:.0f}%"
            hand_hint = font.render(text_top, True, color_top)
            screen.blit(hand_hint, (1280 - 240, 10))
            # 下方小进度条
            bar_y_top = 36
            bar_x_top = 1280 - 240
            bar_w_top = 220
            pygame.draw.rect(screen, (60, 58, 70),
                             (bar_x_top, bar_y_top, bar_w_top, 8), border_radius=4)
            fill_w_top = int(bar_w_top * progress_top)
            pygame.draw.rect(screen, color_top,
                             (bar_x_top, bar_y_top, fill_w_top, 8), border_radius=4)
        else:
            # 未识别手势：显示 FPS（兜底调试信息）
            fps_text = font.render(f"FPS: {_main_loop._fps_value:.1f}", True, (130, 130, 140))
            screen.blit(fps_text, (1280 - 100, 10))

        # === 静音状态显示（FPS 下方）===
        if audio_manager and audio_manager.is_available() and audio_manager.is_muted():
            mute_text = font.render("🔇 已静音 (M键开启)", True, (220, 100, 100))
            screen.blit(mute_text, (1280 - 220, 60))

        # === 手势持续时间进度提示：仅右上角显示（屏幕底部居中卡片已去除） ===
        # 此处保留空位以便以后扩展；右上角的实时提示在主循环前面已绘制

        # === 常驻手势提示（屏幕左上角，按键指示下方，仅在未触发时显示） ===
        cur_g_main2 = gesture_detector.get_current_gesture()
        if cur_g_main2 == 'unknown':
            hint_persist = font.render(
                "✋ 张开手掌 = 暂停反思  |  ✊ 握拳 = 退出",
                True, (160, 165, 175)
            )
            screen.blit(hint_persist, (10, 38))

        # === 处理暂停反思（在所有渲染之后画 overlay，仍需保持手势识别） ===
        if reflection_system.is_paused:
            draw_pause_overlay(
                screen, target_object, emotional_core,
                font_medium, font, 0.0
            )

        pygame.display.flip()
        frame_count += 1

    # === 退出前：保存数据导出（JSON 完整会话 + 文字报告） ===
    try:
        # 计算最终结局（从 target_object 获取 effect 累积）
        try:
            final_effect = float(target_object.effect_score) if hasattr(target_object, 'effect_score') else 0.0
        except Exception:
            final_effect = 0.0
        # 根据 effect_score 决定结局
        if final_effect > 0.3:
            ending = "care"
        elif final_effect < -0.3:
            ending = "harm"
        else:
            ending = "mixed"
        # 保存 JSON
        data_exporter.save_session(
            ending=ending,
            extra_data={
                'final_effect_score': final_effect,
                'positive_count': target_object.positive_count,
                'negative_count': target_object.negative_count,
                'total_fragments': target_object.fragment_count,
            }
        )
        # 生成并保存报告
        report_text = data_exporter.save_report(ending=ending)
        # 在终端打印报告（让用户看到）
        print("\n" + report_text)
    except Exception as e:
        print(f"[DataExporter] 退出时保存失败：{e}")
        import traceback
        traceback.print_exc()

    # === 退出前：显示反思界面 ===
    try:
        _show_reflection_screen(
            screen,
            font_large, font_medium, font,
            positive_count=target_object.positive_count,
            negative_count=target_object.negative_count,
            fragment_count=particle_system.get_particle_count() + target_object.fragment_count,
            gesture_detector=gesture_detector, hand_tracker=hand_tracker, cap=cap,
            relationship_quality=emotional_core.get_relationship_quality(),
            final_state=emotional_core.get_state_description(),
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


# 选择时刻对话框函数 _handle_choice_dialog 已移除


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
                             positive_count, negative_count, fragment_count,
                             gesture_detector=None, hand_tracker=None, cap=None,
                             relationship_quality=0.0, final_state="平静"):
    """
    结束反思界面：根据关系质量 + 生命体最终状态，给出反思文字

    结局判定（基于生命体状态条 / relationship_quality）：
        - 未交互：|quality| < 0.05 且 total == 0
        - 温柔（生命体被你治愈）：quality >= 0.4 且 final_state in ("敞开", "平静")
        - 平和：quality 在 [0.1, 0.4) 且 final_state != "退缩"
        - 急躁：quality 在 [-0.3, 0.1) 且 final_state != "退缩"
        - 粗暴：quality < -0.3 或 final_state in ("退缩", "被忽视")
    """
    clock = pygame.time.Clock()
    waiting = True
    blink = 0
    total = positive_count + negative_count

    # === 结局判定：以动作次数比例为主，以关系质量为辅助 ===
    # 主指标：positive_count / (positive_count + negative_count)
    # 辅指标：relationship_quality（生命体状态条的数值，仅在 total=0 时用）
    if total == 0:
        # 没有动作记录：用关系质量判断
        if abs(relationship_quality) < 0.05:
            ratio_label = "未交互"
            ratio_value = 0.0
        elif relationship_quality >= 0.3:
            ratio_label = "温柔"
            ratio_value = 1.0
        elif relationship_quality >= 0.05:
            ratio_label = "平和"
            ratio_value = 0.5
        elif relationship_quality >= -0.2:
            ratio_label = "急躁"
            ratio_value = -0.3
        else:
            ratio_label = "粗暴"
            ratio_value = -1.0
    else:
        # 有动作记录：以 positive 比例为主判定
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
    elif ratio_label == "温柔":
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
    elif ratio_label == "平和":
        reflection_lines = [
            f"这一次，你的动作以 {ratio_label} 为主。",
            f"  治愈动作 {positive_count} 次，伤害动作 {negative_count} 次。",
            "",
            "它正在慢慢舒展，",
            "暗色也减轻了一些。",
            "",
            "下一次，",
            "愿你再多一些耐心与贴近。",
        ]
    elif ratio_label == "急躁":
        reflection_lines = [
            f"这一次，你的动作以 {ratio_label} 为主。",
            f"  治愈动作 {positive_count} 次，伤害动作 {negative_count} 次。",
            "",
            "它的身上既有柔软的记忆，",
            "也留下了清晰的暗色疤痕。",
            "",
            "我们常常以为自己的言行无关紧要，",
            "但其实，痕迹正在累积。",
        ]
    else:  # 粗暴
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

        # === 手势控制：握拳关闭结算界面 ===
        if (gesture_detector is not None and hand_tracker is not None
                and cap is not None):
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                hand_tracker.get_hand_position(frame)
                landmarks_now = hand_tracker.get_landmarks()
                gesture_detector.update(landmarks_now)
                # 握拳事件触发即关闭
                if gesture_detector.consume_event() == 'close':
                    waiting = False
                    break

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
            f"  生命体最终状态：{final_state}",
            f"  总体倾向：{ratio_label}",
            "",
        ]
        _draw_text_lines(
            screen, stats_lines, font_medium,
            (200, 200, 210),
            screen.get_width() // 2, 180, line_spacing=40,
        )

        # === 关系质量条（与生命体状态条一致） ===
        bar_width = 400
        bar_height = 18
        bar_x = (screen.get_width() - bar_width) // 2
        bar_y = 340
        # 背景条
        pygame.draw.rect(screen, (40, 40, 50),
                         (bar_x, bar_y, bar_width, bar_height), border_radius=8)
        # 中线
        center_x = bar_x + bar_width // 2
        pygame.draw.line(screen, (150, 150, 160),
                         (center_x, bar_y - 4), (center_x, bar_y + bar_height + 4), 2)
        # 填充
        if relationship_quality >= 0:
            fill_w = int(bar_width * 0.5 * relationship_quality)
            color = (180, 220, 150)
            pygame.draw.rect(screen, color,
                             (center_x, bar_y, fill_w, bar_height), border_radius=8)
        else:
            fill_w = int(bar_width * 0.5 * abs(relationship_quality))
            color = (220, 120, 100)
            pygame.draw.rect(screen, color,
                             (center_x - fill_w, bar_y, fill_w, bar_height),
                             border_radius=8)
        # 标签
        q_label = font_medium.render(
            f"关系质量: {relationship_quality:+.2f}", True, (210, 210, 220)
        )
        q_rect = q_label.get_rect(center=(screen.get_width() // 2, bar_y + bar_height + 22))
        screen.blit(q_label, q_rect)

        # 反思正文
        _draw_text_lines(
            screen, reflection_lines, font_medium,
            (220, 215, 205),
            screen.get_width() // 2, 420, line_spacing=42,
        )

        # 闪烁提示
        blink = (blink + 1) % 60
        if blink < 40:
            hint = font.render("按 任意键 或 握拳  退出", True, (160, 160, 170))
            rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))
            screen.blit(hint, rect)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
