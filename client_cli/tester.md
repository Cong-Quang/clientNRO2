# Test Plan — NRO CLI Client

## Hướng dẫn sử dụng

- Đánh dấu `[x]` khi test **PASS**, `[ ]` khi **CHƯA TEST**, `[FAIL]` khi **LỖI**
- Ghi chú lỗi kèm log/output để dễ fix
- Chạy client: `cd client_cli && python main.py`
- Xem CLI arguments: `python main.py --help`

---

## 1. CLI Arguments (--cmd, --login, --show-log, --exit)

### 1.1 --help
- [ ] `python main.py --help` → hiển thị đầy đủ options

### 1.2 --cmd (1 lệnh đơn)
- [ ] `python main.py -c "/map" --exit` → hiển thị map, tự động thoát

### 1.3 --cmd (nhiều lệnh)
- [ ] `python main.py -c "/info" -c "/map" -c "/npcs" --exit` → chạy tuần tự 3 lệnh

### 1.4 --login shortcut
- [ ] `python main.py --login 1 1 -c "/players" --exit` → login và chạy lệnh

### 1.5 --show-log
- [ ] `python main.py --show-log -c "/map" --exit` → hiển thị log console

### 1.6 --exit (không có --exit)
- [ ] `python main.py -c "/map"` → chạy lệnh rồi vào input loop (không thoát)

### 1.7 Unknown args auto-detect
- [ ] `python main.py --map --info --exit` → tự động chuyển thành `/map /info`

### 1.8 Kết nối tùy chỉnh
- [ ] `python main.py --host 127.0.0.1 --port 14445 -u 1 -p 1` → kết nối thành công

---

## 2. Kết nối & Login

### 2.1 Kết nối cơ bản
- [ ] Chạy `python main.py` → kết nối thành công tới server
- [ ] Auto login với username/password mặc định (1/1)
- [ ] Prompt hiển thị `> ` sau khi vào game

### 2.2 Login tùy chỉnh
- [ ] `/login 1 1` → login thành công
- [ ] `/login sai sai` → thông báo lỗi (không crash)

### 2.3 Select nhân vật
- [ ] `/select <tên>` → chọn nhân vật thành công
- [ ] Auto-select nhân vật đầu tiên khi login

### 2.4 Disconnect
- [ ] Server ngắt kết nối → hiển thị "Disconnected."
- [ ] `/quit` → thoát sạch sẽ (xóa `__pycache__`)

---

## 3. Map & Thông tin

### 3.1 Map info
- [ ] `/map` → hiển thị `Map: Tên (ID=X)  Zone: Y`

### 3.2 NPC list
- [ ] `/npcs` → liệt kê NPC trong map kèm tên + tempId + tọa độ
- [ ] Tên NPC đúng (VD: "Bunma (ID=7) at (x,y)")

### 3.3 Players list
- [ ] `/players` → liệt kê player ID + name + tọa độ

### 3.4 Mobs list
- [ ] `/mobs` → liệt kê quái: `[mid] Template=X HP=hp/maxhp (status) at (x,y)`
- [ ] `/mobs` khi không có quái → "Khong co quai nao"

### 3.5 Info
- [ ] `/info` → hiển thị thông tin nhân vật (HP, MP, DMG, DEF...)
- [ ] `/info` → hiển thị số items trong balo
- [ ] `/info` → hiển thị pet nếu có

---

## 4. Di chuyển

### 4.1 Move
- [ ] `/move 100 200` → nhân vật di chuyển đến (100,200)

### 4.2 Zone change
- [ ] `/zone 0` → chuyển sang zone 0
- [ ] `/zone 999` → xử lý khi zone không tồn tại (không crash)

### 4.3 Change map (waypoint)
- [ ] `/changemap` → chuyển map qua waypoint gần nhất
- [ ] Map thay đổi + thông tin map mới hiển thị

### 4.4 Heal / Gocit / Wake
- [ ] `/heal` → hồi phục (gửi magicTree)
- [ ] `/gocit` → hồi sinh về làng
- [ ] `/wake` → tỉnh dậy sau khi chết

---

## 5. Xmap (tự động tìm đường A*)

### 5.1 Tìm đường cơ bản
- [ ] `/xmap 39` → tìm đường từ map hiện tại đến map 39
- [ ] Xmap chạy, prompt hiển thị `xmap(Đi map 39...)>`
- [ ] Đến map đích → hiển thị "Đã đến map X!"

### 5.2 Điều khiển xmap
- [ ] `/xmapstop` → dừng xmap đang chạy
- [ ] `/xmap 0` (đã ở map 0) → "Da den map 0!"

### 5.3 Xmap info
- [ ] `/xmapinfo` → hiển thị path A*, BFS, cost, các bước di chuyển

### 5.4 Xmap settings
- [ ] `/xmapsettings` → toggle ăn đùi gà / capsule

### 5.5 Xmap menu
- [ ] `/xmapmenu` → hiển thị danh sách map theo hành tinh

### 5.6 Select map (teleport)
- [ ] Dùng capsule (item 194) → server gửi danh sách map
- [ ] `/selectmap <n>` → chọn map trong danh sách

---

## 6. NPC & Shop

### 6.1 NPC menu
- [ ] `/npcmenu 7` → mở menu Bunma
- [ ] `/npcmenu 999` (NPC không trong map) → thông báo "khong co o map nay"
- [ ] NPC dialog hiển thị đúng + options

### 6.2 Menu options
- [ ] `/menu 0` hoặc gõ `0` → chọn option 0
- [ ] Menu con hiển thị đúng
- [ ] prompt hiển thị `npc(id)> ` khi đang trong menu

### 6.3 Shop
- [ ] Mở shop NPC → hiển thị tab + items + giá
- [ ] `/buy 0 33` → mua item ID 33 bằng vàng
- [ ] `/buy 1 529` → mua item ID 529 bằng ngọc
- [ ] `/buy 0 33 5` → mua 5 cái

### 6.4 Bán item
- [ ] `/sale 0 0 33` → bán item ID 33 từ balo

### 6.5 Task
- [ ] `/task 7 1 0` → tương tác nhiệm vụ

---

## 7. Item & Pet

### 7.1 Items (balo)
- [ ] `/items` → hiển thị items trong balo kèm index + ID + options
- [ ] Item có sao/vàng hiển thị đúng

### 7.2 Item detail
- [ ] `/item 0` → xem chi tiết item slot 0 (thuộc tính, sao, yêu cầu...)
- [ ] `/item 999` (slot không tồn tại) → thông báo lỗi

### 7.3 Find item
- [ ] `/finditem 33` → tìm item ID=33 trong balo/body/rương
- [ ] `/finditem 99999` (không có) → "Khong tim thay"

### 7.4 Use item
- [ ] `/useitem 0 1 2` → dùng item slot 2 từ balo
- [ ] `/useitem 0 0 0` → mặc item slot 0

### 7.5 Equip
- [ ] `/equip` → hiển thị đồ đang mặc theo slot (Áo, Quần, Găng...)
- [ ] Slot trống hiển thị `(empty)` đúng

### 7.6 Pet
- [ ] `/pet` → hiển thị thông tin pet (HP, MP, damage, skill)
- [ ] Pet equipment hiển thị đúng
- [ ] `/pet` khi không có pet → "No pet info"

### 7.7 Pick item
- [ ] `/pick <itemMapId>` → nhặt item dưới đất

---

## 8. Chat & Log

### 8.1 Chat
- [ ] `/chat Xin chao` → chat map
- [ ] Gõ `Xin chao` (không có /) → chat map tự động
- [ ] Khi có NPC menu và gõ số → chọn option (không chat)

### 8.2 Log
- [ ] `/log list` → xem danh sách categories + levels
- [ ] `/log network on` → bật log network
- [ ] `/log network off` → tắt log network
- [ ] `/log network debug` → bật debug log
- [ ] `/log all off` → tắt hết log

---

## 9. Auto Train

### 9.1 Bật/tắt
- [ ] `/autotrain` → toggle, thông báo BAT/TAT
- [ ] `/autotrain on` → bật
- [ ] `/autotrain off` → tắt
- [ ] Prompt hiển thị `[TRAIN]> ` khi đang train

### 9.2 Mob list
- [ ] `/trainmob add 13` → thêm quái template 13
- [ ] `/trainmob all` → thêm tất cả quái trên map
- [ ] `/trainmob list` → liệt kê quái đang train
- [ ] `/trainmob clear` → xóa danh sách

### 9.3 HP/MP filter
- [ ] `/autotrain hpabove 1000` → chỉ đánh quái HP > 1000
- [ ] `/autotrain hpbelow 50000` → chỉ đánh quái HP < 50000
- [ ] `/autotrain minmp 10` → về nhà khi MP < 10%

### 9.4 Goback
- [ ] `/goback on` → bật goback (lưu map/zone hiện tại)
- [ ] `/goback off` → tắt
- [ ] `/goback coord` → goback theo tọa độ

### 9.5 Zone change
- [ ] `/autozone on` → bật auto đổi khu thông minh
- [ ] `/autozone spam` → bật spam zone (chọn khu cuối)
- [ ] `/autozone off` → tắt

---

## 10. Auto Pick

### 10.1 Bật/tắt
- [ ] `/autopick` → toggle, thông báo BAT/TAT
- [ ] `/autopick on` / `/autopick off`

### 10.2 Pick tất cả
- [ ] `/autopick all` → bật nhặt tất cả (kể cả đồ người khác)

### 10.3 Pick theo danh sách
- [ ] `/autopick add 1070` → thêm item ID vào danh sách
- [ ] `/autopick delete 1070` → xóa item
- [ ] `/autopick by_list` → bật chế độ nhặt theo danh sách
- [ ] `/picklist` → xem danh sách item

### 10.4 Khoảng cách & Teleport
- [ ] `/autopick distance 100` → set khoảng cách nhặt 100px
- [ ] `/autopick teleport` → bật teleport đến item

### 10.5 List status
- [ ] `/autopick list` → hiển thị trạng thái (ON/OFF, khoảng cách...)
- [ ] `/autopick clear` → xóa danh sách

---

## 11. Auto Boss

### 11.1 Bật/tắt
- [ ] `/autoboss` → hiển thị trạng thái
- [ ] `/autoboss on` / `/autoboss off`

### 11.2 Do Boss (quét khu)
- [ ] `/autoboss do` → bắt đầu quét từng khu
- [ ] Tìm thấy boss → thông báo + dừng
- [ ] Không tìm thấy → "Da quet het khu, khong tim thay boss"

### 11.3 Gim Boss
- [ ] `/autoboss gim` → focus boss HP thấp nhất

### 11.4 Tele Boss
- [ ] `/autoboss tele` → tự động teleport đến boss

### 11.5 Attack Boss
- [ ] `/autoboss attack` → tự động tấn công boss (tự bật tele)

### 11.6 Target list
- [ ] `/autoboss add Broly` → chỉ tìm boss Broly
- [ ] `/autoboss remove Broly` → bỏ boss Broly
- [ ] `/autoboss clear` → tìm tất cả boss

### 11.7 List status
- [ ] `/autoboss list` → hiển thị trạng thái + target + boss trong map + tracker sightings

### 11.8 Nhận diện boss
- [ ] Boss có tên viết hoa → nhận diện đúng
- [ ] Pet / Trọng tài / #name / $name → không nhận diện là boss

---

## 12. Auto Farm Nappa

### 12.1 Bật/tắt + chọn boss
- [ ] `/autonappa kuku` → farm Kuku (map 68-72)
- [ ] `/autonappa daudinh` → farm Mập đầu đinh (map 64-67)
- [ ] `/autonappa rambo` → farm Rambo (map 73-77)
- [ ] `/autonappa on` → farm với boss đang chọn
- [ ] `/autonappa off` → dừng farm

### 12.2 Cycle
- [ ] `/autonappa cycle` → chuyển 0→1→2→0

### 12.3 List status
- [ ] `/autonappa list` → hiển thị trạng thái farm + tracker sightings

---

## 13. Auto Skill

### 13.1 Cấu hình slot
- [ ] `/autoskill 0 set 101 "Dragon"` → set skill slot 0
- [ ] `/autoskill list` → hiển thị 10 slot
- [ ] `/autoskill 0 on` → bật auto skill slot 0
- [ ] `/autoskill 0 off` → tắt
- [ ] `/autoskill 0 delay 800` → set delay 800ms
- [ ] `/autoskill 0 freeze` → freeze/unfreeze

### 13.2 Auto Attack & Shield
- [ ] `/autoskill attack` → bật auto attack
- [ ] `/autoskill shield` → bật auto khiên

### 13.3 All toggle
- [ ] `/autoskill all` → toggle tất cả slot

---

## 14. Auto Vứt Đồ

### 14.1 Bật/tắt
- [ ] `/vutdo on` → bật
- [ ] `/vutdo off` → tắt
- [ ] Prompt hiển thị `[VUT]> ` khi bật

### 14.2 Quản lý danh sách
- [ ] `/vutdo add 33 45 67` → thêm ID items
- [ ] `/vutdo delete 33` → xóa ID
- [ ] `/vutdo list` → xem danh sách
- [ ] `/vutdo clear` → xóa tất cả

---

## 15. Boss Tracker

### 15.1 /bosslog
- [ ] `/bosslog` → xem boss sightings 60 phút
- [ ] `/bosslog 30` → xem 30 phút
- [ ] Không có boss → "Khong co boss nao xuat hien"
- [ ] Có boss → hiển thị tên + thời gian + map + zone + vị trí

### 15.2 /tail (realtime)
- [ ] `/tail` → vào chế độ realtime
- [ ] Refresh mỗi 3 giây
- [ ] Ctrl+C → thoát → "Da thoat"

### 15.3 Tích hợp
- [ ] `/autoboss list` → hiển thị tracker sightings
- [ ] `/autonappa list` → hiển thị tracker sightings

---

## 16. Item Detail

### 16.1 Phân tích item
- [ ] `/item 0` → hiển thị đúng tên + ID + upgrade (+4, +7...)
- [ ] Hiển thị sao (★☆☆☆☆)
- [ ] Hiển thị CH lỗ sao nếu có
- [ ] Hiển thị options/thuộc tính
- [ ] Hiển thị yêu cầu (level, power...)

### 16.2 Set kích hoạt
- [ ] Item có set → hiển thị "📦 Set: Tên Set"

### 16.3 Khóa
- [ ] Item bị khóa → hiển thị "🔒 Đã khóa"

---

## 17. Logging

### 17.1 Log levels
- [ ] `log all off` → không in log gì
- [ ] `log network debug` → in debug + info
- [ ] `log network on` → chỉ in info

### 17.2 Tags
- [ ] Tag `BOSS` → gắn màu đúng + category combat
- [ ] Tag `PICK` → đúng category item
- [ ] Tag `NAPPA` → đúng category
- [ ] Tag `ZONE` → đúng category

### 17.3 Compact mode
- [ ] Terminal hẹp (< 60 cột) → tự động bật compact mode
- [ ] Compact: `BOSS>msg` thay vì `[HH:MM:SS][INF][BOSS] msg`

---

## 18. Prompt

### 18.1 Các loại prompt
- [ ] `> ` — bình thường
- [ ] `[TRAIN]> ` — auto train đang bật
- [ ] `[VUT]> ` — auto vứt đồ đang bật
- [ ] `[BOSS]> ` — boss trong map HOẶC auto_boss đang bật
- [ ] `npc(7)> ` — đang trong menu NPC
- [ ] `xmap(Đi map 39...)> ` — xmap đang chạy

### 18.2 Kết hợp tags
- [ ] `[TRAIN BOSS]> ` — cả train + boss

---

## 19. Xử lý lỗi & Edge cases

### 19.1 Không crash
- [ ] Gõ lệnh sai syntax → thông báo "Usage: ..."
- [ ] Gõ lệnh không tồn tại → "Unknown: /abc"
- [ ] Server gửi packet lạ → không crash
- [ ] Mất kết nối đột ngột → hiển thị Disconnected

### 19.2 Input
- [ ] Gõ số khi có NPC menu → chọn option
- [ ] Gõ enter (dòng trống) → bỏ qua, không crash

### 19.3 Thread safety
- [ ] Auto updater (500ms) chạy ổn định
- [ ] Boss tracker chạy song song không crash
- [ ] Xmap + auto module cùng chạy → stable

---

## 20. Hỗ trợ tiếng Việt

### 20.1 Hiển thị
- [ ] Tên item tiếng Việt hiển thị đúng (không bị lỗi font)
- [ ] Tên NPC tiếng Việt hiển thị đúng
- [ ] Fallback UTF-8 khi console không hỗ trợ

### 20.2 Normalize (xmap waypoint)
- [ ] Waypoint popup name có dấu → match đúng
- [ ] So sánh không phân biệt dấu

---

## Ghi chú test

| Ngày test | Người test | PASS | FAIL | Ghi chú |
|-----------|------------|------|------|---------|
|           |            |      |      |         |
|           |            |      |      |         |
