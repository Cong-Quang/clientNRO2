# Memory - NRO CLI Client

## Session 2 - NPC interaction, gold, name fix

### Các thay đổi

**handlers/world.py**
- `handle_player_add`: thêm `c.cName = name` trong `if` branch (không chỉ `elif`) vì `handle_me_load_point` tạo `my_char` trước với name rỗng
- Fix so sánh name: dùng `name.endswith(my_name)` để bỏ qua clan prefix (`$ClanName`)
- `SUB_ME_LOAD_ALL` (sub=0): parse gold/gem/ruby từ initial load packet
- `SUB_ME_LOAD_INFO` (sub=4): parse gold/gem/hp/mp/ruby với try readLong fallback readInt
- `handle_send_money` (cmd=6): handler mới cho gold update trong game

**handlers/authentication.py**
- `handle_not_map` sub=CMD_SELECT_PLAYER: tạo `my_char` với `cName` từ response
- Bỏ debug log

**handlers/interaction.py**
- `handle_confirm`: đọc `readUTF` (NPC dialogue) trước khi đọc option count, hiển thị dialogue + options
- Lưu `state.current_npc_id` khi nhận menu

**service.py**
- `openMenu(npcId)`: sửa thành `cmd=33 + writeShort(npcId)` — khớp C# client (trước gửi sai notMap+27)

**state.py**
- Thêm `current_npc_id`, `current_menu_index`

**ui.py**
- `/menu <opt>`: chọn option từ NPC dialog (dùng `confirmMenu` với `current_npc_id`)
- Giữ `/menu <n> <m> <o>` cho menu đặc biệt
- Sửa help text

**logger.py**
- Tách `_log_enabled` khỏi `_enabled`: `raw()` luôn chạy, chỉ log (info/debug/warn/error) bị tắt
- `_safe_print()`: fallback UTF-8 khi console không hiển thị được Unicode

**main.py**
- Thêm `atexit.register(_cleanup)` — tự động xóa `__pycache__` khi thoát
- Tắt log bằng `log._log_enabled = False`

**.gitignore**
- Python cache, IDE, OS files, test scripts

### NPC Interaction Flow
1. `/npcmenu <templateId>` → gửi `cmd=33 + short(templateId)`
2. Server lookup NPC theo templateId trong zone, gọi `openBaseMenu()`
3. Server trả `cmd=32` (CONFIRM) với: `short(tempId) + UTF(dialogue) + byte(count) + UTF[](options)`
4. Client hiển thị dialogue + options
5. `/menu <n>` → gửi `cmd=32 + short(tempId) + byte(select)` — dùng `current_npc_id` (tempId) đã lưu
6. Server xử lý select, trả submenu mới (lại cmd=32) hoặc mở shop (cmd=-46) hoặc kết thúc

### /map command
- `/map` → hiển thị tên map + ID + zone
- `handle_map_info` parse thêm: planetId, tileId, bgId, mapType, mapName (UTF)

### /npcs command
- `/npcs` → liệt kê NPC trong map kèm tên, tempId, tọa độ
- `npcs_data.py`: lookup table NPC template ID → tên tiếng Việt (từ SQL dump database team2026.sql)
- `handle_map_info` parse NPC section từ map info packet (sau mobs, trước items)

### Vấn đề còn lại
- Console Windows cp1252 không hiển thị được Vietnamese Unicode → đã fallback an toàn
- Chưa xử lý inventory, skill list, NPC shop UI

### Relevant Files
- `handlers/world.py`: ME_LOAD_POINT, PLAYER_ADD, SUB_COMMAND, sendMoney
- `handlers/authentication.py`: char_list, not_map
- `handlers/interaction.py`: confirm (NPC menu display), menu handlers
- `state.py`: GameState (players, npcs, my_char, current_npc_id)
- `Char.py`: Character class + _fmt number formatting
- `logger.py`: Unicode-safe print, separate log/raw flags
- `service.py`: openMenu (fix), confirmMenu, menu
- `ui.py`: /npcmenu, /menu commands
- `client.py`: dispatcher mapping
- `cmd.py`: command constants
