import time
from logger import log


class AutoPick:
    """
    AutoPick - Tự động nhặt đồ trên map dựa trên Mod.community/AutoPick.cs

    Features:
    - Auto nhặt đồ của mình / tất cả
    - Nhặt theo danh sách whitelist
    - Khoảng cách nhặt cấu hình được
    - Cooldown 550ms giữa các lần nhặt
    - Hỗ trợ map NRD (85-91, item 372-378)
    - Teleport đến item (gửi charMove)
    """

    PICK_COOLDOWN = 0.55  # 550ms (giống C#)
    DEFAULT_MAX_DISTANCE = 50

    def __init__(self, state, service):
        self.state = state
        self.service = service

        # Settings
        self.enabled = False
        self.pick_all = False          # Nhặt tất cả (kể cả đồ người khác)
        self.pick_by_list = False      # Nhặt theo danh sách
        self.pick_list = set()         # Danh sách item template IDs
        self.max_distance = self.DEFAULT_MAX_DISTANCE
        self.teleport_to_item = False  # Dịch chuyển đến item

        # Internal
        self._last_pick_time = 0.0

    def update(self):
        """Main update loop - gọi từ auto updater thread mỗi 500ms"""
        if not self.enabled:
            return

        me = self.state.my_char
        if not me:
            return
        items = getattr(self.state, 'items_map', [])
        if not items:
            return

        now = time.time()
        if now - self._last_pick_time < self.PICK_COOLDOWN:
            return

        me_x = getattr(me, 'cx', 0)
        me_y = getattr(me, 'cy', 0)

        # Tìm item gần nhất trong phạm vi
        best_item = None
        best_dist_sq = float('inf')

        for item in items:
            dx = abs(me_x - item['x'])
            dy = abs(me_y - item['y'])
            if dx > self.max_distance or dy > self.max_distance:
                continue
            if not self._can_pick(item):
                continue
            dist_sq = dx * dx + dy * dy
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_item = item

        if best_item is None:
            return

        # Teleport đến item nếu bật
        if self.teleport_to_item:
            self._teleport_to(best_item['x'], best_item['y'])

        # Nhặt item
        self.service.pickItem(best_item['itemMapID'])
        self._last_pick_time = now
        log.info("PICK", f"Auto nhat item id={best_item['templateId']} tai ({best_item['x']},{best_item['y']})")

    def _can_pick(self, item) -> bool:
        """Kiểm tra xem có được nhặt item này không (giống C# isPickIt)"""
        if item is None:
            return False

        # Kiểm tra map NRD (85-91): chỉ nhặt item 372-378
        map_id = self.state.map_id
        if 85 <= map_id <= 91:
            return 372 <= item['templateId'] <= 378

        # Kiểm tra playerId (chỉ nhặt đồ của mình hoặc đồ rơi từ quái)
        is_own = item['playerId'] == -1
        if self.state.my_char and hasattr(self.state.my_char, 'charID'):
            is_own = is_own or item['playerId'] == self.state.my_char.charID

        if self.pick_all:
            return True

        if not is_own:
            return False

        if self.pick_by_list:
            return item['templateId'] in self.pick_list

        return is_own

    def _teleport_to(self, x: int, y: int):
        """Dịch chuyển đến vị trí item (giống C# TeleportTo)"""
        me = self.state.my_char
        if not me:
            return
        me.cx = x
        me.cy = y
        self.service.charMove(x, y, 1)
        me.cy = y + 1
        self.service.charMove(x, y + 1, 1)
        me.cy = y
        self.service.charMove(x, y, 1)

    def toggle(self) -> bool:
        """Bật/tắt AutoPick (C#: Auto Nhặt [STATUS: ON/OFF])"""
        self.enabled = not self.enabled
        self.pick_by_list = False
        self._log_pick(f"Auto Nhat: {'BAT' if self.enabled else 'TAT'}")
        return self.enabled

    def toggle_pick_all(self) -> bool:
        """Bật/tắt nhặt tất cả (C#: Nhặt Tất Cả [STATUS: ON/OFF])"""
        self.pick_all = not self.pick_all
        self._log_pick(f"Nhat Tat Ca: {'BAT' if self.pick_all else 'TAT'}")
        return self.pick_all

    def toggle_pick_by_list(self) -> bool:
        """Bật/tắt nhặt theo danh sách (C#: Nhặt Theo Danh Sách [STATUS: ON/OFF])"""
        if not self.enabled:
            self.enabled = True
        self.pick_by_list = not self.pick_by_list
        self._log_pick(f"Nhat Theo Danh Sach: {'BAT' if self.pick_by_list else 'TAT'}")
        return self.pick_by_list

    def toggle_teleport(self) -> bool:
        """Bật/tắt teleport đến item (C#: Dịch Đến Item [STATUS: ON/OFF])"""
        self.teleport_to_item = not self.teleport_to_item
        self._log_pick(f"Dich Den Item: {'BAT' if self.teleport_to_item else 'TAT'}")
        return self.teleport_to_item

    def set_distance(self, dist: int):
        """Cài đặt khoảng cách nhặt (C#: Khoảng Cách Nhặt: X)"""
        self.max_distance = max(10, min(dist, 500))
        self._log_pick(f"Khoang cach nhat: {self.max_distance}px")
        return self.max_distance

    def add_to_list(self, item_id: int):
        """Thêm item ID vào danh sách nhặt (C#: Đã Thêm Item X)"""
        self.pick_list.add(item_id)
        from items_data import item_name
        name = item_name(item_id)
        self._log_pick(f"Da them: {name} (ID={item_id})")
        return item_id

    def remove_from_list(self, item_id: int):
        """Xóa item ID khỏi danh sách nhặt (C#: Đã xóa...)"""
        self.pick_list.discard(item_id)
        self._log_pick(f"Da xoa ID={item_id} khoi danh sach")

    def clear_list(self):
        """Xóa toàn bộ danh sách nhặt (C#: Đã Clear Danh Sách Nhặt)"""
        self.pick_list.clear()
        self._log_pick("Da xoa toan bo danh sach nhat!")

    def _log_pick(self, msg: str):
        """Phat notification giong C# GameScr.info1.addInfo()"""
        log.info("PICK", msg)

    def list_items(self):
        """Hiển thị danh sách item nhặt"""
        if not self.pick_list:
            log.raw("[Pick] Danh sach nhat trong!")
            return
        from items_data import item_name
        ids = sorted(self.pick_list)
        log.raw(f"[Pick] Danh sach {len(ids)} item:")
        for i, tid in enumerate(ids):
            name = item_name(tid)
            log.raw(f"  [{i}] {tid}: {name}")
