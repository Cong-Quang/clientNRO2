import time
import sys
from logger import log, LogLevel, CATEGORIES, CAT_ALIAS
from client import GameClient
from npcs_data import npc_name
from items_data import item_name
from item_detail import format_item_detail, format_item_short, find_item_by_id, analyze_item


class ConsoleUI:
    def __init__(self, client: GameClient, initial_commands: list[str] = None,
                 auto_exit: bool = False, username: str = '1', password: str = '1'):
        self.client = client
        self.initial_commands = initial_commands or []
        self.auto_exit = auto_exit
        self._username = username
        self._password = password

    def run(self):
        log.auto_config()
        if log._compact:
            log.raw("=== NRO CLI (compact mode) ===")
        else:
            log.raw("=== NRO CLI Client ===")
        self._wait_ready()
        self._send_auto_login()

        # Wait for login to complete and character to be in game
        self._wait_in_game()

        # Execute initial commands from --cmd args
        if self.initial_commands:
            log.raw("")
            log.raw(f"[CLI] Thuc thi {len(self.initial_commands)} lenh tu command-line...")
            for cmd_str in self.initial_commands:
                log.raw(f"[CLI] > {cmd_str}")
                self._handle_input(cmd_str.strip())
                import time
                time.sleep(0.3)
            if self.auto_exit:
                log.raw("[CLI] Da thuc thi xong, thoat.")
                return

        self._print_help()
        self._input_loop()

    def _wait_in_game(self, timeout: float = 20.0):
        """Cho den khi nhan vat vao game + co map data hoac timeout."""
        import time
        for _ in range(int(timeout / 0.2)):
            s = self.client.state
            if s.in_game and s.map_id >= 0:
                return
            time.sleep(0.2)

    def _wait_ready(self, timeout: float = 3.0):
        for _ in range(int(timeout / 0.1)):
            if self.client.session.isConnected():
                return
            time.sleep(0.1)
        if not self.client.session.isConnected():
            log.error("CLIENT", "Failed to connect!")
            sys.exit(1)

    def _send_auto_login(self):
        log.info("LOGIN", f"Logging in as {self._username}...")
        self.client.service.login(self._username, self._password)

    def _print_help(self):
        log.raw("  /login <u> <p>   /select <name>")
        log.raw("  /chat <t>        /move <x> <y>")
        log.raw("  /useitem <t> <w> <i>  /pick <id>")
        log.raw("  /npcmenu <id>    /menu <opt>")
        log.raw("  /zone <id>       /changemap")
        log.raw("  /skill <id>      /buy <t> <id> [qty]")
        log.raw("  /sale <a> <t> <id>  /task <n> <m> [o]")
        log.raw("  /players  /info  /map  /npcs  /mobs")
        log.raw("  /items  /equip  /pet  /item <idx>  /finditem <id>")
        log.raw("  /selectmap <n>   /xmap <mapId>   /xmapstop")
        log.raw("  /heal  /gocit  /wake  /log <cat> on|off|debug")
        log.raw("  === AUTO ===")
        log.raw("  /autotrain on|off  /trainmob all|add <id>|list|clear")
        log.raw("  /goback on|off     /autozone on|off|spam")
        log.raw("  /autoskill attack  /autoskill list  /autoskill all")
        log.raw("  /autoskill <slot> on|off|delay <ms>|freeze|set <id> [name]")
        log.raw("  /autopick on|off     /autopick all|list|distance|teleport")
        log.raw("  /autopick add|delete <id>|clear|by_list")
        log.raw("  /vutdo on|off        /vutdo add|delete|list|clear")
        log.raw("  /autoboss on|off        /autoboss do|gim|tele|attack")
        log.raw("  /autoboss list           /autoboss add|remove <name>|clear")
        log.raw("  /autonappa on|off|cycle|list")
        log.raw("  /bosslog [phut]    /tail")
        log.raw("  /quit\n")

    def _input_loop(self):
        while self.client.session.isConnected():
            try:
                s = self.client.state
                npc_id = s.current_npc_id
                auto_tags = []
                if s.auto_train and s.auto_train.enabled:
                    auto_tags.append("TRAIN")
                if s.auto_vutdo and s.auto_vutdo.enabled:
                    auto_tags.append("VUT")
                has_boss_active = s.auto_boss and (s.auto_boss.do_boss or s.auto_boss.gim_boss or s.auto_boss.tele_boss or s.auto_boss.attack_boss)
                has_boss_in_map = s.boss_tracker and s.boss_tracker.has_boss_in_map()
                if has_boss_active or has_boss_in_map:
                    auto_tags.append("BOSS")
                if s.xmap_runner and s.xmap_runner.is_running():
                    st = s.xmap_runner.status
                    prompt = f"xmap({st})> " if st else "xmap> "
                elif auto_tags:
                    prompt = f"[{' '.join(auto_tags)}]> "
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
        if cmd == '/mobs':
            self._show_mobs()
            return
        if cmd == '/players':
            self._show_players()
            return
        if cmd == '/info':
            self._show_info()
            return

        # === ITEM COMMANDS ===
        if cmd == '/items':
            self.client.service.getBag(0)
            self._show_items()
            return
        if cmd in ('/item', '/i') and len(parts) >= 2:
            self._show_item_detail(parts)
            return
        if cmd in ('/finditem', '/fi') and len(parts) >= 2:
            self._find_item(parts)
            return
        if cmd == '/useitem' and len(parts) == 2:
            self._quick_use_item(parts)
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

        # === AUTO COMMANDS ===
        if cmd == '/autotrain':
            self._handle_autotrain(parts)
            return
        if cmd == '/trainmob':
            self._handle_trainmob(parts)
            return
        if cmd == '/goback':
            self._handle_goback(parts)
            return
        if cmd == '/autozone':
            self._handle_autozone(parts)
            return
        if cmd == '/autoskill':
            self._handle_autoskill(parts)
            return
        if cmd == '/vutdo':
            self._handle_vutdo(parts)
            return
        if cmd == '/autopick':
            self._handle_autopick(parts)
            return
        if cmd == '/picklist':
            self._handle_picklist(parts)
            return
        if cmd == '/autoboss':
            self._handle_autoboss(parts)
            return
        if cmd == '/autonappa':
            self._handle_autonappa(parts)
            return
        if cmd == '/bosslog':
            self._handle_bosslog(parts)
            return
        if cmd == '/bosssightings':
            self._handle_bosslog(parts)
            return
        if cmd == '/tail':
            self._handle_tail(parts)
            return

        # === XMAP COMMANDS ===
        if cmd == '/xmap' and len(parts) >= 2:
            from xmap_runner import XmapRunner
            from xmap_pathfinder import find_path, get_error_message
            cl = self.client
            target = int(parts[1])
            if cl.state.xmap_runner is None:
                cl.state.xmap_runner = XmapRunner(cl.state, cl.service)
            if cl.state.xmap_runner.is_running():
                log.raw("Xmap dang chay, dung /xmapstop de dung")
                return
            if target == cl.state.map_id:
                log.raw(f"Da den map {target}!")
                return
            me = cl.state.my_char
            power = me.cPower if me else 0
            path = find_path(cl.state.map_id, target, power=power)
            if not path:
                err = get_error_message(target, cl.state.map_id, power=power)
                log.raw(f"Xmap: {err}")
                return
            cl.state.xmap_runner.start(target)
            log.raw(f"Xmap: bat dau di den map {target}")
            return
        if cmd == '/xmapstop':
            if self.client.state.xmap_runner:
                self.client.state.xmap_runner.stop()
            log.raw("Xmap: da dung")
            return
        if cmd == '/xmapmenu':
            from xmap_data import PLANETS
            log.raw("Chon hanh tinh (dung /xmap <id> truc tiep hoac xem danh sach):")
            for name, maps in PLANETS.items():
                ids = ', '.join(str(m) for m in maps)
                log.raw(f"  {name}: {ids}")
            return
        if cmd == '/xmapsettings':
            r = self.client.state.xmap_runner
            if r:
                r.eat_chicken = not r.eat_chicken
                r.use_capsule = not r.use_capsule if len(parts) > 1 and parts[1] == 'capsule' else r.use_capsule
                log.raw(f"An dui ga: {'ON' if r.eat_chicken else 'OFF'} | Capsule: {'ON' if r.use_capsule else 'OFF'}")
            else:
                log.raw("Xmap chua duoc khoi tao, dung /xmap <id> truoc")
            return
        if cmd == '/xmapinfo':
            self._show_xmap_info()
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
                    log.raw(f"[NPC] {found} (ID={npc_id}) khong co o map nay")
                    log.raw(f"  Dung /npcs de xem NPC hien co")
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
                    log.raw(f"Chon tu 0 den {len(c.state.map_transport_list)-1}")
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

    # ====================================================================
    # AUTO COMMANDS
    # ====================================================================

    def _handle_autotrain(self, parts):
        """Handle /autotrain [on|off|hpabove <n>|hpbelow <n>|minmp <n>]"""
        t = self.client.state.auto_train
        if not t:
            log.raw("[Train] AutoTrain chua duoc khoi tao")
            return

        if len(parts) == 1:
            # Toggle
            enabled = t.toggle()
            log.raw(f"[Train] Auto Train: {'BAT' if enabled else 'TAT'}")
            return

        sub = parts[1].lower()
        if sub == 'on':
            t.enabled = True
            log.raw("[Train] Auto Train: BAT")
        elif sub == 'off':
            t.enabled = False
            t._current_mob_id = -1
            log.raw("[Train] Auto Train: TAT")
        elif sub == 'hpabove' and len(parts) >= 3:
            t.set_hp_above(int(parts[2]))
        elif sub == 'hpbelow' and len(parts) >= 3:
            t.set_hp_below(int(parts[2]))
        elif sub == 'minmp' and len(parts) >= 3:
            t.set_min_mp(int(parts[2]))
        else:
            log.raw("Usage: /autotrain [on|off|hpabove <n>|hpbelow <n>|minmp <n>]")

    def _handle_trainmob(self, parts):
        """Handle /trainmob all|add <id>|list|clear"""
        t = self.client.state.auto_train
        if not t:
            log.raw("[Train] AutoTrain chua duoc khoi tao")
            return

        if len(parts) < 2:
            log.raw("Usage: /trainmob all|add <id>|list|clear")
            return

        sub = parts[1].lower()
        if sub == 'all':
            t.train_all_mobs()
        elif sub == 'add' and len(parts) >= 3:
            t.add_mob(int(parts[2]))
        elif sub == 'list':
            t.list_mobs()
        elif sub == 'clear':
            t.clear_mobs()
        else:
            log.raw("Usage: /trainmob all|add <id>|list|clear")

    def _handle_goback(self, parts):
        """Handle /goback [on|off|coord]"""
        t = self.client.state.auto_train
        if not t:
            log.raw("[Train] AutoTrain chua duoc khoi tao")
            return

        if len(parts) < 2:
            t.toggle_goback()
            return

        sub = parts[1].lower()
        if sub == 'on':
            t.goback_enabled = True
            log.raw("[Train] Goback: BAT")
        elif sub == 'off':
            t.goback_enabled = False
            log.raw("[Train] Goback: TAT")
        elif sub == 'coord':
            t.toggle_goback_coord()
        else:
            log.raw("Usage: /goback [on|off|coord]")

    def _handle_autozone(self, parts):
        """Handle /autozone [on|off|spam]"""
        t = self.client.state.auto_train
        if not t:
            log.raw("[Train] AutoTrain chua duoc khoi tao")
            return

        if len(parts) < 2:
            t.toggle_auto_zone()
            return

        sub = parts[1].lower()
        if sub == 'on':
            t.auto_change_zone = True
            t.spam_change_zone = False
            log.raw("[Train] Auto doi khu: BAT")
        elif sub == 'off':
            t.auto_change_zone = False
            t.spam_change_zone = False
            log.raw("[Train] Auto doi khu: TAT")
        elif sub == 'spam':
            t.spam_change_zone = True
            t.auto_change_zone = False
            log.raw("[Train] Spam doi khu: BAT")
        else:
            log.raw("Usage: /autozone [on|off|spam]")

    def _handle_autoskill(self, parts):
        """Handle /autoskill [attack|list|<slot> on|off|delay <ms>|freeze|set <id> [name]]"""
        sk = self.client.state.auto_skill
        if not sk:
            log.raw("[Skill] AutoSkill chua duoc khoi tao")
            return

        if len(parts) < 2:
            # Toggle auto attack
            sk.toggle_auto_attack()
            return

        sub = parts[1].lower()

        if sub == 'attack':
            sk.toggle_auto_attack()
        elif sub == 'list':
            sk.list_skills()
        elif sub == 'shield':
            sk.toggle_auto_shield()
        elif sub == 'all':
            # Bật/tắt tất cả slot
            for i in range(sk.MAX_SKILL_SLOTS):
                sk.auto_skills[i] = not sk.auto_skills[i]
            log.raw("[Skill] Da toggle tat ca slot")
        elif sub.isdigit() or (len(parts) >= 3 and parts[1].isdigit()):
            # /autoskill <slot> <subcommand>
            slot = int(parts[1])
            if slot < 0 or slot >= sk.MAX_SKILL_SLOTS:
                log.raw(f"[Skill] Slot phai tu 0 den {sk.MAX_SKILL_SLOTS-1}")
                return

            if len(parts) < 3:
                # Toggle slot
                sk.toggle_slot(slot)
                return

            action = parts[2].lower()
            if action == 'on':
                sk.auto_skills[slot] = True
                sid = sk.skill_ids[slot]
                name = sk.skill_names[slot] or (f"Skill_{sid}" if sid else f"Slot {slot}")
                log.raw(f"[Skill] Auto [{slot}] {name}: BAT")
            elif action == 'off':
                sk.auto_skills[slot] = False
                log.raw(f"[Skill] Auto [{slot}]: TAT")
            elif action == 'delay' and len(parts) >= 4:
                sk.set_delay(slot, int(parts[3]))
            elif action == 'freeze':
                sk.toggle_freeze(slot)
            elif action == 'set' and len(parts) >= 4:
                skill_id = int(parts[3])
                name = ' '.join(parts[4:]) if len(parts) > 4 else ""
                sk.configure_slot(slot, skill_id, name)
            else:
                log.raw(f"Usage: /autoskill {slot} on|off|delay <ms>|freeze|set <id> [name]")
        else:
            log.raw("Usage: /autoskill [attack|list|shield|all|<slot> ...]")

    # ====================================================================
    # AUTO PICK
    # ====================================================================

    def _handle_autopick(self, parts):
        """Handle /autopick [on|off|all|by_list|list|distance <n>|teleport|add <id>|delete <id>|clear]"""
        p = self.client.state.auto_pick
        if not p:
            log.raw("[Pick] AutoPick chua duoc khoi tao")
            return

        if len(parts) < 2:
            p.toggle()
            return

        sub = parts[1].lower()
        if sub == 'on':
            if not p.enabled:
                p.toggle()
        elif sub == 'off':
            if p.enabled:
                p.toggle()
        elif sub == 'all':
            p.toggle_pick_all()
        elif sub == 'list':
            log.raw(f"[Pick] Trang thai: {'ON' if p.enabled else 'OFF'}")
            log.raw(f"  Nhat tat ca: {'ON' if p.pick_all else 'OFF'}")
            log.raw(f"  Nhat theo danh sach: {'ON' if p.pick_by_list else 'OFF'}")
            log.raw(f"  Dich chuyen den item: {'ON' if p.teleport_to_item else 'OFF'}")
            log.raw(f"  Khoang cach: {p.max_distance}px")
            log.raw(f"  So luong item trong danh sach: {len(p.pick_list)}")
            if p.pick_list:
                log.raw("  Dung /picklist de xem chi tiet")
        elif sub == 'distance' and len(parts) >= 3:
            try:
                d = int(parts[2])
                p.set_distance(d)
            except ValueError:
                log.raw("[Pick] So khong hop le")
        elif sub == 'teleport':
            p.toggle_teleport()
        elif sub == 'add' and len(parts) >= 3:
            try:
                item_id = int(parts[2])
                p.add_to_list(item_id)
            except ValueError:
                log.raw("[Pick] ID khong hop le")
        elif sub == 'delete' and len(parts) >= 3:
            try:
                item_id = int(parts[2])
                p.remove_from_list(item_id)
            except ValueError:
                log.raw("[Pick] ID khong hop le")
        elif sub == 'clear':
            p.clear_list()
        elif sub == 'by_list':
            p.toggle_pick_by_list()
        else:
            log.raw("Usage: /autopick [on|off|all|by_list|list|distance <n>|teleport|add <id>|delete <id>|clear]")

    def _handle_picklist(self, parts):
        """Handle /picklist - Xem danh sach item duoc nhat"""
        p = self.client.state.auto_pick
        if not p:
            log.raw("[Pick] AutoPick chua duoc khoi tao")
            return
        p.list_items()

    # ====================================================================
    # AUTO BOSS
    # ====================================================================

    def _handle_autoboss(self, parts):
        """Handle /autoboss [on|off|do|gim|tele|attack|list|add <name>|remove <name>|clear]"""
        b = self.client.state.auto_boss
        if not b:
            log.raw("[Boss] AutoBoss chua duoc khoi tao")
            return

        if len(parts) < 2:
            b.list_status()
            return

        sub = parts[1].lower()
        if sub == 'on':
            if not b.do_boss:
                b.toggle_do_boss()
        elif sub == 'off':
            b.do_boss = False
            b.gim_boss = False
            b.tele_boss = False
            b.attack_boss = False
            log.info("BOSS", "Da tat tat ca chuc nang Boss")
        elif sub == 'do':
            b.toggle_do_boss()
        elif sub == 'gim':
            b.toggle_gim_boss()
        elif sub == 'tele':
            b.toggle_tele_boss()
        elif sub == 'attack':
            b.toggle_attack_boss()
        elif sub == 'list':
            b.list_status()
        elif sub == 'add' and len(parts) >= 3:
            name = ' '.join(parts[2:])
            b.add_target(name)
        elif sub == 'remove' and len(parts) >= 3:
            name = ' '.join(parts[2:])
            b.remove_target(name)
        elif sub == 'clear':
            b.clear_targets()
        else:
            log.raw("Usage: /autoboss [on|off|do|gim|tele|attack|list|add <name>|remove <name>|clear]")

    # ====================================================================
    # AUTO FARM NAPPA
    # ====================================================================

    def _handle_autonappa(self, parts):
        """Handle /autonappa [on|off|kuku|daudinh|rambo|cycle|list]"""
        n = self.client.state.auto_farm_nappa
        if not n:
            log.raw("[Nappa] AutoFarmNappa chua duoc khoi tao")
            return

        if len(parts) < 2:
            n.list_status()
            return

        sub = parts[1].lower()
        if sub == 'on':
            if not n.enabled:
                n.start(n.boss_type)
        elif sub == 'off':
            if n.enabled:
                n.stop()
        elif sub == 'kuku':
            if n.enabled:
                n.stop()
            n.start(0)
        elif sub == 'daudinh':
            if n.enabled:
                n.stop()
            n.start(1)
        elif sub == 'rambo':
            if n.enabled:
                n.stop()
            n.start(2)
        elif sub == 'cycle':
            n.cycle_type()
        elif sub == 'list':
            n.list_status()
        else:
            log.raw("Usage: /autonappa [on|off|kuku|daudinh|rambo|cycle|list]")

    # ====================================================================
    # BOSS TRACKER
    # ====================================================================

    def _handle_bosslog(self, parts):
        """Handle /bosslog [phut] - Xem boss da xuat hien"""
        bt = self.client.state.boss_tracker
        if not bt:
            log.raw("[Tracker] BossTracker chua duoc khoi tao")
            return
        minutes = 60
        if len(parts) >= 2:
            try:
                minutes = int(parts[1])
            except ValueError:
                pass
        bt.list_sightings(minutes)

    def _handle_tail(self, parts):
        """
        Handle /tail - Xem realtime boss tracker log (giong tail -f)
        
        Tu dong lam moi moi 3 giay, hien thi boss sightings moi nhat.
        Nhan Ctrl+C de thoat.
        """
        bt = self.client.state.boss_tracker
        if not bt:
            log.raw("[Tracker] BossTracker chua duoc khoi tao")
            return
        
        log.raw("[Tail] Boss tracker realtime - nhan Ctrl+C de thoat")
        log.raw("")
        
        last_count = -1
        try:
            while self.client.session.isConnected():
                time.sleep(3.0)
                
                sightings = bt.get_sightings()
                current_count = len(sightings)
                
                if current_count != last_count:
                    log.raw("\n" * 3)
                    log.raw(f"[Tail] Boss tracker realtime - Ctrl+C de thoat ({current_count} sightings)")
                    if current_count == 0:
                        log.raw("  (chua co boss nao duoc ghi nhan)")
                    else:
                        now = time.time()
                        for s in sightings[:10]:
                            elapsed = now - s['time']
                            if elapsed < 60:
                                time_str = f"{int(elapsed)}giay"
                            elif elapsed < 3600:
                                time_str = f"{int(elapsed // 60)}p{int(elapsed % 60)}s"
                            else:
                                time_str = f"{int(elapsed // 3600)}h{int((elapsed % 3600) // 60)}p"
                            hp_str = f" HP={s['hp']}" if s['hp'] else ""
                            log.raw(f"  {s['name']}{hp_str} - {time_str} truoc - Map {s['map_name']}({s['map_id']}) Khu {s['zone_id']} ({s['x']},{s['y']})")
                    last_count = current_count
        except KeyboardInterrupt:
            log.raw("")
            log.raw("[Tail] Da thoat")

    # ====================================================================
    # MOBS DISPLAY
    # ====================================================================

    def _show_mobs(self):
        mobs = self.client.state.mobs
        if not mobs:
            log.raw("[Mobs] Khong co quai nao hoac chua co du lieu")
            return
        log.raw(f"[Mobs] {len(mobs)} quai tren map:")
        for m in mobs:
            tid = m.get('templateId', -1)
            mid = m.get('id', -1)
            hp = m.get('hp', 0)
            maxhp = m.get('maxHp', 0)
            status = m.get('status', 0)
            x = m.get('x', 0)
            y = m.get('y', 0)
            status_name = {0: "chet", 1: "chetBay", 2: "dung", 3: "tanCong", 4: "dungBay", 5: "di", 6: "roi", 7: "biDanh"}
            st = status_name.get(status, str(status))
            log.raw(f"  [{mid}] Template={tid} HP={hp}/{maxhp} ({st}) at ({x},{y})")

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

    # ====================================================================
    # ITEM DETAIL COMMANDS
    # ====================================================================

    def _show_item_detail(self, parts):
        index = int(parts[1])
        s = self.client.state
        items = s.items_bag
        if not items:
            log.raw("[Item] Chua co du lieu hanh trang. Dung /items de load.")
            return
        if index < 0 or index >= len(items):
            log.raw(f"[Item] Index {index} khong hop le. Hanh trang co {len(items)} o.")
            return
        item = items[index]
        if item is None:
            log.raw(f"[Item] O {index} trong.")
            return
        detail = format_item_detail(item, index=index, location="bag")
        log.raw("[Item] Chi tiet:")
        for line in detail.split("\n"):
            log.raw(line)

    def _find_item(self, parts):
        item_id = int(parts[1])
        s = self.client.state
        result = find_item_by_id(s, item_id)
        name = item_name(item_id)
        if not result['found']:
            log.raw(f"[Find] Khong tim thay {name} (ID={item_id}) trong balo/body/ruong.")
            return
        log.raw(f"[Find] {name} (ID={item_id}): tim thay {len(result['items'])} cai")
        for entry in result['items']:
            loc = entry['location']
            idx = entry['index']
            item = entry['item']
            short = format_item_short(item, index=idx)
            log.raw(f"  [{loc.upper()}] {short}")
        log.raw(f"  Dung /item {result['items'][0]['index']} de xem chi tiet (neu o bag)")

    def _quick_use_item(self, parts):
        index = int(parts[1])
        s = self.client.state
        items = s.items_bag
        if not items or index < 0 or index >= len(items):
            log.raw(f"[Use] Index {index} khong hop le.")
            return
        item = items[index]
        if item is None:
            log.raw(f"[Use] O {index} trong.")
            return
        item_id = item['id']
        name = item_name(item_id)
        log.raw(f"[Use] Dung {name} (ID={item_id}) tu bag slot {index}...")
        self.client.service.useItem(0, 1, index)

    # ====================================================================
    # ITEM DISPLAY
    # ====================================================================

    def _format_item(self, item: dict, index: int = -1) -> str:
        return format_item_short(item, index=index)

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
                short = format_item_short(item, index=idx)
                log.raw(f"  {short}")
        log.raw("  Dung /item <index> de xem chi tiet")

    def _show_equip(self):
        s = self.client.state
        items = s.items_body
        if not items:
            log.raw("[Equip] No data (use /getbody to request)")
            return
        SLOT_NAMES = ["Ao", "Quan", "Gang", "Giay", "Nhan", "Cai trang", "Chi boi", "Vu khi", "Lien", "Ngu"]
        log.raw("[Equip] Equipped items:")
        for i, item in enumerate(items):
            slot_name = SLOT_NAMES[i] if i < len(SLOT_NAMES) else f"Slot{i}"
            if item:
                short = format_item_short(item)
                detail = analyze_item(item)
                stars = ""
                if detail['star_display']:
                    stars = f"  {detail['star_display']}"
                log.raw(f"  [{slot_name}] {short}{stars}")
                if detail['options']:
                    opts = " | ".join(detail['options'][:5])
                    log.raw(f"       {opts}")
                    if len(detail['options']) > 5:
                        log.raw(f"       ... va {len(detail['options'])-5} chi so khac")
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
            log.raw("  Equipment:")
            for i, item in enumerate(body):
                if item:
                    detail = analyze_item(item)
                    short = format_item_short(item, index=i)
                    stars = ""
                    if detail['star_display']:
                        stars = f"  {detail['star_display']}"
                    log.raw(f"    {short}{stars}")
                    if detail['options']:
                        for opt in detail['options'][:3]:
                            log.raw(f"      {opt}")
                        if len(detail['options']) > 3:
                            log.raw(f"      ...(+{len(detail['options'])-3})")
                else:
                    log.raw(f"    [{i}] (empty)")
        skills = pet.get('skills', [])
        if skills:
            log.raw("  Skills:")
            for sk in skills:
                if sk.get('id') == -1:
                    log.raw(f"    [Locked] {sk.get('locked', '')}")
                else:
                    log.raw(f"    Skill ID: {sk['id']}")

    # ---------------------------------------------------------------------------
    # XMAP INFO
    # ---------------------------------------------------------------------------
    MOVE_TYPE_NAMES = {
        0: "Waypoint",
        1: "NPC menu",
        2: "NPC index",
        3: "Item",
        4: "Walk",
    }

    def _show_xmap_info(self):
        s = self.client.state
        r = s.xmap_runner
        from xmap_pathfinder import find_path_with_cost, get_next_link, find_path_bfs
        from xmap_data import get_map_name
        me = s.my_char
        power = me.cPower if me else 0
        current_map = s.map_id
        if r is None:
            log.raw("[Xmap] Xmap chua duoc khoi tao. Dung /xmap <mapId> truoc.")
            return
        target_map = r.target_map
        if target_map < 0 or (not r.is_running() and not r.path):
            log.raw("[Xmap] Xmap chua chay hoac chua co target. Dung /xmap <mapId> truoc.")
            return
        recalc_path, astar_cost = find_path_with_cost(current_map, target_map, power=power)
        bfs_path = find_path_bfs(current_map, target_map, power=power)
        bfs_hops = len(bfs_path) - 1 if bfs_path else 0
        is_running = r.is_running()
        header = f"[Xmap] Map hien tai: {current_map} -> Target: {target_map}"
        if is_running:
            header += f"  ({r.status})"
        else:
            header += "  (da dung)"
        log.raw(header)
        if is_running:
            log.raw(f"  Settings: Capsule={'ON' if r.use_capsule else 'OFF'} | Ga={'ON' if r.eat_chicken else 'OFF'} | Delay={r.map_delay}s")
        if not recalc_path:
            log.raw("  (khong tim thay duong di)")
            return
        log.raw(f"  Path A*:   {' -> '.join(str(m) for m in recalc_path)}")
        log.raw(f"  Cost A*:   {astar_cost}")
        if bfs_path:
            log.raw(f"  Path BFS:  {' -> '.join(str(m) for m in bfs_path)}")
            log.raw(f"  Hops BFS:  {bfs_hops}")
            if recalc_path != bfs_path:
                log.raw("  A* chon duong khac BFS (toi uu cost, khong nhat thiet ngan nhat)")
        if is_running and r.path and recalc_path != r.path:
            log.raw(f"  Path luu:  {' -> '.join(str(m) for m in r.path)} (da thay doi do di chuyen)")
        log.raw("")
        log.raw("  Cac buoc di chuyen:")
        for i in range(len(recalc_path) - 1):
            fm = recalc_path[i]
            to = recalc_path[i + 1]
            link = get_next_link(fm, to)
            fm_name = get_map_name(fm) or f"Map {fm}"
            to_name = get_map_name(to) or f"Map {to}"
            if link:
                mtype = self.MOVE_TYPE_NAMES.get(link.move_type, f"Loai {link.move_type}")
                cost = self._get_move_cost(link.move_type)
                detail = self._link_detail(link)
                log.raw(f"    {i+1}. {fm_name}({fm}) -> {to_name}({to})")
                log.raw(f"       Loai: {mtype} (cost={cost}) {detail}")
            else:
                log.raw(f"    {i+1}. {fm_name}({fm}) -> {to_name}({to}) [KHONG CO LINK]")

    def _get_move_cost(self, move_type: int) -> int:
        from xmap_pathfinder import MOVE_COST
        return MOVE_COST.get(move_type, 5)

    def _link_detail(self, link) -> str:
        parts = []
        if link.npc_id >= 0:
            npc_name_str = npc_name(link.npc_id) or f"NPCBoss {link.npc_id}"
            parts.append(f"npc={npc_name_str}(ID={link.npc_id})")
        if link.menus:
            parts.append(f"menus={link.menus}")
        if link.item_id >= 0:
            parts.append(f"item={link.item_id}")
        if link.walk_x >= 0 or link.walk_y >= 0:
            parts.append(f"walk=({link.walk_x},{link.walk_y})")
        if link.move_type == 0:
            side = "trai" if link.wp_pos == -1 else "phai" if link.wp_pos == 1 else "giua"
            parts.append(f"waypoint={side}")
        return " | ".join(parts) if parts else ""
