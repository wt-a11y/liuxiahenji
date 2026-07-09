"""
膜扰动系统视觉测试

测试生命体对碎片吸收的动态反馈：
- CONTACT: 局部凹陷 + 涟漪
- ABSORBING: 整体收缩 + 内部纹理流动偏置
- COMPLETED: 恢复平静

运行：python test_membrane_disturbance.py
"""

import os
import sys
import pygame
import random
import math
import time

import target_object
from target_object import TargetObject, MembraneDisturbance


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Membrane Disturbance Test - Active Absorption Feedback")
    clock = pygame.time.Clock()

    # 创建生命体
    target = TargetObject(640, 360)
    print("生命体已创建")
    print(f"膜扰动系统: {target.membrane.disturbance}")

    # 阶段控制
    phase = "approaching"  # approaching -> contact -> absorbing -> completed
    phase_start_time = time.time()
    auto_trigger_contact = False
    auto_trigger_absorb = False
    auto_trigger_complete = False

    # 手动触发
    triggered = False  # 已触发接触扰动
    absorb_triggered = False  # 已触发吸收响应
    complete_triggered = False  # 已触发完成

    # 模拟一个外部碎片（在生命体右侧）
    fragment_x = 640 + 70
    fragment_y = 360
    fragment_angle = 0  # 右侧
    fragment_id = 999  # 模拟 fragment id
    fragment_intensity = 0.8

    # 截图点
    save_states = {
        'contact_impact': False,  # 接触瞬间（凹陷最深）
        'contact_rebound': False,  # 接触后回弹
        'ripple_spreading': False,  # 涟漪扩散中
        'absorbing_start': False,   # 吸收开始（收缩）
        'absorbing_mid': False,     # 吸收中期（收缩+流动偏置）
        'completed_recovery': False,  # 完成恢复中
        'completed_calm': False,    # 完成平静
    }

    print("\n控制说明：")
    print("  空格: 触发下一个阶段（contact → absorbing → completed）")
    print("  R: 重置")
    print("  ESC: 退出")
    print(f"\n初始阶段: approaching (模拟碎片在 (770, 360) 等待)")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # 手动触发下一阶段
                    if phase == "approaching" and not triggered:
                        target.on_fragment_contact(fragment_id, fragment_angle, fragment_intensity)
                        phase = "contact"
                        phase_start_time = time.time()
                        triggered = True
                        print(f"\n[CONTACT] 触发膜接触扰动 at angle={math.degrees(fragment_angle):.1f}°")
                    elif phase == "contact" and not absorb_triggered:
                        # 等 0.5 秒再触发吸收
                        if time.time() - phase_start_time > 0.5:
                            target.on_absorption_start(fragment_id, fragment_angle, fragment_intensity)
                            phase = "absorbing"
                            phase_start_time = time.time()
                            absorb_triggered = True
                            print(f"[ABSORBING] 启动吸收响应（收缩+流动偏置）")
                    elif phase == "absorbing" and not complete_triggered:
                        if time.time() - phase_start_time > 1.5:
                            target.on_absorption_complete(fragment_id)
                            phase = "completed"
                            phase_start_time = time.time()
                            complete_triggered = True
                            print(f"[COMPLETED] 释放吸收响应（恢复平静）")
                elif event.key == pygame.K_r:
                    # 重置
                    target = TargetObject(640, 360)
                    phase = "approaching"
                    triggered = False
                    absorb_triggered = False
                    complete_triggered = False
                    for k in save_states:
                        save_states[k] = False
                    print("\n[RESET] 生命体已重置")

        # === 自动触发（按阶段时间触发）===
        elapsed = time.time() - phase_start_time
        if phase == "approaching":
            # 模拟碎片停留 0.5 秒后自动接触
            if elapsed > 0.3 and not triggered:
                target.on_fragment_contact(fragment_id, fragment_angle, fragment_intensity)
                phase = "contact"
                phase_start_time = time.time()
                triggered = True
                print(f"\n[AUTO CONTACT] 触发膜接触扰动 at angle={math.degrees(fragment_angle):.1f}°")

        elif phase == "contact":
            # 接触停留 1.0 秒后自动开始吸收
            if elapsed > 1.0 and not absorb_triggered:
                target.on_absorption_start(fragment_id, fragment_angle, fragment_intensity)
                phase = "absorbing"
                phase_start_time = time.time()
                absorb_triggered = True
                print(f"[AUTO ABSORBING] 启动吸收响应（收缩+流动偏置）")

        elif phase == "absorbing":
            # 吸收 2.0 秒后自动完成
            if elapsed > 2.0 and not complete_triggered:
                target.on_absorption_complete(fragment_id)
                phase = "completed"
                phase_start_time = time.time()
                complete_triggered = True
                print(f"[AUTO COMPLETED] 释放吸收响应（恢复平静）")

        # 在 AUTO 触发后重新计算 elapsed（避免使用旧值）
        elapsed = time.time() - phase_start_time

        # === 更新 ===
        # 吸收过程中更新进度
        if phase == "absorbing":
            progress = min(1.0, elapsed / 2.0)
            target.on_absorption_progress(fragment_id, progress)
        elif phase == "completed":
            # 完成后保持小段进度
            target.on_absorption_progress(fragment_id, 1.0)

        target.update()

        # === 渲染 ===
        screen.fill((15, 15, 25))

        # 绘制生命体
        target.draw(screen)

        # 模拟碎片（吸收阶段才显示）
        if phase in ("approaching", "contact"):
            # 绘制模拟碎片
            pygame.draw.circle(screen, (255, 200, 100), (int(fragment_x), int(fragment_y)), 12)
            pygame.draw.circle(screen, (255, 230, 150), (int(fragment_x), int(fragment_y)), 6)

        # 显示信息
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        disturbance = target.membrane.disturbance

        info_lines = [
            f"Phase: {phase}",
            f"Membrane disturbance status:",
            f"  Active indents: {len(disturbance.contact_indents)}",
            f"  Active ripples: {len(disturbance.ripples)}",
            f"  Contraction: {disturbance.absorption_contraction:.3f}",
            f"  Flow bias: angle={math.degrees(disturbance.flow_bias_angle):.1f}° int={disturbance.flow_bias_intensity:.3f}" if disturbance.flow_bias_angle is not None else "  Flow bias: None",
            "",
            f"Life form impact_level: {target.impact_level:.3f}",
            f"Fragment count: {target.fragment_count}",
            "",
            "SPACE: next phase | R: reset | ESC: exit",
        ]

        y = 10
        for line in info_lines:
            color = (200, 220, 240)
            text = small_font.render(line, True, color)
            screen.blit(text, (10, y))
            y += 20

        # === 阶段截图 ===
        # 接触瞬间（凹陷开始下沉，~0.1s）
        if phase == "contact" and elapsed > 0.08 and elapsed < 0.20 and not save_states['contact_impact']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_contact_impact.png")
            pygame.image.save(screen, path)
            save_states['contact_impact'] = True
            print(f"[SCREENSHOT] 接触瞬间 -> {os.path.basename(path)}")

        # 接触回弹（凹陷回弹阶段，~0.5s）
        if phase == "contact" and elapsed > 0.45 and elapsed < 0.55 and not save_states['contact_rebound']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_contact_rebound.png")
            pygame.image.save(screen, path)
            save_states['contact_rebound'] = True
            print(f"[SCREENSHOT] 接触回弹 -> {os.path.basename(path)}")

        # 涟漪扩散中
        if phase == "contact" and elapsed > 0.7 and elapsed < 0.85 and not save_states['ripple_spreading']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_ripple_spreading.png")
            pygame.image.save(screen, path)
            save_states['ripple_spreading'] = True
            print(f"[SCREENSHOT] 涟漪扩散 -> {os.path.basename(path)}")

        # 吸收开始
        if phase == "absorbing" and elapsed > 0.05 and elapsed < 0.20 and not save_states['absorbing_start']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_absorbing_start.png")
            pygame.image.save(screen, path)
            save_states['absorbing_start'] = True
            print(f"[SCREENSHOT] 吸收开始（收缩） -> {os.path.basename(path)}")

        # 吸收中期（收缩+流动偏置）
        if phase == "absorbing" and elapsed > 1.0 and elapsed < 1.15 and not save_states['absorbing_mid']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_absorbing_mid.png")
            pygame.image.save(screen, path)
            save_states['absorbing_mid'] = True
            print(f"[SCREENSHOT] 吸收中期 -> {os.path.basename(path)}")

        # 完成恢复中
        if phase == "completed" and elapsed > 0.2 and elapsed < 0.35 and not save_states['completed_recovery']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_completed_recovery.png")
            pygame.image.save(screen, path)
            save_states['completed_recovery'] = True
            print(f"[SCREENSHOT] 完成恢复中 -> {os.path.basename(path)}")

        # 完成平静
        if phase == "completed" and elapsed > 1.5 and not save_states['completed_calm']:
            path = os.path.join(os.path.dirname(__file__), "disturbance_completed_calm.png")
            pygame.image.save(screen, path)
            save_states['completed_calm'] = True
            print(f"[SCREENSHOT] 完成平静 -> {os.path.basename(path)}")

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
