"""
粒子系统模块

记忆碎片系统 - 半透明、有机的记忆残留
行为痕迹以记忆碎片形式存在，沉积、漂移、渗透进入目标

可直接运行测试：python particle_system.py
"""

import pygame
import random
import math
from typing import List, Tuple, Optional, Dict
import time


# 用于为每个 MemoryFragment 分配唯一 id
_MEMORY_FRAGMENT_ID_COUNTER = [0]


def _next_fragment_id() -> int:
    """生成下一个唯一的 fragment id"""
    _MEMORY_FRAGMENT_ID_COUNTER[0] += 1
    return _MEMORY_FRAGMENT_ID_COUNTER[0]


class MemoryFragment:
    """
    记忆碎片
    
    代表行为痕迹的半透明有机残留
    不规则碎片形态，有旋转和残影效果
    """
    
    def __init__(self, x: float, y: float,
                 intensity: float = 0.5,
                 behavior_speed: float = 0.0,
                 behavior_distance: float = 0.0):
        """
        初始化记忆碎片 - 半透明晶体状碎片

        Args:
            x, y: 初始位置
            intensity: 碎片强度 (0.0 - 1.0)
            behavior_speed: 行为速度
            behavior_distance: 行为距离
        """
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y

        # 唯一标识
        self.id = _next_fragment_id()

        # 碎片属性
        self.intensity = intensity
        self.size = random.uniform(9, 16) * (0.6 + intensity * 0.5)

        # === 晶体形态：不规则多边形 + 方向感 ===
        self._init_crystal_shape()

        # === 旋转 ===
        self.rotation_angle = random.uniform(0, 2 * math.pi)
        self.rotation_speed = random.uniform(-0.012, 0.012)  # 缓慢旋转

        # === 透明度（含轻微脉动） ===
        self.phase = random.uniform(0, 2 * math.pi)
        self.base_transparency = 0.62 + intensity * 0.30
        self.transparency = self.base_transparency
        # _target_transparency 是状态机计算的"基准"透明度（不含脉动）
        # 脉动每帧基于 _target_transparency 重新计算，避免乘法累积导致衰减
        self._target_transparency = self.base_transparency

        # === 颜色调色板：柔和琥珀系（避免高饱和黄） ===
        # 主体：明亮暖琥珀（半透明叠加会变暗，所以用偏亮的基底色）
        self.body_color = (232, 188, 132)
        # 内部核心：更亮、更暖
        self.inner_color = (250, 218, 170)
        # 辉光：温暖的暖橙
        self.glow_color = (235, 185, 130)
        # 高光：近白暖色
        self.highlight_color = (255, 244, 222)
        # 兼容旧接口
        self.base_color = self.body_color
        self.current_color = self.body_color

        # === 残影（晶体经过时留下的光点） ===
        self.trail_positions: List[Tuple[float, float, float]] = []
        self.max_trail_length = 4

        # === 高光位置（在主体内随机偏置，营造不对称感） ===
        self.highlight_offset = (
            random.uniform(-self.size * 0.25, self.size * 0.25),
            random.uniform(-self.size * 0.25, self.size * 0.25)
        )
        self.highlight_size = self.size * random.uniform(0.25, 0.4)

        # === 内部折射纹理（Pillow生成） ===
        self.internal_texture = self._generate_internal_texture()
        self.texture_size = self.size * 1.6  # 纹理在主体内显示的尺寸

        # 状态
        # 完整流程：floating → settling → approaching → contact → absorbing → integrating → (移除)
        # 注意：吸收完成后由 update() 返回 True，从碎片列表中移除
        self.state = 'floating'
        self.state_start_time = time.time()

        # 状态变化追踪（用于通知 TargetObject 触发相应的膜扰动）
        self.previous_state = None
        self.state_changed = False  # 当前帧是否刚发生状态变化

        # 沉积阶段
        self.settle_target_x = x + random.uniform(-20, 20)
        self.settle_target_y = y + random.uniform(15, 35)
        self.settle_speed = random.uniform(0.2, 0.4)

        # 漂移阶段
        self.drift_target = None
        self.drift_speed = 2.5

        # 速度向量
        self.vx = 0.0
        self.vy = 0.0

        # 膜边界距离
        self.membrane_approach_range = 80
        self.membrane_touch_range = 65
        self.membrane_penetration_range = 45
        self.current_distance_to_target = 1000

        # === 5阶段吸收状态机 ===
        # floating → settling → approaching → contact → absorbing → integrating → completed
        # 替换旧的 drifting / penetrating
        self.absorption_state = 'approaching'  # approaching/contact/absorbing/integrating
        self.absorption_progress = 0.0          # 当前阶段内部进度 [0, 1]

        # approaching：漂浮感
        self.approach_lateral_phase = random.uniform(0, 2 * math.pi)
        self.approach_lateral_amplitude = random.uniform(8, 18)  # 侧向漂浮幅度
        self.approach_lateral_speed = random.uniform(0.6, 1.2)   # 侧向漂浮频率
        self.approach_lateral_drift = random.uniform(0, 2 * math.pi)  # 漂浮方向偏移

        # contact：停留时间（碎片接触膜后等一会儿再被吸收）
        self.contact_duration = random.uniform(0.6, 1.1)

        # absorbing：吸收动画时长
        self.absorbing_duration = random.uniform(1.6, 2.2)
        # 晶体瓦解 - 顶点抖动量（absorbing阶段会逐渐增大）
        self.vertex_jitter_base = 0.0
        # 边缘模糊起始alpha（0=清晰，越大越模糊）

        # 兼容旧字段名（保留接口）
        self.penetration_progress = 0.0
        self.penetration_speed = 1.0 / 180.0
        self.size_scale = 1.0
        self.is_touching_membrane = False
        self.has_penetrated_membrane = False

        # 颜色扩散（absorbing阶段的视觉重点）
        self.color_diffusion_intensity = 0.0  # 0=无扩散，1=完全扩散

        # 生命周期
        self.birth_time = time.time()
        self.max_lifetime = 60

    def _init_crystal_shape(self):
        """初始化不规则晶体形态 - 有方向感的尖端 + 不对称分布"""
        self.num_vertices = random.randint(6, 8)
        self.vertex_angles: List[float] = []
        self.vertex_distances: List[float] = []

        # 主轴方向（尖端方向）
        self.tip_angle = random.uniform(0, 2 * math.pi)
        # 尖端顶点索引
        self.tip_vertex_idx = 0

        for i in range(self.num_vertices):
            # 顶点角度：沿周向不均匀分布，尖端方向有突出
            t = i / self.num_vertices
            # 基础角度从尖端对面开始，环绕一周
            base_angle = self.tip_angle + math.pi
            angle = base_angle + t * 2 * math.pi
            # 加上随机扰动（制造不规则感）
            angle += random.uniform(-0.18, 0.18)
            self.vertex_angles.append(angle)

            # 距离：第一个顶点（尖端）更远，其他更短且随机
            if i == self.tip_vertex_idx:
                distance = random.uniform(1.25, 1.5)
            else:
                distance = random.uniform(0.6, 1.0)
            self.vertex_distances.append(distance)

    def _generate_internal_texture(self) -> Optional[pygame.Surface]:
        """使用Pillow生成晶体的内部折射纹理

        包含：
        - 放射状"棱"线条（晶面边界）
        - 折射高光亮点
        - 整体柔和模糊
        """
        try:
            from PIL import Image, ImageDraw, ImageFilter
        except ImportError:
            return None

        size = 128  # 纹理分辨率（提高以获得更清晰细节）
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2

        # 1) 内部棱 - 从中心放射的细线（晶面边界）
        num_facets = random.randint(5, 7)
        for _ in range(num_facets):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(32, 52)
            x2 = cx + math.cos(angle) * length
            y2 = cy + math.sin(angle) * length
            # 棱用亮色高对比，模拟光线在晶体内部反射
            alpha = random.randint(140, 200)
            draw.line([(cx, cy), (x2, y2)],
                      fill=(255, 245, 220, alpha), width=2)

        # 2) 折射高光 - 几个小亮点（更亮更大）
        for _ in range(random.randint(4, 6)):
            bx = cx + random.uniform(-30, 30)
            by = cy + random.uniform(-30, 30)
            br = random.uniform(1.2, 2.8)
            # 亮白色，模拟光折射
            draw.ellipse([bx - br, by - br, bx + br, by + br],
                         fill=(255, 250, 235, random.randint(200, 255)))

        # 3) 一些小的内部次棱（更细的线）
        for _ in range(random.randint(2, 4)):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(15, 30)
            x2 = cx + math.cos(angle) * length
            y2 = cy + math.sin(angle) * length
            draw.line([(cx, cy), (x2, y2)],
                      fill=(255, 235, 200, random.randint(80, 130)), width=1)

        # 4) 柔和模糊（让边缘更自然）
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

        # 转为pygame surface（不调用convert_alpha，需要display初始化）
        texture = pygame.image.fromstring(
            img.tobytes(), img.size, img.mode
        )
        return texture
        
    def update(self, target_position: Optional[Tuple[float, float]] = None):
        """
        更新碎片状态
        
        Args:
            target_position: 目标对象位置，用于漂移阶段
        """
        current_time = time.time()
        state_duration = current_time - self.state_start_time

        # 更新旋转
        self.rotation_angle += self.rotation_speed

        # 记录残影位置（只在接近生命体之前的状态）
        if self.state in ['floating', 'settling', 'approaching']:
            self.trail_positions.append((self.x, self.y, self.transparency * 0.5))
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)

        # 状态机
        if self.state == 'floating':
            # 悬浮阶段 - 轻微摆动（更安静）
            self.x += math.sin(current_time * 1.5 + self.base_x) * 0.15
            self.y += math.cos(current_time * 1.2 + self.base_y) * 0.1

            # 5秒后进入沉积阶段
            if state_duration > 5.0:
                self._transition_to('settling')

        elif self.state == 'settling':
            # 沉积阶段 - 缓慢移动到沉积位置
            dx = self.settle_target_x - self.x
            dy = self.settle_target_y - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance > 1:
                self.x += (dx / distance) * self.settle_speed
                self.y += (dy / distance) * self.settle_speed
            else:
                # 到达沉积位置，停留一段时间
                if state_duration > 12.0:
                    if target_position:
                        self._transition_to('approaching', target_position)
                    else:
                        self._transition_to('floating')

        elif self.state == 'approaching':
            # APPROACHING: 漂浮靠近，接近时减速
            is_touching = False  # 初始化默认值
            if target_position:
                dx = target_position[0] - self.x
                dy = target_position[1] - self.y
                self.current_distance_to_target = math.sqrt(dx ** 2 + dy ** 2)

                if self.current_distance_to_target > 0:
                    dir_x = dx / self.current_distance_to_target
                    dir_y = dy / self.current_distance_to_target
                else:
                    dir_x, dir_y = 0, 0

                # 速度随距离递减：远时 1.0x，膜边界时 0.4x
                if self.current_distance_to_target > self.membrane_touch_range:
                    # 在 approach_range 内开始减速
                    if self.current_distance_to_target < self.membrane_approach_range:
                        is_touching = True
                        # 减速比例：从 approach_range(80) 到 touch_range(65) 线性从 1.0 → 0.4
                        slow_factor = 0.4 + 0.6 * (self.current_distance_to_target - self.membrane_touch_range) / (self.membrane_approach_range - self.membrane_touch_range)
                        current_speed = self.drift_speed * slow_factor
                    else:
                        is_touching = False
                        current_speed = self.drift_speed
                else:
                    # 已接触膜 - 转入CONTACT状态
                    self.is_touching_membrane = True
                    self.has_penetrated_membrane = True
                    self._transition_to('contact', target_position)
                    current_speed = 0

                # 侧向漂浮（垂直于目标方向）
                # 漂浮振幅随距离缩小（接近膜时更"安静"）
                proximity = max(0.0, min(1.0,
                    (self.membrane_approach_range - self.current_distance_to_target)
                    / self.membrane_approach_range))
                lateral_amp = self.approach_lateral_amplitude * (1.0 - proximity * 0.6)

                # 侧向单位向量（垂直于主方向）
                perp_x = -dir_y
                perp_y = dir_x

                # 漂浮位移（正弦摆动 + 缓慢漂移）
                wobble = math.sin(current_time * self.approach_lateral_speed
                                  + self.approach_lateral_phase) * lateral_amp
                drift = math.sin(current_time * 0.3
                                 + self.approach_lateral_drift) * lateral_amp * 0.3

                # 接触膜时停侧向漂浮
                if self.current_distance_to_target <= self.membrane_touch_range:
                    wobble = 0
                    drift = 0

                # 更新位置：径向移动 + 侧向漂浮
                self.x += dir_x * current_speed + perp_x * (wobble * 0.04 + drift * 0.02)
                self.y += dir_y * current_speed + perp_y * (wobble * 0.04 + drift * 0.02)

                # 速度向量
                self.vx = dir_x * current_speed
                self.vy = dir_y * current_speed

                # 接触膜时更新_target透明度（接触阶段会再变）
                if is_touching:
                    self._target_transparency = self.base_transparency + 0.05

        elif self.state == 'contact':
            # CONTACT: 接触膜后停留，等待生命体"识别"
            if target_position:
                dx = target_position[0] - self.x
                dy = target_position[1] - self.y
                self.current_distance_to_target = math.sqrt(dx ** 2 + dy ** 2)

            # 短暂停留 - 轻微颤抖（生命体"感知"碎片）
            tremble = 0.6
            self.x += math.sin(current_time * 8.0 + self.phase) * tremble
            self.y += math.cos(current_time * 7.5 + self.phase + 1.0) * tremble

            # 记录接触状态
            self.is_touching_membrane = True
            self.has_penetrated_membrane = True

            # 透明度轻微提升（接触瞬间的"激活"效果）
            self._target_transparency = min(1.0, self.base_transparency + 0.15)

            # 接触结束 → 进入ABSORBING
            if state_duration > self.contact_duration:
                self._transition_to('absorbing', target_position)

        elif self.state == 'absorbing':
            # ABSORBING: 重点视觉 - 边缘模糊/晶体瓦解/颜色扩散
            # 进度 0→1 持续 absorbing_duration 秒
            self.absorption_progress = min(1.0, state_duration / self.absorbing_duration)
            # 兼容旧接口
            self.penetration_progress = self.absorption_progress

            # 缓慢向中心漂移（阻力感）
            if target_position:
                dx = target_position[0] - self.x
                dy = target_position[1] - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist > 6:
                    # 进度越深阻力越大
                    resistance = 1.0 - self.absorption_progress * 0.85
                    move_factor = 0.05 * resistance
                    self.x += (dx / dist) * move_factor
                    self.y += (dy / dist) * move_factor

            # 透明度：从 base_transparency 渐变到 0
            initial = getattr(self, '_initial_absorption_transparency', self._target_transparency)
            # ease-in 曲线 - 开始时慢，逐渐加快
            eased = self.absorption_progress ** 1.4
            self._target_transparency = max(0.0, initial * (1.0 - eased))

            # 大小逐渐缩小（暗示被吸收）
            self.size_scale = max(0.18, 1.0 - self.absorption_progress * 0.82)

            # 旋转减慢
            self.rotation_speed = 0.004 * (1.0 - self.absorption_progress * 0.7)

            # 顶点抖动（晶体瓦解）
            self.vertex_jitter_base = self.absorption_progress * self.size * 0.55

            # 颜色扩散强度 - 在生命体上产生柔和光晕
            # 0 → 1 渐变，到达 0.7 后保持
            self.color_diffusion_intensity = min(1.0, self.absorption_progress * 1.3)

            # absorbing 完成 → INTEGRATING
            if self.absorption_progress >= 1.0:
                self._transition_to('integrating', target_position)

        elif self.state == 'integrating':
            # INTEGRATING: 短过渡，碎片几乎不可见，但生命体内部整合
            # 默认 0.6 秒
            integrating_duration = getattr(self, '_integrating_duration', 0.6)
            self.absorption_progress = min(1.0, state_duration / integrating_duration)
            self.penetration_progress = 1.0

            # 极慢向中心移动
            if target_position:
                dx = target_position[0] - self.x
                dy = target_position[1] - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist > 2:
                    self.x += (dx / dist) * 0.3
                    self.y += (dy / dist) * 0.3

            # 透明度快速衰减到 0
            self._target_transparency = max(0.0, self._target_transparency * 0.85)
            # 颜色扩散维持最强
            self.color_diffusion_intensity = 1.0
            # 大小保持最小
            self.size_scale = 0.18

            if state_duration > integrating_duration:
                # COMPLETED - 标记移除
                return True

        # === 透明度脉动（呼吸感） ===
        if self.state in ('floating', 'settling', 'approaching'):
            pulse = 0.92 + 0.08 * math.sin(current_time * 1.8 + self.phase)
            self.transparency = max(0.0, min(1.0, self._target_transparency * pulse))
        elif self.state == 'contact':
            # 接触时更明显的脉动（生命体在"识别"）
            pulse = 0.85 + 0.15 * math.sin(current_time * 4.5 + self.phase)
            self.transparency = max(0.0, min(1.0, self._target_transparency * pulse))
        else:
            # absorbing/integrating：直接使用_target（无脉动，平滑衰减）
            self.transparency = max(0.0, min(1.0, self._target_transparency))

        return False  # 继续存活

    def _transition_to(self, new_state: str, target_position: Optional[Tuple[float, float]] = None):
        """状态转换"""
        # 追踪状态变化（用于通知 TargetObject 触发膜扰动）
        if self.state != new_state:
            self.previous_state = self.state
            self.state = new_state
            self.state_changed = True

        self.state_start_time = time.time()

        if new_state == 'absorbing':
            # 进入吸收时记录初始透明度（_target版本），保持视觉连续性
            self._initial_absorption_transparency = self._target_transparency
            self.absorption_progress = 0.0
            self.penetration_progress = 0.0
        elif new_state == 'integrating':
            self.absorption_progress = 0.0

    def get_polygon_points(self) -> List[Tuple[float, float]]:
        """
        获取多边形顶点（用于绘制不规则碎片）

        在 absorbing 阶段，顶点会加入随机抖动以体现"晶体瓦解"。

        Returns:
            多边形顶点坐标列表
        """
        size_scale = getattr(self, 'size_scale', 1.0)
        jitter = getattr(self, 'vertex_jitter_base', 0.0)

        points = []
        for i in range(self.num_vertices):
            angle = self.vertex_angles[i] + self.rotation_angle
            distance = self.size * self.vertex_distances[i] * size_scale

            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance

            # absorbing 阶段：顶点随机抖动（晶体瓦解）
            if jitter > 0.01:
                t = time.time() * 6.0 + i * 0.7
                jx = math.sin(t) * jitter
                jy = math.cos(t * 1.3 + 1.0) * jitter
                x += jx
                y += jy

            points.append((x, y))

        return points

    def get_current_color_with_alpha(self) -> Tuple[int, int, int, int]:
        """获取当前颜色（带透明度）"""
        alpha = int(255 * self.transparency)
        return (*self.current_color, alpha)

    def is_alive(self) -> bool:
        """检查是否存活"""
        current_time = time.time()
        return (current_time - self.birth_time) < self.max_lifetime

    def get_state(self) -> str:
        """获取当前状态"""
        return self.state

    def get_penetration_data(self) -> Optional[Dict]:
        """
        获取渗透数据（用于影响目标对象）

        在 absorbing/integrating 阶段返回数据。

        Returns:
            渗透数据字典
        """
        if self.state in ('absorbing', 'integrating'):
            return {
                'intensity': self.intensity,
                'position': (self.x, self.y),
                'progress': self.absorption_progress,
                'state': self.state,
                'diffusion_intensity': self.color_diffusion_intensity,
            }
        return None


class MemoryCloud:
    """
    记忆碎片云
    
    管理一组记忆碎片
    """
    
    def __init__(self):
        """初始化记忆碎片云"""
        self.fragments: List[MemoryFragment] = []
        self.target_position: Optional[Tuple[float, float]] = None
        
    def add_fragments_from_trajectory(self, trajectory: List[Tuple[int, int]], 
                                     behavior_speed: float = 0.0,
                                     behavior_distance: float = 0.0):
        """
        从轨迹生成记忆碎片
        
        Args:
            trajectory: 轨迹点列表
            behavior_speed: 行为速度
            behavior_distance: 行为距离
        """
        if len(trajectory) < 3:
            return
        
        # 根据轨迹长度决定碎片数量
        num_fragments = min(8, max(3, len(trajectory) // 15))
        
        # 从轨迹中均匀采样点生成碎片
        step = len(trajectory) // num_fragments
        
        for i in range(num_fragments):
            idx = min(i * step, len(trajectory) - 1)
            x, y = trajectory[idx]
            
            # 强度根据轨迹特征计算
            intensity = min(1.0, (behavior_speed / 20.0) * 0.3 + 
                          (behavior_distance / 500.0) * 0.7)
            
            fragment = MemoryFragment(
                x=float(x), 
                y=float(y),
                intensity=intensity,
                behavior_speed=behavior_speed,
                behavior_distance=behavior_distance
            )
            self.fragments.append(fragment)
            
        print(f"生成 {num_fragments} 个记忆碎片")
        
    def set_target(self, target_position: Tuple[float, float]):
        """
        设置目标位置
        
        Args:
            target_position: 目标对象位置
        """
        self.target_position = target_position
        
    def get_fragments_data(self) -> List[Dict]:
        """
        获取所有碎片的状态数据（用于检查是否靠近膜边界）

        Returns:
            碎片数据列表
        """
        fragments_data = []
        for fragment in self.fragments:
            fragment_data = {
                'id': fragment.id,
                'x': fragment.x,
                'y': fragment.y,
                'intensity': fragment.intensity,
                'is_touching_membrane': fragment.is_touching_membrane,
                'has_penetrated_membrane': fragment.has_penetrated_membrane,
                'distance_to_target': fragment.current_distance_to_target,
                'state': fragment.state,
                'previous_state': fragment.previous_state,
                'state_changed': fragment.state_changed,
                'absorption_progress': getattr(fragment, 'absorption_progress', 0.0),
            }
            fragments_data.append(fragment_data)

            # 状态变化已被消费（下一帧重新检测）
            if fragment.state_changed:
                fragment.state_changed = False

        return fragments_data
    
    def update(self) -> List[Dict]:
        """
        更新所有碎片
        
        Returns:
            完成渗透的碎片数据列表
        """
        completed_penetrations = []
        
        for fragment in self.fragments:
            if fragment.is_alive():
                completed = fragment.update(self.target_position)
                if completed:
                    # 碎片渗透完成
                    penetration_data = fragment.get_penetration_data()
                    if penetration_data:
                        completed_penetrations.append(penetration_data)
                        
        # 移除死亡或完成的碎片
        self.fragments = [f for f in self.fragments 
                         if f.is_alive() and f.get_state() != 'penetrating_completed']
        
        return completed_penetrations
    
    def draw(self, screen: pygame.Surface):
        """
        绘制所有碎片 - 晶体渲染

        层级结构（从下到上）：
        1. 残影（柔和光点）
        2. 辉光（扩散的多边形剪影）
        3. 主体（半透明琥珀色晶体）
        4. 内部折射纹理（棱+高光）
        5. 局部高光（暖白小亮点）
        6. 吸收时的颜色扩散（向生命体方向的柔光）

        注意：
        - absorbing/integrating 状态继续绘制（让透明度自然衰减）
        - 颜色扩散是向生命体的"颜色吸收"轨迹
        - 在 main.py 中碎片绘制在 target_object 之前，
          生命体会自然覆盖已渗入内部的碎片，呈现"进入"效果。

        Args:
            screen: Pygame屏幕表面
        """
        for fragment in self.fragments:
            if fragment.get_state() == 'penetrating_completed':
                continue
            self._draw_fragment_trail(screen, fragment)
            # 吸收阶段：先在生命体方向绘制扩散光（颜色渗入）
            self._draw_color_diffusion(screen, fragment)
            self._draw_fragment_body(screen, fragment)

    def _draw_fragment_trail(self, screen: pygame.Surface,
                             fragment: 'MemoryFragment'):
        """绘制碎片残影 - 柔和光点轨迹"""
        if not fragment.trail_positions:
            return

        trail_count = len(fragment.trail_positions)
        for i, (tx, ty, t_alpha) in enumerate(fragment.trail_positions):
            if t_alpha <= 0.03:
                continue
            # 越靠近当前位置越亮
            fade = (i + 1) / trail_count
            alpha = int(180 * t_alpha * fade * 0.5)
            if alpha <= 0:
                continue
            # 残影大小（越远越小）
            r = max(1, int(fragment.size * 0.32 * fade))
            # 用柔和的琥珀色
            color = (*fragment.glow_color, alpha)
            # 创建小的alpha surface
            surf_size = r * 2 + 2
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (r + 1, r + 1), r)
            screen.blit(surf, (tx - r - 1, ty - r - 1))

    def _draw_color_diffusion(self, screen: pygame.Surface,
                              fragment: 'MemoryFragment'):
        """
        绘制颜色扩散 - absorbing/integrating 阶段的视觉重点

        表现为从碎片向生命体方向延伸的柔和光带/光斑，
        模拟"颜色被生命体吸收"的过程。

        注意：此方法直接绘制到屏幕（不在临时surface中），
        这样可以跨越碎片本地坐标，绘制更长的扩散轨迹。
        """
        # 仅在 absorbing / integrating 阶段生效
        if fragment.state not in ('absorbing', 'integrating'):
            return
        if fragment.color_diffusion_intensity <= 0.01:
            return
        if not self.target_position:
            return

        intensity = fragment.color_diffusion_intensity
        fx, fy = fragment.x, fragment.y
        tx, ty = self.target_position
        dx = tx - fx
        dy = ty - fy
        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist < 1:
            return

        # 单位方向
        ux, uy = dx / dist, dy / dist

        # 扩散带长度：随进度变长，但限制不超过当前距离
        band_length = min(dist, fragment.size * 4.5 * intensity)
        # 扩散带宽度：碎片大小
        band_width = max(2, fragment.size * (0.6 + intensity * 0.5))

        # 多个层叠的圆点，模拟渐变光带
        num_steps = 8
        for i in range(num_steps):
            t = (i + 1) / num_steps
            # 位置：从碎片向生命体方向
            px = fx + ux * band_length * t
            py = fy + uy * band_length * t

            # 越靠近生命体越亮（被吸收方向）
            layer_alpha = int(140 * intensity * t * (1.0 - t * 0.3))
            if layer_alpha <= 2:
                continue
            # 半径向生命体方向递减
            r = max(1, int(band_width * (1.0 - t * 0.5)))

            color = (*fragment.body_color, layer_alpha)
            surf_size = r * 2 + 2
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (r + 1, r + 1), r)
            screen.blit(surf, (px - r - 1, py - r - 1))

        # 在生命体附近加一个亮斑（"被吸收"焦点）
        focus_t = 0.85
        focus_x = fx + ux * band_length * focus_t
        focus_y = fy + uy * band_length * focus_t
        focus_alpha = int(180 * intensity)
        if focus_alpha > 4:
            for factor, a_mult in [(0.4, 1.0), (0.7, 0.6), (1.0, 0.3)]:
                r = max(1, int(band_width * factor))
                a = int(focus_alpha * a_mult)
                if a <= 2:
                    continue
                color = (*fragment.highlight_color, a)
                surf_size = r * 2 + 2
                surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (r + 1, r + 1), r)
                screen.blit(surf, (focus_x - r - 1, focus_y - r - 1))

    def _draw_fragment_body(self, screen: pygame.Surface,
                            fragment: 'MemoryFragment'):
        """绘制晶体主体 - 多层渲染

        absorbing 阶段添加边缘模糊：
        - 多层放大的半透明多边形，模拟羽化边缘
        - 内部纹理变淡（晶体结构瓦解的暗示）
        """
        points = fragment.get_polygon_points()
        if len(points) < 3:
            return

        # 边界框
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # 临时surface留出边距
        # absorbing 阶段需要更大边距以容纳边缘模糊
        is_absorbing = fragment.state in ('absorbing', 'integrating')
        extra_pad = int(fragment.size * 0.8 * fragment.size_scale) if is_absorbing else 0
        pad = max(8, int(fragment.size * 0.6)) + extra_pad
        width = int(max_x - min_x) + pad * 2
        height = int(max_y - min_y) + pad * 2
        if width <= 0 or height <= 0:
            return

        # 创建透明surface
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        offset_x = min_x - pad
        offset_y = min_y - pad
        # 多边形坐标变换到surface本地坐标
        local_points = [(p[0] - offset_x, p[1] - offset_y) for p in points]
        cx_local = width // 2
        cy_local = height // 2

        alpha_total = max(0, min(255, int(255 * fragment.transparency)))

        # === 1) 外层辉光（稍微放大的多边形剪影） ===
        glow_alpha = int(alpha_total * 0.18)
        if glow_alpha > 4:
            glow_scale = 1.18
            glow_points = [
                (cx_local + (p[0] - cx_local) * glow_scale,
                 cy_local + (p[1] - cy_local) * glow_scale)
                for p in local_points
            ]
            glow_color = (*fragment.glow_color, glow_alpha)
            pygame.draw.polygon(surf, glow_color, glow_points)

        # === 1.5) 边缘模糊层（absorbing/integrating阶段）- 模拟羽化边缘 ===
        if is_absorbing and alpha_total > 8:
            # 模糊层数随进度增加
            blur_progress = getattr(fragment, 'absorption_progress', 0.0)
            num_blur_layers = 4
            for i in range(num_blur_layers):
                t = (i + 1) / num_blur_layers
                # 缩放（越外越大）
                blur_scale = 1.0 + 0.15 * t * (1.0 + blur_progress)
                # alpha 越外越低
                blur_alpha = int(alpha_total * (0.15 - 0.03 * i) * (0.5 + blur_progress * 0.5))
                if blur_alpha <= 1:
                    continue
                blur_points = [
                    (cx_local + (p[0] - cx_local) * blur_scale,
                     cy_local + (p[1] - cy_local) * blur_scale)
                    for p in local_points
                ]
                blur_color = (*fragment.body_color, blur_alpha)
                pygame.draw.polygon(surf, blur_color, blur_points)

        # === 2) 晶体主体 - 半透明琥珀色（无边框） ===
        body_color = (*fragment.body_color, alpha_total)
        pygame.draw.polygon(surf, body_color, local_points)

        # === 3) 内部折射纹理 ===
        # absorbing 阶段纹理变淡（暗示晶体结构瓦解）
        if fragment.internal_texture is not None:
            tex_w = int(fragment.texture_size)
            tex_h = int(fragment.texture_size)
            if tex_w > 0 and tex_h > 0:
                scaled_tex = pygame.transform.smoothscale(
                    fragment.internal_texture, (tex_w, tex_h)
                )
                tex_alpha_mult = alpha_total / 255.0 * 0.85
                # 吸收阶段纹理逐渐变淡
                if is_absorbing:
                    tex_alpha_mult *= (1.0 - 0.7 * getattr(fragment, 'absorption_progress', 0.0))
                if tex_alpha_mult > 0.02:
                    tex_surf = scaled_tex.copy()
                    tex_surf.fill((255, 255, 255, int(255 * tex_alpha_mult)),
                                  special_flags=pygame.BLEND_RGBA_MULT)
                    tex_x = cx_local - tex_w // 2
                    tex_y = cy_local - tex_h // 2
                    surf.blit(tex_surf, (tex_x, tex_y))

        # === 4) 内部核心（更亮的小多边形）- 增强晶体感 ===
        if fragment.intensity > 0.35:
            core_alpha = int(alpha_total * 0.4)
            if core_alpha > 4:
                # 吸收阶段核心变小（结构瓦解）
                if is_absorbing:
                    core_alpha = int(core_alpha * (1.0 - 0.6 * getattr(fragment, 'absorption_progress', 0.0)))
                if core_alpha > 2:
                    # 内核比主体小60%，形成层次
                    core_scale = 0.5
                    core_points = [
                        (cx_local + (p[0] - cx_local) * core_scale,
                         cy_local + (p[1] - cy_local) * core_scale)
                        for p in local_points
                    ]
                    core_color = (*fragment.inner_color, core_alpha)
                    pygame.draw.polygon(surf, core_color, core_points)

        # === 5) 局部高光（暖白小亮点，模拟光线折射） ===
        if alpha_total > 60:
            hl_x = cx_local + int(fragment.highlight_offset[0])
            hl_y = cy_local + int(fragment.highlight_offset[1])
            hl_r = max(1, int(fragment.highlight_size))
            # 吸收阶段高光扩大并变淡
            if is_absorbing:
                hl_r = int(hl_r * (1.0 + 0.3 * getattr(fragment, 'absorption_progress', 0.0)))
            # 多层渐变高光
            for factor, a in [(0.35, 200), (0.7, 110), (1.0, 50)]:
                r = max(1, int(hl_r * factor))
                hl_alpha = int(alpha_total * a / 255)
                if is_absorbing:
                    # 吸收阶段高光alpha衰减
                    hl_alpha = int(hl_alpha * (1.0 - 0.5 * getattr(fragment, 'absorption_progress', 0.0)))
                if hl_alpha > 2:
                    pygame.draw.circle(surf,
                                       (*fragment.highlight_color, hl_alpha),
                                       (hl_x, hl_y), r)

        # 绘制到屏幕
        screen.blit(surf, (offset_x, offset_y))
    
    def get_fragment_count(self) -> int:
        """获取当前碎片数量"""
        return len(self.fragments)
    
    def get_fragments_by_state(self, state: str) -> int:
        """获取特定状态的碎片数量"""
        return sum(1 for f in self.fragments if f.get_state() == state)
    
    def clear(self):
        """清除所有碎片"""
        self.fragments.clear()


class ParticleSystem:
    """
    粒子系统（主类，兼容旧接口）
    
    现在主要管理记忆碎片云
    """
    
    def __init__(self):
        """初始化粒子系统"""
        self.memory_cloud = MemoryCloud()
        self.target_position: Optional[Tuple[float, float]] = None
        
    def set_target(self, target_position: Tuple[float, float]):
        """
        设置目标位置
        
        Args:
            target_position: 目标对象位置
        """
        self.target_position = target_position
        self.memory_cloud.set_target(target_position)
        
    def create_trace_from_trajectory(self, trajectory: List[Tuple[int, int]],
                                    behavior_speed: float = 0.0,
                                    behavior_distance: float = 0.0):
        """
        从轨迹创建记忆碎片
        
        Args:
            trajectory: 轨迹点列表
            behavior_speed: 行为速度
            behavior_distance: 行为距离
        """
        self.memory_cloud.add_fragments_from_trajectory(
            trajectory, behavior_speed, behavior_distance
        )
        
    def update(self) -> List[Dict]:
        """
        更新粒子系统
        
        Returns:
            完成渗透的碎片数据列表
        """
        return self.memory_cloud.update()
    
    def get_fragments_data(self) -> List[Dict]:
        """
        获取所有碎片的状态数据（用于检查是否靠近膜边界）
        
        Returns:
            碎片数据列表
        """
        return self.memory_cloud.get_fragments_data()
    
    def draw(self, screen: pygame.Surface):
        """
        绘制粒子系统
        
        Args:
            screen: Pygame屏幕表面
        """
        self.memory_cloud.draw(screen)
        
    def get_particle_count(self) -> int:
        """获取当前粒子数量"""
        return self.memory_cloud.get_fragment_count()
    
    def clear(self):
        """清除所有粒子"""
        self.memory_cloud.clear()


def main():
    """
    测试函数：测试记忆碎片系统
    
    操作：
    - 鼠标移动生成轨迹
    - 静止 0.8秒生成记忆碎片
    - 碎片沉积 → 漂移 → 渗透
    - 'c' 清除
    - 'q' 退出
    """
    import time
    from behavior_analysis import BehaviorAnalyzer
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Memory Fragment Test - 记忆碎片系统")
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 28)
    
    # 初始化系统
    particle_system = ParticleSystem()
    analyzer = BehaviorAnalyzer()
    
    # 设置目标位置（屏幕中央）
    target_pos = (640, 360)
    particle_system.set_target(target_pos)
    
    # 当前轨迹
    current_trajectory: List[Tuple[int, int]] = []
    
    print("=" * 50)
    print("记忆碎片系统测试")
    print("=" * 50)
    print("移动鼠标绘制轨迹")
    print("静止 0.8秒 → 生成记忆碎片 → 沉积 → 漂移 → 渗透")
    print("'c' - 清除")
    print("'q' - 退出")
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
                    particle_system.clear()
                    analyzer.clear()
                    current_trajectory.clear()
                    print("已清除")
        
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hand_pos = {"x": mouse_x, "y": mouse_y}
        
        # 记录轨迹
        current_trajectory.append((mouse_x, mouse_y))
        if len(current_trajectory) > 150:
            current_trajectory.pop(0)
        
        # 更新行为分析器
        action = analyzer.update(hand_pos)
        
        if action:
            # 动作结束，生成记忆碎片
            action_dict = action.to_dict()
            particle_system.create_trace_from_trajectory(
                action_dict['trajectory'],
                action_dict['speed'],
                action_dict['distance']
            )
            current_trajectory.clear()
            print(f"生成记忆碎片: speed={action_dict['speed']:.2f}, distance={action_dict['distance']:.2f}")
        
        # 更新粒子系统（获取渗透数据）
        penetrations = particle_system.update()
        if penetrations:
            print(f"{len(penetrations)} 个碎片完成渗透")
        
        # 渲染
        screen.fill((15, 15, 25))  # 深色背景
        
        # 绘制目标位置（目标对象占位符）
        pygame.draw.circle(screen, (100, 150, 200, 100), target_pos, 50, 2)
        pygame.draw.circle(screen, (150, 180, 220, 50), target_pos, 30)
        
        # 绘制当前轨迹
        if len(current_trajectory) >= 2:
            pygame.draw.lines(screen, (80, 160, 220), False, current_trajectory, 2)
            if current_trajectory:
                pygame.draw.circle(screen, (120, 200, 255), current_trajectory[-1], 5)
        
        # 绘制记忆碎片
        particle_system.draw(screen)
        
        # 显示信息
        info_lines = [
            f"轨迹点: {len(current_trajectory)}",
            f"记忆碎片: {particle_system.get_particle_count()}",
            f"悬浮: {particle_system.memory_cloud.get_fragments_by_state('floating')}",
            f"沉积: {particle_system.memory_cloud.get_fragments_by_state('settling')}",
            f"接近: {particle_system.memory_cloud.get_fragments_by_state('approaching')}",
            f"接触: {particle_system.memory_cloud.get_fragments_by_state('contact')}",
            f"吸收: {particle_system.memory_cloud.get_fragments_by_state('absorbing')}",
            f"整合: {particle_system.memory_cloud.get_fragments_by_state('integrating')}",
            f"静止: {analyzer.get_inactive_duration():.2f}s / 0.8s",
            "",
            "移动鼠标 → 静止0.8秒 → 碎片飞向目标"
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("测试结束")


if __name__ == "__main__":
    main()