from logger import log
from network import Message
from state import GameState


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
        action = msg.readByte()
        log.info("SHOP", f"action={action} size={msg.available()}")

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

    def handle_body(self, msg: Message):
        action = msg.readByte()
        log.info("BODY", f"action={action}")

    def handle_bag(self, msg: Message):
        action = msg.readByte()
        log.info("BAG", f"action={action}")

    def handle_box(self, msg: Message):
        action = msg.readByte()
        log.info("BOX", f"action={action}")

    def handle_upgrade(self, msg: Message):
        action = msg.readByte()
        log.info("UPGRADE", f"action={action}")

    def handle_open_ui_zone(self, msg: Message):
        count = msg.readByte()
        log.info("UI", f"Zone list ({count} zones)")

    def handle_open_ui_shop(self, msg: Message):
        log.debug("UI", "Opening shop...")

    def handle_open_ui_collect(self, msg: Message):
        log.debug("UI", "Opening collection...")

    def handle_open_ui_pt(self, msg: Message):
        log.debug("UI", "Opening party...")

    def handle_open_ui_trade(self, msg: Message):
        log.debug("UI", "Opening trade...")

    def handle_open_ui_say(self, msg: Message):
        log.debug("UI", "Opening chat input...")

    def handle_npc_miss(self, msg: Message):
        npc_id = msg.readByte()
        log.debug("NPC", f"NPC {npc_id} missed")
