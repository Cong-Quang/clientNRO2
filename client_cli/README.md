# NRO CLI Client

Python CLI client cho NRO (Ngọc Rồng Online) game server. Kết nối qua socket TCP, parse packet theo protocol Java server. Tích hợp đầy đủ tính năng auto: train quái, nhặt đồ, boss, farm boss Nappa, skill, vứt đồ rác, boss tracker, xmap (tự động tìm đường A*).

## Yêu cầu

- Python 3.10+
- Server NRO chạy local tại `127.0.0.1:14445` (mặc định)
- Không cần thư viện ngoài — chỉ dùng Python standard library

## Cài đặt & Chạy

```bash
cd client_cli
python main.py
```

Mặc định tự động login với `username=1, password=1`.

## CLI Arguments

```bash
python main.py --help

# Thông số kết nối
python main.py --username admin --password 123456 --host 192.168.1.100 --port 14445
python main.py --login 1 1                                          # Shortcut đăng nhập

# Thực thi nhanh 1 hoặc nhiều lệnh (--exit để tự thoát)
python main.py -c "/map" -c "/info" --exit
python main.py --login 1 1 -c "/items" -c "/equip" --exit

# Hiện log console để debug
python main.py --show-log
python main.py --show-log -c "/autoboss list" --exit

# Unknown args tự động chuyển thành lệnh
python main.py --map --info --exit                                   # Tương đương -c "/map" -c "/info"
```

### Chi tiết arguments

| Argument | Mô tả |
|----------|-------|
| `--host HOST` | Server host (default: `127.0.0.1`) |
| `--port PORT` | Server port (default: `14445`) |
| `-u, --username` | Tài khoản (default: `1`) |
| `-p, --password` | Mật khẩu (default: `1`) |
| `--login USER PASS` | Đăng nhập nhanh |
| `-c, --cmd CMD` | Lệnh cần thực thi (dùng nhiều `-c`) |
| `--show-log, --log` | Hiển thị log ra console |
| `--exit, --quit` | Tự động thoát sau khi chạy `-c` |

## Luồng hoạt động

Sau khi chạy, client tự động:

1. Kết nối tới server
2. Gửi `setClientType` (thông tin client)
3. Login với username/password
4. Nhận danh sách nhân vật → tự động chọn nhân vật đầu tiên
5. Vào game (gửi `clientOk` + request map/skill/item data)
6. Nếu có `-c`: thực thi lệnh, nếu có `--exit` thì thoát
7. Nếu không: hiển thị prompt `> ` sẵn sàng nhận lệnh
8. Các module auto chạy ngầm trong thread riêng (mỗi 500ms)

## Prompt

Prompt tự động hiển thị trạng thái:

| Prompt | Ý nghĩa |
|--------|---------|
| `> ` | Bình thường |
| `[TRAIN]> ` | Auto Train đang bật |
| `[VUT]> ` | Auto Vứt Đồ đang bật |
| `[BOSS]> ` | Boss đang trong map HOẶC auto_boss đang bật |
| `npc(7)> ` | Đang trong menu NPC |
| `xmap(Đi map 39)> ` | Xmap đang chạy |

## Các lệnh

### Thông tin cơ bản

| Lệnh | Mô tả |
|------|-------|
| `/info` | Thông tin nhân vật + tóm tắt |
| `/map` | Thông tin map + zone hiện tại |
| `/npcs` | Danh sách NPC trong map |
| `/players` | Danh sách người chơi trong map |
| `/mobs` | Danh sách quái trong map (Template ID, HP, vị trí) |

### Di chuyển

| Lệnh | Mô tả |
|------|-------|
| `/move <x> <y>` | Di chuyển tới tọa độ |
| `/zone <id>` | Chuyển zone |
| `/changemap` | Chuyển map (qua cổng) |
| `/heal` | Hồi phục (cây tiềm năng) |
| `/gocit` | Hồi sinh về làng |
| `/wake` | Tỉnh dậy (sau khi chết) |
| `/selectmap <n>` | Chọn map trong danh sách teleport |

### Xmap (tự động tìm đường A*)

| Lệnh | Mô tả |
|------|-------|
| `/xmap <mapId>` | Tự động tìm đường đến map (A* pathfinding) |
| `/xmapstop` | Dừng xmap |
| `/xmapmenu` | Xem danh sách map theo hành tinh |
| `/xmapinfo` | Xem thông tin chi tiết đường đi |
| `/xmapsettings` | Bật/tắt ăn đùi gà / capsule |

### NPC & Shop

| Lệnh | Mô tả |
|------|-------|
| `/npcmenu <tempId>` | Mở menu NPC theo template ID |
| `/menu <opt>` hoặc gõ số | Chọn option trong menu NPC |
| `/buy <t> <itemId> [qty]` | Mua đồ từ shop (`t=0`: vàng, `1`: ngọc) |
| `/sale <a> <t> <id>` | Bán item |

### Đồ đạc & Item

| Lệnh | Mô tả |
|------|-------|
| `/items` | Xem đồ trong balo (kèm options, sao, upgrade) |
| `/equip` | Xem đồ đang mặc (từng slot) |
| `/pet` | Xem thông tin pet (stats, đồ, skill) |
| `/item <index>` | Xem chi tiết item trong balo |
| `/finditem <templateId>` | Tìm item theo ID trong balo/body/rương |
| `/useitem <t> <w> <i>` | Dùng/mặc/tháo item |
| `/pick <itemMapId>` | Nhặt item dưới đất |
| `/skill <id>` | Chọn skill |
| `/task <n> <m> [o]` | Tương tác nhiệm vụ |

**`/useitem <t> <w> <i>`:**
- `t` (type): `0`=balo, `1`=body, `2`=rương
- `w` (where): `0`=mặc vào, `1`=sử dụng, `2`=cất
- `i` (index): số thứ tự slot

Ví dụ: `/useitem 0 1 2` = dùng thuốc slot 2 từ balo

### Chat

| Lệnh | Mô tả |
|------|-------|
| `/chat <text>` | Chat map |
| Gõ text không có `/` | Chat map (tự động) |

Khi có NPC menu và gõ số → chọn option.

### Log

| Lệnh | Mô tả |
|------|-------|
| `/log list` | Xem trạng thái log |
| `/log <cat> on\|off\|debug` | Bật/tắt log category |
| `/log all off` | Tắt hết log |

## Auto Modules

### Auto Train (`/autotrain`)

Tự động tìm quái, di chuyển đến và tấn công.

```
/autotrain on|off                  # Bật/tắt auto train
/autotrain hpabove <n>             # Chỉ đánh quái HP trên n
/autotrain hpbelow <n>             # Chỉ đánh quái HP dưới n
/autotrain minmp <n>               # Về nhà khi MP dưới n%
/trainmob add <templateId>         # Thêm quái cần train
/trainmob all                      # Thêm tất cả quái trên map
/trainmob list                     # Xem danh sách quái
/trainmob clear                    # Xóa danh sách
/goback on|off|coord               # Tự động về nhà khi hết MP/HP
/autozone on|off|spam              # Tự động đổi khu (thông minh: chọn ít người)
```

**Smart Zone Change:** `/autozone on` quét danh sách khu từ server, chọn khu ít người nhất. `spam` chọn khu cuối còn chỗ.

### Auto Pick (`/autopick`)

Tự động nhặt đồ trên map.

```
/autopick on|off                   # Bật/tắt
/autopick all                      # Nhặt tất cả (kể cả đồ người khác)
/autopick by_list                  # Nhặt theo danh sách
/autopick add <templateId>         # Thêm item vào danh sách
/autopick delete <templateId>      # Xóa item khỏi danh sách
/autopick clear                    # Xóa toàn bộ danh sách
/autopick distance <n>             # Khoảng cách nhặt (px)
/autopick teleport                 # Dịch chuyển đến item
/autopick list                     # Xem trạng thái
/picklist                          # Xem danh sách item
```

### Auto Boss (`/autoboss`)

Tự động tìm, teleport và tấn công boss.

```
/autoboss on|off                   # Bật/tắt tất cả
/autoboss do                       # Dò boss (quét từng khu để tìm)
/autoboss gim                      # Gim boss (focus HP thấp nhất)
/autoboss tele                     # Teleport đến boss
/autoboss attack                   # Tấn công boss (tự bật tele)
/autoboss list                     # Xem trạng thái + boss + tracker sightings
/autoboss add <name>               # Chỉ tìm boss tên X
/autoboss remove <name>            # Bỏ boss khỏi danh sách
/autoboss clear                    # Tìm tất cả boss
```

`/autoboss list` hiển thị:
- Trạng thái ON/OFF các chức năng do/gim/tele/attack
- Danh sách target names
- Boss đang có trong map (tên, HP, tọa độ)
- Boss tracker sightings 30 phút gần đây

**Nhận diện boss:** Tên viết hoa chữ cái đầu, không phải pet/trọng tài/#/$.

### Auto Farm Boss Nappa (`/autonappa`)

Tự động farm boss Nappa (state machine 11 bước).

```
/autonappa on|off                  # Bật/tắt farm
/autonappa kuku                    # Farm Kuku (map 68-72)
/autonappa daudinh                 # Farm Mập đầu đinh (map 64-67)
/autonappa rambo                   # Farm Rambo (map 73-77)
/autonappa cycle                   # Chuyển loại boss 0→1→2→0
/autonappa list                    # Xem trạng thái + tracker sightings
```

**Tính năng:**
- Quét từng khu trên map, phát hiện boss qua danh sách player
- Tự động gim/tele/attack boss
- Phát hiện boss ảo (timeout 10s không damage → skip)
- Nhặt Mảnh Thiên Sứ (ID=1070) sau khi boss chết
- Xử lý chết: tự hồi sinh + quay lại map
- Xử lý lạc map: tự động quay lại map boss

### Auto Skill (`/autoskill`)

Cấu hình auto sử dụng kỹ năng.

```
/autoskill attack                  # Auto tấn công (khi có mob focus)
/autoskill list                    # Xem danh sách 10 slot
/autoskill shield                  # Tự động dùng khiên
/autoskill <slot> on|off           # Bật/tắt auto skill slot
/autoskill <slot> delay <ms>       # Set delay (ms) cho slot
/autoskill <slot> freeze           # Freeze/unfreeze (cooldown = 0)
/autoskill <slot> set <id> [name]  # Cấu hình skill ID cho slot
/autoskill all                     # Toggle tất cả slot
```

### Auto Vứt Đồ (`/vutdo`)

Tự động vứt đồ rác trong balo.

```
/vutdo on|off                      # Bật/tắt
/vutdo add <id1> <id2> ...         # Thêm ID item cần vứt
/vutdo delete <id1> <id2> ...      # Xóa ID item
/vutdo list                        # Xem danh sách
/vutdo clear                       # Xóa toàn bộ
```

### Boss Tracker (`/bosslog`)

Theo dõi boss xuất hiện (chạy ngầm, không cần bật auto_boss).

```
/bosslog [phút]                    # Xem boss đã xuất hiện
/tail                              # Xem realtime boss tracker (Ctrl+C để thoát)
```

**`/bosslog`:** Xem boss sightings trong khoảng thời gian (mặc định 60 phút).
```
[Tracker] Boss xuat hien trong 60 phut qua (3 lan):
  Broly HP=50000 - 5 phut 23 giay - Map 68 Khu 3 (1200,384)
  Kuku HP=30000 - 12 phut 8 giay - Map 70 Khu 5 (800,240)
```

**`/tail`:** Chế độ realtime (giống `tail -f`):
- Tự động refresh mỗi 3 giây, chỉ in khi có sightings mới
- Hiển thị 10 sightings gần nhất
- Nhấn `Ctrl+C` để thoát

## Cấu trúc thư mục

```
client_cli/
├── main.py                    # Entry point (có CLI args)
├── client.py                  # GameClient - kết nối các module
├── cmd.py                     # Command constants
├── network.py                 # Socket + Message (đọc/ghi packet)
├── service.py                 # Service - gửi packet
├── state.py                   # GameState - trạng thái runtime
├── ui.py                      # ConsoleUI - vòng lặp nhập lệnh
├── logger.py                  # Logging framework (màu, level)
├── Char.py                    # Character data model
├── handler.py                 # Abstract message handler

├── auto_boss.py               # Auto tìm/gim/tele/attack boss
├── auto_pick.py               # Auto nhặt đồ
├── auto_skill.py              # Auto kỹ năng
├── auto_train.py              # Auto train quái
├── auto_vutdo.py              # Auto vứt đồ rác
├── auto_farm_nappa.py         # Auto farm boss Nappa
├── boss_tracker.py            # Theo dõi boss xuất hiện

├── xmap_data.py               # Graph map + navigation data
├── xmap_pathfinder.py         # A* pathfinding
├── xmap_runner.py             # Xmap runner state machine

├── items_data.py              # Item template ID → tên (2000+)
├── item_detail.py             # Phân tích item options/upgrade/sao
├── item_option_data.py        # Option template names
├── npcs_data.py               # NPC template ID → tên

├── handlers/
│   ├── __init__.py            # Module exports
│   ├── connection.py          # Xử lý kết nối
│   ├── authentication.py      # Xử lý login
│   ├── world.py               # Xử lý map, player, mob
│   ├── interaction.py         # Xử lý NPC, shop, item
│   ├── communication.py       # Xử lý chat, dialog
│   └── social.py              # Xử lý bạn bè, party, pet

├── README.md                  # File này
├── tester.md                  # Test checklist
└── requirements.txt           # Không cần thư viện ngoài
```

## Protocol

Client kết nối tới Java server NRO qua TCP socket. Dùng mã hóa XOR key sau khi nhận session key từ server.

### Packet format

```
[byte cmd][short length][data...]
hoặc [byte cmd][3-byte length][data...] (cho cmd đặc biệt)
```

Sau khi nhận key: mỗi byte được XOR với key ring.

### Login flow

```
Client → Server:
  GET_SESSION_ID(-27)                     → nhận key
  NOT_LOGIN(227) + CMD_CLIENT_INFO(2)     → set client type
  NOT_LOGIN(227) + CMD_LOGIN(0)           → login

Server → Client:
  NOT_LOGIN(227) + byte(response)         → login response
  NOT_MAP(228)                            → vào game screen

Client → Server:
  NOT_MAP(228) + CMD_SELECT_PLAYER(1)     → chọn nhân vật

Server → Client:
  ME_LOAD_POINT(214)                      → stats nhân vật
  PLAYER_ADD(251)                         → các player khác
  SUB_COMMAND(226) + sub=0                → full data (items)
```

### Shop packet

```
Message(SHOP=212):
  byte: shopType (0=vàng/ngọc, 3=đặc biệt, 8=mua lại)
  byte: tabCount
  for each tab:
    UTF: tabName
    byte: itemCount
    for each item:
      short: itemTemplateId
      [pricing theo shopType]
      byte: optionCount
      for each option: byte id, short param
      byte: isNew
      byte: hasPart (short head/body/leg/bag)
```

### Zone packet

```
Message(OPEN_UI_ZONE=29):
  byte: count
  for each zone:
    byte: zoneId
    byte: pts
    byte: numPlayer
    byte: maxPlayer
    byte: hasRank
    [if hasRank: UTF rankName1, int rank1, UTF rankName2, int rank2]
```
