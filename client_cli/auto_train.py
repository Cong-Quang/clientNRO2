"""
AutoTrain - Tự động train quái
Dựa trên ModNroPc/Mod.CuongLe/AutoTrainCL.cs và Mod.community/AutoSkill.cs
"""
import time
import random
from logger import log
from items_data import item_name


# Skill IDs không cần focus (AOE, buff, v.v.)
NO_FOCUS_SKILLS = {6, 8, 12, 13, 19, 21}
# Item IDs
TDKT_ID = 521       # Tự động luyện tập
NHO_XANH_ID = 212   # Nho xanh (hồi stamina)
NHO_TIM_ID = 211    # Nho tím


class AutoTrain:
    def __init__(self, state, service):
        self.state = state
        self.service = service

        # Core
        self.enabled = False

        # Mob list: dict[map_id] -> list[mob_template_id]
        self.train_mobs: dict[int, list[int]] = {}

        # Goback
        self.goback_enabled = False
        self.goback_map_id = -1
        self.goback_zone_id = -1
        self.goback_x = 0
        self.goback_y = 0
        self.goback_coord = False
        self.min_mp_percent = 5  # %MP → về nhà

        # Auto change zone
        self.auto_change_zone = False
        self.spam_change_zone = False
        self._last_change_zone_time = 0
        self.change_zone_delay = 11.0  # seconds

        # Filter
        self.hp_above = 0
        self.hp_below = 2**63 - 1  # practically unlimited

        # Auto use items
        self.auto_use_tdkt = True  # tự dùng TDKT

        # Internal state
        self._current_mob_id = -1  # mob id đang focus
        self._last_attack_time = 0
        self._attack_interval = 0.8  # seconds
        self._last_skill_select_time = 0
        self._last_mob_search_time = 0
        self._mob_search_interval = 0.5
        self._last_grape_time = 0
        self._grape_interval = 30.0

        # Stats
        self.total_kills = 0

    def get_current_mob_focus(self):
        """Public method: trả về mob ID đang focus hoặc None."""
        if self._current_mob_id >= 0:
            return self._current_mob_id
        return None

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            if self._get_current_mob_list():
                log.raw(f"[Train] Auto Train: BẬT (quái: {len(self._get_current_mob_list())} ID)")
            else:
                log.raw("[Train] Auto Train: BẬT (chưa có quái, dùng /trainmob add <id>)")
        else:
            self._current_mob_id = -1
            log.raw("[Train] Auto Train: TẮT")
        return self.enabled

    def set_hp_above(self, hp: int):
        self.hp_above = hp
        log.raw(f"[Train] Chỉ đánh quái HP trên: {hp}")

    def set_hp_below(self, hp: int):
        self.hp_below = hp
        log.raw(f"[Train] Chỉ đánh quái HP dưới: {hp}")

    def set_min_mp(self, percent: int):
        self.min_mp_percent = percent
        log.raw(f"[Train] Về nhà khi MP dưới {percent}%")

    # === MOB LIST MANAGEMENT ===
    def _get_current_mob_list(self) -> list[int]:
        """Lấy danh sách quái cần train ở map hiện tại."""
        map_id = self.state.map_id
        if map_id not in self.train_mobs:
            self.train_mobs[map_id] = []
        return self.train_mobs[map_id]

    def train_all_mobs(self):
        """Thêm tất cả quái trên map hiện tại vào danh sách train."""
        mobs = self.state.mobs
        if not mobs:
            log.raw("[Train] Không có quái nào trên map")
            return
        added = set()
        for m in mobs:
            if not m.get('isMobMe', False):
                tid = m.get('templateId')
                if tid is not None:
                    added.add(tid)
        self._get_current_mob_list().clear()
        self._get_current_mob_list().extend(list(added))
        log.raw(f"[Train] Đã thêm {len(added)} loại quái: {', '.join(str(x) for x in sorted(added))}")

    def add_mob(self, template_id: int):
        """Thêm 1 loại quái vào danh sách train."""
        mlist = self._get_current_mob_list()
        if template_id in mlist:
            log.raw(f"[Train] Quái ID={template_id} đã có trong danh sách")
            return
        mlist.append(template_id)
        log.raw(f"[Train] Đã thêm quái ID={template_id}")

    def clear_mobs(self):
        """Xóa danh sách quái train ở map hiện tại."""
        self._get_current_mob_list().clear()
        self._current_mob_id = -1
        self.enabled = False
        log.raw("[Train] Đã xóa danh sách quái train")

    def list_mobs(self):
        mlist = self._get_current_mob_list()
        if not mlist:
            log.raw("[Train] Danh sách quái train trống")
            return
        log.raw(f"[Train] Quái train ở map {self.state.map_id}: {', '.join(str(x) for x in mlist)}")

    # === GOBACK ===
    def toggle_goback(self):
        self.goback_enabled = not self.goback_enabled
        if self.goback_enabled:
            self.goback_map_id = self.state.map_id
            self.goback_zone_id = self.state.zone_id
            me = self.state.my_char
            self.goback_x = me.cx if me else 0
            self.goback_y = me.cy if me else 0
            self.goback_coord = False
            log.raw(f"[Train] Goback: BẬT (map={self.goback_map_id} zone={self.goback_zone_id})")
        else:
            log.raw("[Train] Goback: TẮT")
        return self.goback_enabled

    def toggle_goback_coord(self):
        self.goback_enabled = not self.goback_enabled
        if self.goback_enabled:
            self.goback_map_id = self.state.map_id
            self.goback_zone_id = self.state.zone_id
            me = self.state.my_char
            self.goback_x = me.cx if me else 0
            self.goback_y = me.cy if me else 0
            self.goback_coord = True
            log.raw(f"[Train] Goback tọa độ: BẬT ({self.goback_x},{self.goback_y})")
        else:
            log.raw("[Train] Goback: TẮT")
        return self.goback_enabled

    # === ZONE CHANGE ===
    def toggle_auto_zone(self):
        self.auto_change_zone = not self.auto_change_zone
        self.spam_change_zone = False
        log.raw(f"[Train] Auto đổi khu ít người: {'BẬT' if self.auto_change_zone else 'TẮT'}")
        return self.auto_change_zone

    def toggle_spam_zone(self):
        self.spam_change_zone = not self.spam_change_zone
        self.auto_change_zone = False
        log.raw(f"[Train] Spam đổi khu: {'BẬT' if self.spam_change_zone else 'TẮT'}")
        return self.spam_change_zone

    # === MAIN UPDATE LOOP ===
    def update(self):
        """Gọi mỗi tick (~500ms)."""
        me = self.state.my_char
        if not me:
            return

        if not self.enabled:
            return

        # Check dead
        if me.cHP <= 0 or me.cHPFull <= 0:
            return

        now = time.time()

        # Auto dùng TDKT
        if self.auto_use_tdkt:
            self._try_use_tdkt()

        # Auto dùng nho khi stamina thấp
        if me.cStamina <= 5 and now - self._last_grape_time > self._grape_interval:
            self._try_use_grape()
            self._last_grape_time = now

        # Check goback (MP thấp hoặc HP=1)
        if self.goback_enabled and self._is_low_mp_hp():
            self._handle_goback()
            return

        # Check auto change zone
        if self.auto_change_zone or self.spam_change_zone:
            self._try_change_zone(now)

        # Find next mob
        mob = self._find_next_mob()
        if not mob:
            return

        # Move to mob
        self._move_to_mob(mob)

        # Attack
        if now - self._last_attack_time > self._attack_interval:
            self._attack_mob(mob)
            self._last_attack_time = now

    def _is_low_mp_hp(self) -> bool:
        """Check if need to go home."""
        me = self.state.my_char
        if not me:
            return False
        if me.cHP == 1 and me.cHPFull > 1:
            return True
        if me.cMPFull > 0 and self.min_mp_percent > 0:
            mp_pct = (me.cMP * 100) // me.cMPFull
            if mp_pct < self.min_mp_percent:
                return True
        return False

    def _handle_goback(self):
        """Xử lý goback về nhà (phiên bản đơn giản hóa)."""
        me = self.state.my_char
        if not me:
            return

        home_map_id = 21 + me.cgender  # Nhà tương ứng gender

        if self.state.map_id != self.goback_map_id and self.state.map_id != home_map_id:
            # Đang ở map khác → không làm gì
            return

        if self.state.map_id != home_map_id:
            # Cần về nhà
            if me.cHP == 1 and me.cHPFull > 1:
                # Chết → về nhà
                self.service.returnTownFromDead()
            else:
                # Dùng xmap để về nhà nếu có xmap_runner
                xr = getattr(self.state, 'xmap_runner', None)
                if xr and not xr.is_running():
                    xr.start(home_map_id)
                    log.raw("[Train] Goback: Dang ve nha...")
            return

        # Đã ở nhà → heal (ăn đùi gà)
        self._try_eat_chicken()

        # Quay lại map cũ
        if self.state.map_id == home_map_id and self.goback_map_id != home_map_id and self.goback_map_id > 0:
            xr = getattr(self.state, 'xmap_runner', None)
            if xr and not xr.is_running():
                xr.start(self.goback_map_id)
                log.raw(f"[Train] Goback: Quay lai map {self.goback_map_id}")

    def _try_eat_chicken(self):
        """Try to eat chicken to heal."""
        bag = getattr(self.state, 'items_bag', []) or []
        for i, item in enumerate(bag):
            if item and item.get('id') in (73, 74):  # Đùi gà, Đùi gà nướng
                self.service.useItem(0, 1, i)
                return

    def _try_use_tdkt(self):
        """Auto use Tự Động Luyện Tập (item 521)."""
        bag = getattr(self.state, 'items_bag', []) or []
        for i, item in enumerate(bag):
            if item and item.get('id') == TDKT_ID:
                self.service.useItem(0, 1, i)
                return

    def _try_use_grape(self):
        """Auto use nho xanh/nho tím khi stamina thấp."""
        bag = getattr(self.state, 'items_bag', []) or []
        # Ưu tiên nho xanh
        for item_id in (NHO_XANH_ID, NHO_TIM_ID):
            for i, item in enumerate(bag):
                if item and item.get('id') == item_id:
                    self.service.useItem(0, 1, i)
                    return

    def _try_change_zone(self, now: float):
        """Try change zone to one with fewer players."""
        if now - self._last_change_zone_time < self.change_zone_delay:
            return

        # Check if already has mob focus
        if self._current_mob_id >= 0:
            return

        # Don't change zone in home
        me = self.state.my_char
        if me and self.state.map_id == 21 + me.cgender:
            return

        self._last_change_zone_time = now
        self.service.openUIZone()
        # Chọn zone ngẫu nhiên từ các zone (server sẽ xử lý)
        # Đơn giản: gửi request change zone về zone 0 (server tự xử lý)
        if self.spam_change_zone:
            # Thử zone random
            random_zone = random.randint(0, 10)
            self.service.requestChangeZone(random_zone)
        else:
            self.service.requestChangeZone(0)

    def _find_next_mob(self) -> dict | None:
        """Find next mob to attack from current map."""
        now = time.time()
        if now - self._last_mob_search_time < self._mob_search_interval:
            return None

        self._last_mob_search_time = now
        mlist = self._get_current_mob_list()
        if not mlist:
            return None

        mobs = getattr(self.state, 'mobs', []) or []

        target_ids = set(mlist)
        best_mob = None
        min_dist = float('inf')

        me = self.state.my_char

        for m in mobs:
            tid = m.get('templateId')
            hp = m.get('hp', 0)
            status = m.get('status', 0)
            is_mob_me = m.get('isMobMe', False)

            # Skip mob me, dead, invalid
            if is_mob_me:
                continue
            if status == 0 or status == 1:  # dead or dying
                continue
            if tid not in target_ids:
                continue

            # HP filter
            if hp < self.hp_above:
                continue
            if hp > self.hp_below:
                continue

            # Distance
            if me:
                dx = abs(me.cx - m.get('x', 0))
                dy = abs(me.cy - m.get('y', 0))
                dist = dx + dy
                if dist < min_dist:
                    min_dist = dist
                    best_mob = m

        return best_mob

    def _move_to_mob(self, mob: dict):
        """Move player to mob position."""
        me = self.state.my_char
        if not me:
            return

        mx = mob.get('x', 0)
        my = mob.get('y', 0)
        dx = abs(me.cx - mx)
        dy = abs(me.cy - my)

        # Only teleport if far away
        if dx > 50 or dy > 50:
            # Move to mob -> gửi charMove
            self.service.charMove(mx, my, 1, 1)
            # Cập nhật vị trí local
            me.cx = mx
            me.cy = my

    def _attack_mob(self, mob: dict):
        """Send attack to mob, su dung AutoSkill neu co."""
        mob_id = mob.get('id')
        if mob_id is None:
            return

        self._current_mob_id = mob_id

        # Uu tien dung AutoSkill de attack (co cooldown tracking)
        sk = getattr(self.state, 'auto_skill', None)
        if sk:
            sk.attack_mob(mob_id)
        else:
            self.service.sendPlayerAttack([mob_id], [], -1, 1)
