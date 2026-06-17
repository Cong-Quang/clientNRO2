from logger import log
from network import Message
from state import GameState


class CommunicationHandler:
    def __init__(self, state: GameState):
        self.state = state

    def handle_dialog(self, msg: Message):
        text = msg.readUTF()
        log.info("DIALOG", text)

    def handle_server_msg(self, msg: Message):
        text = msg.readUTF()
        log.info("SERVER", text)

    def handle_chat(self, msg: Message):
        pid = msg.readInt()
        text = msg.readUTF()
        name = self.state.get_player_name(pid)
        log.info("CHAT", f"{name}: {text}")

    def handle_big_msg(self, msg: Message):
        text = msg.readUTF()
        log.info("BIG_MSG", text)

    def handle_alert_message(self, msg: Message):
        text = msg.readUTF()
        log.info("ALERT", text)

    def handle_npc_chat(self, msg: Message):
        text = msg.readUTF()
        log.info("NPC", text)

    def handle_boss_skill(self, msg: Message):
        boss_id = msg.readByte()
        skill_id = msg.readShort()
        x = msg.readShort()
        y = msg.readShort()
        log.info("BOSS", f"id={boss_id} skill={skill_id} at ({x},{y})")

    def handle_mabu_hold(self, msg: Message):
        player_id = msg.readInt()
        hold = msg.readByte()
        log.debug("MABU", f"player={player_id} hold={hold}")

    def handle_have_attack_player(self, msg: Message):
        player_id = msg.readInt()
        log.warn("PVP", f"Player {player_id} attacked you!")
