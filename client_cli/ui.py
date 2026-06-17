import time
import sys
from logger import log, LogLevel, CATEGORIES
from client import GameClient
from npcs_data import npc_name
from items_data import item_name


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
        log.raw("  /npcmenu <id>    /menu <opt>  (chọn option NPC)")
        log.raw("  /zone <id>       /changemap")
        log.raw("  /skill <id>      /buy <t> <id> [qty]  (t=0:vàng,1:ngọc)")
        log.raw("  /sale <a> <t> <id>  /task <n> <m> [o]")
        log.raw("  /players  /info  /map  /npcs  /items  /equip  /pet  /heal  /gocit  /wake")
        log.raw("  /selectmap <n>  (chọn map khi dùng capsule)")
        log.raw("  /xmap <mapId>   /xmapstop   /xmapmenu   /xmapsettings")
        log.raw("  /log <cat> on|off|debug   /log list")
        log.raw("  /log all on|off|debug     /quit\n")

    def _input_loop(self):
        while self.client.session.isConnected():
            try:
                s = self.client.state
                npc_id = s.current_npc_id
                if s.xmap_runner and s.xmap_runner.is_running():
                    st = s.xmap_runner.status
                    prompt = f"xmap({st})> " if st else "xmap> "
                elif npc_id:
                    prompt = f"npc({npc_id})> "
                else:
                    prompt = "> "
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
        if cmd == '/items':
            self.client.service.getBag(0)
            self._show_items()
            return
        if cmd == '/equip':
            self.client.service.getBody(0)
            self._show_equip()
            return
        if cmd == '/pet':
            self.client.service.petInfo()
            self._show_pet()
            return
        if cmd == '/log' or cmd == '/debug':
            self._handle_log(parts)
            return
        if cmd == '/xmap' and len(parts) >= 2:
            from xmap_runner import XmapRunner
            cl = self.client
            target = int(parts[1])
            if cl.state.xmap_runner is None:
                cl.state.xmap_runner = XmapRunner(cl.state, cl.service)
            if cl.state.xmap_runner.is_running():
                log.raw(f"Xmap đang chạy, dùng /xmapstop để dừng")
                return
            cl.state.xmap_runner.start(target)
            log.raw(f"Xmap: bắt đầu đi đến map {target}")
            return
        if cmd == '/xmapstop':
            if self.client.state.xmap_runner:
                self.client.state.xmap_runner.stop()
            log.raw("Xmap: đã dừng")
            return
        if cmd == '/xmapmenu':
            from xmap_data import PLANETS
            log.raw("Chọn hành tinh (dùng /xmap <id> trực tiếp hoặc xem danh sách):")
            for name, maps in PLANETS.items():
                ids = ', '.join(str(m) for m in maps)
                log.raw(f"  {name}: {ids}")
            return
        if cmd == '/xmapsettings':
            r = self.client.state.xmap_runner
            if r:
                r.eat_chicken = not r.eat_chicken
                r.use_capsule = not r.use_capsule if len(parts) > 1 and parts[1] == 'capsule' else r.use_capsule
                log.raw(f"Ăn đùi gà: {'ON' if r.eat_chicken else 'OFF'} | Capsule: {'ON' if r.use_capsule else 'OFF'}")
            else:
                log.raw("Xmap chưa được khởi tạo, dùng /xmap <id> trước")
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
                npc_id = int(parts[1])
                if not any(n['tempId'] == npc_id for n in c.state.npcs):
                    found = npc_name(npc_id)
                    log.raw(f"[NPC] {found} (ID={npc_id}) không có ở map này")
                    log.raw(f"  Dùng /npcs để xem NPC hiện có")
                else:
                    c.service.openMenu(npc_id)
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
            elif cmd == '/selectmap' and len(parts) >= 2:
                idx = int(parts[1])
                if 0 <= idx < len(c.state.map_transport_list):
                    c.service.requestMapSelect(idx)
                    c.state.map_transport_list.clear()
                else:
                    log.raw(f"Chọn từ 0 đến {len(c.state.map_transport_list)-1}")
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
            if s.items_body:
                worn = [item for item in s.items_body if item]
                if worn:
                    log.raw(f"  Equipped: {len(worn)} items")
            if s.items_bag:
                count = sum(1 for x in s.items_bag if x)
                log.raw(f"  Bag: {count} items")
            if s.pet:
                log.raw(f"  Pet: {s.pet.get('name', '?')}")
        else:
            log.raw("  (no character data)")

    def _format_item(self, item: dict, index: int = -1) -> str:
        name = item_name(item['id'])
        prefix = f"[{index}] " if index >= 0 else ""
        item_id_str = f"[#{item['id']}] "
        info = item.get('info', '').strip()
        if info:
            lines = info.split('\n')
            opts_formatted = ("\n" + " " * (len(prefix) + len(item_id_str) + 2)).join(lines)
            return f"  {prefix}{item_id_str}{name} x{item['quantity']}\n      {opts_formatted}"
        return f"  {prefix}{item_id_str}{name} x{item['quantity']}"

    def _show_items(self):
        s = self.client.state
        items = s.items_bag
        if not items:
            log.raw("[Bag] No items (use /getbag to request)")
            return
        count = sum(1 for x in items if x)
        log.raw(f"[Bag] {count} items:")
        for idx, item in enumerate(items):
            if item:
                log.raw(self._format_item(item, idx))

    def _show_equip(self):
        s = self.client.state
        items = s.items_body
        if not items:
            log.raw("[Equip] No data (use /getbody to request)")
            return
        SLOT_NAMES = ["Áo", "Quần", "Găng", "Giày", "Nhẫn", "Cải trang", "Chí bôi", "Vũ khí", "Liễn", "Ngữ"]
        log.raw("[Equip] Equipped items:")
        for i, item in enumerate(items):
            slot_name = SLOT_NAMES[i] if i < len(SLOT_NAMES) else f"Slot{i}"
            if item:
                log.raw(f"  [{slot_name}] {self._format_item(item)}")
            else:
                log.raw(f"  [{slot_name}] (empty)")

    def _show_pet(self):
        pet = self.client.state.pet
        if not pet:
            log.raw("[Pet] No pet info")
            return
        log.raw(f"[Pet] {pet.get('name', '?')} ({pet.get('level_str', '')})")
        log.raw(f"  HP: {pet.get('hp', 0)}/{pet.get('hpMax', 0)}  MP: {pet.get('mp', 0)}/{pet.get('mpMax', 0)}")
        log.raw(f"  Damage: {pet.get('damage', 0)}  Defense: {pet.get('def', 0)}  Crit: {pet.get('crit', 0)}%")
        log.raw(f"  Power: {pet.get('power', 0)}  Potential: {pet.get('potential', 0)}")
        log.raw(f"  Stamina: {pet.get('stamina', 0)}/{pet.get('staminaMax', 0)}")
        status_names = {0: "Follow", 1: "Protect", 2: "Attack", 3: "Gohome", 4: "Fusion"}
        st = pet.get('status', 0)
        log.raw(f"  Status: {status_names.get(st, st)}")
        body = pet.get('items_body', [])
        if body:
            log.raw(f"  Equipment:")
            for i, item in enumerate(body):
                if item:
                    info = item.get('info', '').strip()
                    line = f"    [{i}] [#{item['id']}] {item_name(item['id'])} x{item['quantity']}"
                    if info:
                        line += f"\n      {info}"
                    log.raw(line)
        skills = pet.get('skills', [])
        if skills:
            log.raw(f"  Skills:")
            for sk in skills:
                if sk.get('id') == -1:
                    log.raw(f"    [Locked] {sk.get('locked', '')}")
                else:
                    log.raw(f"    Skill ID: {sk['id']}")
