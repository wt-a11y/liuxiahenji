"""
视觉测试脚本 - 渲染记忆碎片并保存截图
"""
import os
import sys
import pygame
import random
import math
import time

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import particle_system


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Crystal Visual Test")

    # 预创建多个碎片，分布在不同位置和强度
    fragments = []
    random.seed(42)  # 固定随机种子

    for i in range(12):
        x = 200 + (i % 4) * 250 + random.uniform(-30, 30)
        y = 200 + (i // 4) * 150 + random.uniform(-30, 30)
        intensity = random.uniform(0.5, 1.0)
        f = particle_system.MemoryFragment(x, y, intensity=intensity)
        # 让一些碎片处于不同状态
        f.rotation_angle = random.uniform(0, 2 * math.pi)
        # 锁定在floating状态，添加残影让效果更明显
        f.state = 'floating'
        f.base_x = x
        f.base_y = y
        # 添加残影位置以显示残影效果
        for k in range(4):
            f.trail_positions.append((x - k * 6, y + k * 3, f.base_transparency))
        fragments.append(f)

    # 创建粒子系统并添加
    ps = particle_system.ParticleSystem()
    ps.memory_cloud.fragments = fragments
    # 不设置target，避免drift状态干扰

    # 渲染若干帧，捕捉视觉效果
    clock = pygame.time.Clock()
    frame_count = 30
    for frame in range(frame_count):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # 渲染（不调用update，避免位置改变）
        screen.fill((15, 15, 25))

        # 绘制参考网格（中心）
        pygame.draw.circle(screen, (60, 60, 80), (640, 360), 100, 1)

        # 绘制碎片
        ps.draw(screen)

        # 帧数文字
        font = pygame.font.Font(None, 24)
        text = font.render(f"Frame {frame}/{frame_count}", True, (200, 200, 200))
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    # 保存截图
    output_path = os.path.join(os.path.dirname(__file__), "crystal_visual.png")
    pygame.image.save(screen, output_path)
    print(f"Screenshot saved to: {output_path}")
    print(f"Fragments rendered: {len(fragments)}")
    print(f"All with internal texture: {all(f.internal_texture is not None for f in fragments)}")

    pygame.quit()


if __name__ == "__main__":
    main()
