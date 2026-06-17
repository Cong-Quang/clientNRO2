# NRO CLI Client

Python CLI client for NRO (Ngọc Rồng Online) game server. Kết nối qua socket TCP, parse packet theo protocol Java server.

## Yêu cầu

- Python 3.10+
- Server NRO chạy local tại `127.0.0.1:14445` (mặc định)

## Cài đặt & Chạy

```bash
cd client_cli
py main.py
```

Mặc định tự động login với `username=1, password=1`. Có thể chỉ định:

```bash
py main.py --username admin --password 123456 --host 192.168.1.100 --port 14445
```

## Luồng hoạt động

Sau khi chạy, client tự động:

1. Kết nối tới server
2. Gửi `setClientType` (thông tin client)
3. Login với username/password
4. Nhận danh sách nhân vật → tự động chọn nhân vật đầu tiên
5. Vào game (gửi `clientOk` + request map/skill/item data)
6. Hiển thị prompt `> ` sẵn sàng nhận lệnh

## Các lệnh

### Thông tin cơ bản

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/info` | Thông tin nhân vật + tóm tắt đồ | `/info` |
| `/map` | Thông tin map hiện tại | `/map` |
| `/npcs` | Danh sách NPC trong map | `/npcs` |
| `/players` | Danh sách người chơi trong map | `/players` |

### Di chuyển & Map

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/move <x> <y>` | Di chuyển tới tọa độ | `/move 100 200` |
| `/zone <id>` | Chuyển zone | `/zone 0` |
| `/changemap` | Chuyển map (qua cổng) | `/changemap` |
| `/heal` | Hồi phục (cây tiềm năng) | `/heal` |
| `/gocit` | Hồi sinh về làng | `/gocit` |
| `/wake` | Tỉnh dậy (sau khi chết) | `/wake` |

### NPC & Shop

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/npcmenu <id>` | Mở menu NPC theo template ID | `/npcmenu 7` |
| `/menu <opt>` hoặc gõ số | Chọn option trong menu NPC | `/menu 0` hoặc `0` |
| `/buy <t> <id> [qty]` | Mua đồ từ shop (`t=0`:vàng, `1`:ngọc) | `/buy 0 33` |

Ví dụ mua đồ từ Bunma:

```
> /npcmenu 7
[NPC] Cậu cần trang bị gì cứ đến chỗ tôi nhé
  [0] Cửa hàng

npc(7)> 0
[SHOP] type=0 tabs=3
  [0] Áo Quần (24 items)
    [33] Áo thun 3 lỗ - Vàng:5000
    [3] Áo vải dày - Vàng:10000
    ...
  [1] Phụ kiện (42 items)
    [529] Giáp tập luyện cấp 1 - Ngọc:30
    ...
```

Mua áo thun 3 lỗ (ID 33) bằng vàng:

```
> /buy 0 33
```

### Đồ đạc & Pet

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/items` | Xem đồ trong balo (kèm options) | `/items` |
| `/equip` | Xem đồ đang mặc (từng slot) | `/equip` |
| `/pet` | Xem thông tin pet (stats, đồ, skill) | `/pet` |

Ví dụ:

```
> /items
[Bag] 3 items:
  [0] [#33] Áo thun 3 lỗ x1
      +sức đánh 1000
      +giáp 500
  [1] [#6] Quần vải đen x1
      +HP 5000
```

```
> /equip
[Equip] Equipped items:
  [Áo] [#33] Áo thun 3 lỗ x1
      +sức đánh 1000
  [Quần] [#6] Quần vải đen x1
      +HP 5000
```

```
> /pet
[Pet] Thần Long (Cấp 50)
  HP: 50000/50000  MP: 10000/10000
  Damage: 15000  Defense: 2000  Crit: 10%
  Power: 1000000  Potential: 50000
  Stamina: 100/100
  Status: Follow
  Equipment:
    [0] [#1234] Đai Thần Long x1
        +HP 20000
  Skills:
    Skill ID: 102
    Skill ID: 201
```

### Teleport (Capsule đặc biệt)

Khi dùng item Capsule đặc biệt (ID 194), server gửi danh sách map:

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/selectmap <n>` | Chọn map trong danh sách teleport | `/selectmap 1` |

Ví dụ:

```
> /items                     # xem slot của capsule
[Bag] 3 items:
  [2] [#194] Viên Capsule đặc biệt x1

> /useitem 0 1 2             # dùng capsule ở slot 2
[Teleport] Chọn map để dịch chuyển (12 maps):
  [0] Về nhà
  [1] Làng Aru
  [2] Đảo Guru
  ...
Dùng /selectmap <số> để chọn

> /selectmap 1               # chọn map Làng Aru
```

### Chat

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/chat <text>` | Chat map | `/chat Xin chao` |
| Gõ text không có `/` | Chat map (tự động) | `Xin chao` |

### Kỹ năng

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/skill <id>` | Chọn skill | `/skill 101` |
| `/task <n> <m> [o]` | Tương tác nhiệm vụ | `/task 7 1 0` |

### Item

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/pick <id>` | Nhặt item dưới đất (id = item map id) | `/pick 5` |
| `/useitem <t> <w> <i>` | Dùng item (xem giải thích bên dưới) | `/useitem 0 1 2` |
| `/sale <a> <t> <id>` | Bán item (`a`=action, `t`=0:balo/1:body, `id`=itemId) | `/sale 0 0 33` |

**`/useitem <t> <w> <i>` - Giải thích tham số:**
- `t` (type): `0`=balo, `1`=body (đồ đang mặc), `2`=rương
- `w` (where/tab): `0`=mặc vào (bag→body), `1`=sử dụng, `2`=cất (body→bag)
- `i` (index): số thứ tự slot (0, 1, 2, ...) trong danh sách

Ví dụ:
- Mặc áo slot 0 từ balo: `/useitem 0 0 0`
- Dùng thuốc slot 2 từ balo: `/useitem 0 1 2`
- Cởi áo đang mặc slot 0 (về balo): `/useitem 1 2 0`

### Khác

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/quit` | Thoát | `/quit` |
| `/help` | In help | `/help` |

### Log

| Lệnh | Mô tả | Ví dụ |
|------|-------|-------|
| `/log list` | Xem trạng thái log các category | `/log list` |
| `/log <cat> on` | Bật log category | `/log network on` |
| `/log <cat> off` | Tắt log category | `/log network off` |
| `/log <cat> debug` | Bật debug log | `/log network debug` |
| `/log all off` | Tắt hết log | `/log all off` |

## Cấu trúc thư mục

```
client_cli/
├── main.py                    # Entry point
├── client.py                  # GameClient - kết nối các module
├── cmd.py                     # Command constants
├── network.py                 # Socket + Message (đọc/ghi packet)
├── service.py                 # Service - gửi packet theo nghiệp vụ
├── state.py                   # GameState - trạng thái runtime
├── ui.py                      # ConsoleUI - vòng lặp nhập lệnh
├── logger.py                  # Logging framework
├── Char.py                    # Character data model
├── npcs_data.py               # NPC template ID → tên
├── items_data.py              # Item template ID → tên (2000+ items)
├── memory.md                  # Project memory
├── README.md                  # File này
├── .gitignore
├── handlers/
│   ├── __init__.py
│   ├── connection.py          # Xử lý kết nối
│   ├── authentication.py      # Xử lý login
│   ├── world.py               # Xử lý map, player, mob
│   ├── interaction.py         # Xử lý NPC, shop, item
│   ├── communication.py       # Xử lý chat, dialog
│   └── social.py              # Xử lý bạn bè, party, trade, pet
└── __pycache__/               # Tự động xóa khi thoát
```

## Protocol

Client kết nối tới Java server NRO qua TCP socket.

### Login flow

```
Client → Server:
  Message(CMD_NOT_LOGIN=227) + msg.writeByte(CMD_CLIENT_INFO=2) → setClientType
  Message(CMD_NOT_LOGIN=227) + msg.writeByte(CMD_LOGIN=0) → login

Server → Client:
  Message(CMD_NOT_LOGIN=227) + msg.writeByte(response) → login response
  Message(CMD_NOT_MAP=228) → vào game (enter game screen)

Client → Server:
  Message(CMD_NOT_MAP=228) + msg.writeByte(CMD_SELECT_PLAYER=1) → chọn nhân vật

Server → Client:
  Message(CMD_ME_LOAD_POINT=214) → thông tin nhân vật trong map
  Message(CMD_PLAYER_ADD=251) → các player khác trong map
  Message(CMD_SUB_COMMAND=226) + sub=0 → full data (body, bag, box items)

Client → Server:
  clientOk() + updateMap() + updateSkill() + updateItem() → hoàn tất vào game
```

### Shop packet

Server gửi `Message(CMD_SHOP=212)` khi mở shop:

```
byte: shopType (0=vàng/ngọc, 1=tiềm năng, 3=đặc biệt, 8=mua lại)
byte: tabCount
for each tab:
  UTF: tabName
  byte: itemCount
  for each item:
    short: itemTemplateId
    [pricing theo shopType]
    byte: optionCount
    for each option:
      byte: optionTemplateId
      short: param
    byte: isNew
    byte: hasPart
    if hasPart:
      short: head, body, leg, bag
```

## NPC Template IDs phổ biến

| ID | Tên | Chức năng |
|----|-----|-----------|
| 0 | Ông Gôhan | Thu mua, nhiệm vụ |
| 4 | Đậu thần | Hồi phục |
| 7 | Bunma | Shop đồ Trái Đất |
| 8 | Dende | Chữa lành, hồi sinh |
| 10 | Dr. Brief | Nâng cấp đồ |
| 11 | Cargo | Tàu vũ trụ (chuyển map) |
| 13 | Quy Lão Kame | Học skill, nhiệm vụ |
| 18 | Thần mèo Karin | Nhiệm vụ |
| 24 | Rồng Thiêng | Cầu rồng |
| 37 | Bunma (bản sao) | Shop đồ |
