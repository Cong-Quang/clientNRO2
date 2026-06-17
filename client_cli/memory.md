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

## Session 3 - Shop, items, pet, inventory display

### Các thay đổi

**items_data.py (MỚI)**
- 2000+ item template names extracted từ SQL dump (`database team2026.sql`)
- `item_name(id)` helper function

**handlers/interaction.py**
- `handle_shop`: parse đầy đủ shop packet (cmd=-44) gồm tabs, items, options, part data
- Hỗ trợ shop types: 0 (vàng/ngọc), 1 (tiềm năng), 2 (ký gửi), 3 (đặc biệt), 4 (vòng quay), 8 (mua lại)
- Hiển thị tên item + giá (vàng/ngọc) trong shop
- `_parse_items()`: helper parse danh sách items (chung cho bag/body/box)
- `handle_body`/`handle_bag`/`handle_box`: parse đầy đủ items + options, lưu vào state
- `handle_hide_wait_dialog` (cmd=-99): hiển thị "[NPC] Không có NPC nào ở đây"

**handlers/world.py**
- `handle_sub_command` SUB_ME_LOAD_ALL: parse thêm body[], bag[], box[] items sections sau gold/gem/ruby

**handlers/social.py**
- `handle_pet_info` sub=2: parse đầy đủ pet info (body items, HP/MP, damage, name, power, potential, stamina, skills)

**state.py**
- Thêm `items_bag`, `items_body`, `items_box`, `pet`

**ui.py**
- `/items` → hiển thị balo + options (tự động request bag từ server)
- `/equip` → hiển thị đồ đang mặc theo slot (Áo/Quần/Găng/Giày/Nhẫn/...)
- `/pet` → hiển thị thông tin pet (stats, equipment, skills)
- `/info` → thêm summary: số lượng items trong bag/body, có pet không
- Help text cập nhật thêm `/items`, `/equip`, `/pet`

**cmd.py**
- Thêm `CMD_HIDE_WAIT_DIALOG = -99 & 0xFF`

### Shop Flow
1. `/npcmenu <id>` → mở NPC
2. `/menu 0` hoặc `0` → chọn option "Cửa hàng"
3. Server gửi cmd=-44 (SHOP) → hiển thị tab + item + giá
4. `/buy <t> <itemId>` → mua đồ (`t=0`: vàng, `t=1`: ngọc)

### Item Options
- Mỗi item có list options: `{id, param}`
- Example: option id=0 là "sức đánh", param=1000 → "+sức đánh 1000"
- Server gửi kèm info string (text mô tả) trong mỗi item

### Packet: Bag/Body/Box (action=0)
```
byte: action
[if BODY: short: head]
byte: count
for each slot:
  short: template.id (or -1 = empty)
  if not empty:
    int: quantity
    UTF: info (description)
    UTF: content (requirement)
    byte: optionCount
    for each option:
      byte: optionTemplate.id
      short: param
```

### Packet: Pet Info (sub=2)
```
byte: sub (2)
short: avatar
byte: bodyCount
[body items... same format as above]
int: hp, hpMax, mp, mpMax, damage
UTF: name
UTF: level_str
long: power, potential
byte: status
short: stamina, staminaMax
byte: crit
short: def
byte: skillCount (5)
for each:
  short: skillId (or -1)
  if -1: UTF: reason
```

### README
- `README.md` — hướng dẫn chi tiết bằng tiếng Việt kèm ví dụ cụ thể

## Session 4 - Item display format, teleport/capsule handling

### Các thay đổi

**ui.py**
- `_format_item`: thêm `[index] [#id]` prefix (số thứ tự + item ID), options hiển thị từng dòng riêng từ `info` string
- `_show_items`: dùng enumerate để truyền index vào `_format_item`
- `_show_equip`: mỗi slot hiển thị item name + ID + options
- `_show_pet`: pet equipment hiển thị index + item ID
- Thêm `/selectmap <n>` command

**handlers/social.py**
- `handle_map_transport`: parse đầy đủ map names + planet names từ cmd=-91, hiển thị danh sách + hướng dẫn `/selectmap`

**state.py**
- Thêm `map_transport_list: list[str]` — lưu danh sách map names từ teleport

**service.py**
- Thêm `requestMapSelect(index)` — gửi cmd=-91 + byte(index) để chọn map

### Teleport/Capsule Flow
1. `/useitem 0 1 <index>` (hoặc `/useitem 0 1 -1 194`) → dùng capsule
2. Server gửi `cmd=-91 (MAP_TRASPORT)`: `byte count, utf[] names, utf[] planets`
3. Client hiển thị danh sách map
4. `/selectmap <n>` → gửi `cmd=-91 + byte(selectedIndex)`
5. Server teleport

### Packet: MAP_TRASPORT (cmd=-91)
**Server → Client:**
```
byte: count
for each: utf: mapName, utf: planetName
```

**Client → Server (chọn map):**
```
byte: selectedIndex
```

### Item display format
```
> /items
[Bag] 3 items:
  [0] [#33] Áo thun 3 lỗ x1
      +sức đánh 1000
      +giáp 500
  [1] [#6] Quần vải đen x1
      +HP 5000


