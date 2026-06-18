# Test Plan — NRO CLI Client

## Hướng dẫn sử dụng

- Đánh dấu `[x]` khi test **PASS**, `[ ]` khi **CHƯA TEST**, `[FAIL]` khi **LỖI**
- Ghi chú lỗi kèm log/output để dễ fix
- Chạy client: `cd client_cli && python main.py`

---

## 1. Kết nối & Login

### 1.1 Kết nối cơ bản
- [ ] Chạy `python main.py` → kết nối thành công tới server
- [ ] Host/port tùy chỉnh: `python main.py --host 192.168.1.100 --port 14445`
- [ ] Auto login với username/password mặc định (1/1)
- [ ] Prompt hiển thị `> ` sau khi vào game

### 1.2 Login tùy chỉnh
- [ ] `/login 1 1` → login thành công
- [ ] `/login sai sai` → thông báo lỗi (không crash)

### 1.3 Select nhân vật
- [ ] `/select <tên>` → chọn nhân vật thành công
- [ ] Auto-select nhân vật đầu tiên khi login

### 1.4 Disconnect
- [ ] Server ngắt kết nối → hiển thị "Disconnected."
- [ ] `/quit` → thoát sạch sẽ (xóa `__pycache__`)

---

## 2. Map & Thông tin

### 2.1 Map info
- [ ] `/map` → hiển thị `Map: Tên (ID=X)  Zone: Y`
- [ ] Map name từ server (không phải "Unknown")

### 2.2 NPC list
- [ ] `/npcs` → liệt kê NPC trong map kèm tên + tempId + tọa độ
- [ ] Tên NPC đúng (VD: "Bunma (ID=7) at (x,y)")

### 2.3 Players list
- [ ] `/players` → liệt kê player ID + name + tọa độ

### 2.4 Mobs list
- [ ] `/mobs` → liệt kê quái: `[mid] Template=X HP=hp/maxhp (status) at (x,y)`
- [ ] `/mobs` khi không có quái → "Khong co quai nao"

### 2.5 Info
- [ ] `/info` → hiển thị thông tin nhân vật (HP, MP, DMG, DEF...)
- [ ] `/info` → hiển thị số items trong balo
- [ ] `/info` → hiển thị pet nếu có

---

## 3. Di chuyển

### 3.1 Move
- [ ] `/move 100 200` → nhân vật di chuyển đến (100,200)
- [ ] Server cập nhật vị trí

### 3.2 Zone change
- [ ] `/zone 0` → chuyển sang zone 0
- [ ] `/zone 999` → xử lý khi zone không tồn tại (không crash)

### 3.3 Change map (waypoint)
- [ ] `/changemap` → chuyển map qua waypoint gần nhất
- [ ] Map thay đổi + thông tin map mới hiển thị

### 3.4 Heal / Gocit / Wake
- [ ] `/heal` → hồi phục (gửi magicTree)
- [ ] `/gocit` → hồi sinh về làng
- [ ] `/wake` → tỉnh dậy sau khi chết

---

## 4. Xmap (tự động tìm đường)

### 4.1 Tìm đường cơ bản
- [ ] `/xmap 39` → tìm đường từ map hiện tại đến map 39
- [ ] Xmap chạy, prompt hiển thị `xmap(Đi map 39...)>`
- [ ] Đến map đích → hiển thị "Đã đến map X!"

### 4.2 Điều khiển xmap
- [ ] `/xmapstop` → dừng xmap đang chạy
- [ ] `/xmap 0` (đã ở map 0) → "Da den map 0!"

### 4.3 Xmap info
- [ ] `/xmapinfo` → hiển thị path A*, BFS, cost, các bước di chuyển

### 4.4 Xmap settings
- [ ] `/xmapsettings` → toggle ăn đùi gà / capsule

### 4.5 Xmap menu
- [ ] `/xmapmenu` → hiển thị danh sách map theo hành tinh

### 4.6 Select map (teleport)
- [ ] Dùng capsule (item 194) → server gửi danh sách map
- [ ] `/selectmap <n>` → chọn map trong danh sách

---

## 5. NPC & Shop

### 5.1 NPC menu
- [ ] `/npcs` → xem NPC có trong map
- [ ] `/npcmenu 7` → mở menu Bunma
- [ ] `/npcmenu 999` (NPC không trong map) → thông báo "khong co o map nay"
- [ ] NPC dialog hiển thị đúng + options

### 5.2 Menu options
- [ ] `/menu 0` hoặc gõ `0` → chọn option 0
- [ ] Menu con hiển thị đúng
- [ ] prompt hiển thị `npc(id)> ` khi đang trong menu

### 5.3 Shop
- [ ] Mở shop NPC → hiển thị tab + items + giá
- [ ] `/buy 0 33` → mua item ID 33 bằng vàng
- [ ] `/buy 1 529` → mua item ID 529 bằng ngọc
- [ ] `/buy 0 33 5` → mua 5 cái

### 5.4 Bán item
- [ ] `/sale 0 0 33` → bán item ID 33 từ balo

### 5.5 Task
- [ ] `/task 7 1 0` → tương tác nhiệm vụ

---

## 6. Item & Pet

### 6.1 Items (balo)
- [ ] `/items` → hiển thị items trong balo kèm index + ID + options
- [ ] Item có sao/vàng hiển thị đúng `[#33] Áo thun 3 lỗ +4 ★★★☆☆`

### 6.2 Item detail
- [ ] `/item 0` → xem chi tiết item slot 0 (thuộc tính, sao, yêu cầu...)
- [ ] `/item 999` (slot không tồn tại) → thông báo lỗi

### 6.3 Find item
- [ ] `/finditem 33` → tìm item ID=33 trong balo/body/rương
- [ ] `/finditem 99999` (không có) → "Khong tim thay"

### 6.4 Use item
- [ ] `/useitem 0 1 2` → dùng item slot 2 từ balo
- [ ] `/useitem 0 0 0` → mặc item slot 0

### 6.5 Equip
- [ ] `/equip` → hiển thị đồ đang mặc theo slot (Áo, Quần, Găng...)
- [ ] Slot trống hiển thị `(empty)` đúng

### 6.6 Pet
- [ ] `/pet` → hiển thị thông tin pet (HP, MP, damage, skill)
- [ ] Pet equipment hiển thị đúng
- [ ] `/pet` khi không có pet → "No pet info"

### 6.7 Pick item
- [ ] `/pick <itemMapId>` → nhặt item dưới đất

---

## 7. Chat & Log

### 7.1 Chat
- [ ] `/chat Xin chao` → chat map
- [ ] Gõ `Xin chao` (không có /) → chat map tự động
- [ ] Khi có NPC menu và gõ số → chọn option (không chat)

### 7.2 Log
- [ ] `/log list` → xem danh sách categories + levels
- [ ] `/log network on` → bật log network
- [ ] `/log network off` → tắt log network
- [ ] `/log network debug` → bật debug log
- [ ] `/log all off` → tắt hết log

---

## 8. Auto Train

### 8.1 Bật/tắt
- [ ] `/autotrain` → toggle, thông báo BAT/TAT
- [ ] `/autotrain on` → bật
- [ ] `/autotrain off` → tắt
- [ ] Prompt hiển thị `[TRAIN]> ` khi đang train

### 8.2 Mob list
- [ ] `/trainmob add 13` → thêm quái template 13
- [ ] `/trainmob all` → thêm tất cả quái trên map
- [ ] `/trainmob list` → liệt kê quái đang train
- [ ] `/trainmob clear` → xóa danh sách

### 8.3 Auto train chạy
- [ ] Auto train tự động tìm quái trong danh sách
- [ ] Di chuyển đến quái (charMove)
- [ ] Tấn công quái (sendPlayerAttack)
- [ ] Tự động dùng TDKT (item 521) nếu có trong balo

### 8.4 HP/MP filter
- [ ] `/autotrain hpabove 1000` → chỉ đánh quái HP > 1000
- [ ] `/autotrain hpbelow 50000` → chỉ đánh quái HP < 50000
- [ ] `/autotrain minmp 10` → về nhà khi MP < 10%

### 8.5 Goback
- [ ] `/goback on` → bật goback (lưu map/zone hiện tại)
- [ ] Khi MP thấp → tự động về nhà
- [ ] Khi về nhà → ăn đùi gà heal
- [ ] Sau khi heal → quay lại map cũ
- [ ] `/goback off` → tắt
- [ ] `/goback coord` → goback theo tọa độ

### 8.6 Zone change
- [ ] `/autozone on` → bật auto đổi khu thông minh
- [ ] Tự động chọn khu ít người nhất
- [ ] `/autozone spam` → bật spam zone (chọn khu cuối)
- [ ] `/autozone off` → tắt

---

## 9. Auto Pick

### 9.1 Bật/tắt
- [ ] `/autopick` → toggle, thông báo BAT/TAT
- [ ] `/autopick on` / `/autopick off`

### 9.2 Pick tất cả
- [ ] `/autopick all` → bật nhặt tất cả (kể cả đồ người khác)
- [ ] Auto nhặt item trong phạm vi

### 9.3 Pick theo danh sách
- [ ] `/autopick add 1070` → thêm item ID vào danh sách
- [ ] `/autopick delete 1070` → xóa item
- [ ] `/autopick by_list` → bật chế độ nhặt theo danh sách
- [ ] `/picklist` → xem danh sách item

### 9.4 Khoảng cách & Teleport
- [ ] `/autopick distance 100` → set khoảng cách nhặt 100px
- [ ] `/autopick teleport` → bật teleport đến item

### 9.5 List status
- [ ] `/autopick list` → hiển thị trạng thái (ON/OFF, khoảng cách...)
- [ ] `/autopick clear` → xóa danh sách

---

## 10. Auto Boss

### 10.1 Bật/tắt
- [ ] `/autoboss` → hiển thị trạng thái
- [ ] `/autoboss on` / `/autoboss off`

### 10.2 Do Boss (quét khu)
- [ ] `/autoboss do` → bắt đầu quét từng khu
- [ ] Tìm thấy boss → thông báo + dừng
- [ ] Không tìm thấy → "Da quet het khu, khong tim thay boss"
- [ ] Map không có boss (21,22,23...) → "Map nay khong co boss!"

### 10.3 Gim Boss
- [ ] `/autoboss gim` → focus boss HP thấp nhất
- [ ] Gim log hiển thị đúng tên + HP

### 10.4 Tele Boss
- [ ] `/autoboss tele` → tự động teleport đến boss
- [ ] Tele khi boss ở xa (> 30px)

### 10.5 Attack Boss
- [ ] `/autoboss attack` → tự động tấn công boss (tự bật tele)

### 10.6 Target list
- [ ] `/autoboss add Broly` → chỉ tìm boss Broly
- [ ] `/autoboss remove Broly` → bỏ boss Broly
- [ ] `/autoboss clear` → tìm tất cả boss

### 10.7 List status (hiển thị tracker sightings)
- [ ] `/autoboss list` → hiển thị:
  - [ ] Trạng thái ON/OFF
  - [ ] Danh sách target
  - [ ] Boss trong map (nếu có)
  - [ ] Boss tracker sightings 30 phút gần đây

### 10.8 Nhận diện boss
- [ ] Boss có tên viết hoa → nhận diện đúng
- [ ] Pet / Trọng tài / #name / $name → không nhận diện là boss

---

## 11. Auto Farm Nappa

### 11.1 Bật/tắt + chọn boss
- [ ] `/autonappa kuku` → farm Kuku (map 68-72)
- [ ] `/autonappa daudinh` → farm Mập đầu đinh (map 64-67)
- [ ] `/autonappa rambo` → farm Rambo (map 73-77)
- [ ] `/autonappa on` → farm với boss đang chọn
- [ ] `/autonappa off` → dừng farm

### 11.2 Cycle
- [ ] `/autonappa cycle` → chuyển 0→1→2→0

### 11.3 State machine (kiểm tra log)
- [ ] Initialize (state 0) → xác nhận "Khoi tao he thong"
- [ ] Xmap đến map boss (state 2)
- [ ] Vào map → mở UI zone → quét zone
- [ ] Tìm thấy boss → chuyển state Monitoring
- [ ] Boss bị damage → chuyển Fighting
- [ ] Boss chết → Picking Items (nhặt Mảnh Thiên Sứ)
- [ ] Hết zone → chuyển map tiếp theo

### 11.4 Xử lý sự cố
- [ ] Chết → tự hồi sinh + quay lại map
- [ ] Lạc map → tự động quay lại

### 11.5 List status
- [ ] `/autonappa list` → hiển thị trạng thái farm + tracker sightings

---

## 12. Auto Skill

### 12.1 Cấu hình slot
- [ ] `/autoskill 0 set 101 "Dragon"` → set skill slot 0
- [ ] `/autoskill list` → hiển thị 10 slot
- [ ] `/autoskill 0 on` → bật auto skill slot 0
- [ ] `/autoskill 0 off` → tắt
- [ ] `/autoskill 0 delay 800` → set delay 800ms
- [ ] `/autoskill 0 freeze` → freeze/unfreeze

### 12.2 Auto Attack
- [ ] `/autoskill attack` → bật auto attack
- [ ] Tự động tấn công mob focus
- [ ] `/autoskill shield` → bật auto khiên

### 12.3 All toggle
- [ ] `/autoskill all` → toggle tất cả slot

---

## 13. Auto Vứt Đồ

### 13.1 Bật/tắt
- [ ] `/vutdo on` → bật
- [ ] `/vutdo off` → tắt
- [ ] Prompt hiển thị `[VUT]> ` khi bật

### 13.2 Quản lý danh sách
- [ ] `/vutdo add 33 45 67` → thêm ID items
- [ ] `/vutdo delete 33` → xóa ID
- [ ] `/vutdo list` → xem danh sách
- [ ] `/vutdo clear` → xóa tất cả

### 13.3 Auto vứt
- [ ] Khi có item trong danh sách trong balo → tự động vứt
- [ ] Dùng `useItem(2, 1, i)` để vứt

---

## 14. Boss Tracker

### 14.1 /bosslog
- [ ] `/bosslog` → xem boss sightings 60 phút
- [ ] `/bosslog 30` → xem 30 phút
- [ ] Không có boss → "Khong co boss nao xuat hien"
- [ ] Có boss → hiển thị tên + thời gian + map + zone + vị trí

### 14.2 /tail (realtime)
- [ ] `/tail` → vào chế độ realtime
- [ ] Hiển thị "Ctrl+C de thoat"
- [ ] Refresh mỗi 3 giây
- [ ] Có sightings mới → in ra
- [ ] Không có sightings mới → không spam
- [ ] Ctrl+C → thoát → "Da thoat"

### 14.3 Tích hợp với /autoboss list
- [ ] `/autoboss list` → hiển thị tracker sightings (giống 14.1)
- [ ] `/autonappa list` → hiển thị tracker sightings

---

## 15. Item Detail

### 15.1 Phân tích item
- [ ] `/item 0` → hiển thị đúng tên + ID + sao
- [ ] Hiển thị upgrade (+4, +7...)
- [ ] Hiển thị sao (★☆☆☆☆)
- [ ] Hiển thị CH lỗ sao nếu có
- [ ] Hiển thị options/thuộc tính
- [ ] Hiển thị yêu cầu (level, power...)

### 15.2 Set kích hoạt
- [ ] Item có set → hiển thị "📦 Set: Tên Set"

### 15.3 Khóa
- [ ] Item bị khóa → hiển thị "🔒 Đã khóa"

---

## 16. Logging

### 16.1 Log levels
- [ ] `log all off` → không in log gì
- [ ] `log network debug` → in debug + info
- [ ] `log network on` → chỉ in info

### 16.2 Tags
- [ ] Tag `BOSS` → gắn màu đúng + category combat
- [ ] Tag `PICK` → đúng category item
- [ ] Tag `NAPPA` → đúng category
- [ ] Tag `ZONE` → đúng category

### 16.3 Compact mode
- [ ] Terminal hẹp (< 60 cột) → tự động bật compact mode
- [ ] Compact: `BOSS>msg` thay vì `[HH:MM:SS][INF][BOSS] msg`

---

## 17. Prompt

### 17.1 Các loại prompt
- [ ] `> ` — bình thường
- [ ] `[TRAIN]> ` — auto train đang bật
- [ ] `[VUT]> ` — auto vứt đồ đang bật
- [ ] `[BOSS]> ` — boss trong map HOẶC auto_boss đang bật
- [ ] `npc(7)> ` — đang trong menu NPC
- [ ] `xmap(Đi map 39...)> ` — xmap đang chạy

### 17.2 Kết hợp tags
- [ ] `[TRAIN BOSS]> ` — cả train + boss

---

## 18. Xử lý lỗi & Edge cases

### 18.1 Không crash
- [ ] Gõ lệnh sai syntax → thông báo "Usage: ..."
- [ ] Gõ lệnh không tồn tại → "Unknown: /abc"
- [ ] Server gửi packet lạ → không crash
- [ ] Mất kết nối đột ngột → hiển thị Disconnected

### 18.2 Input
- [ ] Gõ số khi có NPC menu → chọn option
- [ ] Gõ enter (dòng trống) → bỏ qua, không crash

### 18.3 Thread safety
- [ ] Auto updater (500ms) chạy ổn định
- [ ] Boss tracker chạy song song không crash
- [ ] Xmap + auto module cùng chạy → stable

---

## 19. Hỗ trợ tiếng Việt

### 19.1 Hiển thị
- [ ] Tên item tiếng Việt hiển thị đúng (không bị lỗi font)
- [ ] Tên NPC tiếng Việt hiển thị đúng
- [ ] Fallback UTF-8 khi console không hỗ trợ

### 19.2 Normalize (xmap waypoint)
- [ ] Waypoint popup name có dấu → match đúng
- [ ] So sánh không phân biệt dấu

---

## Ghi chú test

| Ngày test | Người test | Kết quả | Ghi chú |
|-----------|------------|---------|---------|
|           |            |         |         |
|           |            |         |         |
