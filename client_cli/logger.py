import shutil
import sys
from datetime import datetime


class LogLevel:
    OFF = 0
    ERROR = 1
    WARN = 2
    INFO = 3
    DEBUG = 4

    _NAMES = ['OFF', 'ERR', 'WRN', 'INF', 'DBG']

    @classmethod
    def name(cls, level):
        return cls._NAMES[level] if 0 <= level < len(cls._NAMES) else '?'


CATEGORIES = [
    'general', 'connection', 'login', 'map', 'player', 'chat',
    'trade', 'social', 'combat', 'item', 'skill', 'pet',
    'clan', 'party', 'subcmd', 'network',
]

CAT_ALIAS = {
    'conn': 'connection', 'net': 'network', 'sub': 'subcmd',
    'pvp': 'combat', 'fight': 'combat', 'all': 'all',
}

TAG_TO_CAT = {
    'CLIENT': 'connection', 'LOGIN': 'login', 'MAP': 'map',
    'PLAYER': 'player', 'ME': 'player', 'CHAT': 'chat',
    'SERVER': 'chat', 'DIALOG': 'chat', 'BIG_MSG': 'chat',
    'ALERT': 'chat', 'NPC': 'general', 'SUB': 'subcmd',
    'HP': 'combat', 'EXP': 'combat', 'DIE': 'combat',
    'LIVE': 'combat', 'SPEED': 'player', 'LEVEL': 'player',
    'WEAPON': 'item', 'BODY': 'item', 'LEG': 'item',
    'RESET': 'map', 'TRADE': 'trade', 'FRIEND': 'social',
    'ENEMY': 'social', 'CLAN': 'clan', 'PARTY': 'party',
    'PET': 'pet', 'SKILL': 'skill', 'ITEM': 'item',
    'BOSS': 'combat', 'NETWORK': 'network', 'ERROR': 'general',
    'CHECK': 'network', 'VERSION': 'connection', 'AUTO': 'general',
    'UPGRADE': 'item', 'COMBINE': 'item', 'SPECIAL': 'skill',
    'TREE': 'item', 'TASK': 'general', 'MENU': 'general',
    'CONFIRM': 'general', 'TRANSPORT': 'map', 'FLAG': 'social',
    'LUCKY': 'general', 'QUAYSO': 'general', 'CARD': 'item',
    'EFFECT': 'general', 'LOCK': 'item', 'FUSION': 'player',
    'ANDROID': 'player', 'INPUT': 'network', 'TILE': 'map',
    'DATA': 'network', 'COIN': 'item', 'THROW': 'item',
    'PICK': 'item', 'POS': 'map', 'MOB': 'combat', 'MOVE': 'player',
    'ATTACK': 'combat', 'PVP': 'combat', 'GOTO': 'social',
    'NAME': 'login', 'UI': 'general', 'STATS': 'player',
    'BAG': 'item', 'BOX': 'item', 'POTENTIAL': 'skill',
    'SKILL_UP': 'skill', 'SORT': 'item', 'ACHIEVE': 'social',
    'CLIENT': 'connection',
}

C = '\033[{}m'
_RST = C.format(0)
_CYAN = C.format(36)
_GREEN = C.format(32)
_YELLOW = C.format(33)
_RED = C.format(31)
_GREY = C.format(90)
_BOLD = C.format(1)

LEVEL_COLOR = {
    LogLevel.ERROR: _RED,
    LogLevel.WARN: _YELLOW,
    LogLevel.INFO: _CYAN,
    LogLevel.DEBUG: _GREY,
}

TAG_COLOR = _GREEN


class Logger:
    def __init__(self):
        self._levels = {cat: LogLevel.INFO for cat in CATEGORIES}
        self._enabled = True
        self._compact = False
        self._use_color = False
        self._width = 80
        self._last_status = ''
        self._status_dirty = False
        self._safe_print = self._make_safe_print()

    def _make_safe_print(self):
        buf = sys.stdout.buffer
        def sp(text, **kw):
            try:
                print(text, **kw)
            except UnicodeEncodeError:
                try:
                    buf.write((text + '\n').encode('utf-8', 'replace'))
                    buf.flush()
                except Exception:
                    pass
            except Exception:
                pass
        return sp

    def auto_config(self):
        try:
            self._width = shutil.get_terminal_size().columns
        except Exception:
            self._width = 80
        self._compact = self._width < 60
        self._use_color = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

    def set_level(self, category, level):
        if category == 'all':
            for cat in CATEGORIES:
                self._levels[cat] = level
        elif category in self._levels:
            self._levels[category] = level

    def set_enabled(self, category, enabled):
        self.set_level(category, LogLevel.INFO if enabled else LogLevel.OFF)

    def get_level(self, category):
        return self._levels.get(category, LogLevel.INFO)

    def toggle(self):
        self._enabled = not self._enabled

    def status_text(self):
        return self._last_status

    def _write(self, level, tag, msg):
        if not self._enabled:
            return
        cat = TAG_TO_CAT.get(tag, 'general')
        if level > self._levels.get(cat, LogLevel.INFO):
            return

        if self._compact:
            text = f"{tag}>{msg}"
        else:
            ts = datetime.now().strftime('%H:%M:%S')
            lv = LogLevel.name(level)
            text = f"[{ts}][{lv}][{tag}] {msg}"

        if len(text) > self._width - 2:
            text = text[:self._width - 5] + '...'

        if self._use_color:
            lc = LEVEL_COLOR.get(level, '')
            tc = TAG_COLOR
            if self._compact:
                text = f"{tc}{tag}{_RST}>{msg}"
                if len(text) > self._width - 2:
                    text = text[:self._width - 5] + '...'
                out = f"{lc}{text}{_RST}"
            else:
                out = f"{lc}{text}{_RST}"
        else:
            out = text

        if self._status_dirty:
            out = '\r' + ' ' * self._width + '\r' + out
            self._status_dirty = False
        self._safe_print(out)

    def debug(self, tag, msg):
        self._write(LogLevel.DEBUG, tag, msg)

    def info(self, tag, msg):
        self._write(LogLevel.INFO, tag, msg)

    def warn(self, tag, msg):
        self._write(LogLevel.WARN, tag, msg)

    def error(self, tag, msg):
        self._write(LogLevel.ERROR, 'ERROR', msg)

    def raw(self, msg):
        if self._enabled:
            if self._status_dirty:
                self._safe_print('\r' + ' ' * self._width + '\r', end='')
                self._status_dirty = False
            self._safe_print(msg)

    def show_status(self, text):
        if not self._enabled:
            return
        if not self._use_color and not self._compact:
            return
        self._last_status = text
        if self._use_color:
            bar = f"{_BOLD}{_CYAN}{text}{_RST}"
        else:
            bar = text
        if len(bar) > self._width:
            bar = bar[:self._width]
        print(f"\r{bar}\033[K", end='', flush=True)
        self._status_dirty = True


log = Logger()
