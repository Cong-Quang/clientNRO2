from logger import log
from network import Message
from state import GameState
from items_data import item_name


class InteractionHandler:
    def __init__(self, state: GameState):
        self.state = state

    def handle_menu(self, msg: Message):
        npc_id = msg.readByte()
        menu_id = msg.readByte()
        option_id = msg.readByte()
        log.info("MENU", f"npc={npc_id} menu={menu_id} opt={option_id}")

    def handle_menu_id(self, msg: Message):
        menu_id = msg.readShort()
        log.info("MENU", f"Open menu {menu_id}")

    def handle_confirm(self, msg: Message):
        npc_id = msg.readShort()
        npc_say = msg.readUTF()
        count = msg.readByte()
        self.state.current_npc_id = npc_id
        log.raw(f"[NPC] {npc_say}")
        for i in range(count):
            text = msg.readUTF()
            log.raw(f"  [{i}] {text}")

    def handle_npc_menu(self, msg: Message):
        npc_id = msg.readUnsignedShort()
        log.info("NPC", f"Menu for NPC {npc_id}")

    def handle_skill_select(self, msg: Message):
        skill_id = msg.readShort()
        log.info("SKILL", f"Selected skill {skill_id}")

    def handle_item_info(self, msg: Message):
        type_ui = msg.readUnsignedByte()
        index_ui = msg.readUnsignedByte()
        log.info("ITEM", f"type={type_ui} index={index_ui}")

    def handle_task(self, msg: Message):
        npc_id = msg.readUnsignedByte()
        menu_id = msg.readUnsignedByte()
        option_id = msg.readByte() if msg.available() > 0 else -1
        log.info("TASK", f"npc={npc_id} menu={menu_id} opt={option_id}")

    def handle_shop(self, msg: Message):
        shop_type = msg.readByte()
        tab_count = msg.readUnsignedByte()
        log.raw(f"[SHOP] type={shop_type} tabs={tab_count}")
        for t in range(tab_count):
            tab_name = msg.readUTF()
            item_count = msg.readUnsignedByte()
            log.raw(f"  [{t}] {tab_name} ({item_count} items)")
            for _ in range(item_count):
                item_id = msg.readShort()
                if item_id == -1:
                    continue
                if shop_type == 0:
                    coin = msg.readInt(); gold = msg.readInt()
                    price = f"Vàng:{coin}" if coin else f"Ngọc:{gold}"
                elif shop_type == 1:
                    power = msg.readLong()
                    price = f"Tiềm năng:{power}"
                elif shop_type == 2:
                    sid = msg.readShort(); coin = msg.readInt()
                    gold = msg.readInt(); bt = msg.readByte()
                    qty = msg.readInt(); msg.readByte()
                    price = f"Vàng:{coin} Ngọc:{gold} x{qty}"
                elif shop_type == 3:
                    icon = msg.readShort(); cost = msg.readInt()
                    price = f"vật phẩm({icon})x{cost}"
                elif shop_type == 4:
                    reason = msg.readUTF()
                    price = f"| {reason}"
                elif shop_type == 8:
                    coin = msg.readInt(); gold = msg.readInt(); qty = msg.readInt()
                    price = f"Vàng:{coin} Ngọc:{gold} x{qty}"
                else:
                    price = "?"
                opt_count = msg.readByte()
                for _ in range(opt_count):
                    msg.readByte()
                    msg.readShort()
                is_new = msg.readByte()
                has_part = msg.readByte()
                if has_part:
                    msg.readShort()
                    msg.readShort()
                    msg.readShort()
                    msg.readShort()
                log.raw(f"    [{item_id}] {item_name(item_id)} - {price}")

    def handle_skill_not_focus(self, msg: Message):
        status = msg.readByte()
        log.info("SKILL", f"Auto skill status={status}")

    def handle_magic_tree(self, msg: Message):
        action = msg.readByte()
        log.info("TREE", f"action={action}")

    def handle_special_skill(self, msg: Message):
        type_ = msg.readByte()
        log.info("SPECIAL", f"type={type_}")

    def handle_use_item(self, msg: Message):
        action = msg.readByte()
        where = msg.readByte()
        index = msg.readByte()
        info = msg.readUTF()
        log.info("ITEM", f"action={action} where={where} index={index}: {info}")

    def handle_get_item(self, msg: Message):
        type_ = msg.readByte()
        id_ = msg.readByte()
        log.info("ITEM", f"Get type={type_} id={id_}")

    def _parse_items(self, msg: Message, count: int) -> list[dict | None]:
        items = []
        for _ in range(count):
            item_id = msg.readShort()
            if item_id == -1:
                items.append(None)
                continue
            item = {
                'id': item_id,
                'quantity': msg.readInt(),
                'info': msg.readUTF(),
                'content': msg.readUTF(),
            }
            opt_count = msg.readByte()
            item['options'] = []
            for _ in range(opt_count):
                item['options'].append({
                    'id': msg.readByte(),
                    'param': msg.readShort(),
                })
            items.append(item)
        return items

    def handle_body(self, msg: Message):
        action = msg.readByte()
        if action == 0:
            head = msg.readShort()
            count = msg.readUnsignedByte()
            self.state.items_body = self._parse_items(msg, count)
            log.info("BODY", f"Loaded {count} body items, head={head}")
        else:
            log.info("BODY", f"action={action}")

    def handle_bag(self, msg: Message):
        action = msg.readByte()
        if action == 0:
            count = msg.readUnsignedByte()
            self.state.items_bag = self._parse_items(msg, count)
            log.info("BAG", f"Loaded {count} bag items")
        else:
            log.info("BAG", f"action={action}")

    def handle_box(self, msg: Message):
        action = msg.readByte()
        if action == 0:
            count = msg.readUnsignedByte()
            self.state.items_box = self._parse_items(msg, count)
            log.info("BOX", f"Loaded {count} box items")
        else:
            log.info("BOX", f"action={action}")

    def handle_upgrade(self, msg: Message):
        action = msg.readByte()
        log.info("UPGRADE", f"action={action}")

    def handle_open_ui_zone(self, msg: Message):
        count = msg.readByte()
        log.info("UI", f"Zone list ({count} zones)")

    def handle_open_ui_shop(self, msg: Message):
        log.raw("[SHOP] Opening shop interface...")

    def handle_open_ui_collect(self, msg: Message):
        log.debug("UI", "Opening collection...")

    def handle_open_ui_pt(self, msg: Message):
        log.debug("UI", "Opening party...")

    def handle_open_ui_trade(self, msg: Message):
        log.debug("UI", "Opening trade...")

    def handle_open_ui_say(self, msg: Message):
        log.debug("UI", "Opening chat input...")

    def handle_hide_wait_dialog(self, msg: Message):
        type_ = msg.readByte()
        if type_ == -1:
            log.raw("[NPC] Không có NPC nào ở đây")
        else:
            log.info("NPC", f"Enemy list type={type_}, size={msg.available()}")

    def handle_npc_miss(self, msg: Message):
        npc_id = msg.readByte()
        log.debug("NPC", f"NPC {npc_id} missed")
