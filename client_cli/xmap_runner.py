import re
import threading
import time
from state import GameState
from service import Service
from xmap_pathfinder import find_path, get_next_link, get_error_message
from xmap_data import MapLink, is_nrd_map, is_future_map, CAPSULE_ITEM_IDS, MIN_PATH_LENGTH_FOR_CAPSULE, get_map_name, _normalize as _normalize_data, _strip_vietnamese_accents
from logger import log


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = _strip_vietnamese_accents(s)
    return re.sub(r'\s+', '', s)


class XmapRunner:
    def __init__(self, state: GameState, service: Service):
        self.state = state
        self.service = service
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

        self.is_running_flag = False
        self.target_map = -1
        self.xmap_error = False
        self.path: list[int] = []
        self.current_step = 0
        self.status = ""

        self.eat_chicken = True
        self.use_capsule = True
        self.teleport_mode = False
        self.map_delay = 1.5

        self._last_update = 0.0
        self._update_interval = 0.4
        self._last_error_time = 0.0
        self._error_cooldown = 1.0
        self._last_processed_map = -1
        self._last_map_change_time = 0.0
        self._is_processing_map_change = False

        # NPC confirmation system (move_type=1 - name-based)
        self._confirm_npc_id = -1
        self._confirm_menus: list[str] = []
        self._confirm_menus_sub: list[str] = []
        self._confirm_menus_sub2: list[str] = []
        self._confirm_step = 0
        self._confirm_start_time = 0.0
        self._confirm_last_step_time = 0.0
        self._confirm_step_delay = 0.5
        self._confirm_timeout = 3.5
        self._confirm_init_delay = 0.5
        self._running_open_npc = False

        # Capsule system
        self._is_using_capsule = False
        self._is_opening_panel = False
        self._capsule_panel_delay = 0.5
        self._last_capsule_time = 0.0
        self._capsule_map_names: list[str] = []

        # Track current map ID to detect zone-only changes
        self._current_zone_map_id = -1

        # Transport panel (CMD_MAP_TRASPORT - teleport panel from finishUpdate)
        self._panel_open = False
        self._panel_map_names: list[str] = []
        self._panel_planet_names: list[str] = []
        self._last_panel_handle_time = 0.0

        # Chicken pickup
        self._last_chicken_time = 0.0
        self._chicken_pickup_delay = 0.6

        # NPC index action delay (move_type=2 - like C# HandleNpcIndexInteraction)
        self._last_npc_index_time = 0.0
        self._npc_index_delay = 1.7  # customMapDelay + 1.2s as in C#

        # Track NPC interaction state (move_type=2) to prevent panel interference
        self._in_npc_interaction = False
        
        # Retry counter for map change
        self._retry_count = 0
        self._last_waypoint_is_offline = False
        
    def _move_to(self, x: int, y: int):
        """Gửi charMove (giống C# TeleportTo).
        Gửi 3 packet charMove: target position, slightly offset, back to target.
        Type=1 (air/fly) cho waypoint teleport.
        """
        me = self.state.my_char
        if me is None:
            return
        me.cx = x
        me.cy = y
        self.service.charMove(x, y, 1, type_=1)
        time.sleep(0.05)
        me.cy = y + 1
        self.service.charMove(x, y + 1, 1, type_=1)
        time.sleep(0.05)
        me.cy = y
        self.service.charMove(x, y, 1, type_=1)

    def _send_map_request(self, is_offline: bool):
        """Gửi request chuyển map đến server."""
        if is_offline:
            self.service.getMapOffline()
        else:
            self.service.requestChangeMap()
        self._last_map_change_time = time.time()
        self._is_processing_map_change = True

    def _waypoint_transition(self, target_x: int, target_y: int, is_offline: bool):
        """
        Thực hiện chuyển map qua waypoint.
        Giống C# Enter() flow:
        1. Gửi charMove đến waypoint (giống TeleportTo)
        2. Đợi server xử lý (tương đương 1 game tick = 0.4s)
        3. Gửi requestChangeMap / getMapOffline
        """
        # Step 1: Gửi charMove (giống C# TeleportTo)
        self._move_to(target_x, target_y)
        
        # Step 2: Đợi server xử lý charMove (giống C# đợi 1 game tick)
        time.sleep(0.4)
        
        # Step 3: Gửi request chuyển map
        self._send_map_request(is_offline)

    def start(self, target_map: int):
        if target_map == self.state.map_id:
            self.status = f"Đã đến map {target_map}!"
            self.is_running_flag = False
            self.target_map = target_map
            return

        if self._thread and self._thread.is_alive():
            self.stop()
            time.sleep(0.5)
        self.target_map = target_map
        self.path = []
        self.current_step = 0
        self.xmap_error = False
        self._last_processed_map = -1
        self._is_processing_map_change = False

        self._is_using_capsule = False
        self._is_opening_panel = False
        self._confirm_npc_id = -1
        self._retry_count = 0
        self._current_zone_map_id = -1
        self._last_waypoint_is_offline = False
        self.use_capsule = True  # Reset mặc định mỗi lần start
        self._stop.clear()
        self.is_running_flag = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.is_running_flag = False
        self.status = ""

        self._confirm_npc_id = -1
        self._is_using_capsule = False
        self._is_opening_panel = False
        self._current_zone_map_id = -1

    def is_running(self) -> bool:
        return self.is_running_flag

    def on_map_changed(self, map_id: int):
        """
        Called when server sends map info (both actual map change and zone change).
        Chỉ reset flow khi MAP thực sự thay đổi, không reset khi chỉ đổi zone.
        """
        if not self.is_running_flag:
            return

        is_new_map = (map_id != self._current_zone_map_id)
        self._current_zone_map_id = map_id

        if is_new_map:
            # Map thực sự thay đổi: reset toàn bộ flow
            self._last_processed_map = map_id
            self._last_map_change_time = time.time()
            self._is_processing_map_change = False
            self._confirm_npc_id = -1
            self._retry_count = 0
            self._panel_open = False
            self._in_npc_interaction = False
            self._last_waypoint_is_offline = False
        else:
            # Chỉ đổi zone: không reset flow, chỉ cập nhật _is_processing_map_change
            self._is_processing_map_change = False

    def on_capsule_map_list(self, map_names: list[str]):
        if self._is_using_capsule and not self._is_opening_panel:
            self._capsule_map_names = map_names

    def on_transport_panel(self, names: list[str]):
        """Called when CMD_MAP_TRASPORT teleport panel appears from finishUpdate."""
        if self._panel_open:
            return
        self._panel_open = True
        self._panel_map_names = names

    def on_npc_dialog(self, npc_id: int, options: list[str]):
        # Handle name-based NPC menu (move_type=1)
        if self._confirm_npc_id == npc_id:
            self._process_confirm_step(npc_id, options)

    def _process_confirm_step(self, npc_id: int, options: list[str]):
        now = time.time()
        if now - self._confirm_start_time < self._confirm_init_delay:
            return
        if not self._running_open_npc:
            self.service.openMenu(npc_id)
            self._running_open_npc = True
            return
        if self._confirm_last_step_time > 0 and now - self._confirm_last_step_time < self._confirm_step_delay:
            return
        if now - self._confirm_start_time > self._confirm_timeout:
            self._confirm_npc_id = -1
            self._running_open_npc = False
            self.status = "NPC confirm timeout"
            return
        if self._confirm_step < len(self._confirm_menus):
            menu_text = self._confirm_menus[self._confirm_step]
            if not menu_text:
                self._confirm_step += 1
                self._confirm_last_step_time = now
                return
            normalized_target = _normalize(menu_text)
            for i, opt in enumerate(options):
                if _normalize(opt) == normalized_target:
                    self.service.confirmMenu(npc_id, i)
                    self._confirm_step += 1
                    self._confirm_last_step_time = now
                    if self._confirm_step >= len(self._confirm_menus) or not self._confirm_menus[self._confirm_step]:
                        self._confirm_npc_id = -1
                        self._running_open_npc = False
                        self._last_map_change_time = time.time()
                        self._is_processing_map_change = True
                    return
        self._confirm_npc_id = -1
        self._running_open_npc = False

    def _run(self):
        try:
            self._run_impl()
        except Exception as e:
            self.status = f"Lỗi: {e}"
            self.is_running_flag = False
            self.xmap_error = True

    def _run_impl(self):
        self.status = "Đang tìm đường..."
        path = find_path(
            self.state.map_id, self.target_map,
            power=self.state.my_char.cPower if self.state.my_char else 0,
            task_id=0,
            has_clan=False
        )
        if not path:
            err = get_error_message(
                self.target_map, self.state.map_id,
                power=self.state.my_char.cPower if self.state.my_char else 0,
                task_id=0
            )
            self.status = err
            self.xmap_error = True
            self.is_running_flag = False
            return

        self.path = path
        self.status = f"Tìm thấy đường: {' → '.join(str(m) for m in path)}"
        self.current_step = 0
        self._last_processed_map = self.state.map_id

        while not self._stop.is_set():
            now = time.time()
            me = self.state.my_char
            if me is None:
                time.sleep(0.1)
                continue

            # Reached destination?
            if self.state.map_id == self.target_map:
                self.status = f"Đã đến map {self.target_map}!"
                self.is_running_flag = False
                return

            # Handle death (like C# HandleDeathState)
            if hasattr(me, 'meDead') and me.meDead:
                if self.is_running_flag:
                    self.service.returnTownFromDead()
                time.sleep(1.0)
                continue

            # Handle NPC index action delay (like C# IsWaitingForNpcIndexDelay)
            if self._last_npc_index_time > 0:
                if now - self._last_npc_index_time < self._npc_index_delay:
                    time.sleep(0.1)
                    continue
                self._last_npc_index_time = 0.0
                self._in_npc_interaction = False

            # Handle name-based NPC confirmation
            if self._confirm_npc_id != -1:
                if not self._running_open_npc and now - self._confirm_start_time > self._confirm_init_delay:
                    self.service.openMenu(self._confirm_npc_id)
                    self._running_open_npc = True
                    self.status = "Đang mở menu NPC..."
                if now - self._confirm_start_time > self._confirm_timeout:
                    self._confirm_npc_id = -1
                    self._running_open_npc = False
                    self._in_npc_interaction = False
                time.sleep(0.1)
                continue

            # Handle transport teleport panel (CMD_MAP_TRASPORT)
            if self._panel_open and self.path:
                if not self._in_npc_interaction:
                    if now - self._last_panel_handle_time > 1.0:
                        if self._handle_teleport_panel():
                            self._panel_open = False
                            self._last_panel_handle_time = now
                        else:
                            self._panel_open = False
                            self.status += " (skip panel, thử waypoint)"
                time.sleep(0.1)
                continue

            # Handle map change processing/retry
            if self._is_processing_map_change:
                if now - self._last_map_change_time < self.map_delay:
                    time.sleep(0.1)
                    continue
                self._retry_count += 1
                if self._retry_count > 5:
                    self.status = "Quá nhiều lần thử, dừng xmap"
                    self._in_npc_interaction = False
                    self.is_running_flag = False
                    return
                
                self._is_processing_map_change = False
                self._in_npc_interaction = False
                self.status = f"Retry map change ({self._retry_count}/5)..."
                self._last_map_change_time = now

            if not self._should_update(now):
                time.sleep(0.05)
                continue

            if not self._handle_future_map():
                self._update_xmap()
            time.sleep(0.05)

        self.is_running_flag = False

    def _should_update(self, now: float) -> bool:
        if not self.is_running_flag:
            return False
        if now - self._last_update <= self._update_interval:
            return False
        self._last_update = now
        return True

    def _handle_future_map(self) -> bool:
        if not is_future_map(self.target_map):
            return False
        if self.state.my_char and hasattr(self.state.my_char, 'taskId') and self.state.my_char.taskId <= 24:
            self.status = "Cần hoàn thành nhiệm vụ để vào map tương lai"
            self.xmap_error = True
            self.is_running_flag = False
            return True
        npc_38_found = any(n.get('tempId') == 38 for n in self.state.npcs)
        if npc_38_found:
            return False
        if self.state.map_id == 27:
            self._set_next_target(28)
            return True
        elif self.state.map_id == 28:
            if hasattr(self, '_find_npc_29to27') and self._find_npc_29to27:
                self._set_next_target(27)
            else:
                self._set_next_target(29)
            return True
        elif self.state.map_id == 29:
            self._find_npc_29to27 = True
            self._set_next_target(28)
            return True
        return False

    def _set_next_target(self, next_map: int):
        self.path = [self.state.map_id, next_map]
        self.current_step = 0

    def _update_xmap(self):
        me = self.state.my_char
        if me is None:
            return

        current_map = self.state.map_id

        if current_map != self._last_processed_map:
            self._last_processed_map = current_map
            self._last_map_change_time = time.time()

        path = find_path(
            current_map, self.target_map,
            power=me.cPower if me.cPower else 0,
            task_id=0,
            has_clan=False
        )
        if path is None or len(path) < 2:
            now = time.time()
            if now - self._last_error_time >= self._error_cooldown:
                err = get_error_message(self.target_map, current_map,
                                        power=me.cPower if me.cPower else 0, task_id=0)
                self.status = err
                self._last_error_time = now
                self.xmap_error = True
            return

        if self._try_use_capsule(path):
            return

        next_map = path[1]
        self._goto_next_map(current_map, next_map)

    def _teleport_to_npc(self, npc_id: int) -> bool:
        for npc in self.state.npcs:
            if npc.get('tempId') == npc_id:
                nx, ny = npc['x'], npc['y']
                self._move_to(nx, ny - 3)
                return True
        return False

    def _get_item_in_bag(self, template_id: int) -> dict | None:
        for item in self.state.items_bag:
            if item and item['id'] == template_id:
                return item
        return None

    def _try_use_capsule(self, path: list[int]) -> bool:
        if not self.use_capsule:
            return False

        if not self._path_crosses_planets(path):
            return False

        if self._is_using_capsule:
            if self._is_opening_panel:
                return False
            now = time.time()
            if now - self._last_capsule_time < self._capsule_panel_delay:
                return True
            if self._capsule_map_names:
                for i in range(len(path) - 1, 0, -1):
                    target_name = get_map_name(path[i])
                    if not target_name:
                        continue
                    target_lower = target_name.lower()
                    for j, name in enumerate(self._capsule_map_names):
                        if target_lower in name.lower():
                            self._is_opening_panel = True
                            self.service.requestMapSelect(j)
                            self.status = f"Capsule: teleport {target_name}"
                            return True
                self._is_using_capsule = False
                self._is_opening_panel = True
                self.use_capsule = False
                self.status = "Capsule panel không có map trong path, tắt capsule"
                return False
            self._is_using_capsule = False
            self._is_opening_panel = True
            return False

        if len(path) < MIN_PATH_LENGTH_FOR_CAPSULE:
            return False

        capsule_item = self._get_item_in_bag(194) or self._get_item_in_bag(193)
        if capsule_item is None:
            return False

        self._is_using_capsule = True
        self._is_opening_panel = False
        self._last_capsule_time = time.time()
        self._capsule_map_names = list(self.state.map_transport_list)
        self.service.useItem(0, 1, -1, capsule_item['id'])
        return True

    def _path_crosses_planets(self, path: list[int]) -> bool:
        from xmap_data import TRAI_DAT, NAMEK, XAYDA, NAPPA, TUONG_LAI, COLD, THAP_LEO, MANH_VO_BT, KHI_GAS, MAP_KHAC
        planets = [
            set(TRAI_DAT), set(NAMEK), set(XAYDA), set(NAPPA),
            set(TUONG_LAI), set(COLD), set(THAP_LEO),
            set(MANH_VO_BT), set(KHI_GAS), set(MAP_KHAC),
        ]
        found_planets = set()
        for mid in path:
            for pi, pset in enumerate(planets):
                if mid in pset:
                    found_planets.add(pi)
                    break
        return len(found_planets) >= 2

    def _goto_next_map(self, current_map: int, next_map: int):
        self.status = f"Map {current_map} → {next_map}"
        link = get_next_link(current_map, next_map)
        if link is None:
            self.status = f"Không tìm thấy link {current_map} → {next_map}"
            self.xmap_error = True
            return
        self._execute_step(link)

    def _execute_step(self, link: MapLink):
        move_type = link.move_type
        if move_type == 0:
            self._handle_waypoint(link)
        elif move_type in (1, 2):
            self._handle_npc(link)
        elif move_type == 3:
            self._handle_item(link)
        elif move_type == 4:
            self._handle_walk(link)

    # ---------------------------------------------------------------------------
    # WAYPOINT MATCHING BY POPUP NAME (giống C# NextMap.GetWayPoint)
    # ---------------------------------------------------------------------------
    def _find_correct_waypoint(self, wp_pos: int, dest_map: int | None = None) -> dict | None:
        wps = self.state.waypoints
        if not wps:
            return None

        # Match by popup name (giống C#)
        if dest_map is not None:
            dest_name = get_map_name(dest_map)
            if dest_name:
                norm_dest = _normalize_data(dest_name)
                matched = [wp for wp in wps if _normalize_data(wp.get('popupName', '')) == norm_dest]
                if matched:
                    wps = matched
                    if len(matched) == 1:
                        return matched[0]

                # Partial match
                partial_matched = []
                for wp in wps:
                    popup = _normalize_data(wp.get('popupName', ''))
                    if popup and (norm_dest in popup or popup in norm_dest):
                        partial_matched.append(wp)
                if partial_matched:
                    wps = partial_matched
                    if len(partial_matched) == 1:
                        return partial_matched[0]

                # Word-by-word match
                dest_words = set()
                dest_name_raw = get_map_name(dest_map) if dest_map else ""
                if dest_name_raw:
                    for w in dest_name_raw.lower().split():
                        normalized = re.sub(r'\s+', '', w)
                        if normalized:
                            dest_words.add(normalized)
                word_matched = []
                for wp in wps:
                    popup_raw = wp.get('popupName', '')
                    if popup_raw:
                        popup_words = set()
                        for w in popup_raw.lower().split():
                            normalized = re.sub(r'\s+', '', w)
                            if normalized:
                                popup_words.add(normalized)
                        if dest_words & popup_words:
                            word_matched.append(wp)
                if word_matched:
                    wps = word_matched
                    if len(word_matched) == 1:
                        return word_matched[0]

        # Select by position
        if wp_pos == -1:
            selected = min(wps, key=lambda wp: wp['minX'])
        elif wp_pos == 1:
            selected = max(wps, key=lambda wp: wp['maxX'])
        else:
            mid_map = 1200
            selected = min(wps, key=lambda wp: abs((wp['minX'] + wp['maxX']) // 2 - mid_map))

        # Y-tiebreaker for stacked waypoints
        sel_cx = (selected['minX'] + selected['maxX']) // 2
        same_x_wps = [wp for wp in wps if 
            abs((wp['minX'] + wp['maxX']) // 2 - sel_cx) < 24]
        if len(same_x_wps) >= 2:
            me = self.state.my_char
            if me is not None:
                elevated = [wp for wp in same_x_wps if abs(wp['maxY'] - me.cy) > 50]
                if elevated:
                    return max(elevated, key=lambda wp: abs(wp['maxY'] - me.cy))
                return max(same_x_wps, key=lambda wp: abs(wp['maxY'] - me.cy))

        return selected

    def _calc_target_pos(self, wp: dict, wp_pos: int = 0) -> tuple[int, int]:
        """
        Calculate target position from a waypoint.
        Chọn vị trí TRONG waypoint bounds để server getWaypointPlayerIn() tìm thấy.
        Dùng center của waypoint thay vì edge offset để đảm bảo trong bounds.
        """
        min_x = wp['minX']
        max_x = wp['maxX']
        min_y = wp['minY']
        max_y = wp['maxY']

        # Luôn dùng center của waypoint - đảm bảo trong bounds [minX, maxX], [minY, maxY]
        tx = (min_x + max_x) // 2
        ty = (min_y + max_y) // 2

        return (tx, ty)

    def _handle_waypoint(self, link: MapLink):
        current_map = self.state.map_id

        if is_nrd_map(current_map):
            self._handle_nrd_waypoint(link)
            return

        dest_name = get_map_name(link.dest)
        self.status = f"Map {current_map} → {link.dest} "
        
        # Show available exit waypoints for debug
        waypoint_info = []
        for wp in self.state.waypoints:
            if not wp.get('isEnter'):
                waypoint_info.append(f"'{wp.get('popupName','')}'")
        if waypoint_info:
            self.status += f"exitWPs=[{','.join(waypoint_info)}]"

        wp = self._find_correct_waypoint(link.wp_pos, link.dest)
        if wp is None:
            self.status = f"Không tìm thấy waypoint cho '{dest_name}'"
            return

        target_x, target_y = self._calc_target_pos(wp, link.wp_pos)
        is_offline = wp.get('isOffline', False)
        popup_name = wp.get('popupName', '')
        
        # Debug: log waypoint bounds và target
        log.info("XMAP", f"Waypoint '{popup_name}' bounds=({wp['minX']},{wp['minY']})-({wp['maxX']},{wp['maxY']}) target=({target_x},{target_y}) isOffline={is_offline}")
        self.status += f" → '{popup_name}' ({target_x},{target_y}) offline={is_offline}"
        
        self._last_waypoint_is_offline = is_offline
        
        # Thực hiện waypoint transition: charMove + delay + request
        self._waypoint_transition(target_x, target_y, is_offline)

    def _handle_teleport_panel(self) -> bool:
        if not self._panel_map_names or not self.path:
            return True
        for i in range(len(self.path) - 1, 0, -1):
            mid = self.path[i]
            target_name = get_map_name(mid)
            if not target_name:
                continue
            target_lower = target_name.lower()
            for j, panel_name in enumerate(self._panel_map_names):
                if target_lower in panel_name.lower():
                    self.status = f"Teleport panel: chọn [{j}] {panel_name}"
                    self.service.requestMapSelect(j)
                    self._is_processing_map_change = True
                    self._last_map_change_time = time.time()
                    return True
        path_names = set()
        for mid in self.path:
            name = get_map_name(mid)
            if name:
                path_names.add(name.lower())
        for j, panel_name in enumerate(self._panel_map_names):
            panel_lower = panel_name.lower()
            for pmap_name in path_names:
                if panel_lower in pmap_name:
                    self.status = f"Panel: chọn [{j}] {panel_name}"
                    self.service.requestMapSelect(j)
                    self._is_processing_map_change = True
                    self._last_map_change_time = time.time()
                    return True
        self.status = f"Panel: ko match, chọn [0] để đóng"
        self.service.requestMapSelect(0)
        self._is_processing_map_change = True
        self._last_map_change_time = time.time()
        return True

    def _handle_nrd_waypoint(self, link: MapLink):
        if link.wp_pos == 2:
            npc_nrd = self._find_nrd_npc()
            if npc_nrd:
                self._move_to(npc_nrd['x'], npc_nrd['y'] - 3)
                self._send_map_request(False)
                return

        dest_name = get_map_name(link.dest)
        wp = self._find_correct_waypoint(link.wp_pos, link.dest)
        if wp:
            target_x, target_y = self._calc_target_pos(wp)
            popup_name = wp.get('popupName', '')
            self.status += f" → '{popup_name}' ({target_x},{target_y})"
            self._waypoint_transition(target_x, target_y, wp.get('isOffline', False))

    def _find_nrd_npc(self):
        for npc in self.state.npcs:
            if 30 <= npc.get('tempId', 0) <= 36:
                return npc
        return None

    # ---------------------------------------------------------------------------
    # NPC TRANSITIONS
    # ---------------------------------------------------------------------------
    def _handle_npc(self, link: MapLink):
        if link.npc_id < 0:
            return
        self.status += f" → NPC {link.npc_id}"
        self._teleport_to_npc(link.npc_id)
        time.sleep(0.2)

        self._in_npc_interaction = True

        if link.move_type == 2:
            self.service.openMenu(link.npc_id)
            time.sleep(0.1)
            for idx in link.menus:
                self.service.confirmMenu(link.npc_id, idx)
                time.sleep(0.1)
            self._last_npc_index_time = time.time()
            self._last_map_change_time = time.time()
            self._is_processing_map_change = True
        else:
            self._confirm_npc_id = link.npc_id
            self._confirm_menus = link.menus[:]
            self._confirm_menus_sub = link.menus_sub[:]
            self._confirm_menus_sub2 = link.menus_sub2[:]
            self._confirm_step = 0
            self._confirm_start_time = time.time()
            self._confirm_last_step_time = 0.0
            self._running_open_npc = False

    def _handle_item(self, link: MapLink):
        if link.item_id < 0:
            return
        self.status += f" → item {link.item_id}"
        bag_item = self._get_item_in_bag(link.item_id)
        if bag_item is None:
            self.status = f"Không có item {link.item_id} trong balo"
            return
        self.service.useItem(0, 1, -1, link.item_id)
        time.sleep(0.5)

    def _handle_walk(self, link: MapLink):
        self.status += f" → walk ({link.walk_x},{link.walk_y})"
        self.service.charMove(link.walk_x, link.walk_y, 1)
        time.sleep(0.5)
