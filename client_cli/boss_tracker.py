"""
BossTracker - Theo dõi boss xuất hiện (tên, map, zone, tọa độ, thời gian)
Chạy passive - không cần bật auto_boss

Ghi lại mỗi lần phát hiện boss trong map, có thể xem qua /bosslog
"""
import time
from logger import log
from auto_boss import is_boss

# Khoảng thời gian tối thiểu giữa 2 lần ghi cùng 1 boss trên cùng map/zone (giây)
DEDUP_INTERVAL = 120.0  # 2 phút
MAX_SIGHTINGS = 50      # Giữ tối đa 50 bản ghi


class BossTracker:
    """
    BossTracker - Ghi lại boss xuất hiện để xem sau.
    
    Luôn chạy passive, không cần bật auto_boss.
    Mỗi lần phát hiện boss trong map sẽ ghi log với timestamp.
    Dùng /bosslog de xem lich su.
    """

    SCAN_INTERVAL = 5.0  # Quet map moi 5 giay

    def __init__(self, state, service):
        self.state = state
        self.service = service

        # Danh sach boss da phat hien: list of dicts
        # {name, map_id, zone_id, x, y, time, map_name}
        self.sightings: list[dict] = []

        # Set de tranh trung: (name_lo, map_id, zone_id) -> last_time
        self._seen: dict[tuple, float] = {}

        self._last_scan = 0.0
        self.enabled = True  # Luon chay

    def update(self):
        """Goi tu auto updater thread moi 500ms"""
        if not self.enabled:
            return
        if self.state.my_char is None:
            return

        now = time.time()
        if now - self._last_scan < self.SCAN_INTERVAL:
            return
        self._last_scan = now

        self._scan(now)

    def _scan(self, now: float):
        """Quet tat ca player trong map, ghi lai boss phat hien"""
        me = self.state.my_char
        if not me:
            return
        me_id = getattr(me, 'charID', -1)
        map_id = self.state.map_id
        zone_id = self.state.zone_id
        map_name = getattr(self.state, 'map_name', '') or str(map_id)

        for pid, p in self.state.players.items():
            if pid == me_id:
                continue
            if not is_boss(p):
                continue
            name = p.get('name', '?')
            hp = p.get('hp', 0)
            if hp <= 0:
                continue
            x = p.get('x', 0)
            y = p.get('y', 0)

            # Kiem tra trung: cung ten, cung map, cung zone
            key = (name.lower(), map_id, zone_id)
            last_time = self._seen.get(key, 0.0)
            if now - last_time < DEDUP_INTERVAL:
                continue

            # Ghi nhan boss moi
            sighting = {
                'name': name,
                'map_id': map_id,
                'zone_id': zone_id,
                'map_name': map_name,
                'x': x,
                'y': y,
                'time': now,
                'hp': hp,
            }
            self.sightings.append(sighting)
            self._seen[key] = now

            # Gioi han so luong
            if len(self.sightings) > MAX_SIGHTINGS:
                self.sightings = self.sightings[-MAX_SIGHTINGS:]

            log.info("BOSS", f"[TRACKER] Phat hien boss: {name} o Map {map_name}({map_id}) Khu {zone_id} tai ({x},{y})")

    def get_sightings(self) -> list[dict]:
        """Tra ve danh sach boss sightings (moi nhat truoc)"""
        return list(reversed(self.sightings))

    def get_bosses_in_map(self, map_id: int = None) -> list[str]:
        """Lay danh sach ten boss dang co trong map (hoac map hien tai)"""
        if map_id is None:
            map_id = self.state.map_id
        bosses = set()
        for pid, p in self.state.players.items():
            if is_boss(p) and p.get('hp', 0) > 0:
                name = p.get('name', '')
                if name:
                    bosses.add(name)
        return sorted(bosses)

    def get_recent_bosses(self, minutes: int = 30) -> list[dict]:
        """Lay danh sach boss xuat hien trong X phut gan day"""
        cutoff = time.time() - minutes * 60
        return [s for s in reversed(self.sightings) if s['time'] >= cutoff]

    def has_boss_in_map(self) -> bool:
        """Kiem tra co boss nao trong map hien tai khong (loai tru ban than)"""
        me = self.state.my_char
        me_id = getattr(me, 'charID', -1) if me else -1
        for pid, p in self.state.players.items():
            if pid == me_id:
                continue
            if is_boss(p) and p.get('hp', 0) > 0:
                return True
        return False

    def list_sightings(self, minutes: int = 60):
        """Hien thi danh sach boss sightings trong X phut"""
        cutoff = time.time() - minutes * 60
        recent = [s for s in reversed(self.sightings) if s['time'] >= cutoff]

        if not recent:
            log.raw(f"[Tracker] Khong co boss nao xuat hien trong {minutes} phut qua")
            return

        log.raw(f"[Tracker] Boss xuat hien trong {minutes} phut qua ({len(recent)} lan):")
        for s in recent:
            elapsed = time.time() - s['time']
            if elapsed < 60:
                time_str = f"{int(elapsed)} giay truoc"
            elif elapsed < 3600:
                time_str = f"{int(elapsed // 60)} phut {int(elapsed % 60)} giay truoc"
            else:
                time_str = f"{int(elapsed // 3600)}h{int((elapsed % 3600) // 60)}p truoc"
            hp_str = f" HP={s['hp']}" if s['hp'] else ""
            log.raw(f"  {s['name']}{hp_str} - {time_str} - Map {s['map_name']}({s['map_id']}) Khu {s['zone_id']} ({s['x']},{s['y']})")

    def list_bosses_now(self):
        """Hien thi boss dang co trong map hien tai"""
        bosses = self.get_bosses_in_map()
        if not bosses:
            log.raw("[Tracker] Khong co boss nao trong map hien tai")
            return
        log.raw(f"[Tracker] Boss trong map ({len(bosses)}):")
        for name in bosses:
            log.raw(f"  {name}")
