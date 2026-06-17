class GameState:
    def __init__(self):
        self.logged_in = False
        self.in_game = False
        self.my_char_id = -1
        self.players: dict[int, dict] = {}
        self.mobs: list[dict] = []
        self.npcs: list[dict] = []
        self.map_id = -1
        self.zone_id = -1
        self.my_char = None

    def add_player(self, pid: int, data: dict):
        self.players[pid] = data

    def remove_player(self, pid: int) -> dict | None:
        return self.players.pop(pid, None)

    def get_player_name(self, pid: int) -> str:
        return self.players.get(pid, {}).get('name', str(pid))

    def update_player_pos(self, pid: int, x: int, y: int):
        if pid in self.players:
            self.players[pid]['x'] = x
            self.players[pid]['y'] = y

    def clear(self):
        self.players.clear()
        self.mobs.clear()

    def set_map(self, map_id: int, zone_id: int):
        self.map_id = map_id
        self.zone_id = zone_id
