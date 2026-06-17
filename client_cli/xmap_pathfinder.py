from collections import deque
from xmap_data import build_graph, MapLink, is_cold_map, is_future_map, is_clan_map, requires_clan, POWER_40B, POWER_60B

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def find_path(current_map: int, target_map: int, power: int = 0, task_id: int = 0, has_clan: bool = False) -> list[int] | None:
    g = get_graph()
    if current_map not in g or target_map not in g:
        return None
    if current_map == target_map:
        return [current_map]

    visited = {current_map}
    parent = {current_map: None}
    q = deque([current_map])

    while q:
        cur = q.popleft()
        for link in g.get(cur, []):
            nxt = link.dest
            if nxt in visited:
                continue
            if nxt not in g:
                continue
            if is_future_map(nxt) and task_id <= 24:
                continue
            if requires_clan(nxt) and not has_clan:
                continue
            if power < _required_power(nxt):
                continue
            if cur == 19 and nxt == 109 and task_id <= 30:
                continue
            if is_cold_map(nxt) and task_id <= 30:
                continue
            visited.add(nxt)
            parent[nxt] = (cur, link)
            if nxt == target_map:
                return _reconstruct(parent, target_map)
            q.append(nxt)
    return None


def _required_power(mid: int) -> int:
    if mid in {155, 166}:
        return POWER_60B
    if mid in {156, 157, 158, 159}:
        return POWER_40B
    return 0


def _reconstruct(parent: dict, target: int) -> list[int]:
    path = []
    cur = target
    while cur is not None:
        entry = parent.get(cur)
        if entry is None:
            path.append(cur)
            break
        path.append(cur)
        cur = entry[0]
    path.reverse()
    return path


def get_next_link(current_map: int, next_map: int) -> MapLink | None:
    g = get_graph()
    best = None
    for link in g.get(current_map, []):
        if link.dest == next_map:
            if link.move_type != 0:
                return link
            if best is None:
                best = link
    return best


def get_error_message(target_map: int, current_map: int, power: int = 0, task_id: int = 0, has_clan: bool = False) -> str:
    if _required_power(target_map) > 0 and power < _required_power(target_map):
        need = _required_power(target_map)
        return f"Yêu cầu sức mạnh tối thiểu: {need:N0}."
    if is_future_map(target_map) and task_id <= 24:
        return "Hãy hoàn thành nhiệm vụ để vào map này."
    if requires_clan(target_map) and not has_clan:
        return "Cần có pt để vào map này."
    if target_map == 160:
        return "Không có Nhẫn thời không!"
    return f"Không thể tìm thấy đường đi từ map {current_map} đến map {target_map}."
