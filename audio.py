"""
音效模块（单音钢琴音色）
========================
每个音效只用 1 个音符，纯净简明。
合成原理：基频 + 6 谐波叠加 + 5ms 攻击 + 指数衰减。
"""

import numpy as np
import pygame


SAMPLE_RATE = 22050
MASTER_VOLUME = 0.30
_available = False


# C2-C6 音域（向低扩展到 C2 容纳警觉状态）
NOTE_C2 = 65.41   # 警觉（低沉压迫）
NOTE_C3 = 130.81  # 退缩
NOTE_C4 = 261.63  # 敞开
NOTE_D4 = 293.66
NOTE_E4 = 329.63
NOTE_F4 = 349.23
NOTE_G4 = 392.00
NOTE_A4 = 440.00
NOTE_B4 = 493.88
NOTE_C5 = 523.25
NOTE_D5 = 587.33
NOTE_E5 = 659.25
NOTE_F5 = 698.46
NOTE_G5 = 783.99
NOTE_A5 = 880.00
NOTE_B5 = 987.77
NOTE_C6 = 1046.50


def _piano_note(freq, duration, velocity=1.0, decay=3.0):
    """钢琴单音：基频 + 6 谐波 + 指数衰减包络"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.zeros_like(t)
    for n in range(1, 7):
        wave += np.sin(2 * np.pi * freq * n * t) / n
    attack_n = max(1, int(0.005 * SAMPLE_RATE))
    if attack_n >= len(t):
        attack_n = len(t) // 2
    env = np.ones_like(t)
    env[:attack_n] = np.linspace(0, 1, attack_n)
    env = env * np.exp(-t * decay)
    return wave * env * velocity


def _normalize(wave, peak=0.95):
    m = np.max(np.abs(wave))
    return wave / m * peak if m > 1e-6 else wave


def _make_sound(wave, volume=1.0):
    if not _available:
        return None
    wave = _normalize(wave) * volume * MASTER_VOLUME
    samples = (wave * 32767).astype(np.int16)
    if samples.ndim == 1:
        samples = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(np.ascontiguousarray(samples))


# ============= 4 个单音音效（按频率映射情绪） =============
# 设计原则：
# - 正向（轻柔/敞开）= 低频（C3 130Hz，沉稳、克制）
# - 负向（警觉/退缩/剧烈/伤害）= 高频（C5 523Hz，警惕、紧张）
# - 简洁到极致：只 4 个音，每个就是单音钢琴

def _make_gentle_sound():
    """轻柔画线：C3 低频（正向）"""
    return _make_sound(_piano_note(NOTE_C3, 0.7, decay=2.5), volume=0.7)


def _make_violent_sound():
    """剧烈画线：C5 高频（负向）"""
    return _make_sound(_piano_note(NOTE_C5, 0.4, decay=4.5), volume=0.8)


def _make_alert_sound():
    """进入红圈 / 警觉状态：C6（最高频，优先级最高）"""
    return _make_sound(_piano_note(NOTE_C6, 0.4, decay=4.0), volume=0.85)


def _make_withdrawn_sound():
    """退缩状态：C5 高频（负向，但低于警觉 C6）"""
    return _make_sound(_piano_note(NOTE_C5, 0.6, decay=3.5), volume=0.75)


def _make_open_sound():
    """敞开状态：C3 低频（正向，与轻柔同一低音）"""
    return _make_sound(_piano_note(NOTE_C3, 0.7, decay=2.2), volume=0.8)


def _make_harm_sound():
    """伤害冲击：C5 高频（负向，紧张）"""
    return _make_sound(_piano_note(NOTE_C5, 0.5, decay=4.0), volume=0.85)


def _make_breath_sound():
    """生命体呼吸：低频正弦（环境音）"""
    duration = 3.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    lfo = np.sin(2 * np.pi * 0.33 * t)
    wave = np.sin(2 * np.pi * 30 * t) * (0.3 + 0.7 * lfo) * 0.3
    return _make_sound(wave, volume=0.4)


class AudioManager:
    # 频率从高到低的音优先级排序（警觉 C6 最高、退缩 C5 次之、正向最低）
    # 用于排他播放：优先音频打断低优先级音频
    PRIORITY_ORDER = ['enter_red', 'harm', 'state_withdrawn', 'violent',
                      'state_open', 'gentle']

    # 警觉是绝对最高级：进入红圈时，独占所有负向音
    ALERT_HIGH_PRIORITY = {'enter_red'}

    def __init__(self):
        self.sounds = {}
        self.channels = {}        # name -> Channel（独占播放用）
        self.muted = False
        self.available = False
        self._init_mixer()

    def _init_mixer(self):
        global _available
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init()
            # 预留 8 个独立通道（默认是 8）
            pygame.mixer.set_num_channels(16)
            self.available = True
            _available = True
            self._load_sounds()
            print(f"[Audio] 音效初始化成功 ({len(self.sounds)} 个钢琴单音)")
        except pygame.error as e:
            self.available = False
            _available = False
            print(f"[Audio] 音效初始化失败：{e}")

    def _load_sounds(self):
        self.sounds['gentle'] = _make_gentle_sound()
        self.sounds['violent'] = _make_violent_sound()
        self.sounds['enter_red'] = _make_alert_sound()
        self.sounds['state_withdrawn'] = _make_withdrawn_sound()
        self.sounds['state_open'] = _make_open_sound()
        self.sounds['harm'] = _make_harm_sound()
        self.sounds['breath'] = _make_breath_sound()
        # 为每个音效预留独立通道（避免互相顶替）
        for name, sound in self.sounds.items():
            self.channels[name] = pygame.mixer.Channel(self._next_channel_id())
            self.channels[name].set_volume(1.0)

    def _next_channel_id(self):
        """按需分配通道 ID（0-15）"""
        used = {ch.get_volume() for ch in self.channels.values()}
        # 简单实现：直接顺序取下一个可用 ID
        for i in range(16):
            if not any(ch.get_queue() is not None for ch in [self.channels.get(n) for n in self.channels]):
                return i
        return len(self.channels) % 16

    def play(self, name, loops=0):
        """播放指定音效，警觉将打断低优先级音频"""
        if not self.available or self.muted:
            return
        sound = self.sounds.get(name)
        ch = self.channels.get(name)
        if sound is None or ch is None:
            return

        # 警觉（最高优先级）：打断所有负向音频
        if name in self.ALERT_HIGH_PRIORITY:
            self._stop_negative()

        # 用独占通道播放
        try:
            ch.play(sound, loops=loops)
        except pygame.error as e:
            print(f"[Audio] 播放失败 {name}: {e}")

    def _stop_negative(self):
        """打断所有负向音频（警觉专用）"""
        negative = {'violent', 'harm', 'state_withdrawn'}
        for n in negative:
            ch = self.channels.get(n)
            if ch:
                ch.stop()

    def stop(self, name=None):
        if not self.available:
            return
        if name is None:
            pygame.mixer.stop()
        else:
            ch = self.channels.get(name)
            if ch:
                ch.stop()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop()
        return self.muted

    def is_available(self):
        return self.available

    def is_muted(self):
        return self.muted


_audio_manager = None


def get_audio():
    return _audio_manager


def init_audio():
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager
