"""
新手引导模块
============
提供 8 张全屏引导卡，依次展示：
1. 主题
2. 核心问题
3. 操作方式
4. 生命体
5. 空间隐喻
6. 行为含义
7. 数据记录（强调有 3 个文件可查看）⭐
8. 开始提示

每张卡等待用户按任意键/点击切换；ESC 跳过所有卡直接进入。
"""

import sys
import pygame
import cv2


def _draw_text_lines(screen, lines, font, color, center_x, start_y, line_spacing=None):
    """居中绘制多行文字，返回最终 y 坐标（与 main.py 同款）"""
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


def show_tutorial(screen, font_large, font_medium, font,
                gesture_detector=None, hand_tracker=None, cap=None):
    """
    显示新手引导。

    参数:
        screen: pygame.Surface
        font_large: 大号字体（标题用）
        font_medium: 中号字体（正文用）
        font: 小号字体（提示用）

    行为:
        - 按任意键 / 点击鼠标 → 切换到下一张卡
        - ESC / Q → 跳过所有卡直接开始
        - 最后一页按任意键 → 开始
    """
    clock = pygame.time.Clock()
    page = 0
    blink = 0
    waiting = True

    # 所有引导卡（按顺序）
    pages = [
        # === 1. 主题 ===
        {
            "title": "留下的痕迹",
            "title_color": (232, 188, 132),
            "subtitle": "The Trace We Leave",
            "subtitle_color": (160, 130, 100),
            "body": [
                "",
                "",
                "一次关于「人际关系」的隐喻",
                "——",
                "你的每一个行为，都会在对方身上",
                "留下痕迹。",
            ],
            "body_color": (220, 215, 205),
            "tip": "按任意键继续",
        },
        # === 2. 核心问题 ===
        {
            "title": "在人与人的相处中",
            "title_color": (200, 180, 200),
            "subtitle": "",
            "body": [
                "",
                "",
                "我们的行为，会影响他人。",
                "",
                "那么——",
                "应该怎样控制自己的行为？",
            ],
            "body_color": (220, 215, 205),
            "tip": "按任意键继续",
        },
        # === 3. 操作方式 ===
        {
            "title": "操作方式",
            "title_color": (170, 210, 200),
            "subtitle": "How to interact",
            "body": [
                "",
                "举起你的手，对准摄像头",
                "",
                "指尖会出现黄色光标",
                "移动手部即可绘制轨迹",
                "",
                "静止 0.8 秒，动作结束",
            ],
            "body_color": (200, 220, 215),
            "tip": "按任意键继续",
        },
        # === 4. 生命体 ===
        {
            "title": "中心的生命体",
            "title_color": (220, 180, 180),
            "subtitle": "Another being",
            "body": [
                "",
                "它有情感，会记住你",
                "",
                "它的状态会随你的行为而改变",
                "它会通过颜色和形态表达感受",
                "",
                "它不是数据节点——它有内心",
            ],
            "body_color": (215, 200, 195),
            "tip": "按任意键继续",
        },
        # === 5. 空间隐喻 ===
        {
            "title": "空间与距离",
            "title_color": (220, 160, 140),
            "subtitle": "Personal space",
            "body": [
                "",
                "红圈 = 它的舒适区（进入 = 警觉）",
                "蓝圈 = 安全的社交距离",
                "",
                "你的手越接近中心，影响越深",
                "突然闯入 = 你靠得太近了",
            ],
            "body_color": (220, 200, 195),
            "tip": "按任意键继续",
        },
        # === 6. 行为含义 ===
        {
            "title": "你的行为会怎样",
            "title_color": (200, 220, 170),
            "subtitle": "What your actions mean",
            "body": [
                "",
                "轻柔、缓慢   =   治愈、信任",
                "剧烈、快速   =   伤害、退缩",
                "",
                "试着像对待真实的人一样——",
                "温柔地，慢慢地靠近",
            ],
            "body_color": (210, 220, 200),
            "tip": "按任意键继续",
        },
        # === 7. 数据记录 ⭐ 用户特别要求 ===
        {
            "title": "你的行为会被记录",
            "title_color": (180, 200, 230),
            "subtitle": "Session data export",
            "body": [
                "",
                "本次互动结束后，会生成 3 个文件：",
                "",
                "📄  actions_*.csv   每次行为的详细日志",
                "📦  session_*.json  完整会话数据",
                "📋  report_*.txt    可读的文字报告",
                "",
                "在程序目录的 sessions 文件夹中",
                "退出后即可查看",
            ],
            "body_color": (200, 215, 230),
            "tip": "按任意键继续",
        },
        # === 8. 开始 ===
        {
            "title": "准备好了吗？",
            "title_color": (240, 200, 140),
            "subtitle": "Are you ready",
            "body": [
                "",
                "",
                "请举起你的手",
                "",
                "——开始与它相处。",
            ],
            "body_color": (230, 220, 200),
            "tip": "按任意键开始",
        },
    ]

    # 清空事件队列，确保第一次按键立即生效
    pygame.event.clear()
    pygame.display.flip()

    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                # ESC/Q 跳过所有卡
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return
                # 其他任意键 → 下一张
                page += 1
                if page >= len(pages):
                    waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 点击鼠标 → 下一张
                page += 1
                if page >= len(pages):
                    waiting = False

        # 防止 while 循环最后再跑一次（page 已越界）
        if page >= len(pages):
            break

        # === 驱动摄像头 + 手势检测（每帧）===
        if hand_tracker is not None and cap is not None and gesture_detector is not None:
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)  # 镜像翻转（与主循环保持一致）
                hand_tracker.get_hand_position(frame)
                landmarks_now = hand_tracker.get_landmarks()
                gesture_detector.update(landmarks_now)

        # === 手势控制（每帧消费事件，避免堆积）===
        if gesture_detector is not None:
            evt = gesture_detector.consume_event()
            if evt == 'open':
                page += 1
                if page >= len(pages):
                    waiting = False
                    break
                continue  # 跳到下一帧，不渲染当前页（手感更顺畅）
            elif evt == 'close':
                return  # 跳过引导

        # === 渲染当前页 ===
        screen.fill((18, 16, 22))

        p = pages[page]

        # 顶部：主标题
        _draw_text_lines(
            screen, [p["title"]], font_large,
            p["title_color"],
            screen.get_width() // 2, 80, line_spacing=70,
        )

        # 副标题
        if p.get("subtitle"):
            _draw_text_lines(
                screen, [p["subtitle"]], font,
                p.get("subtitle_color", (140, 140, 150)),
                screen.get_width() // 2, 160, line_spacing=24,
            )

        # 主体内容
        _draw_text_lines(
            screen, p["body"], font_medium,
            p["body_color"],
            screen.get_width() // 2, 230, line_spacing=46,
        )

        # 分页指示（右下角）
        page_indicator = font.render(
            f"{page + 1} / {len(pages)}", True, (90, 90, 100)
        )
        screen.blit(page_indicator, (screen.get_width() - 80, screen.get_height() - 35))

        # 闪烁提示（底部）
        blink = (blink + 1) % 60
        if blink < 40:
            tip_color = (160, 160, 170) if page < len(pages) - 1 else (240, 200, 140)
            hint = font.render(p["tip"], True, tip_color)
            rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 60))
            screen.blit(hint, rect)

        # 跳过提示（左下角）
        skip = font.render("握拳跳过", True, (80, 80, 90))
        screen.blit(skip, (20, screen.get_height() - 35))

        # 翻页提示（右下角，仅当未触发手势时显示）
        if gesture_detector is None or gesture_detector.get_current_gesture() == 'unknown':
            advance_hint = font.render("张开手掌 → 下一张", True, (140, 180, 160))
            screen.blit(advance_hint, (screen.get_width() - 260, screen.get_height() - 35))

        # 手势持续进度（右下角）
        if gesture_detector is not None:
            gest_progress_t = gesture_detector.get_hold_progress()
            cur_g = gesture_detector.get_current_gesture()
            if cur_g != 'unknown' and gest_progress_t > 0:
                g_name = '张开手掌' if cur_g == 'open' else '握拳'
                bar_w = 120
                bar_x = screen.get_width() - bar_w - 20
                bar_y = screen.get_height() - 35
                # 进度条背景
                pygame.draw.rect(screen, (50, 50, 60), (bar_x, bar_y, bar_w, 8), border_radius=4)
                # 进度条填充
                fill_w = int(bar_w * gest_progress_t)
                fill_color = (140, 200, 160) if cur_g == 'open' else (200, 130, 130)
                pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_w, 8), border_radius=4)
                # 标签
                g_label_small = font.render(g_name, True, (180, 180, 195))
                screen.blit(g_label_small, (bar_x, bar_y - 22))

        pygame.display.flip()
        clock.tick(60)
