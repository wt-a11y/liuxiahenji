"""
诊断测试：检查颜色等级系统的实际行为

不修改任何产品代码，仅观察并打印：
- absorbed_fragments (absorbed_count)
- fragment_count
- memory_level
- _current_core_color (实际显示的核心色)
- _current_texture_color (内部纹理色)
- _current_vein_color (脉络色)
- 视觉描述
"""
import os
import sys
import io
import contextlib

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import target_object


def color_distance(c1, c2):
    """计算两个 RGB 颜色之间的欧氏距离"""
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5


def describe_color(rgb):
    """简单描述颜色色调（冷/暖/橙/黄）"""
    r, g, b = rgb
    if r > 200 and g < 180 and b < 150:
        return "橙/暖"
    elif r > 200 and g > 180 and b < 180:
        return "琥珀/暖"
    elif b > r and b > g:
        return "冷青"
    elif g > r and g >= b:
        return "青绿"
    elif r > b and g > b and abs(r - g) < 30:
        return "中性偏暖"
    else:
        return f"RGB({r},{g},{b})"


# 冻结 print 以模拟"沉默"模式运行
buf = io.StringIO()
t = target_object.TargetObject()

# 测试关键碎片数量点
test_points = [0, 1, 2, 3, 4, 5, 7, 8, 9, 12, 13, 15, 20]

print("=" * 80)
print("诊断：碎片数量 → 等级 → 颜色映射 实际值")
print("=" * 80)
print()
print(f"{'碎片数':<6} {'等级':<5} {'核心色':<12} {'核心描述':<10} "
      f"{'纹理色':<12} {'纹理描述':<10} {'脉络色':<12} {'脉络描述':<10}")
print("-" * 80)

# 在每个测试点重置，然后吸收指定数量
for n in test_points:
    t.reset_position()
    # 让颜色先稳定 100 帧
    with contextlib.redirect_stdout(buf):
        for _ in range(100):
            t.update()
    # 吸收 n 个碎片
    with contextlib.redirect_stdout(buf):
        for i in range(n):
            t.receive_impact(value=0.5, source_position={'x': t.x + 50, 'y': t.y + 30})
    # 让颜色稳定收敛（200 帧 ≈ 90% 收敛）
    with contextlib.redirect_stdout(buf):
        for _ in range(200):
            t.update()

    core = tuple(int(c) for c in t._current_core_color)
    tex = tuple(int(c) for c in t._current_texture_color)
    vein = tuple(int(c) for c in t._current_vein_color)

    print(f"{n:<6} L{t.memory_level:<4} "
          f"{str(core):<12} {describe_color(core):<10} "
          f"{str(tex):<12} {describe_color(tex):<10} "
          f"{str(vein):<12} {describe_color(vein):<10}")

# === 相邻等级的颜色变化距离 ===
print()
print("=" * 80)
print("诊断：相邻等级核心色变化距离（数字越大 = 视觉跳变越明显）")
print("=" * 80)
print()

# 重新跑一遍，只收集核心色
core_samples = {}
for n in test_points:
    t.reset_position()
    with contextlib.redirect_stdout(buf):
        for _ in range(100):
            t.update()
        for i in range(n):
            t.receive_impact(value=0.5, source_position={'x': t.x + 50, 'y': t.y + 30})
        for _ in range(500):
            t.update()
    core_samples[n] = tuple(int(c) for c in t._current_core_color)

prev = None
prev_n = None
LEVEL_OF = {0: 0, 1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 7: 2, 8: 3, 9: 3, 12: 3, 13: 4, 15: 4, 20: 4}
for n in test_points:
    c = core_samples[n]
    if prev is not None:
        d = color_distance(c, prev)
        marker = "  ← 跳变明显" if d > 30 else ""
        print(f"  碎片 {prev_n}→{n} (L{LEVEL_OF[prev_n]}→L{LEVEL_OF[n]}): "
              f"距离 {d:5.1f}{marker}")
    prev = c
    prev_n = n

# === 脉络色与基底色对比 ===
print()
print("=" * 80)
print("诊断：脉络色 vs 核心基底色 差异（脉络叠加后是否突变）")
print("=" * 80)
print()

for n in test_points:
    t.reset_position()
    with contextlib.redirect_stdout(buf):
        for _ in range(100):
            t.update()
        for i in range(n):
            t.receive_impact(value=0.5, source_position={'x': t.x + 50, 'y': t.y + 30})
        for _ in range(500):
            t.update()
    core = tuple(int(c) for c in t._current_core_color)
    tex = tuple(int(c) for c in t._current_texture_color)
    vein = tuple(int(c) for c in t._current_vein_color)
    vein_str = t.get_memory_level_vein_strength(n)
    d_core_vein = color_distance(core, vein)
    d_tex_vein = color_distance(tex, vein)
    print(f"  碎片 {n} (L{t.memory_level}, 脉络强度 {vein_str:.2f}):")
    print(f"    核心 {core}  vs  脉络 {vein}  → 距离 {d_core_vein:.1f} {'(脉络明显跳脱基底)' if d_core_vein > 40 else ''}")
    print(f"    纹理 {tex}  vs  脉络 {vein}  → 距离 {d_tex_vein:.1f} {'(脉络明显跳脱纹理)' if d_tex_vein > 40 else ''}")

print()
print("=" * 80)
print("分析完成。请查看上方输出识别问题。")
print("=" * 80)
sys.exit(0)
