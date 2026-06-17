import re
import threading
import time
from state import GameState
from service import Service
from xmap_pathfinder import find_path, get_next_link, get_error_message
from xmap_data import MapLink, is_nrd_map, is_future_map, CAPSULE_ITEM_IDS, MIN_PATH_LENGTH_FOR_CAPSULE


def _normalize(s: str) -> str:
    return re.sub(r'\s+', '', s.lower().strip())


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

        self._npc_wait_id = -1
        self._npc_wait_menus: list[int] = []
        self._npc_wait_start = 0.0
        self._npc_wait_timeout = 5.0

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

        self._is_using_capsule = False
        self._is_opening_panel = False
        self._capsule_panel_delay = 0.5
        self._last_capsule_time = 0.0
        self._capsule_map_names: list[str] = []

        self._last_chicken_time = 0.0
        self._chicken_pickup_delay = 0.6
        self._retry_count = 0
        self._max_retries = 5

    def start(self, target_map: int):
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
        self._npc_wait_id = -1
        self._confirm_npc_id = -1
        self._retry_count = 0
        self._stop.clear()
        self.is_running_flag = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.is_running_flag = False
        self.status = ""
        self._npc_wait_id = -1
        self._confirm_npc_id = -1
        self._is_using_capsule = False
        self._is_opening_panel = False

    def is_running(self) -> bool:
        return self.is_running_flag

    def on_map_changed(self, map_id: int):
        if not self.is_running_flag:
            return
        self._last_processed_map = map_id
        self._last_map_change_time = time.time()
        self._is_processing_map_change = False
        self._npc_wait_id = -1
        self._confirm_npc_id = -1
        self._retry_count = 0

    def on_capsule_map_list(self, map_names: list[str]):
        if self._is_using_capsule and not self._is_opening_panel:
            self._capsule_map_names = map_names

    def on_npc_dialog(self, npc_id: int, options: list[str]):
        if self._npc_wait_id == npc_id:
            now = time.time()
            for idx in self._npc_wait_menus:
                if 0 <= idx < len(options):
                    self.service.confirmMenu(npc_id, idx)
                    time.sleep(0.3)
            self._npc_wait_id = -1
            self._last_map_change_time = time.time()
            self._is_processing_map_change = True
            return

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

            if self.state.map_id == self.target_map:
                self.status = f"Đã đến map {self.target_map}!"
                self.is_running_flag = False
                return

            if self._npc_wait_id != -1:
                if now - self._npc_wait_start > self._npc_wait_timeout:
                    self._npc_wait_id = -1
                    self.status = "NPC timeout"
                time.sleep(0.1)
                continue

            if self._confirm_npc_id != -1:
                time.sleep(0.1)
                continue

            if self._is_processing_map_change:
                if now - self._last_map_change_time < self.map_delay:
                    time.sleep(0.1)
                    continue
                self._retry_count += 1
                if self._retry_count > self._max_retries:
                    self.status = "Quá nhiều lần thử, dừng xmap"
                    self.is_running_flag = False
                    return
                self._is_processing_map_change = False
                self.status = f"Retry map change ({self._retry_count}/{self._max_retries})..."
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
            self._is_processing_map_change = False

        if self._is_processing_map_change:
            now = time.time()
            if now - self._last_map_change_time < self.map_delay:
                return
            self._is_processing_map_change = False
            self.status = "Retry map change..."
            self._last_map_change_time = now

        path = find_path(
            current_map, self.target_map,
            power=me.cPower if me.cPower else 0,
            task_id=0,
            has_clan=False
        )
        if path is None or len(path) < 2:
            now = time.time()
            if now - self._last_error_time >= self._error_cooldown:
                err = get_error_message(self.target_map, current_map, power=me.cPower if me.cPower else 0, task_id=0)
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
                self.service.charMove(nx, ny - 3, 1)
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
        if self._is_using_capsule:
            if self._is_opening_panel:
                return False
            now = time.time()
            if now - self._last_capsule_time < self._capsule_panel_delay:
                return True
            if self._capsule_map_names:
                for i in range(len(path) - 1, 0, -1):
                    target_name = str(path[i])
                    for j, name in enumerate(self._capsule_map_names):
                        if target_name in name:
                            self._is_opening_panel = True
                            self.service.requestMapSelect(j)
                            return True
                self._is_opening_panel = True
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

    def _handle_waypoint(self, link: MapLink):
        current_map = self.state.map_id

        if is_nrd_map(current_map):
            self._handle_nrd_waypoint(link)
            return

        x, y = self._calc_waypoint_pos(link.wp_pos)
        if x == -1:
            self.status = f"Không tìm thấy waypoint trên map {current_map}"
            return

        self.service.charMove(x, y, 1)
        time.sleep(0.3)
        self.service.requestChangeMap()
        self._last_map_change_time = time.time()
        self._is_processing_map_change = True

    def _calc_waypoint_pos(self, wp_pos: int) -> tuple[int, int]:
        wps = [wp for wp in self.state.waypoints if wp.get('isEnter')]
        if not wps:
            wps = self.state.waypoints
        if wp_pos == -1:
            left = [wp for wp in wps if wp['maxX'] < 60]
            if left:
                wp = left[0]
                return (wp['minX'] + 15, wp['maxY'])
            return (60, 360)
        elif wp_pos == 1:
            right = [wp for wp in wps if wp['minX'] > 2320]
            if right:
                wp = right[0]
                return (wp['maxX'] - 15, wp['maxY'])
            return (2350, 360)
        else:
            center = [wp for wp in wps if wp['minX'] >= 60 and wp['maxX'] <= 2320]
            if center:
                wp = center[0]
                return ((wp['minX'] + wp['maxX']) // 2, wp['maxY'])
            return (1200, 360)

    def _handle_nrd_waypoint(self, link: MapLink):
        if link.wp_pos == 2:
            npc_nrd = self._find_nrd_npc()
            if npc_nrd:
                self.service.charMove(npc_nrd['x'], npc_nrd['y'] - 3, 1)
                time.sleep(0.3)
                self.service.requestChangeMap()
                self._last_map_change_time = time.time()
                self._is_processing_map_change = True
                return
        x, y = self._calc_waypoint_pos(link.wp_pos)
        self.service.charMove(x, y, 1)
        time.sleep(0.3)
        self.service.requestChangeMap()
        self._last_map_change_time = time.time()
        self._is_processing_map_change = True

    def _find_nrd_npc(self):
        for npc in self.state.npcs:
            if 30 <= npc.get('tempId', 0) <= 36:
                return npc
        return None

    def _handle_npc(self, link: MapLink):
        if link.npc_id < 0:
            return
        self.status += f" → NPC {link.npc_id}"
        self._teleport_to_npc(link.npc_id)
        time.sleep(0.2)
        self.service.openMenu(link.npc_id)
        if link.move_type == 2:
            self._npc_wait_id = link.npc_id
            self._npc_wait_menus = link.menus[:]
            self._npc_wait_start = time.time()
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
