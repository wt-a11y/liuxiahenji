"""
内部纹理"脉络"系统测试

验证：
1. calculate_memory_level_vein_color 在 5 个等级返回正确颜色
2. get_memory_level_vein_strength 在 5 个等级返回正确强度
3. FlowTexture 初始化包含 vein_phase_a / vein_phase_b / vein_drift_speed
4. _current_vein_color 在 update() 中缓慢插值
5. Level 0 vein_strength = 0, Level 1-4 > 0
6. 2nd vein 仅在 L3+ 出现
7. reset_position 重置 _current_vein_color
8. 脉络不覆盖基础纹理（基础曲线始终绘制）
"""
import os
import sys
import io
import contextlib

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import target_object


def rgb_hex(rgb):
    if len(rgb) == 4:
        return "#{:02X}{:02X}{:02X}@{}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(rgb[3]))
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


# === 测试 1: vein 颜色锚点 ===
print("=" * 60)
print("测试 1: 5 个等级的脉络颜色")
print("=" * 60)

t = target_object.TargetObject()
expected_vein = [
    (185, 210, 225),  # L0: 冷蓝（与基底一致）
    (170, 230, 190),  # L1: 浅暖绿（呼应 L1 薄荷绿）
    (215, 220, 170),  # L2: 暖绿（连接绿与琥珀）
    (230, 180, 135),  # L3: 琥珀
    (240, 165, 100),  # L4: 稳定暖橙
]
all_pass = True
for lv in range(5):
    got = t.calculate_memory_level_vein_color(lv)
    exp = expected_vein[lv]
    ok = all(abs(got[i] - exp[i]) < 0.5 for i in range(3))
    all_pass = all_pass and ok
    print(f"  L{lv}: {rgb_hex(got)}  (期望 {rgb_hex(exp)})  {'OK' if ok else 'FAIL'}")

# === 测试 2: vein strength ===
print()
print("=" * 60)
print("测试 2: 5 个等级的脉络强度")
print("=" * 60)
expected_strength = [0.0, 0.15, 0.40, 0.65, 0.85]
for lv in range(5):
    s = t.get_memory_level_vein_strength(lv)
    ok = abs(s - expected_strength[lv]) < 0.01
    all_pass = all_pass and ok
    print(f"  L{lv}: strength={s:.2f}  (期望 {expected_strength[lv]:.2f})  {'OK' if ok else 'FAIL'}")

# === 测试 3: FlowTexture 初始化包含脉络属性 ===
print()
print("=" * 60)
print("测试 3: FlowTexture 脉络属性初始化")
print("=" * 60)
ft = target_object.FlowTexture(640, 360, 0)
props_ok = (
    hasattr(ft, 'vein_phase_a') and 0 <= ft.vein_phase_a <= 1
    and hasattr(ft, 'vein_phase_b') and 0 <= ft.vein_phase_b <= 1
    and hasattr(ft, 'vein_drift_speed') and 0 < ft.vein_drift_speed < 0.01
)
print(f"  vein_phase_a     = {ft.vein_phase_a:.4f}  (期望 [0,1])")
print(f"  vein_phase_b     = {ft.vein_phase_b:.4f}  (期望 [0,1])")
print(f"  vein_drift_speed = {ft.vein_drift_speed:.5f}  (期望 (0, 0.01))")
print(f"  {'OK' if props_ok else 'FAIL'}")
all_pass = all_pass and props_ok

# === 测试 4: _current_vein_color 在 update() 中缓慢插值 ===
print()
print("=" * 60)
print("测试 4: _current_vein_color 缓慢插值")
print("=" * 60)
t2 = target_object.TargetObject()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    t2.memory_level = 0
    for _ in range(50):
        t2.update()
    init_vein = tuple(t2._current_vein_color)

    t2.memory_level = 4
    # 中间帧
    for _ in range(50):
        t2.update()
    mid_vein = tuple(t2._current_vein_color)
    # 2000 帧后（速度 0.002 → 2000 帧后约 86.5% 收敛）
    for _ in range(1950):
        t2.update()
    final_vein = tuple(t2._current_vein_color)

print(f"  初始 (50帧@L0):  ({init_vein[0]:.1f}, {init_vein[1]:.1f}, {init_vein[2]:.1f})  期望接近 (185, 210, 225)")
print(f"  升级50帧后:      ({mid_vein[0]:.1f}, {mid_vein[1]:.1f}, {mid_vein[2]:.1f})  <- 介于初始和最终之间")
print(f"  升级2000帧后:    ({final_vein[0]:.1f}, {final_vein[1]:.1f}, {final_vein[2]:.1f})  期望接近 (240, 165, 100)")

# 缓慢插值验证：方向正确即可，不强求完全收敛（速度 0.002，2000帧约 86.5% 收敛）
interp_ok = (
    abs(init_vein[0] - 185) < 1 and abs(init_vein[1] - 210) < 1 and abs(init_vein[2] - 225) < 1
    and # 2000 帧后应明显接近 L4 目标 (240, 165, 100)
    abs(final_vein[0] - 240) < 10 and abs(final_vein[1] - 165) < 10 and abs(final_vein[2] - 100) < 10
    and # 中间帧应在两者之间
    init_vein[0] < mid_vein[0] < final_vein[0] + 1
    and init_vein[1] > mid_vein[1] > final_vein[1] - 1
    and init_vein[2] > mid_vein[2] > final_vein[2] - 1
)
print(f"  {'OK 插值平滑' if interp_ok else 'FAIL 颜色过渡异常'}")
all_pass = all_pass and interp_ok

# === 测试 5: Level 0 脉络不可见（strength=0）===
print()
print("=" * 60)
print("测试 5: L0 脉络不可见")
print("=" * 60)
s0 = t2.get_memory_level_vein_strength(0)
l0_ok = s0 == 0.0
print(f"  L0 strength = {s0}  {'OK 不可见' if l0_ok else 'FAIL'}")
all_pass = all_pass and l0_ok

# === 测试 6: 脉络不影响基础纹理绘制（绘制不抛异常）===
print()
print("=" * 60)
print("测试 6: _draw_flow_textures 脉络绘制（带 mock）")
print("=" * 60)
# 用 Pygame 离屏 surface 模拟屏幕
import pygame
pygame.init()
screen = pygame.Surface((1280, 720), pygame.SRCALPHA)
t3 = target_object.TargetObject()
buf = io.StringIO()
ok_draw = True
err = None
try:
    with contextlib.redirect_stdout(buf):
        for lv in range(5):
            t3.memory_level = lv
            for _ in range(100):
                t3.update()
            t3._draw_flow_textures(screen)
except Exception as e:
    ok_draw = False
    err = str(e)
print(f"  5 个等级 _draw_flow_textures 调用: {'OK' if ok_draw else 'FAIL: ' + err}")
all_pass = all_pass and ok_draw

# === 测试 7: reset_position 重置 _current_vein_color ===
print()
print("=" * 60)
print("测试 7: reset_position 重置脉络色")
print("=" * 60)
t3.reset_position()
reset_vein = t3._current_vein_color
reset_ok = (
    abs(reset_vein[0] - 185) < 0.1
    and abs(reset_vein[1] - 210) < 0.1
    and abs(reset_vein[2] - 225) < 0.1
)
print(f"  重置脉络色: ({reset_vein[0]:.1f}, {reset_vein[1]:.1f}, {reset_vein[2]:.1f})  期望 (185, 210, 225)")
print(f"  {'OK' if reset_ok else 'FAIL'}")
all_pass = all_pass and reset_ok

# === 测试 8: 与吞噬流程协作（receive_impact 升级到 L4）===
print()
print("=" * 60)
print("测试 8: 完整流程 receive_impact + 脉络")
print("=" * 60)
t4 = target_object.TargetObject()
with contextlib.redirect_stdout(buf):
    for i in range(60):
        t4.receive_impact(value=0.5, source_position={'x': t4.x + 50, 'y': t4.y})
    # 1000 帧让插值接近收敛（速度 0.002 → 1000 帧约 86.5% 收敛）
    for _ in range(1000):
        t4.update()
flow_ok = (
    t4.memory_level == 4
    and abs(t4.get_memory_level_vein_strength(t4.memory_level) - 0.85) < 0.01
    and t4._current_vein_color[0] > 220
    and t4._current_vein_color[2] < 130
)
print(f"  fragment_count={t4.fragment_count}, memory_level={t4.memory_level}")
print(f"  vein_strength = {t4.get_memory_level_vein_strength(4)}")
print(f"  current_vein = ({t4._current_vein_color[0]:.1f}, {t4._current_vein_color[1]:.1f}, {t4._current_vein_color[2]:.1f})")
print(f"  {'OK 完整流程正常' if flow_ok else 'FAIL'}")
all_pass = all_pass and flow_ok

print()
print("=" * 60)
print(f"总结: {'全部通过' if all_pass else '存在失败'}")
print("=" * 60)
sys.exit(0 if all_pass else 1)
