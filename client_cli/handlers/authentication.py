import cmd as C
from logger import log
from network import Message
from state import GameState
from service import Service


class AuthHandler:
    def __init__(self, state: GameState, service: Service):
        self.state = state
        self.service = service
        self._entering_game = False

    def handle_get_image_source(self, msg: Message):
        pass

    def handle_not_login(self, msg: Message):
        pass

    def handle_char_list(self, msg: Message):
        count = msg.readByte()
        log.info("LOGIN", f"Character list ({count} chars):")
        first_name = None
        for i in range(count):
            pid = msg.readInt()
            name = msg.readUTF()
            head = msg.readShort()
            body = msg.readShort()
            leg = msg.readShort()
            ppoint = msg.readLong()
            log.info("LOGIN", f"  [{i}] ID={pid} '{name}' h={head} b={body} l={leg} pw={ppoint}")
            if first_name is None:
                first_name = name
                self.state.my_char_id = pid
        self.state.logged_in = True
        if count == 1 and first_name:
            log.info("LOGIN", f"Auto-selecting: {first_name}")
            self.service.selectChar(first_name)
        elif count > 0:
            log.info("LOGIN", "Use /select <name> to choose a character")

    def handle_not_map(self, msg: Message):
        sub = msg.readByte()
        if sub == C.CMD_SELECT_PLAYER:
            chname = msg.readUTF()
            log.info("GAME", f"Selected character: {chname}")
            self.state.in_game = True
            from Char import Char
            self.state.my_char = Char()
            self.state.my_char.cName = chname
        elif sub == C.CMD_CREATE_PLAYER:
            name = msg.readUTF()
            log.info("GAME", f"Created character: {name}")
        elif sub in (0, 4):
            if sub == 0:
                log.info("GAME", "Login OK")
            else:
                log.info("GAME", "Entering game...")
            self.state.in_game = True
            if not self._entering_game:
                self._entering_game = True
                self.service.clientOk()
                self.service.updateMap()
                self.service.updateSkill()
                self.service.updateItem()
        else:
            pass
