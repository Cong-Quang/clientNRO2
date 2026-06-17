# Memory - NRO CLI Client

## Current State

### Hoàn thành
- Auto-login flow: kết nối → setClientType → login → auto-select char → clientOk + updateMap/Skill/Item → finishLoadMap/Update
- `handle_me_load_point`: parse đúng 54 bytes theo Java server (7×Int + 4×Byte + 2×Int + 1×Byte + 1×Long + 1×Short + 1×Short + 1×Byte)
- `handle_player_add`: parse đúng theo Java server (clanID, level, boolean, typePk, gender×2, head, name(UTF), hp, hpMax, body, leg, bag, -1, x, y, effbuffhp/mp, numeff, idMark, monkey, mount, cFlag, 0, aura, effFront, hat)
- `handle_sub_command` SUB_ME_LOAD_ALL (sub=0): parse gold/gem/ruby từ initial load packet
- `handle_sub_command` SUB_ME_LOAD_INFO (sub=4): parse gold/gem/hp/mp/ruby
- `handle_send_money` (cmd=6): parse gold/gem/ruby khi có thay đổi
- `Char.py`: class lưu stats (HP/MP/Damage/Def/Crit/Speed/Potential/Gold/Gem), có format() với _fmt()
- Number formatting: k (nghìn), m (triệu), b (tỷ) — tự động
- `/info` command: hiển thị đầy đủ thông tin nhân vật
- Logger xử lý Unicode an toàn (safe_print fallback)

### Cách fix vàng không hiển thị

**Vấn đề:** Gold/Gem luôn hiển thị 0 dù server gửi dữ liệu.

**Nguyên nhân:**
1. Server gửi gold qua SUB_ME_LOAD_ALL (sub=0) trong `Service.player()`, không phải SUB_ME_LOAD_INFO (sub=4)
2. Handler SUB_ME_LOAD_ALL cũ chỉ ghi log "Loading all data..." mà không parse dữ liệu
3. Handler SUB_ME_LOAD_INFO (sub=4) đã viết đúng nhưng server không gửi sub=4 trong initial load

**Fix:**
1. Parse gold từ SUB_ME_LOAD_ALL (sub=0):
   - readInt(id) → readByte(taskId) → readByte(gender) → readShort(head) → readUTF(name) → readByte(cPk) → readByte(typePk) → readLong(power) → readShort×2(reserved) → readByte(gender2) → readByte(skillCount) → readShort×skillCount → try readLong/readInt(gold) → readInt(ruby) → readInt(gem)
2. Thêm handler `handle_send_money` cho cmd=6:
   - try readLong/readInt(gold) → readInt(gem) → readInt(ruby)
   - Java server chỉ dùng cmd=6 cho sendMoney (theo C# Controller.cs), dù cmd=6 cũng là UPDATE_MAP

### Vấn đề còn lại
- Name hiển thị có clan prefix (`$Đệ tử`) — do server gửi `Service.gI().name()` có thêm `[$CLAN]`
- Console Windows (cp1252) không hiển thị được ký tự Unicode như Đ, ệ, ư → đã xử lý fallback an toàn
- Chưa xử lý inventory, skill, NPC interaction

### Server Test
- Host: 127.0.0.1:14445
- Account: tk=1, mk=1
- Version string: "2.4.5" → server parse thành 245 → dùng writeLong cho gold

### Files chính
- `handlers/world.py`: ME_LOAD_POINT, PLAYER_ADD, SUB_COMMAND, sendMoney
- `handlers/authentication.py`: char_list, not_map (select/enter game)
- `Char.py`: Character class + _fmt number formatting
- `logger.py`: Unicode-safe print
- `client.py`: Dispatcher mapping
- `cmd.py`: Command constants
