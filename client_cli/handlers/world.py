import cmd as C
from logger import log
from network import Message
from state import GameState
from Char import Char


class WorldHandler:
    def __init__(self, state: GameState, service=None):
        self.state = state
        self.service = service

    def handle_map_info(self, msg: Message):
        self.state.map_id = msg.readUnsignedByte()
        self.state.zone_id = msg.readByte()
        log.info("MAP", f"mapId={self.state.map_id} zoneId={self.state.zone_id}")
        log.show_status(f"Map:{self.state.map_id} Z:{self.state.zone_id} Players:{len(self.state.players)}")
        if self.service:
            self.service.finishLoadMap()
            self.service.finishUpdate()

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
        try:
            hpg = msg.readInt()
            mpg = msg.readInt()
            dameg = msg.readInt()
            hpMax = msg.readInt()
            mpMax = msg.readInt()
            hp = msg.readInt()
            mp = msg.readInt()
            speed = msg.readByte()
            msg.readByte()
            msg.readByte()
            msg.readByte()
            dame = msg.readInt()
            def_ = msg.readInt()
            crit = msg.readByte()
            tiemNang = msg.readLong()
            msg.readShort()
            defg = msg.readShort()
            critg = msg.readByte()
        except Exception as e:
            log.error("STATS", f"Parse error: {e} raw={msg.getData().hex() if msg.getData() else 'empty'}")
            return
        if self.state.my_char is None:
            self.state.my_char = Char()
        c = self.state.my_char
        c.cHPGoc = hpg
        c.cMPGoc = mpg
        c.cDamGoc = dameg
        c.cHPFull = hpMax
        c.cMPFull = mpMax
        c.cHP = hp
        c.cMP = mp
        c.cspeed = speed
        c.cDamFull = dame
        c.cDefull = def_
        c.cCriticalFull = crit
        c.cTiemNang = tiemNang
        c.cDefGoc = defg
        c.cCriticalGoc = critg
        log.info("STATS", f"HP={hp}/{hpMax} MP={mp}/{mpMax} SPD={speed} Dmg={dame} Def={def_}")
        log.show_status(f"Map:{self.state.map_id} HP:{hp}/{hpMax} MP:{mp}/{mpMax}")

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
        if self.state.my_char:
            self.state.my_char.xu = coin
        log.info("COIN", f"Gold: {coin}")

    def handle_send_money(self, msg: Message):
        try:
            gold = msg.readLong()
        except Exception:
            gold = msg.readInt()
        gem = msg.readInt()
        msg.readInt()  # ruby
        if self.state.my_char:
            self.state.my_char.xu = gold
            self.state.my_char.luong = gem
        log.info("COIN", f"Gold={gold} Gem={gem}")

    def handle_player_attack_n_p(self, msg: Message):
        log.debug("ATTACK", f"size={msg.available()}")

    def handle_sub_command(self, msg: Message):
        sub = msg.readByte()
        if sub == C.SUB_ME_LOAD_ALL:
            pid = msg.readInt()
            task_id = msg.readByte()
            gender = msg.readByte()
            head = msg.readShort()
            chname = msg.readUTF()
            msg.readByte()  # cPk (0)
            msg.readByte()  # typePk
            msg.readLong()  # power
            msg.readShort() # reserved
            msg.readShort() # reserved
            msg.readByte()  # gender dup
            skill_count = msg.readByte()
            for _ in range(skill_count):
                msg.readShort()
            try:
                gold = msg.readLong()
            except Exception:
                gold = msg.readInt()
            ruby = msg.readInt()
            gem = msg.readInt()
            if self.state.my_char:
                self.state.my_char.xu = gold
                self.state.my_char.luong = gem
                self.state.my_char.luongKhoa = ruby
            log.info("SUB", f"Loaded: pid={pid} name={chname} gold={gold} gem={gem}")
        elif sub == C.SUB_ME_LOAD_CLASS:
            log.info("SUB", "Loading class...")
        elif sub == C.SUB_ME_LOAD_SKILL:
            log.info("SUB", "Loading skills...")
        elif sub == C.SUB_ME_LOAD_INFO:
            try:
                gold = msg.readLong()
            except Exception:
                gold = msg.readInt()
            gem = msg.readInt()
            msg.readInt()
            msg.readInt()
            msg.readInt()
            if self.state.my_char:
                self.state.my_char.xu = gold
                self.state.my_char.luong = gem
            log.info("SUB", f"Gold={gold} Gem={gem}")
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
            if player_id == self.state.my_char_id and self.state.my_char:
                self.state.my_char.clevel = level
            log.info("LEVEL", f"player={player_id} level={level}")
        elif sub == C.SUB_PLAYER_LOAD_VUKHI:
            player_id = msg.readInt()
            weapon_id = msg.readShort()
            if player_id == self.state.my_char_id and self.state.my_char:
                self.state.my_char.wp = weapon_id
            log.info("WEAPON", f"player={player_id} weapon={weapon_id}")
        elif sub == C.SUB_PLAYER_LOAD_AO:
            player_id = msg.readInt()
            body_id = msg.readShort()
            if player_id == self.state.my_char_id and self.state.my_char:
                self.state.my_char.body = body_id
            log.info("BODY", f"player={player_id} body={body_id}")
        elif sub == C.SUB_PLAYER_LOAD_QUAN:
            player_id = msg.readInt()
            leg_id = msg.readShort()
            if player_id == self.state.my_char_id and self.state.my_char:
                self.state.my_char.leg = leg_id
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
        try:
            pid = msg.readInt()
            clan_id = msg.readInt()
            level = msg.readByte()
            msg.readByte()
            type_pk = msg.readByte()
            gender = msg.readByte()
            msg.readByte()
            head = msg.readShort()
            name = msg.readUTF()
            hp = msg.readInt()
            hp_max = msg.readInt()
            body = msg.readShort()
            leg = msg.readShort()
            bag = msg.readByte()
            msg.readByte()
            x = msg.readShort()
            y = msg.readShort()
            msg.readShort()
            msg.readShort()
            msg.readByte()
            msg.readByte()
            msg.readByte()
            msg.readShort()
            msg.readByte()
            msg.readByte()
            msg.readShort()
            msg.readByte()
            msg.readShort()
        except Exception as e:
            log.error("PLAYER", f"Parse error: {e}")
            return
        data = {
            'id': pid, 'name': name, 'clan_id': clan_id,
            'head': head, 'body': body, 'leg': leg,
            'gender': gender, 'x': x, 'y': y, 'level': level,
        }
        self.state.add_player(pid, data)
        my_name = self.state.my_char.cName if self.state.my_char else ''
        if self.state.my_char and (name == my_name or name.endswith(my_name)):
            c = self.state.my_char
            c.charID = pid
            c.cName = name
            c.head = head
            c.body = body
            c.leg = leg
            c.cgender = gender
            c.clevel = level
            c.cx = x
            c.cy = y
            log.info("ME", f"Spawned at ({x},{y})")
        elif self.state.my_char is None and name:
            c = Char()
            c.charID = pid
            c.cName = name
            c.head = head
            c.body = body
            c.leg = leg
            c.cgender = gender
            c.clevel = level
            c.cx = x
            c.cy = y
            self.state.my_char = c
            log.info("ME", f"Spawned at ({x},{y})")
        else:
            log.info("PLAYER", f"{pid} at ({x},{y})")
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
