"""
AutoBoss - Tu dong do boss, gim boss, teleport va tan cong boss.
Duoc phan tich tu C# Mod.CuongLe/AutoBossCL.cs

Chuc nang:
- DoBoss (do boss): Quet tung khu tren map hien tai de tim boss
- GimBoss (auto gim): Tu dong focus vao boss co HP thap nhat
- TeleBoss: Tu dong dich chuyen den boss
- TanCongBoss: Tu dong tan cong boss
- Target list: Danh sach boss can tim (de trong = tim tat ca)
"""
import time
from logger import log


def is_boss(player_dict: dict) -> bool:
    """
    Kiem tra xem mot player co phai boss khong (giai thich tu C# MainMod.isBoss)
    
    C# code:
      return ch.cName != null && ch.cName != ""
          && !ch.isPet && !ch.isMiniPet
          && char.IsUpper(ch.cName[0])
          && ch.cName != "Trong tai"
          && !ch.cName.StartsWith("#")
          && !ch.cName.StartsWith("$");
    """
    name = player_dict.get('name', '')
    if not name:
        return False
    
    # Khong phai pet (trong CLI khong co flag isPet, bo qua)
    
    # Ten bat dau bang chu hoa
    if not name[0].isupper():
        return False
    
    # Loai tru cac ten dac biet
    if name in ("Trong tai", "Trọng tài"):
        return False
    if name.startswith("#") or name.startswith("$"):
        return False
    
    return True


class AutoBoss:
    """
    AutoBoss - Tu dong tim, tele va tan cong boss
    
    Giong C# AutoBossCL.cs:
    - DoBoss: Quet tung khu tren map de tim boss
    - aGimBoss: Focus vao boss HP thap nhat moi 500ms
    - AutoteleBoss: Teleport den boss moi 2.5s
    - tanCongBoss: Auto tan cong boss
    - target_names: Danh sach boss can tim
    """

    ZONE_SCAN_DELAY = 1.5    # Delay giua cac lan chuyen khu (1.5s)
    ZONE_CHECK_DELAY = 5.0   # Thoi gian cho o moi khu de kiem tra boss (5s)
    FOCUS_DELAY = 0.5        # Delay focus boss (500ms)
    TELE_DELAY = 2.5         # Delay tele den boss (2.5s)
    ATTACK_DELAY = 1.0       # Delay giua cac lan tan cong

    def __init__(self, state, service):
        self.state = state
        self.service = service

        # Settings
        self.do_boss = False          # Do boss (quet khu)
        self.gim_boss = False         # Auto gim boss (focus HP thap nhat)
        self.tele_boss = False        # Auto tele den boss
        self.attack_boss = False      # Auto tan cong boss
        self.target_names = []        # Danh sach ten boss can tim (rong = tim tat ca)

        # State machines
        self._do_boss_state = 0
        self._do_boss_target_zone = 0
        self._do_boss_timer = 0.0
        self._do_boss_old_map = -1
        # Timers
        self._focus_timer = 0.0
        self._tele_timer = 0.0
        self._attack_timer = 0.0

        # Track boss list
        self._boss_focus_pid = -1

    def update(self):
        """Main update - goi tu auto updater thread moi 500ms"""
        if self.state.my_char is None:
            return
        now = time.time()

        # Do boss
        if self.do_boss:
            self._update_do_boss(now)

        # Gim boss
        if self.gim_boss:
            self._update_gim_boss(now)

        # Tele boss
        if self.tele_boss or self.attack_boss:
            self._update_tele(now)

        # Attack boss
        if self.attack_boss:
            self._update_attack(now)

    def _is_valid_boss(self, name: str) -> bool:
        """Kiem tra ten co phai boss can tim khong"""
        if not self.target_names:
            return True  # Khong co danh sach = tim tat ca
        for target in self.target_names:
            if target.lower() in name.lower():
                return True
        return False

    def _find_boss_players(self, min_hp=True):
        """
        Tim tat ca boss player trong map.
        Neu min_hp=True, tra ve boss co HP thap nhat.
        """
        best = None
        best_hp = float('inf')
        me = self.state.my_char
        me_id = me.charID if me else -1
        now = time.time()

        for pid, p in self.state.players.items():
            if pid == me_id:
                continue
            name = p.get('name', '')
            if not is_boss(p):
                continue
            if not self._is_valid_boss(name):
                continue
            # Kiem tra HP
            hp = p.get('hp', 0)
            if hp <= 0:
                continue
            # Kiem tra vi tri hop le
            x = p.get('x', 0)
            y = p.get('y', 0)
            if x <= 10 or y <= 10:
                continue
            if min_hp:
                if hp < best_hp:
                    best_hp = hp
                    best = (pid, p)
            else:
                best = (pid, p)
                break  # Tra ve ngay cai dau tien

        return best

    def _check_boss_exists(self) -> bool:
        """Kiem tra co boss nao trong map khong"""
        for pid, p in self.state.players.items():
            if not is_boss(p):
                continue
            name = p.get('name', '')
            if not self._is_valid_boss(name):
                continue
            if p.get('hp', 0) <= 0:
                continue
            x = p.get('x', 0)
            y = p.get('y', 0)
            if x <= 10 or y <= 10:
                continue
            return True
        return False

    # ====================================================================
    # DO BOSS - State machine (giong C# UpdateAutoDoBoss)
    # ====================================================================
    """
    States:
    0: Khoi tao / check boss hien tai
    -1: Dang cho zone panel
    1: Goi chuyen zone
    2: Dang cho chuyen zone
    3: Kiem tra boss o zone moi
    4: Cho 5-10s roi chuyen zone tiep
    """

    def _update_do_boss(self, now: float):
        me = self.state.my_char
        if me is None:
            return

        current_map = self.state.map_id

        # Kiem tra map khong co boss
        if current_map in (21, 22, 23, 47, 48, 50, 116):
            self._log_boss("Map nay khong co boss!")
            self.do_boss = False
            return

        # Reset state machine khi doi map
        if current_map != self._do_boss_old_map:
            self._do_boss_old_map = current_map
            self._do_boss_state = 0
            log.info("BOSS", "Doi map -> Reset do boss lai tu dau")

        try:
            if self._do_boss_state == 0:
                # Kiem tra boss o zone hien tai
                if self._check_boss_exists():
                    boss = self._find_boss_players(min_hp=False)
                    name = boss[1].get('name', '?') if boss else '?'
                    self._log_boss(f"Da tim thay boss {name}")
                    self.do_boss = False
                    return

                # Bat dau quet zone
                self._do_boss_target_zone = self.state.zone_id + 1
                self.service.openUIZone()
                self._do_boss_state = -1

            elif self._do_boss_state == -1:
                # Dang cho zone panel
                if self._do_boss_timer == 0:
                    self._do_boss_timer = now + 1.0
                if now >= self._do_boss_timer or getattr(self.state, 'zone_count', 0) > 0:
                    self._do_boss_state = 1
                    # Reset timer cho state 1
                    self._do_boss_timer = 0

            elif self._do_boss_state == 1:
                max_zone = self.state.zone_count or 20
                if self._do_boss_target_zone <= max_zone:
                    self.service.requestChangeZone(self._do_boss_target_zone)
                    self._do_boss_timer = now + self.ZONE_SCAN_DELAY
                    self._do_boss_state = 2
                else:
                    self._log_boss("Da quet het khu, khong tim thay boss")
                    self.do_boss = False

            elif self._do_boss_state == 2:
                if now >= self._do_boss_timer:
                    if self.state.zone_id != self._do_boss_target_zone:
                        # Chua chuyen zone thanh cong, thu lai
                        self.service.requestChangeZone(self._do_boss_target_zone)
                        self._do_boss_timer = now + self.ZONE_SCAN_DELAY
                    else:
                        # Da chuyen zone thanh cong
                        self._do_boss_state = 3

            elif self._do_boss_state == 3:
                if self._check_boss_exists():
                    boss = self._find_boss_players(min_hp=False)
                    name = boss[1].get('name', '?') if boss else '?'
                    self._log_boss(f"Da tim thay boss {name}")
                    self.do_boss = False
                else:
                    # Cho 5-10s de load map xong roi kiem tra lai
                    self._do_boss_timer = now + self.ZONE_CHECK_DELAY
                    self._do_boss_state = 4

            elif self._do_boss_state == 4:
                if now >= self._do_boss_timer:
                    self._do_boss_target_zone += 1
                    if self._do_boss_target_zone <= 20:
                        self._do_boss_state = 1
                    else:
                        self._log_boss("Da quet het khu, khong tim thay boss")
                        self.do_boss = False

        except Exception as e:
            self._log_boss(f"Loi khi do boss: {e}")
            self.do_boss = False

    # ====================================================================
    # GIM BOSS - Auto focus boss HP thap nhat (giong C# UpdateAutoFocusBoss)
    # ====================================================================
    def _update_gim_boss(self, now: float):
        if now < self._focus_timer:
            return

        boss = self._find_boss_players(min_hp=True)
        if boss is not None:
            pid, p = boss
            self._boss_focus_pid = pid
            log.info("BOSS", f"Gim boss: {p.get('name')} HP={p.get('hp')}")

        self._focus_timer = now + self.FOCUS_DELAY

    # ====================================================================
    # TELE BOSS - Auto teleport den boss (giong C# UpdateTeleBoss)
    # ====================================================================
    def _update_tele(self, now: float):
        if now < self._tele_timer:
            return

        me = self.state.my_char
        if me is None:
            return

        boss = self._find_boss_players(min_hp=True)
        if boss is None:
            # Neu khong co boss va dang tan cong, dung lai
            return

        pid, p = boss
        bx = p.get('x', 0)
        by = p.get('y', 0)
        mx = me.cx
        my = me.cy

        # Tinh khoang cach
        dx = bx - mx
        dy = by - my
        dist = (dx * dx + dy * dy) ** 0.5

        self._boss_focus_pid = pid

        if dist > 30:
            # Teleport den boss
            self.service.charMove(bx, by, 1)
            log.info("BOSS", f"Tele den boss {p.get('name')} tai ({bx},{by})")

        self._tele_timer = now + self.TELE_DELAY

    # ====================================================================
    # ATTACK BOSS - Auto tan cong boss
    # ====================================================================
    def _update_attack(self, now: float):
        if now < self._attack_timer:
            return

        if self._boss_focus_pid == -1:
            return

        me = self.state.my_char
        if me is None:
            return

        # Gui tan cong vao player boss
        # Su dung sendPlayerAttack voi charIds
        cdir = 1  # Default direction
        self.service.sendPlayerAttack([], [self._boss_focus_pid], 1, cdir)
        log.debug("BOSS", f"Tan cong boss pid={self._boss_focus_pid}")

        self._attack_timer = now + self.ATTACK_DELAY

    # ====================================================================
    # HELPERS
    # ====================================================================
    def _log_boss(self, msg: str):
        """Phat notification giong C# GameScr.info1.addInfo()"""
        log.info("BOSS", msg)

    def toggle_do_boss(self) -> bool:
        """Bat/tat Do Boss (C#: Dò boss: ON/OFF)"""
        self.do_boss = not self.do_boss
        if not self.do_boss:
            self._do_boss_state = 0
        self._log_boss(f"Do boss: {'BAT' if self.do_boss else 'TAT'}")
        return self.do_boss

    def toggle_gim_boss(self) -> bool:
        """Bat/tat Gim Boss (C#: Auto gim boss: Bật/Tắt)"""
        self.gim_boss = not self.gim_boss
        self._log_boss(f"Gim boss (focus HP): {'BAT' if self.gim_boss else 'TAT'}")
        return self.gim_boss

    def toggle_tele_boss(self) -> bool:
        """Bat/tat Tele Boss (C#: Auto dịch theo Boss [STATUS: ON/OFF])"""
        self.tele_boss = not self.tele_boss
        self._log_boss(f"Tele den boss: {'BAT' if self.tele_boss else 'TAT'}")
        return self.tele_boss

    def toggle_attack_boss(self) -> bool:
        """Bat/tat Attack Boss (C#: Tan cong Boss: ON/OFF, auto bat tele)"""
        self.attack_boss = not self.attack_boss
        if self.attack_boss:
            self.tele_boss = True  # Tu dong bat tele khi tan cong
            self._log_boss("Tan cong Boss: BAT (da tu dong bat Tele Boss)")
        else:
            self.tele_boss = False
            self._log_boss("Tan cong Boss: TAT")
        return self.attack_boss

    def add_target(self, name: str):
        """Them ten boss vao danh sach (C#: Đã thêm boss: X)"""
        if name not in self.target_names:
            self.target_names.append(name)
            self._log_boss(f"Da them boss: {name}")

    def remove_target(self, name: str):
        """Xoa ten boss khoi danh sach (C#: Đã xóa boss: X)"""
        if name in self.target_names:
            self.target_names.remove(name)
            self._log_boss(f"Da xoa boss: {name}")

    def clear_targets(self):
        """Xoa toan bo danh sach boss (C#: Đã xóa danh sách boss)"""
        self.target_names.clear()
        self._log_boss("Da xoa danh sach boss (do tat ca)")

    def list_status(self):
        """Hien thi trang thai"""
        log.raw(f"[Boss] Trang thai:")
        log.raw(f"  Do Boss (quet khu):    {'ON' if self.do_boss else 'OFF'}")
        log.raw(f"  Gim Boss (focus HP):   {'ON' if self.gim_boss else 'OFF'}")
        log.raw(f"  Tele Boss (di chuyen): {'ON' if self.tele_boss else 'OFF'}")
        log.raw(f"  Tan Cong Boss:         {'ON' if self.attack_boss else 'OFF'}")
        if self.target_names:
            log.raw(f"  Danh sach boss: {', '.join(self.target_names)}")
        else:
            log.raw(f"  Danh sach boss: (tat ca)")
        # Dem boss trong map hien tai
        count = 0
        for pid, p in self.state.players.items():
            if is_boss(p) and self._is_valid_boss(p.get('name', '')):
                count += 1
        if count > 0:
            log.raw(f"  Boss trong map: {count}")
            for pid, p in self.state.players.items():
                if is_boss(p) and self._is_valid_boss(p.get('name', '')):
                    name = p.get('name', '?')
                    hp = p.get('hp', 0)
                    x = p.get('x', 0)
                    y = p.get('y', 0)
                    log.raw(f"    {name} HP={hp} tai ({x},{y})")
