"""
长期影响系统测试 - MemoryLayer 多次吸收效果

测试：
- 第1次吸收：内部出现新纹理
- 第2次吸收：方向改变，与已有纹理交叉
- 第3次吸收：结构变化（多分支）
- 第4+次：与最早记忆层共振
- 多次吸收：生命体内部已显著不同

运行：python test_memory_layers.py
"""

import os
import sys
import pygame
import math
import random
import time

from target_object import TargetObject


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Memory Layers Test - Long-term Internal Changes")
    clock = pygame.time.Clock()

    target = TargetObject(640, 360)

    # 模拟多次吸收，每次在不同角度
    # 测试中我们调用 receive_impact 多次，每次在不同方向
    absorption_sequence = [
        # (angle_deg, intensity, label)
        (0, 0.6, "1st-0deg"),       # 第一次 - 右侧
        (90, 0.7, "2nd-90deg"),      # 第二次 - 上方
        (180, 0.5, "3rd-180deg"),    # 第三次 - 左侧
        (270, 0.8, "4th-270deg"),    # 第四次 - 下方
        (45, 0.6, "5th-45deg"),      # 第五次
        (135, 0.7, "6th-135deg"),    # 第六次
        (225, 0.5, "7th-225deg"),    # 第七次 - 共振
    ]

    absorption_index = 0
    pending_absorption = None  # (angle_deg, intensity, label)
    absorption_applied = False

    # 让记忆层生长的等待时间
    growth_wait_frames = 0

    screenshots = {}

    print("=" * 60)
    print("Memory Layers Test - 长期影响")
    print("=" * 60)
    print("\n将依次应用7次吸收在不同方向。")
    print("每次吸收后等待 200 帧让记忆层生长。\n")

    running = True
    frame = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # 自动应用吸收序列
        if absorption_index < len(absorption_sequence) and pending_absorption is None:
            angle_deg, intensity, label = absorption_sequence[absorption_index]
            angle = math.radians(angle_deg)
            # 距离生命体中心 80 像素（膜外）
            distance = 80
            source_pos = {
                'x': target.x + math.cos(angle) * distance,
                'y': target.y + math.sin(angle) * distance,
            }
            target.receive_impact(value=intensity, source_position=source_pos)
            pending_absorption = (angle_deg, intensity, label)
            absorption_applied = False
            print(f"[应用] {label} 强度={intensity:.2f} 方向={angle_deg}°")

        # 等待生长
        if pending_absorption is not None:
            if not absorption_applied:
                absorption_applied = True
                growth_wait_frames = 0
            growth_wait_frames += 1

            # 200 帧后（约3.3秒），截图
            if growth_wait_frames > 200:
                label = pending_absorption[2]
                screenshot_name = f"memory_layer_{label}.png"
                path = os.path.join(os.path.dirname(__file__), screenshot_name)
                # 强制绘制一次再保存
                target.update()
                screen.fill((15, 15, 25))
                target.draw(screen)
                # 显示信息
                font = pygame.font.Font(None, 22)
                info = [
                    f"Frame: {frame}",
                    f"Memory Layers: {len(target.memory_layers)}",
                    f"Structure Changes: {target.structure_changes}",
                    f"Internal Traces: {target.internal_traces}",
                    f"Latest: {label}",
                ]
                y = 10
                for line in info:
                    text = font.render(line, True, (220, 220, 240))
                    screen.blit(text, (10, y))
                    y += 22
                pygame.image.save(screen, path)
                screenshots[label] = path
                print(f"[截图] {screenshot_name} (记忆层={len(target.memory_layers)}, "
                      f"结构变化={target.structure_changes}, 内部痕迹={target.internal_traces})")

                pending_absorption = None
                absorption_index += 1

        # 更新
        target.update()

        # 渲染
        screen.fill((15, 15, 25))
        target.draw(screen)

        # 显示信息
        font = pygame.font.Font(None, 22)
        small_font = pygame.font.Font(None, 18)
        info = [
            f"Frame: {frame}",
            f"Memory Layers: {len(target.memory_layers)}",
            f"Structure Changes: {target.structure_changes}",
            f"Internal Traces: {target.internal_traces}",
            f"Impact Level: {target.impact_level:.3f}",
            f"Fragment Count: {target.fragment_count}",
            f"",
        ]
        if pending_absorption:
            label = pending_absorption[2]
            info.append(f"Current: {label} (waiting {growth_wait_frames}/200 frames)")

        y = 10
        for line in info:
            text = font.render(line, True, (220, 220, 240))
            screen.blit(text, (10, y))
            y += 22

        # 显示当前记忆层详情
        if target.memory_layers:
            y += 10
            text = small_font.render("Memory layers:", True, (200, 200, 220))
            screen.blit(text, (10, y))
            y += 18
            for i, layer in enumerate(target.memory_layers):
                txt = f"  L{i}: idx={layer.layer_index} structure={layer.is_structure} " \
                      f"growth={layer.growth:.2f} angle={math.degrees(layer.impact_angle):.0f}°"
                text = small_font.render(txt, True, (180, 200, 220))
                screen.blit(text, (10, y))
                y += 16

        pygame.display.flip()
        clock.tick(60)
        frame += 1

        # 完成所有吸收后再跑一会就退出
        if absorption_index >= len(absorption_sequence) and pending_absorption is None:
            # 等 100 帧让最终效果稳定
            if growth_wait_frames > 100:
                running = False

    pygame.quit()

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    for label, path in screenshots.items():
        size = os.path.getsize(path)
        print(f"  {label}: {os.path.basename(path)} ({size} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
