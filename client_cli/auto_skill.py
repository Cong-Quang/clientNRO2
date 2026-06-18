"""
AutoSkill - Tự động tấn công và sử dụng kỹ năng
Dựa trên ModNroPc/Mod.community/AutoSkill.cs
"""
import time
from logger import log

# Skill IDs không cần target (AOE, buff, heal)
SKILL_NO_FOCUS = {
    6: 0,   # Thái Dương Hạ San
    8: 1,   # Kaioken
    12: 8,  # Tái tạo năng lượng
    13: 6,  # Trị thương
    19: 9,  # Liên hoàn
    21: 10, # Dịch chuyển
}

# Skill IDs cần cooldown dài hơn
SKILL_LONG_COOLDOWN = {7, 18, 20, 22, 23}  # Khiên, ẩn thân, đặc biệt


class AutoSkill:
    """AutoSkill - quản lý tự động tấn công và sử dụng kỹ năng."""

    MAX_SKILL_SLOTS = 10  # 10 ô kỹ năng như C#

    def __init__(self, state, service):
        self.state = state
        self.service = service

        # === Auto Attack ===
        self.auto_attack = False  # Tự động gửi đòn đánh khi có mob focus
        self._last_attack_time = 0
        self._attack_cooldown = 0.4  # 400ms giữa các đòn

        # === Auto Use Skills (per slot) ===
        self.auto_skills = [False] * self.MAX_SKILL_SLOTS  # Slot nào bật auto
        self.skill_delays = [500] * self.MAX_SKILL_SLOTS    # Delay ms mỗi slot
        self._skill_last_use = [0.0] * self.MAX_SKILL_SLOTS # Last use time
        self.skill_frozen = [False] * self.MAX_SKILL_SLOTS  # Freeze cooldown
        self.skill_ids = [0] * self.MAX_SKILL_SLOTS         # Skill template IDs (người dùng config)
        self.skill_names = [""] * self.MAX_SKILL_SLOTS      # Skill names (người dùng config)

        # === Auto Shield ===
        self.auto_shield = False

    # ====================================================================
    # COMMANDS
    # ====================================================================

    def toggle_auto_attack(self):
        """Bật/tắt auto attack."""
        self.auto_attack = not self.auto_attack
        log.raw(f"[Skill] Auto Attack: {'BAT' if self.auto_attack else 'TAT'}")
        log.raw("[Skill] Tu dong tan cong khi co mob focus")
        return self.auto_attack

    def list_skills(self):
        """Hiển thị danh sách skill slots."""
        log.raw(f"[Skill] {self.MAX_SKILL_SLOTS} o ky nang:")
        log.raw(f"  Slot | ID | Name         | Auto  | Delay  | Frozen")
        log.raw(f"  -----+----+--------------+-------+--------+-------")
        for i in range(self.MAX_SKILL_SLOTS):
            sid = self.skill_ids[i]
            name = self.skill_names[i] or f"Skill_{sid}" if sid else "(empty)"
            auto = "ON" if self.auto_skills[i] else "OFF"
            delay = f"{self.skill_delays[i]}ms" if self.auto_skills[i] else "-"
            frozen = "FROZEN" if self.skill_frozen[i] else ""
            log.raw(f"  [{i}]  | {sid or '-':2} | {name:<13} | {auto:5} | {delay:6} | {frozen}")
        log.raw(f"  Auto Attack: {'BAT' if self.auto_attack else 'TAT'}")
        log.raw(f"  Dung /autoskill <slot> on|off|delay <ms>|freeze de cau hinh")

    def configure_slot(self, slot: int, skill_id: int, name: str = ""):
        """Cấu hình skill ID cho 1 slot."""
        if 0 <= slot < self.MAX_SKILL_SLOTS:
            self.skill_ids[slot] = skill_id
            self.skill_names[slot] = name
            log.raw(f"[Skill] Slot [{slot}] = Skill {skill_id} ({name or 'Unnamed'})")

    def toggle_slot(self, slot: int):
        """Bật/tắt auto dùng skill ở 1 slot."""
        if 0 <= slot < self.MAX_SKILL_SLOTS:
            self.auto_skills[slot] = not self.auto_skills[slot]
            state = "BAT" if self.auto_skills[slot] else "TAT"
            sid = self.skill_ids[slot]
            name = self.skill_names[slot] or (f"Skill_{sid}" if sid else f"Slot {slot}")
            log.raw(f"[Skill] Auto Skill [{slot}] {name}: {state}")
            if self.auto_skills[slot]:
                self._skill_last_use[slot] = 0.0  # Reset timer

    def set_delay(self, slot: int, delay_ms: int):
        """Set delay cho 1 skill slot."""
        if 0 <= slot < self.MAX_SKILL_SLOTS:
            self.skill_delays[slot] = max(100, delay_ms)
            self.auto_skills[slot] = True  # Auto bật khi set delay
            sid = self.skill_ids[slot]
            name = self.skill_names[slot] or (f"Skill_{sid}" if sid else f"Slot {slot}")
            log.raw(f"[Skill] Auto [{slot}] {name}: delay = {delay_ms}ms")

    def toggle_freeze(self, slot: int):
        """Freeze/unfreeze 1 skill slot (cooldown = 0)."""
        if 0 <= slot < self.MAX_SKILL_SLOTS:
            self.skill_frozen[slot] = not self.skill_frozen[slot]
            state = "FROZEN" if self.skill_frozen[slot] else "unfrozen"
            sid = self.skill_ids[slot]
            name = self.skill_names[slot] or (f"Skill_{sid}" if sid else f"Slot {slot}")
            log.raw(f"[Skill] Freeze [{slot}] {name}: {state}")

    def toggle_auto_shield(self):
        """Bật/tắt auto shield (khiên năng lượng)."""
        self.auto_shield = not self.auto_shield
        log.raw(f"[Skill] Auto Khiên: {'BAT' if self.auto_shield else 'TAT'}")

    # ====================================================================
    # UPDATE LOOP (called every ~500ms)
    # ====================================================================

    def update(self):
        """Called from auto updater thread every ~500ms."""
        me = self.state.my_char
        if not me or me.cHP <= 0 or me.cHPFull <= 0:
            return

        now = time.time()

        # 1. Auto Attack (dùng skill đang chọn để đánh mob focus)
        if self.auto_attack:
            self._update_auto_attack(now)

        # 2. Auto Use Skills (per slot)
        for i in range(self.MAX_SKILL_SLOTS):
            if self.auto_skills[i]:
                self._update_auto_skill(i, now)

        # 3. Auto Shield
        if self.auto_shield:
            self._update_auto_shield(now)

    def _update_auto_attack(self, now: float):
        """Auto send attack to mob focus."""
        me = self.state.my_char

        # Check cooldown
        if now - self._last_attack_time < self._attack_cooldown:
            return

        # Check if has mob focus (state.mobs + current_mob_id from auto_train)
        mob_focus_id = self._get_mob_focus()
        if mob_focus_id is not None:
            self.service.sendPlayerAttack([mob_focus_id], [], -1, 1)
            self._last_attack_time = now

    def _update_auto_skill(self, slot: int, now: float):
        """Auto use skill at slot."""
        skill_id = self.skill_ids[slot]
        if skill_id <= 0:
            return  # Chưa cấu hình skill ID

        me = self.state.my_char

        # Nếu skill bị freeze, dùng delay ngắn (500ms) để spam
        if self.skill_frozen[slot]:
            delay_s = 0.5
            # Bỏ qua check MP khi freeze
        else:
            delay_s = self.skill_delays[slot] / 1000.0
            # Check MP (ước lượng 5% MPFull cho mỗi skill)
            if me.cMPFull > 0:
                min_mp = max(50, me.cMPFull * 5 // 100)
                if me.cMP < min_mp:
                    return

        # Check delay
        if now - self._skill_last_use[slot] < delay_s:
            return

        # Not in home map
        if me.cgender is not None and self.state.map_id == 21 + me.cgender:
            return

        self._skill_last_use[slot] = now

        # Chọn skill
        self.service.selectSkill(skill_id)

        # Nếu là skill không cần focus, gửi skill_not_focus
        if skill_id in SKILL_NO_FOCUS:
            status = SKILL_NO_FOCUS[skill_id]
            self.service.skillNotFocus(status)
        else:
            # Skill cần target → gửi attack nếu có mob focus
            mob_focus_id = self._get_mob_focus()
            if mob_focus_id is not None:
                self.service.sendPlayerAttack([mob_focus_id], [], -1, 1)
            self._last_attack_time = now

    def _update_auto_shield(self, now: float):
        """Auto use shield skill.
        Extension: C# AutoSkill chỉ toggle flag, phần update loop này tự thêm.
        """
        shield_slot = -1
        for i in range(self.MAX_SKILL_SLOTS):
            if self.skill_ids[i] in (7, 434, 435, 436, 437, 438, 439, 440):  # Khiên + các cấp
                shield_slot = i
                break

        if shield_slot < 0:
            return

        delay_s = max(5.0, self.skill_delays[shield_slot] / 1000.0)  # Khiên tự dùng mỗi 5s
        if now - self._skill_last_use[shield_slot] < delay_s:
            return

        self._skill_last_use[shield_slot] = now

        # Chọn skill khiên và gửi skill_not_focus
        shield_id = self.skill_ids[shield_slot]
        self.service.selectSkill(shield_id)
        self.service.skillNotFocus(0)

    # ====================================================================
    # HELPERS
    # ====================================================================

    def _get_mob_focus(self) -> int | None:
        """Lấy ID của mob đang focus từ auto_train hoặc từ mob gần nhất."""
        # Kiểm tra auto_train (dùng public method)
        at = getattr(self.state, 'auto_train', None)
        if at and at.enabled:
            mob_id = at.get_current_mob_focus()
            if mob_id is not None:
                return mob_id

        # Nếu không có auto_train, tìm mob alive gần nhất
        mobs = getattr(self.state, 'mobs', []) or []
        me = self.state.my_char
        if not me or not mobs:
            return None

        # Tìm mob alive gần nhất
        best_mob = None
        min_dist = float('inf')
        for m in mobs:
            if m.get('status', 0) in (0, 1):  # dead/dying
                continue
            if m.get('isMobMe', False):
                continue
            dist = abs(me.cx - m.get('x', 0)) + abs(me.cy - m.get('y', 0))
            if dist < min_dist:
                min_dist = dist
                best_mob = m

        return best_mob.get('id') if best_mob else None

    def attack_mob(self, mob_id: int) -> bool:
        """Gửi đòn đánh tới 1 mob cụ thể. Trả về True nếu đã gửi."""
        now = time.time()
        if now - self._last_attack_time < self._attack_cooldown:
            return False
        self.service.sendPlayerAttack([mob_id], [], -1, 1)
        self._last_attack_time = now
        return True
