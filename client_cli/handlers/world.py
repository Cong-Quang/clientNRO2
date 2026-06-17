import cmd as C
from logger import log
from network import Message
from state import GameState


class WorldHandler:
    def __init__(self, state: GameState):
        self.state = state

    def handle_map_info(self, msg: Message):
        self.state.map_id = msg.readUnsignedByte()
        self.state.zone_id = msg.readByte()
        log.info("MAP", f"mapId={self.state.map_id} zoneId={self.state.zone_id}")
        log.show_status(f"Map:{self.state.map_id} Z:{self.state.zone_id} Players:{len(self.state.players)}")

    def handle_map_change(self, msg: Message):
        log.info("MAP", "Changing map...")

    def handle_map_clear(self, msg: Message):
        log.info("MAP", "Map cleared")
        self.state.clear()

    def handle_finish_loadmap(self, msg: Message):
        log.info("MAP", "Finished loading map")

    def handle_finish_update(self, msg: Message):
        log.info("MAP", "Finished updating")

    def handle_update_body(self, msg: Message):
        action = msg.readByte()
        player_id = msg.readInt()
        log.info("BODY", f"Update action={action} player={player_id}")

    def handle_me_load_point(self, msg: Message):
        hp_goc = msg.readInt3Byte()
        mp_goc = msg.readInt3Byte()
        dam_goc = msg.readInt()
        hp_full = msg.readLong()
        mp_full = msg.readLong()
        hp_cur = msg.readLong()
        mp_cur = msg.readLong()
        speed = msg.readByte()
        hp_from_tn = msg.readByte()
        mp_from_tn = msg.readByte()
        dam_from_tn = msg.readByte()
        dam_full = msg.readLong()
        def_full = msg.readLong()
        crit_full = msg.readByte()
        tiem_nang = msg.readLong()
        exp_for_one = msg.readShort()
        def_goc = msg.readInt()
        crit_goc = msg.readByte()
        giam_st = msg.readByte()
        crit_dame_full = msg.readShort()
        log.info("STATS", f"HP={hp_cur}/{hp_full} MP={mp_cur}/{mp_full} SPD={speed}")
        log.show_status(f"Map:{self.state.map_id} HP:{hp_cur}/{hp_full} MP:{mp_cur}/{mp_full}")

    def handle_mob_hp(self, msg: Message):
        mob_id = msg.readByte()
        hp = msg.readLong()
        log.info("MOB", f"id={mob_id} HP={hp}")

    def handle_move_fast(self, msg: Message):
        player_id = msg.readInt()
        x = msg.readShort()
        y = msg.readShort()
        self.state.update_player_pos(player_id, x, y)
        log.debug("MOVE", f"player={player_id} fast to ({x},{y})")

    def handle_check_move(self, msg: Message):
        msg.readInt()
        log.debug("CHECK", "Move heartbeat")

    def handle_set_pos(self, msg: Message):
        x = msg.readShort()
        y = msg.readShort()
        log.info("POS", f"Set ({x},{y})")

    def handle_itemmap_mypick(self, msg: Message):
        item_id = msg.readShort()
        log.info("PICK", f"Picked item {item_id}")

    def handle_me_throw(self, msg: Message):
        index = msg.readByte()
        log.info("THROW", f"Threw index {index}")

    def handle_player_throw(self, msg: Message):
        player_id = msg.readInt()
        log.info("THROW", f"Player {player_id} threw")

    def handle_me_change_coin(self, msg: Message):
        coin = msg.readInt()
        log.info("COIN", f"Coin changed: {coin}")

    def handle_player_attack_n_p(self, msg: Message):
        log.debug("ATTACK", f"size={msg.available()}")

    def handle_sub_command(self, msg: Message):
        sub = msg.readByte()
        if sub == C.SUB_ME_LOAD_ALL:
            log.info("SUB", "Loading all data...")
        elif sub == C.SUB_ME_LOAD_CLASS:
            log.info("SUB", "Loading class...")
        elif sub == C.SUB_ME_LOAD_SKILL:
            log.info("SUB", "Loading skills...")
        elif sub == C.SUB_ME_LOAD_INFO:
            log.info("SUB", "Loading info...")
        elif sub == C.SUB_ME_LOAD_HP:
            log.info("SUB", "Updating HP...")
        elif sub == C.SUB_ME_LOAD_MP:
            log.info("SUB", "Updating MP...")
        elif sub == C.SUB_PLAYER_LOAD_ALL:
            player_id = msg.readInt()
            log.info("SUB", f"Player info: id={player_id}")
        elif sub == C.SUB_PLAYER_LOAD_HP:
            player_id = msg.readInt()
            hp = msg.readInt()
            msg.readByte()
            hpmax = msg.readInt()
            if player_id == self.state.my_char_id:
                log.info("HP", f"HP={hp}/{hpmax}")
                log.show_status(f"Map:{self.state.map_id} HP:{hp}/{hpmax}")
        elif sub == C.SUB_PLAYER_LOAD_LIVE:
            player_id = msg.readInt()
            hp = msg.readInt()
            mp = msg.readInt()
            x = msg.readShort()
            y = msg.readShort()
            if player_id == self.state.my_char_id:
                log.info("LIVE", f"Respawned at ({x},{y}) HP={hp} MP={mp}")
        elif sub == C.SUB_PLAYER_SPEED:
            player_id = msg.readInt()
            speed = msg.readByte()
            log.info("SPEED", f"player={player_id} speed={speed}")
        elif sub == C.SUB_PLAYER_LOAD_LEVEL:
            player_id = msg.readInt()
            level = msg.readByte()
            log.info("LEVEL", f"player={player_id} level={level}")
        elif sub == C.SUB_PLAYER_LOAD_VUKHI:
            player_id = msg.readInt()
            weapon_id = msg.readShort()
            log.info("WEAPON", f"player={player_id} weapon={weapon_id}")
        elif sub == C.SUB_PLAYER_LOAD_AO:
            player_id = msg.readInt()
            body_id = msg.readShort()
            log.info("BODY", f"player={player_id} body={body_id}")
        elif sub == C.SUB_PLAYER_LOAD_QUAN:
            player_id = msg.readInt()
            leg_id = msg.readShort()
            log.info("LEG", f"player={player_id} leg={leg_id}")
        elif sub == C.SUB_PLAYER_LOAD_BODY:
            player_id = msg.readInt()
            log.info("BODY", f"player={player_id}")
        elif sub == C.SUB_POTENTIAL_UP:
            type_pot = msg.readByte()
            point = msg.readShort()
            log.info("POTENTIAL", f"type={type_pot} point={point}")
        elif sub == C.SUB_SKILL_UP:
            skill_id = msg.readShort()
            point = msg.readByte()
            log.info("SKILL_UP", f"skill={skill_id} point={point}")
        elif sub == C.SUB_BAG_SORT:
            log.info("SORT", "Bag sorted")
        elif sub == C.SUB_BOX_SORT:
            log.info("SORT", "Box sorted")
        elif sub == C.SUB_BOX_COIN_OUT:
            coin = msg.readInt()
            log.info("BOX", f"Coin out: {coin}")
        elif sub == C.SUB_REQUEST_ITEM:
            ui_type = msg.readByte()
            log.info("ITEM", f"Request UI type={ui_type}")
        elif sub == C.SUB_ME_ADD_SKILL:
            log.info("SKILL", "Added new skill")
        else:
            log.debug("SUB", f"sub={sub} size={msg.available()}")

    def handle_player_add(self, msg: Message):
        if msg.available() < 4:
            log.debug("PLAYER", f"add too short: {msg.available()}b")
            return
        pid = msg.readInt()
        name = msg.readUTF() if msg.available() > 2 else ''
        head = msg.readShort() if msg.available() >= 2 else 0
        body = msg.readShort() if msg.available() >= 2 else 0
        leg = msg.readShort() if msg.available() >= 2 else 0
        gender = msg.readByte() if msg.available() >= 1 else 0
        is_fusion = msg.readByte() if msg.available() >= 1 else 0
        x = msg.readShort() if msg.available() >= 2 else 0
        y = msg.readShort() if msg.available() >= 2 else 0
        data = {
            'id': pid, 'name': name,
            'head': head, 'body': body, 'leg': leg,
            'gender': gender, 'x': x, 'y': y,
        }
        self.state.add_player(pid, data)
        if pid == self.state.my_char_id:
            log.info("ME", f"Spawned at ({x},{y})")
        else:
            log.info("PLAYER", f"{name} ({pid}) at ({x},{y})")
        log.show_status(f"Map:{self.state.map_id} Players:{len(self.state.players)}")

    def handle_player_remove(self, msg: Message):
        pid = msg.readInt()
        player = self.state.remove_player(pid)
        if player:
            log.info("PLAYER", f"{player['name']} left")
        log.show_status(f"Map:{self.state.map_id} Players:{len(self.state.players)}")

    def handle_player_move(self, msg: Message):
        pid = msg.readInt()
        x = msg.readShort()
        y = msg.readShort()
        self.state.update_player_pos(pid, x, y)

    def handle_player_die(self, msg: Message):
        pid = msg.readShort()
        msg.readByte()
        x = msg.readShort()
        y = msg.readShort()
        name = self.state.get_player_name(pid)
        log.info("DIE", f"{name} died at ({x},{y})")

    def handle_player_exp(self, msg: Message):
        pid = msg.readInt()
        exp = msg.readLong()
        name = self.state.get_player_name(pid)
        log.info("EXP", f"{name} exp={exp}")

    def handle_me_back(self, msg: Message):
        log.info("ME", "Returned to town")

    def handle_me_live(self, msg: Message):
        log.info("ME", "Revived")

    def handle_me_die(self, msg: Message):
        log.info("ME", "You died!")

    def handle_reset_point(self, msg: Message):
        x = msg.readShort()
        y = msg.readShort()
        log.info("RESET", f"Position reset to ({x},{y})")
