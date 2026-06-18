"""
AutoVutDo - Tự động vứt đồ rác theo danh sách ID
Dựa trên ModNroPc/Mod.CuongLe/AutoVutDoCL.cs
"""
import time
from logger import log
from items_data import item_name


class AutoVutDo:
    def __init__(self, state, service):
        self.state = state
        self.service = service
        self.enabled = False
        self.trash_ids: list[int] = []  # danh sách ID item cần vứt
        self._trash_index = 0
        self._last_trash_time = 0
        self._trash_interval = 500  # ms giữa các lần vứt

    def toggle(self):
        self.enabled = not self.enabled
        status = "BẬT" if self.enabled else "TẮT"
        log.raw(f"[VutDo] Auto vứt đồ: {status}")
        if self.enabled and not self.trash_ids:
            log.raw("[VutDo] Danh sách rỗng! Thêm ID bằng /vutdo add <id>")
        return self.enabled

    def add_ids(self, ids: list[int]):
        added = []
        existed = []
        for item_id in ids:
            if item_id in self.trash_ids:
                existed.append(item_id)
            else:
                self.trash_ids.append(item_id)
                added.append(item_id)
        if added:
            names = ", ".join(f"{item_name(i)}(ID={i})" for i in added)
            log.raw(f"[VutDo] Đã thêm: {names}")
        if existed:
            names = ", ".join(f"{item_name(i)}(ID={i})" for i in existed)
            log.raw(f"[VutDo] Đã tồn tại: {names}")

    def remove_ids(self, ids: list[int]):
        removed = []
        not_found = []
        for item_id in ids:
            if item_id in self.trash_ids:
                self.trash_ids.remove(item_id)
                removed.append(item_id)
            else:
                not_found.append(item_id)
        if removed:
            names = ", ".join(f"{item_name(i)}(ID={i})" for i in removed)
            log.raw(f"[VutDo] Đã xóa: {names}")
        if not_found:
            names = ", ".join(f"{item_name(i)}(ID={i})" for i in not_found)
            log.raw(f"[VutDo] Không tìm thấy: {names}")

    def clear(self):
        self.trash_ids.clear()
        self._trash_index = 0
        log.raw("[VutDo] Đã xóa toàn bộ danh sách")

    def list_items(self):
        if not self.trash_ids:
            log.raw("[VutDo] Danh sách rỗng")
            return
        log.raw(f"[VutDo] Danh sách vật phẩm ({len(self.trash_ids)} cái):")
        for item_id in self.trash_ids:
            name = item_name(item_id)
            log.raw(f"  {item_id}: {name}")

    def update(self):
        """Gọi mỗi tick (~500ms) từ auto update thread."""
        if not self.enabled or not self.trash_ids:
            return

        now_ms = int(time.time() * 1000)
        if now_ms - self._last_trash_time < self._trash_interval:
            return

        bag = getattr(self.state, 'items_bag', []) or []
        if not bag:
            return

        target_id = self.trash_ids[self._trash_index]

        # Tìm item trong bag
        for i, item in enumerate(bag):
            if item and item.get('id') == target_id:
                # type=2 (throw), where=1 (bag), index=i
                self.service.useItem(2, 1, i)
                self._last_trash_time = now_ms
                return

        # Chuyển sang ID tiếp theo
        self._trash_index += 1
        if self._trash_index >= len(self.trash_ids):
            self._trash_index = 0
            self._last_trash_time = now_ms + 1500  # delay sau 1 vòng
