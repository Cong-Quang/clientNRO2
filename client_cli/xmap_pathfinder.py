import heapq
from collections import deque
from xmap_data import build_graph, MapLink, is_cold_map, is_future_map, is_clan_map, requires_clan, POWER_40B, POWER_60B

_graph = None
_all_distances: dict[int, dict[int, int]] = {}  # Precomputed all-pairs BFS distances (admissible heuristic)


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _precompute_distances():
    """Precompute BFS shortest path distances for all nodes.
    These unweighted distances serve as the admissible heuristic for A*:
    since min edge cost = 1, BFS distance <= actual weighted cost.
    """
    global _all_distances
    g = get_graph()
    _all_distances = {}
    for start in g:
        dist = {start: 0}
        q = deque([start])
        while q:
            cur = q.popleft()
            for link in g[cur]:
                nxt = link.dest
                if nxt not in dist and nxt in g:
                    dist[nxt] = dist[cur] + 1
                    q.append(nxt)
        _all_distances[start] = dist


def _heuristic(cur: int, target: int) -> int:
    """Admissible heuristic for A*: precomputed BFS distance.
    Guaranteed <= actual weighted cost (since waypoint cost=1 is minimum possible).
    """
    if not _all_distances:
        _precompute_distances()
    return _all_distances.get(cur, {}).get(target, 0)


# Weighted costs per move type
# Ưu tiên: waypoint(0) < walk(4) < npc_index(2) < npc_menu(1) < item(3)
MOVE_COST = {
    0: 1,   # waypoint - cheapest, most reliable
    4: 2,   # walk - cần di chuyển nhẹ
    2: 3,   # npc_index - nhanh, ít lỗi
    1: 5,   # npc_menu - chậm, dễ fail text matching
    3: 10,  # item - tốn item, expensive
}


def _move_cost(move_type: int) -> int:
    return MOVE_COST.get(move_type, 5)


def find_path(current_map: int, target_map: int, power: int = 0, task_id: int = 0, has_clan: bool = False) -> list[int] | None:
    g = get_graph()
    if current_map not in g or target_map not in g:
        return None
    if current_map == target_map:
        return [current_map]

    # Precompute heuristic if first call
    if not _all_distances:
        _precompute_distances()

    # A* priority queue: (f_score, g_score, tiebreaker, node)
    # tiebreaker ensures stable ordering for equal f-scores
    tiebreaker = 0
    start_h = _heuristic(current_map, target_map)
    pq = [(start_h, 0, tiebreaker, current_map)]
    g_cost = {current_map: 0}
    parent: dict[int, tuple[int, MapLink] | None] = {current_map: None}

    while pq:
        _, cost_so_far, _, cur = heapq.heappop(pq)

        if cur == target_map:
            return _reconstruct(parent, target_map)

        # Skip outdated entries (found better path already)
        if cost_so_far > g_cost.get(cur, float('inf')):
            continue

        for link in g.get(cur, []):
            nxt = link.dest
            if nxt not in g:
                continue

            # --- Constraint checks (same as BFS) ---
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

            edge_cost = _move_cost(link.move_type)
            new_cost = cost_so_far + edge_cost

            if new_cost < g_cost.get(nxt, float('inf')):
                g_cost[nxt] = new_cost
                tiebreaker += 1
                f_score = new_cost + _heuristic(nxt, target_map)
                parent[nxt] = (cur, link)
                heapq.heappush(pq, (f_score, new_cost, tiebreaker, nxt))

    return None


def find_path_bfs(current_map: int, target_map: int, power: int = 0, task_id: int = 0, has_clan: bool = False) -> list[int] | None:
    """Original BFS implementation kept as fallback reference."""
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


def find_path_with_cost(current_map: int, target_map: int, power: int = 0, task_id: int = 0, has_clan: bool = False) -> tuple[list[int] | None, int]:
    """Like find_path but also returns the total weighted cost."""
    g = get_graph()
    if current_map not in g or target_map not in g:
        return None, 0
    if current_map == target_map:
        return [current_map], 0

    if not _all_distances:
        _precompute_distances()

    tiebreaker = 0
    start_h = _heuristic(current_map, target_map)
    pq = [(start_h, 0, tiebreaker, current_map)]
    g_cost = {current_map: 0}
    parent: dict[int, tuple[int, MapLink] | None] = {current_map: None}

    while pq:
        _, cost_so_far, _, cur = heapq.heappop(pq)

        if cur == target_map:
            return _reconstruct(parent, target_map), cost_so_far

        if cost_so_far > g_cost.get(cur, float('inf')):
            continue

        for link in g.get(cur, []):
            nxt = link.dest
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

            edge_cost = _move_cost(link.move_type)
            new_cost = cost_so_far + edge_cost

            if new_cost < g_cost.get(nxt, float('inf')):
                g_cost[nxt] = new_cost
                tiebreaker += 1
                f_score = new_cost + _heuristic(nxt, target_map)
                parent[nxt] = (cur, link)
                heapq.heappush(pq, (f_score, new_cost, tiebreaker, nxt))

    return None, 0


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
    if is_cold_map(target_map) and task_id <= 30:
        return "Cần hoàn thành nhiệm vụ (task > 30) để vào hành tinh Cold."
    return f"Không thể tìm thấy đường đi từ map {current_map} đến map {target_map}."
