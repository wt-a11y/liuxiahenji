"""
反思时刻模块

实现三种反思机制：
- 暂停反思：按空格暂停，查看当前状态
- 选择时刻：每2分钟弹出"继续"或"改变"选择
- 结局分支：根据行为模式显示不同结局
"""

import pygame
import time
from typing import List, Dict, Optional, Tuple
import math


class ReflectionSystem:
    """
    反思时刻管理器
    
    管理三种反思触发的时机和内容
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 选择时刻计时（每2分钟触发一次）
        self.choice_interval = 120.0  # 秒
        self.time_since_last_choice = 0.0
        self.choice_pending = False
        self.choice_count = 0

        # 暂停状态
        self.is_paused = False
        self.pause_surface = None  # 暂停时的快照

        # 结局评估
        self.ending_threshold_harm = 0.7  # 伤害主导的阈值
        self.ending_threshold_care = 0.6  # 关怀主导的阈值

        # 选择时刻的统计数据（用于生成有意义的提示）
        self.last_choice_care = 0.0
        self.last_choice_harm = 0.0
        self.last_choice_relationship = 0.0
    def update(self, dt: float) -> Optional[str]:
        """
        更新反思系统
        
        Returns:
            'pause' - 触发暂停反思
            'choice' - 触发选择时刻
            None - 无事件
        """
        if self.is_paused:
            return 'pause'
        
        self.time_since_last_choice += dt

        # 选择时刻已移除：不自动触发任何 choice_pending
        # 保留 time_since_last_choice 字段以兼容外部代码
        
        return None
    
    def trigger_pause(self, screen: pygame.Surface) -> pygame.Surface:
        """
        触发暂停，保存当前画面快照
        
        Returns:
            暂停时显示的 surface
        """
        self.is_paused = True
        self.pause_surface = screen.copy()
        return self.pause_surface
    
    def end_pause(self):
        """结束暂停"""
        self.is_paused = False
        self.pause_surface = None
    
    def evaluate_ending(self, emotional_core, consequence_manager) -> str:
        """
        评估最终结局

        Returns:
            'harm' - 伤害主导
            'care' - 关怀主导
            'mixed' - 混合
        """
        relationship = emotional_core.get_relationship_quality()
        cumulative = consequence_manager.get_cumulative_effect()

        if relationship < -self.ending_threshold_harm:
            return 'harm'
        elif relationship > self.ending_threshold_care:
            return 'care'
        else:
            return 'mixed'

    def apply_change_choice(self, emotional_core, particle_system, target_object):
        """
        应用"改变"选择的具体效果

        选择"改变"不是简单的清除，而是：
        1. 暂停"伤害-伤害-伤害"的惯性循环
        2. 给玩家一段"缓冲时间"重新建立连接
        3. 提示生命体"玩家在尝试不同"

        实际效果：
        - 累积伤害冻结（不重置，让玩家看到自己造成的）
        - 生命体进入"OPEN"状态（向玩家敞开）
        - 弹出温和提示
        """
        # 记录选择时刻的数据
        self.last_choice_care = emotional_core.cumulative_care
        self.last_choice_harm = emotional_core.cumulative_harm
        self.last_choice_relationship = emotional_core.get_relationship_quality()

        # 轻微降低累积伤害的权重（不是清除，是"降权"）
        emotional_core.cumulative_harm *= 0.7
        # 显著增加关怀
        emotional_core.cumulative_care += 1.5

        # 强制生命体进入"敞开"状态——这是"改变"的视觉确认
        from emotional_state import EmotionalState
        emotional_core._transition_to(EmotionalState.OPEN, intensity=0.7)

    def record_current_stats(self, emotional_core):
        """
        在选择时刻触发时记录当前统计数据
        """
        self.last_choice_care = emotional_core.cumulative_care
        self.last_choice_harm = emotional_core.cumulative_harm
        self.last_choice_relationship = emotional_core.get_relationship_quality()
    
    def get_choice_message(self, choice_num: int) -> str:
        """
        根据当前状态生成有意义的选择提示

        选择时刻的意义：
        1. 让玩家意识到"我有选择"——惯性 ≠ 必须
        2. 量化显示过去2分钟的行为倾向
        3. 给玩家一个"刹车点"——犹豫时主动暂停
        4. 让"改变"成为可操作选项，不只是口号
        """
        rel = self.last_choice_relationship
        care = self.last_choice_care
        harm = self.last_choice_harm

        if rel < -0.3:
            # 关系受损较重
            return (
                f"过去 2 分钟内，你造成了 {harm:.1f} 点伤害，"
                f"仅带来 {care:.1f} 点治愈。\n"
                f"它正在退缩。\n"
                f"你可以选择继续... 或者，停下来想一想。"
            )
        elif rel > 0.3:
            # 关系良好
            return (
                f"过去 2 分钟，你带来了 {care:.1f} 点治愈，"
                f"仅造成 {harm:.1f} 点伤害。\n"
                f"它正在敞开自己。\n"
                f"继续保持？还是尝试新的方式？"
            )
        else:
            # 关系中性
            return (
                f"过去 2 分钟，你的治愈和伤害都在累积。\n"
                f"（治愈 {care:.1f} / 伤害 {harm:.1f}）\n"
                f"你希望这段关系走向哪里？"
            )


def draw_pause_overlay(screen: pygame.Surface, 
                       target_object, 
                       emotional_core,
                       font_medium, font_small,
                       paused_time: float = 0.0):
    """
    绘制暂停反思界面
    
    Args:
        screen: 主屏幕
        target_object: 生命体对象
        emotional_core: 情感核心
        font_medium, font_small: 字体
        paused_time: 已暂停时长
    """
    # 半透明遮罩
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((10, 8, 18, 200))
    screen.blit(overlay, (0, 0))
    
    # 顶部标题
    title_text = "— 暂 停 反 思 —"
    title_surf = font_medium.render(title_text, True, (232, 188, 132))
    title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 80))
    screen.blit(title_surf, title_rect)
    
    # 当前状态
    state = emotional_core.current_state
    state_desc = emotional_core.get_state_description()
    
    # 状态显示
    state_color = {
        'calm': (150, 200, 180),
        'alert': (255, 180, 100),
        'withdrawn': (130, 130, 180),
        'open': (255, 220, 150),
        'neglected': (100, 100, 120),
    }.get(state.value, (200, 200, 200))
    
    state_label = font_medium.render(f"生命体状态: {state_desc}", True, state_color)
    state_rect = state_label.get_rect(center=(screen.get_width() // 2, 160))
    screen.blit(state_label, state_rect)
    
    # 累积数据
    y_offset = 220
    data_lines = [
        f"累积伤害: {emotional_core.cumulative_harm:.2f}",
        f"累积关怀: {emotional_core.cumulative_care:.2f}",
        f"关系质量: {emotional_core.get_relationship_quality():.2f}",
    ]
    
    for line in data_lines:
        text = font_small.render(line, True, (200, 200, 210))
        rect = text.get_rect(center=(screen.get_width() // 2, y_offset))
        screen.blit(text, rect)
        y_offset += 32
    
    # 关系条
    rel = emotional_core.get_relationship_quality()
    bar_width = 400
    bar_height = 20
    bar_x = (screen.get_width() - bar_width) // 2
    bar_y = y_offset + 20
    
    # 背景条
    pygame.draw.rect(screen, (40, 40, 50), 
                     (bar_x, bar_y, bar_width, bar_height), border_radius=10)
    
    # 关系指示（-1 伤害, 0 中性, 1 关怀）
    center_x = bar_x + bar_width // 2
    if rel >= 0:
        # 关怀（向右）
        fill_width = int(bar_width * 0.5 * rel)
        pygame.draw.rect(screen, (180, 220, 150), 
                         (center_x, bar_y, fill_width, bar_height), border_radius=10)
    else:
        # 伤害（向左）
        fill_width = int(bar_width * 0.5 * abs(rel))
        pygame.draw.rect(screen, (220, 120, 100), 
                         (center_x - fill_width, bar_y, fill_width, bar_height), 
                         border_radius=10)
    
    # 中线
    pygame.draw.line(screen, (150, 150, 160),
                     (center_x, bar_y - 5), (center_x, bar_y + bar_height + 5), 2)
    
    # 标签
    harm_label = font_small.render("伤害", True, (220, 120, 100))
    care_label = font_small.render("关怀", True, (180, 220, 150))
    screen.blit(harm_label, (bar_x - 50, bar_y))
    screen.blit(care_label, (bar_x + bar_width + 10, bar_y))
    
    # 提示（键盘 + 手势）
    hint = font_small.render("空格键 / ✋ 张开手掌 继续", True, (160, 160, 170))
    hint_rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 60))
    screen.blit(hint, hint_rect)
    
    # 反思提示
    reflection = font_small.render(
        "问问自己：接下来，你想怎样对待它？", 
        True, (180, 180, 190)
    )
    ref_rect = reflection.get_rect(center=(screen.get_width() // 2, screen.get_height() - 100))
    screen.blit(reflection, ref_rect)


def draw_choice_dialog(screen: pygame.Surface,
                        message: str,
                        font_large, font_medium, font_small,
                        selected: int = 0) -> int:
    """
    绘制选择时刻对话框

    选项设计意图：
    - "继续"代表惯性，让玩家意识到"我正在重复某种模式"
    - "改变"代表觉察，给予具体的改变路径
    """
    # 半透明遮罩
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((10, 8, 18, 220))
    screen.blit(overlay, (0, 0))

    # 标题
    title = font_large.render("— 选 择 时 刻 —", True, (232, 188, 132))
    title_rect = title.get_rect(center=(screen.get_width() // 2, 80))
    screen.blit(title, title_rect)

    # 副标题
    subtitle = font_small.render("（这是你的选择点，不是必须做的）", True, (150, 150, 160))
    sub_rect = subtitle.get_rect(center=(screen.get_width() // 2, 130))
    screen.blit(subtitle, sub_rect)

    # 提示消息（支持多行）
    lines = message.split('\n')
    msg_y = 180
    for line in lines:
        msg_surf = font_medium.render(line, True, (220, 220, 220))
        msg_rect = msg_surf.get_rect(center=(screen.get_width() // 2, msg_y))
        screen.blit(msg_surf, msg_rect)
        msg_y += 38

    # 选项
    options = [
        ("继续当前方式", "保持惯性，不做改变"),
        ("停下来，尝试改变", "用不同的方式对待它"),
    ]

    option_y = 380
    for i, (text, sub) in enumerate(options):
        is_selected = (i == selected)

        if is_selected:
            # 高亮背景
            opt_rect = pygame.Rect(0, 0, 700, 90)
            opt_rect.center = (screen.get_width() // 2, option_y)
            pygame.draw.rect(screen, (60, 50, 40), opt_rect, border_radius=10)
            pygame.draw.rect(screen, (232, 188, 132), opt_rect, 2, border_radius=10)
            text_color = (255, 220, 150)
            sub_color = (200, 200, 210)
        else:
            text_color = (150, 150, 160)
            sub_color = (110, 110, 120)

        # 主文本
        opt_surf = font_medium.render(text, True, text_color)
        opt_rect = opt_surf.get_rect(center=(screen.get_width() // 2, option_y - 12))
        screen.blit(opt_surf, opt_rect)

        # 副文本
        sub_surf = font_small.render(sub, True, sub_color)
        sub_rect = sub_surf.get_rect(center=(screen.get_width() // 2, option_y + 22))
        screen.blit(sub_surf, sub_rect)

        option_y += 110

    # 操作提示
    hint = font_small.render("← → 选择   回车 确认   ESC 跳过", True, (140, 140, 150))
    hint_rect = hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 40))
    screen.blit(hint, hint_rect)

    return selected


def draw_ending_screen(screen: pygame.Surface,
                       ending_type: str,
                       stats: Dict,
                       font_large, font_medium, font_small):
    """
    绘制结局界面
    
    Args:
        screen: 主屏幕
        ending_type: 'harm', 'care', 'mixed'
        stats: 统计数据
    """
    # 背景
    screen.fill((15, 12, 22))
    
    if ending_type == 'harm':
        # 伤害主导
        title = "伤 害 的 累 积"
        title_color = (220, 120, 100)
        messages = [
            "",
            "你是否意识到，",
            "有些痕迹，是无法完全抹去的。",
            "",
            "在人与人的相处中，",
            "我们有时会忽略自己的行为，",
            "直到看见对方身上的伤痕。",
            "",
            "——那么，在这样的前提下，",
            "应该怎样控制自己的行为？",
        ]
    elif ending_type == 'care':
        # 关怀主导
        title = "温 柔 的 力 量"
        title_color = (180, 220, 150)
        messages = [
            "",
            "你选择了温柔。",
            "",
            "它在你的关怀下，",
            "逐渐舒展、信任、回应。",
            "",
            "原来，治愈不需要激烈的方式，",
            "只需要持续、耐心、真诚的靠近。",
            "",
            "——这种力量，",
            "往往比我们想象中更强大。",
        ]
    else:
        # 混合
        title = "关 系 的 复 杂"
        title_color = (200, 180, 150)
        messages = [
            "",
            "伤害与修复，",
            "本就是关系中交织的两面。",
            "",
            "你伤害过它，",
            "也试图治愈它。",
            "",
            "——也许这就是真实的相处：",
            "没有完美，只有不断的觉察与调整。",
        ]
    
    # 标题
    title_surf = font_large.render(title, True, title_color)
    title_rect = title_surf.get_rect(center=(screen.get_width() // 2, 100))
    screen.blit(title_surf, title_rect)
    
    # 消息
    y = 200
    for line in messages:
        if line:
            text = font_medium.render(line, True, (220, 220, 220))
            rect = text.get_rect(center=(screen.get_width() // 2, y))
            screen.blit(text, rect)
        y += 45
    
    # 统计数据
    stats_y = screen.get_height() - 200
    stats_lines = [
        f"累积关怀: {stats.get('cumulative_care', 0):.1f}",
        f"累积伤害: {stats.get('cumulative_harm', 0):.1f}",
        f"持续时间: {stats.get('duration', 0):.0f} 秒",
    ]
    
    for line in stats_lines:
        text = font_small.render(line, True, (160, 160, 170))
        rect = text.get_rect(center=(screen.get_width() // 2, stats_y))
        screen.blit(text, rect)
        stats_y += 28
    
    # 退出提示
    exit_hint = font_small.render("按 ESC 退出", True, (140, 140, 150))
    exit_rect = exit_hint.get_rect(center=(screen.get_width() // 2, screen.get_height() - 30))
    screen.blit(exit_hint, exit_rect)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("反思时刻模块测试")
    print("=" * 50)
    
    print("\n该模块提供以下功能：")
    print("1. ReflectionSystem - 反思系统管理")
    print("2. draw_pause_overlay - 暂停反思界面")
    print("3. draw_choice_dialog - 选择时刻对话框")
    print("4. draw_ending_screen - 结局界面")
    print("\n" + "=" * 50)
