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
        self.planet_id = 0
        self.tile_id = 0
        self.bg_id = 0
        self.map_type = 0
        self.map_name = ''
        self.my_char = None
        self.current_npc_id = 0
        self.current_menu_index = 0
        self.items_bag: list[dict | None] = []
        self.items_body: list[dict | None] = []
        self.items_box: list[dict | None] = []
        self.pet: dict | None = None
        self.map_transport_list: list[str] = []
        self.waypoints: list[dict] = []
        self.xmap_runner = None

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
        self.waypoints = []

    def set_map(self, map_id: int, zone_id: int):
        self.map_id = map_id
        self.zone_id = zone_id

    def set_map(self, map_id: int, zone_id: int):
        self.map_id = map_id
        self.zone_id = zone_id
