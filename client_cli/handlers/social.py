from logger import log
from network import Message
from state import GameState


class SocialHandler:
    def __init__(self, state: GameState):
        self.state = state

    def handle_friend_invite(self, msg: Message):
        name = msg.readUTF()
        log.info("FRIEND", f"Invite from {name}")

    def handle_friend(self, msg: Message):
        action = msg.readByte()
        log.debug("FRIEND", f"action={action}")

    def handle_friend_add(self, msg: Message):
        player_id = msg.readInt()
        log.info("FRIEND", f"Added {player_id}")

    def handle_giao_dich(self, msg: Message):
        action = msg.readByte()
        log.info("TRADE", f"action={action}")

    def handle_trade_invite(self, msg: Message):
        player_id = msg.readInt()
        log.info("TRADE", f"Invite from {player_id}")

    def handle_trade_invite_accept(self, msg: Message):
        player_id = msg.readInt()
        log.info("TRADE", f"{player_id} accepted")

    def handle_trade_lock_item(self, msg: Message):
        log.info("TRADE", "Items locked")

    def handle_trade_accept(self, msg: Message):
        log.info("TRADE", "Accepted")

    def handle_trade_invite_cancel(self, msg: Message):
        log.info("TRADE", "Cancelled")

    def handle_combine(self, msg: Message):
        action = msg.readByte()
        log.info("COMBINE", f"action={action}")

    def handle_player_menu(self, msg: Message):
        pid = msg.readInt()
        log.debug("PLAYER", f"Menu for {pid}")

    def handle_pet_info(self, msg: Message):
        sub = msg.readByte()
        if sub == 2:
            pet = {}
            pet['avatar'] = msg.readShort()
            body_count = msg.readUnsignedByte()
            pet['items_body'] = []
            for _ in range(body_count):
                item_id = msg.readShort()
                if item_id == -1:
                    pet['items_body'].append(None)
                    continue
                item = {'id': item_id, 'quantity': msg.readInt(), 'info': msg.readUTF(), 'content': msg.readUTF()}
                opt_count = msg.readByte()
                item['options'] = [{'id': msg.readByte(), 'param': msg.readShort()} for _ in range(opt_count)]
                pet['items_body'].append(item)
            pet['hp'] = msg.readInt()
            pet['hpMax'] = msg.readInt()
            pet['mp'] = msg.readInt()
            pet['mpMax'] = msg.readInt()
            pet['damage'] = msg.readInt()
            pet['name'] = msg.readUTF()
            pet['level_str'] = msg.readUTF()
            pet['power'] = msg.readLong()
            pet['potential'] = msg.readLong()
            pet['status'] = msg.readByte()
            pet['stamina'] = msg.readShort()
            pet['staminaMax'] = msg.readShort()
            pet['crit'] = msg.readByte()
            pet['def'] = msg.readShort()
            skill_count = msg.readByte()
            pet['skills'] = []
            for _ in range(skill_count):
                skill_id = msg.readShort()
                if skill_id == -1:
                    reason = msg.readUTF()
                    pet['skills'].append({'id': -1, 'locked': reason})
                else:
                    pet['skills'].append({'id': skill_id})
            self.state.pet = pet
        else:
            log.info("PET", f"sub={sub}")

    def handle_pet_status(self, msg: Message):
        status = msg.readByte()
        log.info("PET", f"status={status}")

    def handle_transport(self, msg: Message):
        log.info("TRANSPORT", "")

    def handle_flag(self, msg: Message):
        sub = msg.readByte()
        log.debug("FLAG", f"sub={sub}")

    def handle_clan_create(self, msg: Message):
        sub = msg.readByte()
        if sub == 0:
            log.info("CLAN", "Create info...")

    def handle_set_clienttype(self, msg: Message):
        ct = msg.readByte()
        log.info("CLIENT", f"Client type set: {ct}")

    def handle_server_screen(self, msg: Message):
        log.info("SERVER", "Switching server screen...")

    def handle_update_data(self, msg: Message):
        log.info("DATA", f"Update ({msg.available()} bytes)")

    def handle_big_boss(self, msg: Message):
        action = msg.readByte()
        log.info("BOSS", f"Big boss action={action}")

    def handle_big_boss_2(self, msg: Message):
        action = msg.readByte()
        log.info("BOSS", f"Big boss 2 action={action}")

    def handle_server_effect(self, msg: Message):
        effect_id = msg.readByte()
        log.debug("EFFECT", f"Server effect {effect_id}")

    def handle_client_input(self, msg: Message):
        count = msg.readByte()
        log.info("INPUT", f"Request ({count} fields)")

    def handle_check_controller(self, msg: Message):
        log.debug("CHECK", "Controller check")

    def handle_check_map(self, msg: Message):
        log.debug("CHECK", "Map check")

    def handle_tile_set(self, msg: Message):
        log.debug("TILE", f"Data ({msg.available()} bytes)")

    def handle_map_transport(self, msg: Message):
        count = msg.readByte()
        names = []
        planets = []
        for _ in range(count):
            names.append(msg.readUTF())
            planets.append(msg.readUTF())
        self.state.map_transport_list = names
        log.raw(f"[Teleport] Chọn map để dịch chuyển ({count} maps):")
        for i, name in enumerate(names):
            planet = planets[i] if planets[i] else ""
            log.raw(f"  [{i}] {name} {planet}")
        log.raw("Dùng /selectmap <số> để chọn")

    def handle_item_time(self, msg: Message):
        if msg.available() < 1:
            return
        id_ = msg.readByte()
        text = msg.readUTF() if msg.available() > 2 else ''
        time_ = msg.readShort() if msg.available() >= 2 else 0
        log.info("ITEM", f"id={id_} '{text}' time={time_}")

    def handle_lucky_round(self, msg: Message):
        log.debug("LUCKY", f"size={msg.available()}")

    def handle_quayso(self, msg: Message):
        log.debug("QUAYSO", f"size={msg.available()}")

    def handle_rada_card(self, msg: Message):
        action = msg.readByte()
        log.debug("CARD", f"action={action}")

    def handle_char_effect(self, msg: Message):
        effect_id = msg.readByte()
        log.debug("EFFECT", f"Char effect {effect_id}")

    def handle_lock_inventory(self, msg: Message):
        log.info("LOCK", "Inventory lock status")

    def handle_android_pack(self, msg: Message):
        log.debug("ANDROID", "")

    def handle_fusion(self, msg: Message):
        action = msg.readByte()
        log.info("FUSION", f"action={action}")

    def handle_extra_big(self, msg: Message):
        sub = msg.readByte()
        log.debug("EXTRA", f"big sub={sub}")

    def handle_extra(self, msg: Message):
        sub = msg.readByte()
        log.debug("EXTRA", f"sub={sub}")

    def handle_party_invite(self, msg: Message):
        player_id = msg.readInt()
        log.info("PARTY", f"Invite from {player_id}")

    def handle_party_accept(self, msg: Message):
        log.info("PARTY", "Accepted")

    def handle_party_cancel(self, msg: Message):
        log.info("PARTY", "Cancelled")

    def handle_player_in_party(self, msg: Message):
        log.info("PARTY", "Player in party")

    def handle_party_out(self, msg: Message):
        log.info("PARTY", "Left party")

    def handle_please_input_party(self, msg: Message):
        log.debug("PARTY", "Please input")

    def handle_accept_please_party(self, msg: Message):
        log.debug("PARTY", "Accept please")

    def handle_request_players(self, msg: Message):
        log.debug("PARTY", "Request players")

    def handle_update_achievement(self, msg: Message):
        log.debug("ACHIEVE", f"size={msg.available()}")

    def handle_auto_server(self, msg: Message):
        action = msg.readByte()
        log.debug("AUTO", f"action={action}")

    def handle_change_name(self, msg: Message):
        log.info("NAME", "Change name")

    def handle_register(self, msg: Message):
        log.info("LOGIN", "Register response")

    def handle_delete_player(self, msg: Message):
        log.info("LOGIN", "Delete player response")

    def handle_client_info(self, msg: Message):
        log.debug("CLIENT", "Client info")

    def handle_client_ok(self, msg: Message):
        log.info("CLIENT", "OK")

    def handle_client_ok_inmap(self, msg: Message):
        log.info("CLIENT", "OK in map")

    def handle_update_version_ok(self, msg: Message):
        log.info("VERSION", "Version OK")

    def handle_enemy_list(self, msg: Message):
        action = msg.readByte()
        log.info("ENEMY", f"action={action}")

    def handle_player_vs_player(self, msg: Message):
        type_pk = msg.readByte()
        player_id = msg.readInt()
        log.info("PVP", f"type={type_pk} opponent={player_id}")

    def handle_goto_player(self, msg: Message):
        player_id = msg.readInt()
        log.debug("GOTO", f"Target {player_id}")
