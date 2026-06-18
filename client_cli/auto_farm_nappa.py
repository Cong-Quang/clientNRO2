"""
AutoFarmBossNappa - Tu dong farm boss Nappa (Kuku, Map dau dinh, Rambo)
Duoc phan tich tu Mod.CuongLe/AutoFarmBossNappa.cs

Boss types:
  0 = Kuku (map 68-72)
  1 = Map dau dinh (map 64-67)
  2 = Rambo (map 73-77)

State machine:
  0=Khoi tao  1=Cho load map  2=Xmap den map  3=Khoi tao zone
  4=Request zone  41=Cho zone load  5=Kiem tra boss
  51=Theo doi HP boss  6=Dang danh boss  61=Nhat items
  7=Cho truoc zone tiep
"""
import time
import random
from logger import log

# Boss names mapping
BOSS_NAMES = ["Kuku", "Mập đầu đinh", "Rambo"]

# Map ranges per boss type
MAP_RANGES = {
    0: (68, 72),   # Kuku
    1: (64, 67),   # Map dau dinh
    2: (73, 77),   # Rambo
}

# Constants (matching C#)
GANG_THIEN_SU_ITEM_ID = 1070
BOSS_NO_DAMAGE_TIMEOUT = 10.0       # 10s
MAX_PICK_ATTEMPTS = 5
PICK_ITEM_DELAY = 0.8               # 800ms
ZONE_CHANGE_DELAY = 1.2             # 1.2s
MAP_LOAD_DELAY = 1.5                # 1.5s
BOSS_FIGHT_CHECK_DELAY = 2.0        # 2s
HP_CHECK_INTERVAL = 2.0             # 2s
HP_STUCK_CHECK_INTERVAL = 3.0       # 3s
WAIT_AFTER_BOSS_DEATH = 2.0         # 2s
MAX_CONSECUTIVE_NO_DAMAGE = 5
MAX_CONSECUTIVE_NO_DAMAGE_IN_FIGHT = 3
DEFAULT_START_ZONE = 2

# State constants
S_INITIALIZE = 0
S_WAITING_FOR_MAP_LOAD = 1
S_XMAP_TO_MAP = 2
S_INITIALIZE_ZONES = 3
S_REQUESTING_ZONE = 4
S_WAITING_FOR_ZONE_LOAD = 41
S_CHECKING_FOR_BOSS = 5
S_MONITORING_BOSS = 51
S_FIGHTING_BOSS = 6
S_PICKING_ITEMS = 61
S_WAITING_NEXT_ZONE = 7


class AutoFarmNappa:
    """Auto farm boss Nappa (Kuku, Map dau dinh, Rambo)"""

    def __init__(self, state, service):
        self.state = state
        self.service = service

        # Config
        self.enabled = False
        self.boss_type = 0  # 0=Kuku, 1=Map dau dinh, 2=Rambo

        # State machine
        self._state = S_INITIALIZE
        self._timer = 0.0
        self._current_map_id = 68
        self._target_zone = DEFAULT_START_ZONE

        # Boss tracking
        self._boss_entry_time = 0.0
        self._boss_damaged = False
        self._last_boss_hp = -1
        self._last_hp_check_time = 0.0
        self._consecutive_no_damage = 0
        self._boss_death_time = 0.0

        # Item pickup
        self._last_pick_time = 0.0
        self._pick_attempts = 0

        # Flags
        self._map_initialized = False
        self._resume_from_death = False

        # Status message
        self.status = ""

    def _log(self, msg: str):
        """Phat notification giong C# GameScr.info1.addInfo()"""
        log.info("NAPPA", msg)
        self.status = msg

    # ====================================================================
    # PUBLIC CONTROL
    # ====================================================================

    def start(self, boss_type: int = 0):
        """Bat dau auto farm boss Nappa"""
        self.boss_type = boss_type
        self.enabled = True
        self._reset_all()
        boss_name = BOSS_NAMES[boss_type] if 0 <= boss_type < len(BOSS_NAMES) else f"Type{boss_type}"
        self._log(f"Auto Farm Boss {boss_name}: BAT")

    def stop(self):
        """Dung auto farm (C#: Stop())"""
        self.enabled = False
        # Tat gim/tele/attack boss
        if self.state.auto_boss:
            self.state.auto_boss.gim_boss = False
            self.state.auto_boss.tele_boss = False
            self.state.auto_boss.attack_boss = False
        self._state = S_INITIALIZE
        self._target_zone = DEFAULT_START_ZONE
        self._consecutive_no_damage = 0
        self._log("Da dung auto farm boss Nappa")

    def cycle_type(self):
        """Chuyen loai boss (0→1→2→0)"""
        self.boss_type = (self.boss_type + 1) % 3
        if self.enabled:
            self._reset_all()
            self._state = S_INITIALIZE
        boss_name = BOSS_NAMES[self.boss_type]
        self._log(f"Chuyen sang farm: {boss_name}")
        return self.boss_type

    def is_running(self) -> bool:
        return self.enabled

    def list_status(self):
        """Hien thi trang thai"""
        boss_name = BOSS_NAMES[self.boss_type] if 0 <= self.boss_type < len(BOSS_NAMES) else f"Type{self.boss_type}"
        log.raw(f"[NAPPA] Auto Farm Boss Nappa: {'ON' if self.enabled else 'OFF'}")
        log.raw(f"  Loai boss: {boss_name}")
        if self.enabled:
            log.raw(f"  Trang thai: {self.status}")
            log.raw(f"  Map hien tai: {self.state.map_id}")
            log.raw(f"  Target zone: {self._target_zone}")
        # Hien thi boss tracker sightings gan day
        bt = getattr(self.state, 'boss_tracker', None)
        if bt:
            log.raw("")
            bt.list_sightings(30)

    # ====================================================================
    # MAIN UPDATE LOOP
    # ====================================================================

    def update(self):
        """Goi tu auto updater thread moi 500ms"""
        if not self.enabled:
            return

        try:
            # Handle death
            if self._handle_death():
                return

            # Handle lost (wrong map)
            if self._handle_lost():
                return

            self._process_state()
        except Exception as e:
            self._log(f"Loi update: {e}")
            self.stop()

    def _handle_death(self) -> bool:
        """Check chet va tu hoi sinh (C#: HandlePlayerDeath)"""
        me = self.state.my_char
        if not me or me.cHP > 0:
            return False

        # Chet -> hoi sinh
        self._log("Dang hoi sinh...")
        self.service.returnTownFromDead()
        self._timer = time.time() + MAP_LOAD_DELAY

        if self._current_map_id > 0:
            self._go_to_start_map()
            self._resume_from_death = True
        return True

    def _handle_lost(self) -> bool:
        """Kiem tra player co bi lac map khong (C#: HandlePlayerLost)"""
        if self._state == S_INITIALIZE:
            return False
        if self.state.map_id == self._current_map_id:
            return False
        if self.state.xmap_runner and self.state.xmap_runner.is_running():
            return False

        self._log("Quay lai map boss (lac duong)")
        self._go_to_start_map()
        self._resume_from_death = True
        return True

    def _process_state(self):
        """Xu ly state machine hien tai"""
        handlers = {
            S_INITIALIZE: self._handle_initialize,
            S_WAITING_FOR_MAP_LOAD: self._handle_waiting_map,
            S_XMAP_TO_MAP: self._handle_xmap,
            S_INITIALIZE_ZONES: self._handle_init_zones,
            S_REQUESTING_ZONE: self._handle_request_zone,
            S_WAITING_FOR_ZONE_LOAD: self._handle_wait_zone,
            S_CHECKING_FOR_BOSS: self._handle_check_boss,
            S_MONITORING_BOSS: self._handle_monitor_boss,
            S_FIGHTING_BOSS: self._handle_fight_boss,
            S_PICKING_ITEMS: self._handle_pick_items,
            S_WAITING_NEXT_ZONE: self._handle_wait_next_zone,
        }
        handler = handlers.get(self._state)
        if handler:
            handler()

    # ====================================================================
    # STATE HANDLERS
    # ====================================================================

    def _handle_initialize(self):
        """State 0: Khoi tao - chon map ngau nhien (C#: HandleInitialize)"""
        self._log("Khoi tao he thong")
        self._initialize_start_map()

    def _handle_waiting_map(self):
        """State 1: Cho map load xong (C#: HandleWaitingForMapLoad)"""
        if self.state.map_id != self._current_map_id:
            self._log("Dang di chuyen den map boss")
            self._go_to_start_map()
        elif self.state.zone_count > 0:
            self._log("Khoi tao danh sach khu")
            self._init_zones()
            self._state = S_INITIALIZE_ZONES

    def _handle_xmap(self):
        """State 2: Dang xmap (C#: HandleXmapToMap)"""
        xr = self.state.xmap_runner
        if not xr or not xr.is_running():
            # Xmap xong -> mo UI zone
            self.service.openUIZone()
            self._state = S_WAITING_FOR_MAP_LOAD
            self._log("Mo UI Zone")
        else:
            self._log("Dang Xmap den map boss")

    def _handle_init_zones(self):
        """State 3: Khoi tao zones - request zone dau tien (C#: HandleInitializeZones)"""
        max_zone = self.state.zone_count or 20
        if self._target_zone <= max_zone:
            self._log(f"Chuan bi doi khu {self._target_zone}")
            self._request_zone(self._target_zone)
            self._state = S_REQUESTING_ZONE
        else:
            self._log("Het khu, chuyen map tiep theo")
            self._move_to_next_map()

    def _handle_request_zone(self):
        """State 4: Dang request chuyen zone (C#: HandleRequestingZoneChange)"""
        now = time.time()
        if now < self._timer:
            self._log(f"Dang doi khu {self._target_zone}...")
            return

        if self.state.zone_id == self._target_zone:
            self._log(f"Da vao khu {self._target_zone}")
            self._timer = now + MAP_LOAD_DELAY
            self._state = S_WAITING_FOR_ZONE_LOAD
        else:
            self._log(f"Dang cho vao khu {self._target_zone}")
            self._request_zone(self._target_zone)

    def _handle_wait_zone(self):
        """State 41: Cho zone load xong (C#: HandleWaitingForZoneLoad)"""
        now = time.time()
        if now >= self._timer:
            self._log("Map da load, bat dau kiem tra boss")
            self._state = S_CHECKING_FOR_BOSS
        else:
            self._log(f"Dang doi map load (Khu {self._target_zone})...")

    def _handle_check_boss(self):
        """State 5: Kiem tra boss trong khu (C#: HandleCheckingForBoss)"""
        self._log("Kiem tra boss trong khu")

        if self._is_boss_present():
            self._on_boss_found()
        else:
            self._on_boss_not_found()

    def _handle_monitor_boss(self):
        """State 51: Theo doi HP boss (C#: HandleMonitoringBossHealth)"""
        self._log(f"Dang theo doi HP boss (Khu {self.state.zone_id})")

        boss = self._get_first_boss()
        if boss is None:
            self._on_boss_disappeared()
            return

        now = time.time()
        if now - self._last_hp_check_time < HP_CHECK_INTERVAL:
            self._log(f"Dang theo doi boss (HP: {boss.get('hp', 0)})")
            return

        self._check_boss_health(boss, now)
        self._check_phantom_boss(now)

    def _handle_fight_boss(self):
        """State 6: Dang danh boss (C#: HandleFightingBoss)"""
        now = time.time()

        if now < self._timer:
            self._log(f"Dang danh boss (Khu {self.state.zone_id})")
            return

        if self._is_boss_present():
            self._check_fight_progress(now)
            self._timer = now + BOSS_FIGHT_CHECK_DELAY
            self._log("Boss con song, tiep tuc danh")
        else:
            self._log("Boss da chet, cho 2 giay roi kiem tra item")
            self._boss_death_time = now
            self._reset_pickup()
            self._state = S_PICKING_ITEMS

    def _handle_pick_items(self):
        """State 61: Nhat item (C#: HandlePickingUpItems)"""
        now = time.time()

        # Cho 2s sau khi boss chet
        if now - self._boss_death_time < WAIT_AFTER_BOSS_DEATH:
            self._log(f"Cho boss respawn/tai item ({(now - self._boss_death_time)*1000:.0f}ms)")
            return

        if not self._has_gang_thien_su():
            self._log("Khong co manh thien su, chuyen khu")
            self._on_pickup_complete()
            return

        if now - self._last_pick_time < PICK_ITEM_DELAY:
            self._log(f"Dang nhat manh thien su ({self._pick_attempts}/{MAX_PICK_ATTEMPTS})")
            return

        if self._pick_gang_thien_su():
            self._last_pick_time = now
            self._pick_attempts += 1
            self._log(f"Da nhat manh thien su (lan {self._pick_attempts}/{MAX_PICK_ATTEMPTS})")

            if self._pick_attempts >= MAX_PICK_ATTEMPTS:
                self._log("Da nhat du so lan, chuyen khu")
                self._on_pickup_complete()
        else:
            self._log("Da nhat het manh thien su, chuyen khu")
            self._on_pickup_complete()

    def _handle_wait_next_zone(self):
        """State 7: Cho roi chuyen zone tiep (C#: HandleWaitingBeforeNextZone)"""
        now = time.time()
        if now >= self._timer:
            max_zone = self.state.zone_count or 20
            if self._target_zone < max_zone:
                self._target_zone += 1
                self._log(f"Chuyen sang khu {self._target_zone}")
                self._state = S_INITIALIZE_ZONES
            else:
                self._log("Het khu, chuyen map")
                self._move_to_next_map()
        else:
            self._log(f"Dang cho... (Khu {self._target_zone})")

    # ====================================================================
    # BOSS DETECTION
    # ====================================================================

    def _is_boss_present(self) -> bool:
        """Kiem tra co boss Nappa trong map khong (C#: IsBossPresent)"""
        for pid, p in self.state.players.items():
            name = p.get('name', '')
            if not name:
                continue
            if self._is_nappa_boss(p):
                return True
        return False

    def _get_first_boss(self) -> dict | None:
        """Tim boss Nappa dau tien trong map (C#: GetFirstBossInMap)"""
        for pid, p in self.state.players.items():
            if self._is_nappa_boss(p):
                return p
        return None

    def _is_nappa_boss(self, p: dict) -> bool:
        """Kiem tra player co phai boss Nappa khong (C#: IsValidBoss + IsValidBossInBounds)"""
        name = p.get('name', '')
        if not name:
            return False
        hp = p.get('hp', 0)
        if hp <= 0:
            return False
        # Kiem tra ten bat dau bang boss name
        if not self._starts_with_boss_name(name):
            return False
        # Kiem tra vi tri hop le
        x = p.get('x', 0)
        y = p.get('y', 0)
        if x <= 10 or y <= 10:
            return False
        return True

    def _starts_with_boss_name(self, name: str) -> bool:
        """Kiem tra ten co bat dau bang boss name khong (C#: StartsWithBossName)"""
        for boss_name in BOSS_NAMES:
            if name.lower().startswith(boss_name.lower()):
                return True
        return False

    def is_boss_nappa(self, name: str) -> bool:
        """Public method: kiem tra ten co phai boss Nappa khong (C#: IsBossNappa)"""
        if not name:
            return False
        return self._starts_with_boss_name(name)

    # ====================================================================
    # BOSS EVENTS
    # ====================================================================

    def _on_boss_found(self):
        """Xu ly khi tim thay boss (C#: OnBossFound)"""
        boss = self._get_first_boss()
        if boss is None:
            self._on_boss_not_found()
            return

        now = time.time()
        self._last_boss_hp = boss.get('hp', 0)
        self._last_hp_check_time = now
        self._boss_entry_time = now
        self._boss_damaged = False
        self._consecutive_no_damage = 0

        # Clear focus
        self._clear_focus()

        self._log(f"Tim thay boss {boss.get('name')} (HP: {boss.get('hp', 0)})")
        self._state = S_MONITORING_BOSS

    def _on_boss_not_found(self):
        """Xu ly khi khong tim thay boss (C#: OnBossNotFound)"""
        self._reset_boss_tracking()
        delay = 10.5  # ~10500ms cho manual play
        self._timer = time.time() + delay
        self._log("Khong co boss, cho chuyen khu tiep theo")
        self._state = S_WAITING_NEXT_ZONE

    def _on_boss_disappeared(self):
        """Xu ly khi boss bien mat (C#: OnBossDisappeared)"""
        self._log("Boss bien mat khi theo doi")
        self._reset_boss_tracking()
        self._move_to_next_zone_or_map()

    def _on_pickup_complete(self):
        """Xu ly khi nhat item xong (C#: OnItemPickupComplete)"""
        self._reset_boss_tracking()
        self._move_to_next_zone_or_map()

    # ====================================================================
    # BOSS HEALTH MONITORING
    # ====================================================================

    def _check_boss_health(self, boss: dict, now: float):
        """Kiem tra thay doi HP cua boss (C#: CheckBossHealthChange)"""
        hp = boss.get('hp', 0)
        if hp < self._last_boss_hp:
            self._on_boss_damaged(boss, now)
        elif hp == self._last_boss_hp:
            self._on_boss_stagnant(boss, now)
        else:
            self._on_boss_healed(boss, now)

    def _on_boss_damaged(self, boss: dict, now: float):
        """Boss bi mat HP (C#: OnBossTakingDamage)"""
        self._boss_damaged = True
        self._consecutive_no_damage = 0
        self._last_boss_hp = boss.get('hp', 0)
        self._last_hp_check_time = now
        self._timer = now + 2.5
        self._log(f"Boss dang bi danh (HP: {boss.get('hp', 0)})")
        self._state = S_FIGHTING_BOSS

    def _on_boss_stagnant(self, boss: dict, now: float):
        """HP boss khong doi (C#: OnBossHealthStagnant)"""
        self._consecutive_no_damage += 1
        self._last_hp_check_time = now
        self._log(f"Theo doi boss - HP khong doi lan {self._consecutive_no_damage} (HP: {boss.get('hp', 0)})")

    def _on_boss_healed(self, boss: dict, now: float):
        """HP boss tang len (C#: OnBossHealthIncreased)"""
        self._last_boss_hp = boss.get('hp', 0)
        self._last_hp_check_time = now
        self._consecutive_no_damage = 0

    def _check_phantom_boss(self, now: float):
        """Kiem tra boss ao (C#: CheckForPhantomBoss)"""
        timeout_reached = now - self._boss_entry_time >= BOSS_NO_DAMAGE_TIMEOUT
        too_many_checks = self._consecutive_no_damage >= MAX_CONSECUTIVE_NO_DAMAGE

        if (timeout_reached or too_many_checks) and not self._boss_damaged:
            self._log("Boss ao hoac khong the danh, bo qua khu")
            self._reset_boss_tracking()
            self._move_to_next_zone_or_map()

    def _check_fight_progress(self, now: float):
        """Kiem tra tien do danh boss (C#: CheckBossFightProgress)"""
        boss = self._get_first_boss()
        if boss is None:
            return

        if now - self._last_hp_check_time < HP_STUCK_CHECK_INTERVAL:
            return

        hp = boss.get('hp', 0)
        if hp < self._last_boss_hp:
            self._consecutive_no_damage = 0
            self._last_boss_hp = hp
            self._last_hp_check_time = now
        elif hp == self._last_boss_hp:
            self._consecutive_no_damage += 1
            self._last_hp_check_time = now

            if self._consecutive_no_damage >= MAX_CONSECUTIVE_NO_DAMAGE_IN_FIGHT:
                self._log("Boss ket/ao khi danh, chuyen khu")
                self._reset_boss_tracking()
                self._move_to_next_zone_or_map()
        else:
            self._last_boss_hp = hp
            self._last_hp_check_time = now
            self._consecutive_no_damage = 0

    # ====================================================================
    # ITEM PICKUP
    # ====================================================================

    def _has_gang_thien_su(self) -> bool:
        """Kiem tra co item Manh Thien Su (ID=1070) tren map khong (C#: HasGangThienSuItems)"""
        items = getattr(self.state, 'items_map', []) or []
        for item in items:
            if self._is_gang_thien_su(item):
                return True
        return False

    def _pick_gang_thien_su(self) -> bool:
        """Nhat item Manh Thien Su tren map (C#: PickAllGangThienSuItems)"""
        items = getattr(self.state, 'items_map', []) or []
        for item in items:
            if self._is_gang_thien_su(item):
                self._teleport_and_pick(item)
                return True
        return False

    def _is_gang_thien_su(self, item: dict) -> bool:
        """Kiem tra item co phai Manh Thien Su (C#: IsGangThienSuItem)"""
        if not item:
            return False
        me = self.state.my_char
        player_id = item.get('playerId', -1)
        template_id = item.get('templateId', -1)
        # Nhat item cua minh hoac Manh Thien Su
        if me and player_id == getattr(me, 'charID', -1):
            return True
        return template_id == GANG_THIEN_SU_ITEM_ID

    def _teleport_and_pick(self, item: dict):
        """Teleport den item va nhat (C#: TeleportAndPickItem)"""
        x = item.get('x', 0)
        y = item.get('y', 0)
        item_id = item.get('itemMapID', 0)
        # Teleport
        self.service.charMove(x, y, 1)
        # Pick
        self.service.pickItem(item_id)

    # ====================================================================
    # MAP & ZONE NAVIGATION
    # ====================================================================

    def _initialize_start_map(self):
        """Chon map ngau nhien dua vao boss type (C#: InitializeStartMap)"""
        map_range = MAP_RANGES.get(self.boss_type, (68, 72))
        self._current_map_id = random.randint(map_range[0], map_range[1])
        boss_name = BOSS_NAMES[self.boss_type] if self.boss_type < len(BOSS_NAMES) else f"Type{self.boss_type}"
        self._log(f"Chon map {boss_name} ({self._current_map_id})")

        # Configure auto settings (C#: ConfigureAutoSettings)
        self._configure_auto()

        self._reset_flags()
        self._consecutive_no_damage = 0
        self._state = S_WAITING_FOR_MAP_LOAD

    def _configure_auto(self):
        """Cau hinh auto settings (C#: ConfigureAutoSettings)"""
        # Auto dung TDKT
        if self.state.auto_train:
            self.state.auto_train.try_use_tdkt()
        # Bat gim/tele/attack boss
        if self.state.auto_boss:
            self.state.auto_boss.gim_boss = True
            self.state.auto_boss.tele_boss = True
            self.state.auto_boss.attack_boss = True
        self._log("Da cau hinh auto: Gim+Tele+Attack Boss")

    def _init_zones(self):
        """Khoi tao zone count (C#: InitializeZones)"""
        zone_count = getattr(self.state, 'zone_count', 0) or 20
        self._log(f"Khoi tao: {zone_count} khu")

        if self._map_initialized:
            return

        if self._resume_from_death:
            if self._target_zone < DEFAULT_START_ZONE or self._target_zone > zone_count:
                self._target_zone = DEFAULT_START_ZONE
            self._log(f"Tiep tuc tu khu {self._target_zone}")
            self._resume_from_death = False
        else:
            self._target_zone = DEFAULT_START_ZONE
            self._log("Bat dau tu khu 2")

        self._map_initialized = True

    def _go_to_start_map(self):
        """Xmap den map boss (C#: GoToStartMap)"""
        xr = self.state.xmap_runner
        if xr and not xr.is_running():
            xr.start(self._current_map_id)
        self._log(f"Dang Xmap den map {self._current_map_id}")
        self._state = S_XMAP_TO_MAP
        self._map_initialized = False

    def _request_zone(self, zone: int):
        """Request chuyen zone (C#: RequestZoneChange)"""
        self.service.requestChangeZone(zone)
        self._timer = time.time() + ZONE_CHANGE_DELAY
        self._log(f"Request doi khu {zone}")

    def _move_to_next_zone_or_map(self):
        """Chuyen sang zone tiep hoac map tiep (C#: MoveToNextZoneOrMap)"""
        if self.state.zone_id < (self.state.zone_count or 20):
            self._target_zone = self.state.zone_id + 1
            self._state = S_INITIALIZE_ZONES
        else:
            self._move_to_next_map()

    def _move_to_next_map(self):
        """Chuyen sang map tiep theo (C#: MoveToNextMap)"""
        map_range = MAP_RANGES.get(self.boss_type, (68, 72))
        if self._current_map_id >= map_range[1]:
            self._current_map_id = map_range[0]
        else:
            self._current_map_id += 1

        boss_name = BOSS_NAMES[self.boss_type] if self.boss_type < len(BOSS_NAMES) else f"Type{self.boss_type}"
        self._log(f"Chuyen map {boss_name} tiep theo ({self._current_map_id})")

        self._target_zone = DEFAULT_START_ZONE
        self._reset_flags()
        self._state = S_WAITING_FOR_MAP_LOAD

    # ====================================================================
    # HELPERS
    # ====================================================================

    def _clear_focus(self):
        """Xoa focus (C#: ClearPlayerFocus)"""
        pass  # CLI khong can clear focus

    def _reset_all(self):
        """Reset toan bo state (C#: ResetAllState)"""
        self._state = S_INITIALIZE
        self._timer = 0.0
        self._current_map_id = 68
        self._target_zone = DEFAULT_START_ZONE
        self._reset_boss_tracking()
        self._reset_pickup()
        self._reset_flags()
        self.status = ""

    def _reset_boss_tracking(self):
        """Reset boss tracking (C#: ResetBossTracking)"""
        self._boss_entry_time = 0.0
        self._boss_damaged = False
        self._last_boss_hp = -1
        self._last_hp_check_time = 0.0
        self._consecutive_no_damage = 0
        self._boss_death_time = 0.0

    def _reset_pickup(self):
        """Reset item pickup (C#: ResetItemPickup)"""
        self._last_pick_time = 0.0
        self._pick_attempts = 0

    def _reset_flags(self):
        """Reset flags (C#: ResetFlags)"""
        self._map_initialized = False
        self._resume_from_death = False
