"""
视觉特效工具模块

纯 Pygame 实现，替代 py5 的以下视觉效果：
- Perlin Noise（形变 / 背景场 / 纹理）
- Blur（高斯模糊后期）
- Glow（辉光叠加）
- Trail（残影拖尾）
- Radial Gradient（径向渐变）
- Noise Field（背景噪声场）

无需 Java 依赖，无需额外 pip 安装。
"""

import math
import random
import numpy as np
from typing import List, Tuple, Optional
import pygame


# ============================================================
#  1. Perlin Noise
# ============================================================

class PerlinNoise:
    """
    2D Perlin Noise 实现

    用于：
    - 有机体形变（顶点偏移）
    - 背景噪声场（缓慢流动的渐变）
    - 纹理不规则性
    """

    # 梯度向量表（256 个方向）
    _GRAD2 = [
        (1, 1), (-1, 1), (1, -1), (-1, -1),
        (1, 0), (-1, 0), (0, 1), (0, -1),
    ]

    def __init__(self, seed: int = 0):
        self.perm = list(range(256))
        random.seed(seed)
        random.shuffle(self.perm)
        self.perm += self.perm  # 双倍长度，避免取模

    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """2D 梯度贡献"""
        g = self._GRAD2[hash_val % len(self._GRAD2)]
        return g[0] * x + g[1] * y

    def _fade(self, t: float) -> float:
        """Smoothstep 缓动"""
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def noise(self, x: float, y: float) -> float:
        """
        采样 2D Perlin Noise

        Args:
            x, y: 采样坐标（可以是非整数，可以是负数）

        Returns:
            noise 值 [-1, 1]
        """
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        p = self.perm
        aa = p[p[xi] + yi]
        ab = p[p[xi] + yi + 1]
        ba = p[p[xi + 1] + yi]
        bb = p[p[xi + 1] + yi + 1]

        return self._lerp(
            self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u),
            self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u),
            v,
        )

    def noise_octaves(self, x: float, y: float, octaves: int = 4,
                      persistence: float = 0.5) -> float:
        """
        多倍频叠加（fbm / 分形布朗运动）

        用于更丰富的纹理细节

        Args:
            x, y: 采样坐标
            octaves: 倍频数量
            persistence: 衰减系数

        Returns:
            叠加后的 noise 值 [-1, 1]（大致范围）
        """
        total = 0.0
        amplitude = 1.0
        max_val = 0.0
        frequency = 1.0

        for i in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= 2.0

        return total / max_val


# ============================================================
#  2. Blur（高斯模糊）
# ============================================================

def gaussian_blur(surface: pygame.Surface, radius: int = 2,
                  passes: int = 1) -> pygame.Surface:
    """
    对 pygame Surface 做高效近似高斯模糊

    使用缩放模糊（scale down + scale up）算法，
    比逐像素 box blur 快 10-50 倍。

    Args:
        surface: 输入 Surface（RGBA）
        radius: 模糊半径（越大越模糊，但越慢）
        passes: 模糊遍数（多次叠加更平滑）

    Returns:
        模糊后的新 Surface
    """
    if radius <= 0:
        return surface.copy()

    w, h = surface.get_size()

    # 缩放因子：半径越大，缩放越多，性能越好
    # 限制最小尺寸为 32x32，避免过度模糊
    scale = max(1.0, radius / 2.0)
    small_w = max(32, int(w / scale))
    small_h = max(32, int(h / scale))

    # 缩小
    small = pygame.transform.smoothscale(surface, (small_w, small_h))

    # 多次 passes：在缩小后的图像上做简单模糊
    for _ in range(passes):
        # 使用 pygame 内置的 smoothscale 作为快速模糊
        # 先稍微放大再缩回原尺寸，产生模糊效果
        temp = pygame.transform.smoothscale(small, (small_w + 2, small_h + 2))
        small = pygame.transform.smoothscale(temp, (small_w, small_h))

    # 放大回原始尺寸
    result = pygame.transform.smoothscale(small, (w, h))

    return result


# ============================================================
#  3. Glow（辉光叠加）
# ============================================================

def draw_glow(screen: pygame.Surface, center: Tuple[float, float],
              inner_radius: float, outer_radius: float,
              inner_color: Tuple[int, int, int, int],
              outer_color: Tuple[int, int, int, int],
              layers: int = 3):
    """
    绘制多层辉光（从内核向外扩散）- 优化版

    使用预计算的径向渐变纹理 + 缩放，减少实时计算。

    Args:
        screen: 目标 Surface
        center: 辉光中心 (x, y)
        inner_radius: 内核半径
        outer_radius: 外圈半径
        inner_color: 内核颜色 (r, g, b, a)
        outer_color: 外圈颜色 (r, g, b, a)
        layers: 叠加层数（建议 2-3）
    """
    cx, cy = int(center[0]), int(center[1])

    # 减少 layers 数量，使用更大的步长
    effective_layers = min(layers, 3)

    for i in range(effective_layers):
        t = i / (effective_layers - 1) if effective_layers > 1 else 0.0
        r = int(inner_radius + (outer_radius - inner_radius) * t)
        if r <= 0:
            continue

        # 简化的颜色计算
        ca = int(inner_color[3] * (1.0 - t * 0.7))
        if ca <= 10:
            continue

        # 使用径向渐变替代多层圆叠加
        color = (inner_color[0], inner_color[1], inner_color[2], ca)
        draw_radial_gradient(
            screen,
            center=(cx, cy),
            inner_radius=max(1, r // 3),
            outer_radius=r,
            inner_color=color,
            outer_color=(*outer_color[:3], 0),
            irregularity=0.0  # 禁用不规则以提升性能
        )


def draw_glow_polygon(screen: pygame.Surface,
                      vertices: List[Tuple[float, float]],
                      color: Tuple[int, int, int],
                      layers: int = 2):
    """
    绘制多边形辉光（用于碎片）- 优化版

    减少 layers 数量，使用更高效的绘制方式。

    Args:
        screen: 目标 Surface
        vertices: 多边形顶点（屏幕坐标）
        color: 基础颜色 (r, g, b)
        layers: 叠加层数（建议 2）
    """
    if len(vertices) < 3:
        return

    # 计算中心
    cx = sum(v[0] for v in vertices) / len(vertices)
    cy = sum(v[1] for v in vertices) / len(vertices)
    int_verts = [(int(v[0]), int(v[1])) for v in vertices]

    # 限制最大 layers
    effective_layers = min(layers, 2)

    for i in range(effective_layers):
        t = i / (effective_layers - 1) if effective_layers > 1 else 0.0
        alpha = int(60 * (1.0 - t))  # 降低基础透明度
        if alpha <= 5:
            continue
        scale = 1.0 + t * 0.5  # 减小缩放幅度
        scaled = [
            (int(cx + (v[0] - cx) * scale), int(cy + (v[1] - cy) * scale))
            for v in int_verts
        ]
        c = (*color, alpha)
        pygame.draw.polygon(screen, c, scaled)


# ============================================================
#  4. Trail（残影拖尾）
# ============================================================

class TrailSurface:
    """
    残影拖尾管理

    原理：保留上一帧的渲染结果，每帧用半透明黑色覆盖
    来"衰减"旧帧，然后叠加新帧。模拟 motion blur / trail。

    使用方式：
    - 每帧开始时调用 begin_frame()
    - 绘制所有内容到 trail_surface
    - 每帧结束时调用 end_frame() 将 trail_surface 叠加到 screen
    """

    def __init__(self, width: int, height: int, decay: float = 0.06):
        """
        Args:
            width, height: 画布尺寸
            decay: 每帧衰减比例 (0.0 - 1.0)
                   越大残影越短（0.06 约保留 16 帧）
        """
        self.width = width
        self.height = height
        self.decay = decay
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.surface.fill((0, 0, 0, 0))
        # 衰减遮罩（每帧覆盖旧帧）
        self._decay_mask = pygame.Surface((width, height), pygame.SRCALPHA)
        self._decay_mask.fill((0, 0, 0, int(255 * decay)))

    def begin_frame(self):
        """每帧开始：衰减上一帧"""
        self.surface.blit(self._decay_mask, (0, 0),
                          special_flags=pygame.BLEND_RGBA_SUB)

    def apply_to(self, target: pygame.Surface):
        """将 trail surface 叠加到目标 surface"""
        target.blit(self.surface, (0, 0))

    def clear(self):
        """完全清除 trail"""
        self.surface.fill((0, 0, 0, 0))


# ============================================================
#  5. Noise Field（背景噪声场）
# ============================================================

class BackgroundNoiseField:
    """
    背景噪声场

    生成缓慢流动的 Perlin noise 背景，颜色在深蓝→深紫之间渐变。

    使用方式：
    - 初始化时传入画布尺寸
    - 每帧调用 update() 推进时间
    - 调用 draw() 将背景绘制到 screen
    """

    def __init__(self, width: int, height: int,
                 resolution: int = 8, seed: int = 42):
        """
        Args:
            width, height: 画布尺寸
            resolution: 噪声网格分辨率（越小越细腻，但越慢）
            seed: 噪声种子
        """
        self.width = width
        self.height = height
        self.resolution = resolution
        self.cols = width // resolution + 1
        self.rows = height // resolution + 1

        self.noise = PerlinNoise(seed=seed)
        self.time = 0.0
        self._cached_surface = None

    def update(self, dt: float = 1.0 / 60.0):
        """推进噪声时间"""
        self.time += dt * 0.3  # 缓慢流动
        self._cached_surface = None  # 标记缓存失效

    def draw(self, screen: pygame.Surface):
        """
        绘制噪声背景到屏幕 - 优化版

        使用更大的采样网格 + 缩放，减少计算量。
        """
        w, h = self.width, self.height

        # 使用更低的分辨率生成噪声，然后放大
        # 大幅降低计算量
        low_res = 32  # 每 32 像素一个采样点
        cols = w // low_res + 1
        rows = h // low_res + 1

        # 创建低分辨率数组
        arr = np.zeros((cols, rows, 3), dtype=np.uint8)

        for row in range(rows):
            for col in range(cols):
                v = self.noise.noise_octaves(
                    col * 0.5 + self.time * 0.2,
                    row * 0.5 + self.time * 0.15,
                    octaves=2,  # 减少倍频
                    persistence=0.5,
                )

                # noise [-1, 1] → 颜色 [深蓝, 深紫]
                t = v * 0.5 + 0.5
                r = int(12 + (25 - 12) * t)
                g = int(15 + (18 - 15) * t)
                b = int(35 + (42 - 35) * t)

                arr[col, row] = (r, g, b)

        # 创建低分辨率 surface 并放大
        small_surf = pygame.surfarray.make_surface(arr)
        surf = pygame.transform.smoothscale(small_surf, (w, h))
        screen.blit(surf, (0, 0))
        del arr


# ============================================================
#  6. Radial Gradient（径向渐变）
# ============================================================

def draw_radial_gradient(screen: pygame.Surface,
                         center: Tuple[float, float],
                         inner_radius: float, outer_radius: float,
                         inner_color: Tuple[int, int, int, int],
                         outer_color: Tuple[int, int, int, int],
                         irregularity: float = 0.0):
    """
    绘制径向渐变圆（用于暗疤痕、辉光等的软边缘）

    支持 irregularity 参数制造不规则边缘（模拟"伤口"感）。

    Args:
        screen: 目标 Surface
        center: 中心 (x, y)
        inner_radius: 内核半径
        outer_radius: 外圈半径
        inner_color: 内核颜色 (r, g, b, a)
        outer_color: 外圈颜色 (r, g, b, a) 通常 alpha=0
        irregularity: 边缘不规则程度 (0 = 正圆, >0 = 扭曲)
    """
    max_r = int(outer_radius) + 2
    size = max_r * 2 + 4
    if size <= 0:
        return

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > outer_radius:
                continue

            t = max(0.0, min(1.0, dist / max(outer_radius, 1.0)))
            # 不规则边缘：在 dist 上叠加小幅度 noise
            if irregularity > 0.0 and dist > inner_radius:
                angle = math.atan2(dy, dx)
                noise_offset = (math.sin(angle * 7.3 + dist * 0.4) * 0.5 +
                                math.cos(angle * 13.7) * 0.3 +
                                math.sin(angle * 3.1) * 0.2) * irregularity * outer_radius * 0.12
                t = max(0.0, min(1.0, (dist + noise_offset) / max(outer_radius, 1.0)))

            # 颜色插值
            r = int(inner_color[0] + (outer_color[0] - inner_color[0]) * t)
            g = int(inner_color[1] + (outer_color[1] - inner_color[1]) * t)
            b = int(inner_color[2] + (outer_color[2] - inner_color[2]) * t)
            a = int(inner_color[3] + (outer_color[3] - inner_color[3]) * t)

            if a > 0:
                surf.set_at((x, y), (r, g, b, a))

    screen.blit(surf, (int(center[0]) - cx, int(center[1]) - cy))


# ============================================================
#  7. 综合后期处理
# ============================================================

def apply_post_processing(screen: pygame.Surface,
                          blur_radius: int = 0,
                          blur_passes: int = 1,
                          sharpen: float = 0.0) -> pygame.Surface:
    """
    后期处理：模糊 + 锐化

    Args:
        screen: 原始画面
        blur_radius: 模糊半径（0 = 不模糊）
        blur_passes: 模糊遍数
        sharpen: 锐化强度（0 = 不锐化，建议 0.1-0.3）

    Returns:
        处理后的 Surface
    """
    result = screen.copy()

    if blur_radius > 0:
        result = gaussian_blur(result, blur_radius, blur_passes)

    if sharpen > 0.01:
        # 锐化 = 原图 + (原图 - 模糊图) * sharpen
        blurred = gaussian_blur(result, 1, 1)
        arr = pygame.surfarray.pixels3d(result).astype(np.float64)
        arr_blur = pygame.surfarray.pixels3d(blurred).astype(np.float64)

        # 获取原始 screen 并锐化
        arr_orig = pygame.surfarray.pixels3d(screen).astype(np.float64)
        mask = arr_orig - arr_blur
        arr_sharp = np.clip(arr_orig + mask * sharpen, 0, 255).astype(np.uint8)

        result = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.surfarray.blit_array(result, arr_sharp)
        del arr, arr_blur, arr_orig, arr_sharp

    return result