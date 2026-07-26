"""
数据导出模块
============
提供三种数据导出功能：
1. CSV 行为日志：实时追加每次行为，便于 Excel/Pandas 分析
2. JSON 完整会话：退出时保存整个会话的所有数据
3. 文字报告：退出时生成可读的会话报告

文件输出在 ./sessions/ 目录下：
- actions_{session_id}.csv   - 每次行为的实时日志
- session_{session_id}.json  - 完整会话数据
- report_{session_id}.txt    - 文字报告
"""

import csv
import json
import os
import time
from datetime import datetime


# 状态枚举到中文/可读名的映射
STATE_NAMES_CN = {
    "calm": "平静",
    "alert": "警觉",
    "withdrawn": "退缩",
    "open": "敞开",
    "neglected": "被忽视",
}

# 行为分类到中文
ACTION_NAMES_CN = {
    "positive": "轻柔",
    "negative": "剧烈",
    "neutral": "中性",
}


class DataExporter:
    """数据导出器：管理一次会话的所有数据导出"""

    def __init__(self, session_dir="sessions"):
        """
        初始化数据导出器

        参数:
            session_dir: 会话文件保存目录（默认 ./sessions/）
        """
        # 创建会话目录
        os.makedirs(session_dir, exist_ok=True)

        # 生成 session_id（基于时间戳，确保唯一）
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 文件路径
        self.csv_path = os.path.join(session_dir, f"actions_{self.session_id}.csv")
        self.json_path = os.path.join(session_dir, f"session_{self.session_id}.json")
        self.report_path = os.path.join(session_dir, f"report_{self.session_id}.txt")

        # 会话元数据
        self.start_time = time.time()
        self.start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 会话数据（内存中累积）
        self.actions = []              # 所有行为
        self.state_transitions = []    # 状态切换
        self.fragments = []            # 生成的碎片
        self.ending = None             # 最终结局

        # 警觉累计时长统计
        self._alert_in = False
        self._alert_start = 0.0
        self._alert_total_time = 0.0

        # 初始化 CSV 表头
        self._init_csv()

        print(f"[DataExporter] 会话ID: {self.session_id}")
        print(f"[DataExporter] CSV 路径: {self.csv_path}")

    def _init_csv(self):
        """初始化 CSV 文件，写入表头"""
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',            # ISO 时间戳
                'session_time_sec',     # 距离会话开始的秒数
                'action_type_cn',       # 行为类型（中文）
                'action_type',          # 行为类型（英文）
                'intensity',            # 强度 0-1
                'distance_px',          # 轨迹距离（像素）
                'duration_sec',         # 动作持续时间（秒）
                'speed_avg',            # 平均速度
                'acceleration',         # 加速度
                'state_before_cn',      # 动作前状态（中文）
                'state_before',         # 动作前状态（英文）
                'state_after_cn',       # 动作后状态（中文）
                'state_after',          # 动作后状态（英文）
                'inside_personal_space',# 是否在个人空间内（0/1）
            ])

    def log_action(self, action_dict, state_before, state_after, inside_personal_space=False):
        """
        记录一次行为到 CSV（实时追加）+ 内存

        参数:
            action_dict: 行为分析结果（来自 BehaviorAnalyzer）
                - classification: 'positive'/'negative'/'neutral'
                - intensity: 0-1
                - distance: 像素
                - duration: 秒
                - speed: 平均速度
                - acceleration: 加速度
            state_before: 动作前状态（字符串，如 'calm'）
            state_after: 动作后状态（字符串）
            inside_personal_space: 是否在个人空间内
        """
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().isoformat()

        classification = action_dict.get('classification', 'neutral')
        intensity = action_dict.get('intensity', 0.5)

        # 写入 CSV
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                f"{elapsed:.2f}",
                ACTION_NAMES_CN.get(classification, classification),
                classification,
                f"{intensity:.3f}",
                f"{action_dict.get('distance', 0):.1f}",
                f"{action_dict.get('duration', 0):.2f}",
                f"{action_dict.get('speed', 0):.1f}",
                f"{action_dict.get('acceleration', 0):.1f}",
                STATE_NAMES_CN.get(state_before, state_before),
                state_before,
                STATE_NAMES_CN.get(state_after, state_after),
                state_after,
                1 if inside_personal_space else 0,
            ])

        # 同时保存到内存（用于 JSON 导出）
        self.actions.append({
            'timestamp': timestamp,
            'elapsed_sec': elapsed,
            'action': action_dict,
            'state_before': state_before,
            'state_after': state_after,
            'inside_personal_space': inside_personal_space,
        })

    def on_state_change(self, old_state, new_state):
        """
        状态切换回调（绑定到 EmotionalCore.on_state_change）

        参数:
            old_state: EmotionalState 枚举
            new_state: EmotionalState 枚举
        """
        old_name = old_state.value if hasattr(old_state, 'value') else str(old_state)
        new_name = new_state.value if hasattr(new_state, 'value') else str(new_state)

        if old_name == new_name:
            return

        elapsed = time.time() - self.start_time
        self.state_transitions.append({
            'elapsed_sec': elapsed,
            'from': old_name,
            'to': new_name,
        })

        # 警觉时间累计
        if new_name == 'alert' and old_name != 'alert':
            self._alert_in = True
            self._alert_start = elapsed
        elif old_name == 'alert' and new_name != 'alert':
            if self._alert_in:
                self._alert_total_time += elapsed - self._alert_start
                self._alert_in = False

    def log_fragment(self, fragment_type, position):
        """记录一次碎片生成"""
        self.fragments.append({
            'elapsed_sec': time.time() - self.start_time,
            'type': fragment_type,
            'position': list(position) if position else None,
        })

    def save_session(self, ending=None, extra_data=None):
        """
        退出时保存 JSON 完整会话

        参数:
            ending: 结局字符串
            extra_data: 额外数据（如情感总结）
        """
        # 收尾警觉计时
        if self._alert_in:
            self._alert_total_time += time.time() - self.start_time - self._alert_start
            self._alert_in = False

        self.ending = ending or self.ending
        elapsed = time.time() - self.start_time

        # 统计
        positive = sum(1 for a in self.actions
                      if a['action'].get('classification') == 'positive')
        negative = sum(1 for a in self.actions
                      if a['action'].get('classification') == 'negative')
        neutral = sum(1 for a in self.actions
                     if a['action'].get('classification') == 'neutral')

        data = {
            'session_id': self.session_id,
            'start_time': self.start_time_str,
            'end_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'duration_sec': elapsed,
            'ending': self.ending,
            'summary': {
                'total_actions': len(self.actions),
                'positive_actions': positive,
                'negative_actions': negative,
                'neutral_actions': neutral,
                'alert_total_sec': self._alert_total_time,
                'state_transitions_count': len(self.state_transitions),
                'fragments_count': len(self.fragments),
            },
            'actions': self.actions,
            'state_transitions': self.state_transitions,
            'fragments': self.fragments,
        }

        # 合并额外数据
        if extra_data and isinstance(extra_data, dict):
            data['extra'] = extra_data

        # 写入 JSON
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[DataExporter] JSON 会话已保存: {self.json_path}")

    def save_report(self, ending=None):
        """
        生成文字报告

        返回:
            report_text: 报告内容（同时写入 .txt 文件）
        """
        # 收尾警觉计时
        if self._alert_in:
            self._alert_total_time += time.time() - self.start_time - self._alert_start
            self._alert_in = False

        self.ending = ending or self.ending
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        # 统计
        positive = sum(1 for a in self.actions
                      if a['action'].get('classification') == 'positive')
        negative = sum(1 for a in self.actions
                      if a['action'].get('classification') == 'negative')
        neutral = sum(1 for a in self.actions
                     if a['action'].get('classification') == 'neutral')

        # 最强烈的一次行为
        max_intensity_action = None
        if self.actions:
            max_intensity_action = max(
                self.actions,
                key=lambda a: a['action'].get('intensity', 0)
            )

        # 反思建议
        if negative > positive * 2:
            reflection = (
                "  你做出了更多剧烈行为。\n"
                "  试着用更慢、更轻的方式接近。\n"
                "  注意对方是否退缩——那是 TA 在说'我需要空间'。"
            )
        elif positive > negative * 2:
            reflection = (
                "  你以轻柔的关怀为主。\n"
                "  这是一种尊重对方的方式——\n"
                "  对方能感受到你的耐心和体贴。"
            )
        elif negative == 0 and positive == 0:
            reflection = "  这次会话中你没有做出明确的行为。\n  试着靠近一点，看看会发生什么。"
        else:
            reflection = (
                "  你的行为较为均衡。\n"
                "  留意对方的反应——\n"
                "  TA 的状态会告诉你哪种方式更合适。"
            )

        # 报告内容
        lines = []
        lines.append("=" * 52)
        lines.append("  行为空间 - 会话报告")
        lines.append("  The Trace We Leave - Session Report")
        lines.append("=" * 52)
        lines.append(f"会话ID:  {self.session_id}")
        lines.append(f"开始:    {self.start_time_str}")
        lines.append(f"时长:    {minutes}分{seconds}秒")
        lines.append(f"结局:    {self.ending or '未分类'}")
        lines.append("-" * 52)
        lines.append("行为统计:")
        lines.append(f"  轻柔 (positive):  {positive:>4} 次")
        lines.append(f"  剧烈 (negative):  {negative:>4} 次")
        lines.append(f"  中性 (neutral):   {neutral:>4} 次")
        lines.append(f"  警觉累计时长:     {self._alert_total_time:>5.1f} 秒")
        lines.append(f"  状态切换次数:     {len(self.state_transitions):>4} 次")
        lines.append(f"  碎片生成数:       {len(self.fragments):>4} 个")
        lines.append("-" * 52)

        if max_intensity_action:
            act = max_intensity_action['action']
            cls = act.get('classification', 'neutral')
            lines.append("最强烈的一次行为:")
            lines.append(f"  类型: {ACTION_NAMES_CN.get(cls, cls)}")
            lines.append(f"  强度: {act.get('intensity', 0):.2f}")
            lines.append(f"  发生于: {max_intensity_action['elapsed_sec']:.1f} 秒")

        lines.append("-" * 52)
        lines.append("反思:")
        lines.append(reflection)
        lines.append("=" * 52)
        lines.append("详细数据文件:")
        lines.append(f"  CSV日志: {self.csv_path}")
        lines.append(f"  完整会话: {self.json_path}")
        lines.append("=" * 52)

        report_text = "\n".join(lines)

        # 写入文件
        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(f"[DataExporter] 文字报告已保存: {self.report_path}")

        return report_text

    def get_session_duration(self):
        """获取当前会话时长（秒）"""
        return time.time() - self.start_time

    def get_action_counts(self):
        """获取行为统计"""
        positive = sum(1 for a in self.actions
                      if a['action'].get('classification') == 'positive')
        negative = sum(1 for a in self.actions
                      if a['action'].get('classification') == 'negative')
        neutral = sum(1 for a in self.actions
                     if a['action'].get('classification') == 'neutral')
        return {
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'total': len(self.actions),
        }
