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
3. Server trả cmd=-44 (SHOP) → hiển thị tab + item + giá
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
```

## Session 5 - Xmap fixes (waypoint matching, teleport panel, zone-change loop)

### Các bugs đã fix

**Bug 1: isEnter/isOffline SWAPPED trong world.py**
- C# đọc `Waypoint(minX, minY, maxX, maxY, isEnter, isOffline, name)`
- Python cũ đọc `isOffline` trước, `isEnter` sau → SAI! Đã sửa

**Bug 2: Waypoint không match bằng popup name**
- C# `GetWayPoint()` match waypoint bằng popup name (tên map đích)
- Python cũ chỉ dùng vị trí (left/right/center) → sai trên map có nhiều waypoint
- Fix: thêm MAP_NAMES dictionary + match normalized popupName

**Bug 3: charMove luôn gửi byte=0**
- C# gửi byte=1 khi tile là ground (waypoint luôn trên ground)
- Fix: thêm type_ parameter, _move_to gửi type_=1 + 3 lần charMove như C# TeleportTo

**Bug 4: NPC name-based confirm bị deadlock**
- move_type=1: không gọi openMenu → server không gửi dialog → deadlock
- Fix: tự động gọi openMenu từ main loop sau init delay (giống C# UpdateConfirmNpc)

**Bug 5: Teleport panel (CMD_MAP_TRASPORT) block requestChangeMap**
- Server gửi panel trên một số map, không có cách close
- C#: `GameCanvas.isWait()` dừng xmap, capsule system xử lý panel
- Fix: thêm `_handle_teleport_panel()` với 3-tier matching tự động chọn destination

**Bug 6: Zone change reset retry_count → infinite loop**
- Trên map 19, requestChangeMap bị reject → zone change → on_map_changed reset retry_count → loop vô tận
- Fix: `on_map_changed` chỉ reset flow khi MAP thực sự thay đổi, ignore zone-only changes

**Bug 7: NPC spam trong lúc xmap**
- `[NPC] Không có NPC nào ở đây` xuất hiện mỗi khi requestChangeMap bị reject
- Fix: suppress log khi xmap đang chạy

### Các file đã sửa
- `handlers/world.py`: isEnter/isOffline order, waypoint update my_char
- `handlers/interaction.py`: suppress NPC spam khi xmap
- `handlers/social.py`: on_transport_panel call
- `xmap_data.py`: MAP_NAMES dictionary + get_map_name()
- `xmap_runner.py`: toàn bộ logic xmap (waypoint match, teleport panel, zone change fix)
- `xmap_pathfinder.py`: Cold error message
- `service.py`: charMove type_ parameter, getMapOffline
- `cmd.py`: CMD_MAP_OFFLINE

## Session 6 - Xmap fixes (NPC link 84→24, Y-tiebreaker, A* pathfinding)

### Bug 1: NPC link wrong — map 84 → 21 should be 84 → 24

**Vấn đề:**
- `xmap_data.py` có `add_npc_link(84, 21, npc=10, move_type=2, menus=[0])`
- NPC 10 (Tàu Vũ Trụ) trên map 84 (Siêu Thị), chọn "Đến Trái Đất" (index 0) thực tế gửi đến **map 24** (Rừng Bamboo), không phải map 21 (Nhà 1)
- Graph sai → pathfinder đi 84→21, server lại gửi 84→24. Từ 24 pathfinder lại 24→84 → **loop vô tận 24 ↔ 84**

**Fix:** `xmap_data.py`
```python
# CŨ (sai):
add_npc_link(84, 21, npc=10, move_type=2, menus=[0])
# MỚI (đúng):
add_npc_link(84, 24, npc=10, move_type=2, menus=[0])
```

### Bug 2: Teleport panel interfere với NPC interaction

**Vấn đề:**
- Khi xmap đang gọi NPC (move_type=2), server đôi khi gửi CMD_MAP_TRASPORT (teleport panel)
- Panel handler `_handle_teleport_panel()` can thiệp, chọn destination sai, phá flow NPC

**Fix:** `xmap_runner.py`
- Thêm `_in_npc_interaction` flag, set = True khi `_handle_npc` được gọi
- Panel handler chỉ chạy khi `not self._in_npc_interaction`
- Flag được clear ở:
  - `on_map_changed` (map change thành công)
  - NPC index delay hết (`_last_npc_index_time` reset)
  - NPC confirm timeout (`_confirm_npc_id = -1`)
  - Map change retry timeout

### Bug 3: Waypoint stacked theo chiều cao (Núi Fide, v.v.)

**Vấn đề:**
- Trên map Núi Fide (66) và một số map khác, có 2 exit waypoint **cùng tọa độ X** nhưng khác Y (độ cao)
- Popup name không match được (empty), code chọn theo X → chọn sai → đi nhầm map

**Fix:** `xmap_runner.py` — `_find_correct_waypoint()`
- Sau khi chọn waypoint theo X (wp_pos), kiểm tra xem có waypoint nào khác cùng X không
- Nếu có (>= 2 waypoint, sai lệch minX/maxX < 10px): dùng Y của nhân vật để chọn
- `min(same_x_wps, key=lambda wp: abs(wp['maxY'] - me.cy))`

### Bug 4: Capsule auto-use vẫn bật

**Vấn đề:**
- `use_capsule = True` mặc định, xmap tự dùng capsule nếu có trong balo
- Từng gây loop 84↔24 (đã fix ở Bug 1), nhưng người dùng vẫn muốn giữ auto-use

**Kết luận:**
- Cơ chế hiện tại đã đúng: `_try_use_capsule` kiểm tra `_get_item_in_bag(194/193)`, nếu không có capsule thì skip
- Giữ `MIN_PATH_LENGTH_FOR_CAPSULE = 4` (theo yêu cầu user)

### Cải tiến: A* Pathfinding

**Vấn đề:**
- BFS tìm đường ngắn nhất theo số hop, không phân biệt waypoint (dễ) vs NPC (khó)
- Có thể chọn path nhiều NPC thay vì đường dài hơn nhưng toàn waypoint

**Fix:**
- `xmap_pathfinder.py`: BFS → **A\*** với weighted costs

**Chi phí mỗi loại di chuyển (MOVE_COST):**
```
waypoint(0) = 1  (rẻ nhất, ưu tiên)
walk(4)     = 2
npc_index(2)= 3  (nhanh, ít lỗi)
npc_menu(1) = 5  (chậm, dễ fail)
item(3)     = 10 (tốn item)
```

**Heuristic (admissible):**
- Precompute BFS shortest path distances cho tất cả cặp node (~180 nodes)
- Dùng BFS distance làm heuristic: vì min edge cost = 1 (waypoint), BFS distance ≤ weighted cost thực tế → admissible

**Kết quả test:**
- 20→39: A* cost=12 (tránh 2 NPC interactions), BFS cost=13
- 0→66: A* chọn đường dài hơn nhưng ít NPC hơn (1 NPC vs 2 NPC)
- Các path khác: giống hoặc tối ưu hơn

**Thêm:**
- `find_path_bfs()` — giữ BFS làm fallback reference
- `find_path_with_cost()` — trả về path + tổng cost để debug

### Các file đã sửa
- `xmap_data.py`: NPC link 84→24 (fix loop)
- `xmap_runner.py`: `_in_npc_interaction` flag, Y-tiebreaker waypoint stacked
- `xmap_pathfinder.py`: BFS → A* với weighted costs và heuristic
- `memory.md`: session notes

## Session 7 - LoadTwoWaypoints() fallback, C# source analysis

### Bug: Loop 64↔72 (Fide planet) — waypoint stacked ở cùng vị trí X/Y

**Vấn đề:**
- Trên map 64 (Núi dây leo), 2 exit waypoint đến map 65 và map 72 có vị trí gần như nhau
- Popup name matching chọn đúng waypoint (Núi cây quỷ → map 65), move player đến (1668,312)
- Nhưng server KHÔNG dùng popup name — server xác định destination dựa trên **vị trí player**
- Vì 2 waypoint ở cùng vị trí, server không phân biệt được → gửi player về map 72 (sai)

**Phân tích C# source:**

Đã đọc 4 file C#:
- `ModNroPc/Xmap/NextMap.cs` — `GetWayPoint()`, `Enter()`, `CalculateTargetX()`, NPC confirm
- `ModNroPc/Xmap/MainXmapCL.cs` — `UpdateXmap()`, `LoadWaypointsInMap()`, `LoadTwoWaypoints()`, capsule
- `ModNroPc/Xmap/DataXmap.cs` — graph links, planet definitions, NPC links
- `ModNroPc/TileMap.cs` — `mapNames[]`, `pxw` (map width)

**Key differences with Python:**

1. **C# dùng `TileMap.mapNames[]`** — mảng tên tất cả map từ server, gửi qua `createMap()` (cmd=6 = UPDATE_MAP). Python CLI không bắt packet này, chỉ lưu tên map hiện tại qua `handle_map_info`

2. **C# có `TileMap.pxw = tmw * 24px`** — chiều rộng map thật. Python ước lượng từ waypoint → sai số lớn

3. **C# `LoadTwoWaypoints()`** — xử lý 2 waypoint cùng 1 bên (bothLeft || bothRight): xếp waypoint đầu = left (minX+15), waypoint sau = right (maxX-15). Navigation dùng `wp_pos` (-1=left/prev, 1=right/next) để chọn vị trí phù hợp

**Fix: `xmap_runner.py`**

`_calc_target_pos(wp, wp_pos)`:
- Thêm tham số `wp_pos` (hướng: -1=prev/left, 1=next/right)
- `map_width` cố định **2400px** (chuẩn NRO 100 tiles × 24px) thay vì ước lượng từ waypoint
- LoadTwoWaypoints-style **position offset**: khi phát hiện ≥2 waypoint cùng X (abs(minX diff) < 15), tự động +30px nếu đi NEXT, -30px nếu đi PREV

`_handle_waypoint()`:
- Truyền `link.wp_pos` vào `_calc_target_pos(wp, link.wp_pos)`

**C# Packet mapNames (`CMD_UPDATE_MAP = 6`):**
- `Controller.cs` case 6 gọi `createMap(msg.reader())`
- Python `cmd.py` đã có `CMD_UPDATE_MAP = 6`
- Nhưng dispatcher trong `client.py` gán `6: handle_send_money` (sai format)
- Bắt packet này phức tạp vì `createMap()` đọc toàn bộ map templates + NPC templates — không cần thiết
- Giải pháp: `SERVER_MAP_NAMES` dict + `set_server_map_name()` từ `handle_map_info` (đã có sẵn)

### Các file đã sửa
- `xmap_runner.py`: `_calc_target_pos(wp, wp_pos)` + LoadTwoWaypoints position offset
- `memory.md`: session notes

## Session 8 - MAP_NAMES[63] correction, LoadTwoWaypoints verified working

### LoadTwoWaypoints fix THÀNH CÔNG
Log xác nhận: **64→65 đã hoạt động** (không còn loop 64↔72):
```
Map: Núi dây leo (ID=64)  Zone: 8
Map:65 Z:5 Players:0/map
Map: Núi cây quỷ (ID=65)  Zone: 5
```
Position offset trong `_calc_target_pos(wp, wp_pos)` đã giúp server phân biệt waypoint nào được chọn.

### Bug mới: MAP_NAMES[63] sai → loop 65↔64

**Vấn đề:**
- Trên map 65, exit waypoints: 'Núi dây leo' (về 64), 'Trại lính Fide' (đi 63)
- `MAP_NAMES[63] = "Sân đấu 1"` — không match 'Núi dây leo' hay 'Trại lính Fide'
- Cả 3 tier matching đều fail → fallback position-based → chọn 'Núi dây leo' (sai) → loop

**Fix:** `xmap_data.py`
```python
63: "Trại lính Fide"  # thay vì "Sân đấu 1"
```

### Cảnh báo
- Các MAP_NAMES trong chain Fide (66, 67, 73-83) chưa được verify, có thể sai tiếp
- Cần bắt packet `CMD_UPDATE_MAP = 6` để có mapNames array từ server (giải pháp triệt để)

### Các file đã sửa
- `xmap_data.py`: MAP_NAMES[63] = "Trại lính Fide"

## Session 9 - Server source map names, fix toàn bộ Nappa chain

### Phát hiện: Map names từ server source code
Tìm thấy tên map chính thức trong `srcServer/nro/models/map/service/ChangeMapService.java`:
- File này chứa `checkMapCanJoin()` với comments map name cho mỗi map ID
- Map names được đọc từ DATABASE qua `Manager.java` line 805: `rs.getString("name")`

### Các MAP_NAMES đã sửa cho Nappa chain:
```
66: "Núi Fide" → "Trại quỷ già"
67: "Đồi Fide" → "Vực chết"
68: "Thung lũng Nappa" (thử) → "Hành tinh Fide" (giữ nguyên, xác nhận từ log)
73: "Đấu trường 1" → "Thung lũng chết"
74: "Đấu trường 2" → "Đồi cây Fide"
75: "Đấu trường 3" → "Khe núi tử thần"
76: "Đấu trường 4" → "Núi đá"
77: "Đấu trường 5" → "Rừng đá"
79: "Đấu trường 6" → "Núi khỉ đỏ"
80: "Đấu trường 7" → "Núi khỉ vàng"
81: "Đấu trường 8" → "Hang quỷ chim"
82: "Đấu trường 9" → "Núi khỉ đen"
83: "Đấu trường 10" → "Hang khỉ đen"
```

### Lưu ý
- Tên từ server source (Java comments) có thể không khớp 100% với database
- `SERVER_MAP_NAMES` override MAP_NAMES khi player đã từng đến map đó
- Cần thêm packet `CMD_UPDATE_MAP = 6` để có map names array từ server (giải pháp triệt để)

### Các file đã sửa
- `xmap_data.py`: MAP_NAMES 66,67,73-83 (tên thật từ server source)
