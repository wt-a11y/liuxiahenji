"""
视觉测试 - 模拟碎片进入生命体的完整过程
5阶段状态机：APPROACHING → CONTACT → ABSORBING → INTEGRATING → COMPLETED
"""
import os
import sys
import pygame
import random
import math
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import particle_system
import target_object


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Fragment Absorption Test - 5-Stage State Machine")

    # 创建生命体（屏幕中央）
    life_form = target_object.TargetObject(640, 360)
    target_pos = (640, 360)
    life_form_radius = 60

    # 创建一个碎片，初始位置在生命体外
    random.seed(42)
    fragment = particle_system.MemoryFragment(900, 200, intensity=0.8)
    # 跳过前面的floating/settling，直接进入approaching
    fragment._transition_to('approaching', target_pos)

    ps = particle_system.ParticleSystem()
    ps.set_target(target_pos)
    ps.memory_cloud.fragments = [fragment]

    # 模拟过程，记录不同距离/状态的截图
    screenshots = []
    clock = pygame.time.Clock()
    max_frames = 500  # 模拟足够长时间

    # 距离截图点（APPROACHING阶段）
    save_at_distances = [200, 150, 100, 80, 70, 60]
    # 状态截图点
    save_states = {
        'approaching': False,  # 已在距离截图覆盖
        'contact': False,
        'absorbing_30': False,
        'absorbing_50': False,
        'absorbing_80': False,
        'integrating': False,
    }

    for frame in range(max_frames):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # 更新
        ps.update()

        # 渲染
        screen.fill((28, 26, 24))

        # 绘制碎片（在生命体之前）
        ps.draw(screen)

        # 绘制生命体（在碎片之后，覆盖）
        life_form.update()
        life_form.draw(screen)

        # 显示状态
        font = pygame.font.Font(None, 22)
        state = fragment.get_state()
        state_text = f"State: {state}"
        dist_text = f"Distance: {fragment.current_distance_to_target:.1f}"
        trans_text = f"Transparency: {fragment.transparency:.2f}"
        scale_text = f"Size scale: {fragment.size_scale:.2f}"
        abs_text = f"Absorb Progress: {fragment.absorption_progress:.2f}" if state in ('absorbing', 'integrating') else ""
        diff_text = f"Diffusion: {fragment.color_diffusion_intensity:.2f}" if state in ('absorbing', 'integrating') else ""
        jit_text = f"Vertex Jitter: {fragment.vertex_jitter_base:.2f}" if state in ('absorbing', 'integrating') else ""
        for i, text in enumerate([state_text, dist_text, trans_text, scale_text, abs_text, diff_text, jit_text]):
            if not text:
                continue
            t = font.render(text, True, (200, 200, 200))
            screen.blit(t, (10, 10 + i * 22))

        pygame.display.flip()

        # 距离截图 - 只在 approaching 阶段记录
        if state == 'approaching':
            d = fragment.current_distance_to_target
            for save_d in save_at_distances:
                if save_d not in [s[0] for s in screenshots]:
                    if abs(d - save_d) < 3 or (d < save_d):
                        path = os.path.join(os.path.dirname(__file__),
                                            f"absorption_approaching_{int(save_d):03d}.png")
                        pygame.image.save(screen, path)
                        screenshots.append((save_d, path))
                        print(f"[distance={d:.1f}, state={state}] -> {os.path.basename(path)}")
                        break

        # 状态截图
        if state == 'contact' and not save_states['contact']:
            path = os.path.join(os.path.dirname(__file__), "absorption_contact.png")
            pygame.image.save(screen, path)
            screenshots.append(('contact', path))
            save_states['contact'] = True
            print(f"[CONTACT state] -> {os.path.basename(path)}")
        elif state == 'absorbing':
            p = fragment.absorption_progress
            if p >= 0.3 and not save_states['absorbing_30']:
                path = os.path.join(os.path.dirname(__file__), "absorption_absorbing_30.png")
                pygame.image.save(screen, path)
                screenshots.append(('absorb_30', path))
                save_states['absorbing_30'] = True
                print(f"[ABSORBING 30%] -> {os.path.basename(path)}")
            if p >= 0.5 and not save_states['absorbing_50']:
                path = os.path.join(os.path.dirname(__file__), "absorption_absorbing_50.png")
                pygame.image.save(screen, path)
                screenshots.append(('absorb_50', path))
                save_states['absorbing_50'] = True
                print(f"[ABSORBING 50%] -> {os.path.basename(path)}")
            if p >= 0.8 and not save_states['absorbing_80']:
                path = os.path.join(os.path.dirname(__file__), "absorption_absorbing_80.png")
                pygame.image.save(screen, path)
                screenshots.append(('absorb_80', path))
                save_states['absorbing_80'] = True
                print(f"[ABSORBING 80%] -> {os.path.basename(path)}")
        elif state == 'integrating' and not save_states['integrating']:
            path = os.path.join(os.path.dirname(__file__), "absorption_integrating.png")
            pygame.image.save(screen, path)
            screenshots.append(('integrating', path))
            save_states['integrating'] = True
            print(f"[INTEGRATING state] -> {os.path.basename(path)}")

        clock.tick(60)

        # 碎片已完成（被移除）
        if state == 'integrating' and fragment.transparency <= 0.05:
            print(f"Fragment faded out at frame {frame}")
            break

    print(f"\nTotal screenshots: {len(screenshots)}")
    print("Files:")
    for k, p in screenshots:
        print(f"  {k}: {p}")

    pygame.quit()


if __name__ == "__main__":
    main()
