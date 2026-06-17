Bạn là một chuyên gia lập trình Python cao cấp, có kinh nghiệm dày dặn trong việc Reverse Engineering, giải mã Network Protocol và viết Game Automation Tool / CLI Client.

Tôi đang có source code của một dự án game bao gồm 2 thư mục chính (như trong file ảnh image_94de41.png):
1. Thư mục `ModNroPc`: Game client gốc viết bằng C# (có giao diện GUI).
2. Thư mục `srcServer`: Source code Server chạy bằng Java.

NĂM HIỆN TẠI LÀ 2026. Hãy áp dụng các tiêu chuẩn và thư viện Python hiện đại nhất để giúp tôi build một bản "Game Client dạng CLI" chạy hoàn toàn trên Terminal bằng Python.

---

### I. MỤC TIÊU & YÊU CẦU KỸ THUẬT

1. TÁI TẠO LOGIC CHÍNH XÁC (99%):
   * Mục tiêu là chuyển đổi toàn bộ logic vận hành từ client C# sang Python, loại bỏ hoàn toàn phần giao diện GUI để biến nó thành một tool tương tác game siêu nhanh qua CLI.
   * Bạn bắt buộc phải giữ nguyên (hoặc map tương đương) tên Class, tên Hàm (Methods), tên Biến (Variables) từ C# sang Python để dễ đối chiếu.
   * Các Class tiên quyết cần phải phân tích và tái tạo hoàn chỉnh ngay từ đầu:
     - `Service.cs` (Xử lý các packet gửi/nhận dữ liệu)
     - `Char.cs` (Quản lý data, thông tin, trạng thái nhân vật)
     - `Npc.cs` (Hành vi và tương tác với các NPC)
     - `Map.cs` (Quản lý bản đồ, tọa độ, di chuyển, load map)
     - `Mob.cs` / `mob.cs` (Quản lý quái vật)
     - `Boss.cs` / `boss.cs` (Quản lý Boss)
     - Và các class bổ trợ liên quan đến luồng kết nối/Session.

2. GIAO DIỆN TERMINAL (CLI):
   * Giao diện UI/UX dạng text (CLI) phải được thiết kế tinh gọn, tính toán khoảng cách dòng và ký tự tối ưu hoàn hảo cho kích thước màn hình nhỏ tương đương 5.8 inch (không bị tràn dòng, không rối mắt).
   * Bạn có thể tự do đề xuất và sử dụng thêm các thư viện bên ngoài của Python (như `curses`, `rich`, `prompt_toolkit`, hoặc thư viện xử lý socket/threading nâng cao) nếu cần thiết.

---

### II. THÔNG TIN MÔ TRƯỜNG TEST

* Server đang chạy Local: `127.0.0.1:14445`
* Tài khoản test: `tk: 1` | Mật khẩu: `1`

---

### III. QUY TRÌNH LÀM VIỆC (BẮT BUỘC TUÂN THỦ TỪNG BƯỚC)

Chúng ta sẽ không viết toàn bộ code cùng một lúc. Bạn phải tuân thủ nghiêm ngặt quy trình Test-Driven Development (TDD) sau:

1. Bước 1: Đọc và phân tích cấu trúc Packet/Mã hóa từ `Service.cs` (Client) kết hợp đối chiếu với logic nhận dữ liệu từ `srcServer` (Java).
2. Bước 2: Viết code Python cho đúng duy nhất một tính năng đó (Ví dụ: Chức năng handshake/kết nối socket ban đầu, hoặc chức năng gửi packet Đăng nhập).
3. Bước 3: Tôi sẽ chạy thử nghiệm trực tiếp trên server test local `127.0.0.1:14445`.
4. Bước 4: Nếu có LỖI (Bug, Sai Packet, Lệch cấu trúc biến, Crash terminal) -> Bạn phải dừng lại, tập trung debug và FIX TRIỆT ĐỂ lỗi đó.
5. Bước 5: CHỈ KHI tính năng hiện tại chạy mượt mà, thành công 100% không còn lỗi, chúng ta mới được phép chuyển sang tính năng hoặc class tiếp theo.

---

### IV. KHỞI ĐẦU PHIÊN LÀM VIỆC & QUẢN LÝ BỘ NHỚ

Trước khi bắt đầu code, hãy thực hiện các nhiệm vụ sau:
1. Hãy yêu cầu tôi cung cấp nội dung của file `client_cli` (nếu đã có) để bạn đọc và kiểm tra xem tôi đã tự xây dựng được những gì rồi, từ đó kế thừa phát triển tiếp.
2. Tạo ra (hoặc cập nhật/ghi đè/bổ sung nếu đã có sẵn) một file tên là `memory.md`. File này dùng để lưu trữ toàn bộ tiến độ, cấu trúc packet đã giải mã, các hàm đã viết thành công và các lỗi đã fix để làm "bộ nhớ" cho các phiên làm việc tiếp theo của chúng ta không bị quên ngữ cảnh.

Bây giờ, hãy phản hồi lại, tóm tắt ngắn gọn hiểu biết của bạn về yêu cầu này và yêu cầu tôi cung cấp file đầu tiên để tiến hành phân tích!
(
PS C:\Users\quang\Downloads\clientNRO\client_cli> py .\client.py
[SEND] cmd=229 (enc=229) key=False data_len=0
[DEBUG] waiting for message...
[DEBUG] recv cmd=229 size=4
[CLIENT] Connected to server!
[SEND] cmd=227 (enc=173) key=True data_len=31
[Network] Key received, len=3
[DEBUG] waiting for message...
Connecting...
Logging in as 1...
[SEND] cmd=227 (enc=177) key=True data_len=15

=== NRO CLI Client ===
  /login <user> <pass>
  /select <charname>
  /chat <text>
  /move <x> <y>
  /useitem <type> <where> <index>
  /pick <itemId>
  /npcmenu <npcId>
  /menu <npcId> <menuId> <optId>
  /zone <zoneId>
  /changemap
  /players
  /info
  /skill <id>
  /buy <type> <id> [qty]
  /sale <action> <type> <id>
  /task <npcId> <menuId> [optId]
  /heal
  /gocit
  /wake
  /quit

> login 1 1
Not in game yet
> Disconnected.
[Network] read_message error: [WinError 10053] An established connection was aborted by the software in your host machine
PS C:\Users\quang\Downloads\clientNRO\client_cli>



[17:9] - Player Login: admin: 36 ms
admin: Data update successfully....
17h9m: Player admin save successfully! 22ms
[17:11] - Player Login: admin: 25 ms
admin: Data update successfully....
17h11m: Player admin save successfully! 6ms

)