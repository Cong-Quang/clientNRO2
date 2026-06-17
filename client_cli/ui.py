import time
import sys
from logger import log, LogLevel, CATEGORIES
from client import GameClient
from npcs_data import npc_name


class ConsoleUI:
    def __init__(self, client: GameClient):
        self.client = client

    def run(self):
        log.auto_config()
        if log._compact:
            log.raw("=== NRO CLI (compact mode) ===")
        else:
            log.raw("=== NRO CLI Client ===")
        self._wait_ready()
        self._send_auto_login()
        self._print_help()
        self._input_loop()

    def _wait_ready(self, timeout: float = 3.0):
        for _ in range(int(timeout / 0.1)):
            if self.client.session.isConnected():
                return
            time.sleep(0.1)
        if not self.client.session.isConnected():
            log.error("CLIENT", "Failed to connect!")
            sys.exit(1)

    def _send_auto_login(self):
        args = self._parse_args()
        log.info("LOGIN", f"Logging in as {args.username}...")
        self.client.service.login(args.username, args.password)

    def _parse_args(self):
        import argparse
        parser = argparse.ArgumentParser(description='NRO CLI Client')
        parser.add_argument('--host', default='127.0.0.1')
        parser.add_argument('--port', type=int, default=14445)
        parser.add_argument('--username', default='1')
        parser.add_argument('--password', default='1')
        return parser.parse_args()

    def _print_help(self):
        log.raw("  /login <u> <p>   /select <name>")
        log.raw("  /chat <t>        /move <x> <y>")
        log.raw("  /useitem <t> <w> <i>  /pick <id>")
        log.raw("  /npcmenu <id>    /menu <opt> [/menu <n> <m> <o>]")
        log.raw("  /zone <id>       /changemap")
        log.raw("  /skill <id>      /buy <t> <id> [qty]")
        log.raw("  /sale <a> <t> <id>  /task <n> <m> [o]")
        log.raw("  /players  /info  /map  /npcs  /heal  /gocit  /wake")
        log.raw("  /log <cat> on|off|debug   /log list")
        log.raw("  /log all on|off|debug     /quit\n")

    def _input_loop(self):
        while self.client.session.isConnected():
            try:
                npc_id = self.client.state.current_npc_id
                prompt = f"npc({npc_id})> " if npc_id else "> "
                line = input(prompt).strip()
                if not line:
                    continue
                self._handle_input(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error("INPUT", str(e))
        self.client.session.close()
        log.raw("Disconnected.")

    def _handle_input(self, line: str):
        if not line.startswith('/'):
            if self.client.state.current_npc_id and line.isdigit():
                self.client.service.confirmMenu(self.client.state.current_npc_id, int(line))
                self.client.state.current_npc_id = 0
                return
            self._chat(line)
            return
        parts = line.split()
        cmd = parts[0].lower()

        if cmd == '/quit':
            raise EOFError
        if cmd == '/map':
            self._show_map()
            return
        if cmd == '/npcs':
            self._show_npcs()
            return
        if cmd == '/players':
            self._show_players()
            return
        if cmd == '/info':
            self._show_info()
            return
        if cmd == '/log' or cmd == '/debug':
            self._handle_log(parts)
            return
        if cmd == '/help':
            self._print_help()
            return

        c = self.client
        try:
            if cmd == '/login' and len(parts) >= 3:
                c.service.login(parts[1], parts[2])
            elif cmd == '/select':
                c.service.selectChar(' '.join(parts[1:]))
            elif cmd == '/chat':
                self._chat(' '.join(parts[1:]))
            elif cmd == '/move' and len(parts) >= 3:
                c.service.charMove(int(parts[1]), int(parts[2]), 1)
            elif cmd == '/useitem' and len(parts) >= 4:
                c.service.useItem(int(parts[1]), int(parts[2]), int(parts[3]))
            elif cmd == '/pick' and len(parts) >= 2:
                c.service.pickItem(int(parts[1]))
            elif cmd == '/npcmenu' and len(parts) >= 2:
                c.service.openMenu(int(parts[1]))
            elif cmd == '/menu' and len(parts) == 2:
                c.service.confirmMenu(c.state.current_npc_id, int(parts[1]))
            elif cmd == '/menu' and len(parts) >= 4:
                c.service.menu(int(parts[1]), int(parts[2]), int(parts[3]))
            elif cmd == '/zone' and len(parts) >= 2:
                c.service.requestChangeZone(int(parts[1]))
            elif cmd == '/changemap':
                c.service.requestChangeMap()
            elif cmd == '/skill' and len(parts) >= 2:
                c.service.selectSkill(int(parts[1]))
            elif cmd == '/buy' and len(parts) >= 3:
                qty = int(parts[3]) if len(parts) >= 4 else 1
                c.service.buyItem(int(parts[1]), int(parts[2]), qty)
            elif cmd == '/sale' and len(parts) >= 4:
                c.service.saleItem(int(parts[1]), int(parts[2]), int(parts[3]))
            elif cmd == '/task' and len(parts) >= 3:
                opt = int(parts[3]) if len(parts) >= 4 else -1
                c.service.getTask(int(parts[1]), int(parts[2]), opt)
            elif cmd == '/heal':
                c.service.magicTree(1)
            elif cmd == '/gocit':
                c.service.returnTownFromDead()
            elif cmd == '/wake':
                c.service.wakeUpFromDead()
            else:
                log.raw(f"Unknown: {cmd}  (/help)")
        except (IndexError, ValueError):
            log.raw(f"Usage: {cmd} <args>")

    def _handle_log(self, parts):
        if len(parts) == 2 and parts[1] == 'list':
            log.raw("Categories: " + ', '.join(CATEGORIES))
            log.raw("Levels: off, on, debug")
            for cat in CATEGORIES:
                lv = LogLevel.name(log.get_level(cat))
                log.raw(f"  {cat}: {lv}")
            return
        if len(parts) >= 3:
            cat = parts[1].lower()
            if cat in CAT_ALIAS:
                cat = CAT_ALIAS[cat]
            level_str = parts[2].lower()
            if level_str == 'off':
                log.set_level(cat, LogLevel.OFF)
            elif level_str == 'debug':
                log.set_level(cat, LogLevel.DEBUG)
            else:
                log.set_level(cat, LogLevel.INFO)
            log.raw(f"[LOG] {cat} set to {level_str}")
            return
        log.raw("Usage: /log <cat> on|off|debug   or   /log list")

    def _chat(self, text: str):
        if self.client.state.in_game:
            self.client.service.chat(text)
        else:
            log.raw("Not in game yet")

    def _show_map(self):
        s = self.client.state
        log.raw(f"Map: {s.map_name} (ID={s.map_id})  Zone: {s.zone_id}")

    def _show_npcs(self):
        for n in self.client.state.npcs:
            name = npc_name(n['tempId'])
            log.raw(f"  {name} (ID={n['tempId']}) at ({n['x']},{n['y']})")

    def _show_players(self):
        for pid, p in self.client.state.players.items():
            log.raw(f"  [{pid}] {p.get('name','?')} at ({p.get('x',0)},{p.get('y',0)})")

    def _show_info(self):
        s = self.client.state
        c = s.my_char
        log.raw(f"Map: {s.map_id}  Zone: {s.zone_id}  Players: {len(s.players)}")
        if c:
            for line in c.format().split("\n"):
                log.raw("  " + line)
        else:
            log.raw("  (no character data)")
