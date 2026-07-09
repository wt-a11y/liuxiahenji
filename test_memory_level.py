"""
记忆等级逻辑测试

仅测试 calculate_memory_level 的阈值是否正确，
不涉及绘制 / 颜色 / 动画。
"""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
import target_object


def expected_level(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 8:
        return 1
    if count <= 25:
        return 2
    if count <= 55:
        return 3
    return 4


# 关键测试点（包含所有边界）
test_counts = [0, 1, 8, 9, 25, 26, 55, 56, 100]

print("=" * 50)
print("记忆等级阈值测试")
print("=" * 50)

t = target_object.TargetObject()
all_pass = True
for c in test_counts:
    # 模拟当前碎片数
    t.fragment_count = c
    got = t.calculate_memory_level()
    want = expected_level(c)
    ok = (got == want)
    all_pass = all_pass and ok
    mark = "OK " if ok else "FAIL"
    print(f"  [{mark}] fragment_count={c:>2}  level={got}  (期望 {want})")

# 通过 receive_impact 验证等级自动更新
print()
print("=" * 50)
print("receive_impact 自动升级测试")
print("=" * 50)
t2 = target_object.TargetObject()
# 抑制其他print输出
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    for i in range(60):
        t2.receive_impact(value=0.5, source_position={'x': t2.x + 50, 'y': t2.y})
print(f"  累计调用 60 次 receive_impact")
print(f"  fragment_count = {t2.fragment_count}")
print(f"  memory_level   = {t2.memory_level}  (期望 4，因为 60>55)")
print(f"  {'OK' if t2.memory_level == 4 else 'FAIL'}")

# 验证 reset_position 重置等级
print()
print("=" * 50)
print("reset_position 重置测试")
print("=" * 50)
t2.reset_position()
print(f"  reset 后 fragment_count = {t2.fragment_count}")
print(f"  reset 后 memory_level   = {t2.memory_level}  (期望 0)")
print(f"  {'OK' if t2.fragment_count == 0 and t2.memory_level == 0 else 'FAIL'}")

print()
print("=" * 50)
print("总结:", "全部通过" if all_pass else "存在失败")
print("=" * 50)
sys.exit(0 if all_pass else 1)
