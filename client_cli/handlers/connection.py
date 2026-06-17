import sys
from logger import log
from state import GameState
from service import Service


class ConnectionHandler:
    def __init__(self, state: GameState, service: Service):
        self.state = state
        self.service = service

    def on_connect_ok(self, is_main: bool):
        log.info("CLIENT", "Connected to server!")
        self.service.setClientType()

    def on_connection_fail(self, is_main: bool):
        log.error("CLIENT", "Connection failed!")
        sys.exit(1)

    def on_disconnected(self, is_main: bool):
        log.info("CLIENT", "Disconnected!")
        self.state.logged_in = False
        self.state.in_game = False
