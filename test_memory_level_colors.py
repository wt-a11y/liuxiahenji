"""
记忆等级颜色系统测试

验证：
1. calculate_memory_level_colors 在 5 个等级都返回正确颜色
2. update() 中颜色缓慢插值
3. 不会变成纯黄色
4. reset_position 重置颜色
"""
import os
import sys
import io
import contextlib

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import target_object


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


# === 测试 1: 5 个等级的目标颜色 ===
print("=" * 60)
print("测试 1: 5 个等级的目标颜色（不经过插值）")
print("=" * 60)

t = target_object.TargetObject()
all_pass = True

# 期望的核心色和纹理色（来自用户设计）
expected_core = [
    (160, 200, 230),  # Level 0: 冷蓝
    (130, 220, 195),  # Level 1: 薄荷绿
    (170, 215, 170),  # Level 2: 青绿
    (200, 185, 160),  # Level 3: 琥珀
    (215, 170, 135),  # Level 4: 暖橙
]
expected_tex = [
    (200, 220, 240),
    (160, 235, 195),
    (195, 230, 165),
    (225, 195, 140),
    (240, 175, 115),
]

for lv in range(5):
    core, tex = t.calculate_memory_level_colors(lv)
    e_core = expected_core[lv]
    e_tex = expected_tex[lv]
    core_ok = all(abs(core[i] - e_core[i]) < 0.5 for i in range(3))
    tex_ok = all(abs(tex[i] - e_tex[i]) < 0.5 for i in range(3))
    print(f"  Level {lv}: core={rgb_to_hex(core)} (期望 {rgb_to_hex(e_core)}) "
          f"tex={rgb_to_hex(tex)} (期望 {rgb_to_hex(e_tex)}) "
          f"{'OK' if core_ok and tex_ok else 'FAIL'}")
    all_pass = all_pass and core_ok and tex_ok

# === 测试 2: 平滑插值（不直接切换）===
print()
print("=" * 60)
print("测试 2: 缓慢插值（不直接切换）")
print("=" * 60)
t2 = target_object.TargetObject()
# 抑制其他print
buf = io.StringIO()
# 模拟等级提升：先在 Level 0 跑 100 帧，然后提升到 Level 4 跑 100 帧
# 检查颜色是缓慢过渡的（中间帧既不是 Level 0 也不是 Level 4）

with contextlib.redirect_stdout(buf):
    # 起始: Level 0, current colors = Level 0 stops
    t2.memory_level = 0
    for _ in range(50):
        t2.update()
    initial_core = tuple(t2._current_core_color)

    # 升级到 Level 4
    t2.memory_level = 4
    # 检查 50 帧后: 颜色应介于 Level 0 和 Level 4 之间
    for _ in range(50):
        t2.update()
    mid_core = tuple(t2._current_core_color)

    # 200 帧后: 应该接近 Level 4
    for _ in range(150):
        t2.update()
    final_core = tuple(t2._current_core_color)

# 验证：mid 应该在 initial 和 final 之间
mid_between = (
    # R: Level 0 R=160, Level 4 R=215, mid 应在 160-215 之间
    min(initial_core[0], final_core[0]) <= mid_core[0] <= max(initial_core[0], final_core[0])
    and min(initial_core[1], final_core[1]) <= mid_core[1] <= max(initial_core[1], final_core[1])
    and min(initial_core[2], final_core[2]) <= mid_core[2] <= max(initial_core[2], final_core[2])
)
print(f"  初始 (50帧@L0): core=({initial_core[0]:.1f}, {initial_core[1]:.1f}, {initial_core[2]:.1f})")
print(f"  升级后50帧:     core=({mid_core[0]:.1f}, {mid_core[1]:.1f}, {mid_core[2]:.1f})  <- 应该在初始和最终之间")
print(f"  升级后200帧:    core=({final_core[0]:.1f}, {final_core[1]:.1f}, {final_core[2]:.1f})")
interpolation_ok = mid_between and final_core[0] > mid_core[0] > initial_core[0] - 1
print(f"  {'OK 插值平滑' if interpolation_ok else 'FAIL 颜色未平滑过渡'}")
all_pass = all_pass and interpolation_ok

# === 测试 3: 不会变成纯黄色 ===
print()
print("=" * 60)
print("测试 3: 不会变成纯黄色")
print("=" * 60)
t3 = target_object.TargetObject()
with contextlib.redirect_stdout(buf):
    t3.memory_level = 4
    # 跑 1000 帧让颜色完全收敛
    for _ in range(1000):
        t3.update()
final_core = t3._current_core_color
final_tex = t3._current_texture_color

# 纯黄色 = (255, 255, 0). 我们的目标 Level 4 = (215, 170, 135).
# 验证 B 通道不应该太低（不要变成无蓝的暖色）
# 验证 R 不应该超过 250
core_not_yellow = final_core[2] > 100 and final_core[1] > 100
tex_not_yellow = final_tex[2] > 80 and final_tex[1] > 100
print(f"  Level 4 最终核心色: ({final_core[0]:.1f}, {final_core[1]:.1f}, {final_core[2]:.1f})  "
      f"{'OK 非纯黄' if core_not_yellow else 'FAIL 太黄'}")
print(f"  Level 4 最终纹理色: ({final_tex[0]:.1f}, {final_tex[1]:.1f}, {final_tex[2]:.1f})  "
      f"{'OK 非纯黄' if tex_not_yellow else 'FAIL 太黄'}")
all_pass = all_pass and core_not_yellow and tex_not_yellow

# === 测试 4: reset_position 重置颜色 ===
print()
print("=" * 60)
print("测试 4: reset_position 重置颜色")
print("=" * 60)
t3.reset_position()
reset_core = t3._current_core_color
reset_tex = t3._current_texture_color
reset_ok = (
    abs(reset_core[0] - 160) < 0.1
    and abs(reset_core[1] - 200) < 0.1
    and abs(reset_core[2] - 230) < 0.1
    and abs(reset_tex[0] - 200) < 0.1
    and abs(reset_tex[1] - 220) < 0.1
    and abs(reset_tex[2] - 240) < 0.1
)
print(f"  重置核心: ({reset_core[0]:.1f}, {reset_core[1]:.1f}, {reset_core[2]:.1f})  期望 (160, 200, 230)")
print(f"  重置纹理: ({reset_tex[0]:.1f}, {reset_tex[1]:.1f}, {reset_tex[2]:.1f})  期望 (200, 220, 240)")
print(f"  {'OK' if reset_ok else 'FAIL'}")
all_pass = all_pass and reset_ok

# === 测试 5: 与吞噬流程共存（不修改 receive_impact 流程）===
print()
print("=" * 60)
print("测试 5: receive_impact 触发等级提升+颜色变化")
print("=" * 60)
t4 = target_object.TargetObject()
with contextlib.redirect_stdout(buf):
    for i in range(60):
        t4.receive_impact(value=0.5, source_position={'x': t4.x + 50, 'y': t4.y})
    # 1000 帧让插值接近收敛（速度 0.002 → 1000 帧约 86.5% 收敛）
    for _ in range(1000):
        t4.update()
# 60 个碎片 -> Level 4
print(f"  fragment_count={t4.fragment_count}, memory_level={t4.memory_level}")
print(f"  最终核心: ({t4._current_core_color[0]:.1f}, {t4._current_core_color[1]:.1f}, {t4._current_core_color[2]:.1f})")
print(f"  最终纹理: ({t4._current_texture_color[0]:.1f}, {t4._current_texture_color[1]:.1f}, {t4._current_texture_color[2]:.1f})")
flow_ok = (
    t4.memory_level == 4
    and t4._current_core_color[0] > 200  # 接近 215
    and t4._current_texture_color[0] > 230  # 接近 240
)
print(f"  {'OK 吞噬流程与颜色系统正常协作' if flow_ok else 'FAIL'}")
all_pass = all_pass and flow_ok

print()
print("=" * 60)
print(f"总结: {'全部通过' if all_pass else '存在失败'}")
print("=" * 60)
sys.exit(0 if all_pass else 1)
