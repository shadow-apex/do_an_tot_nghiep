# Đồ Án: Tay Robot 3 Bậc Tự Do + Băng Tải Phân Loại Vật Thể Theo Màu Sắc

Hệ thống: **Camera (nhận diện màu) → PC chạy Python (OpenCV) → Arduino
(động học ngược + điều khiển servo/băng tải) → Tay robot gắp-thả vào khay theo màu.**

Hệ thống chạy **HOÀN TOÀN TỰ ĐỘNG**, đúng theo luồng sau:

1. Băng tải tự bật khi cảm biến ĐẦU băng tải phát hiện có vật vừa được đặt vào,
   và **chạy liên tục không dừng** trong suốt quá trình vật di chuyển trên băng
   tải cho tới khi tới vị trí gắp (không dừng-chụp-dừng giữa chừng).
2. Khi vật vừa đi vào tầm nhìn camera — **vật vẫn đang di chuyển, băng tải chưa dừng** —
   Python liên tục chụp khung hình và nhận diện màu, đến khi đủ tin cậy thì **"khóa"**
   lại màu đã nhận diện được cho vật đó.
3. Băng tải **vẫn tiếp tục chạy** cho tới khi vật đến **đúng vị trí gắp đã lập trình
   sẵn (cố định)** — nơi có cảm biến hồng ngoại — thì Arduino **tự động dừng băng tải**.
4. Ngay lúc đó, Python gửi luôn màu đã "khóa" từ bước 2 cho Arduino (không cần chụp
   ảnh lại) → tay robot gắp tại vị trí cố định đó → bỏ vào khay đúng màu.
5. Băng tải trở về trạng thái chờ; khi cảm biến ĐẦU băng tải phát hiện vật tiếp
   theo được đặt vào, băng tải tự chạy lại, quay về bước 2.

> Vật không thuộc 4 màu đã định nghĩa vẫn được gắp bình thường và bỏ vào 1 khay
> riêng ("vật lạ") thay vì làm hệ thống bị kẹt.

---

| Nâng cấp | Lợi ích |
|---|---|
| **Nhận diện màu NGAY KHI vật còn di chuyển**, băng tải chỉ dừng khi tới đúng vị trí gắp | Đúng luồng vận hành thực tế: không phải dừng-chụp-dừng, tận dụng thời gian vật di chuyển để xử lý |
| **Vị trí gắp là CỐ ĐỊNH**, không tính tọa độ từ ảnh mỗi lần nữa | Đơn giản, ổn định hơn — camera chỉ lo việc phân loại màu, không lo tính toán vị trí |
| **`config.json`** chứa toàn bộ tham số hiệu chỉnh phía Python | Đổi cấu hình mà **không cần sửa code Python** |
| Bù sáng tự động (CLAHE) trước khi nhận diện màu | Nhận diện màu ổn định hơn khi ánh sáng thay đổi |
| Bỏ qua vật thể đang chạm viền khung hình | Không lấy nhầm màu của vật đang di chuyển vào/ra (chưa ổn định) |
| Bỏ phiếu đa số (majority vote) trên nhiều khung hình | Chống nhiễu tốt hơn cách cũ (yêu cầu *mọi* khung hình phải giống nhau tuyệt đối) |
| Tự hủy "khóa" màu nếu quá lâu không thấy báo tới vị trí gắp | Không bị "dính" mãi 1 màu cũ nếu vật rơi khỏi băng tải hoặc cảm biến lỗi |
| Khay riêng cho **"vật lạ"** (mã màu `X`) | Vật không thuộc 4 màu đã định nghĩa vẫn được gắp bỏ vào khay riêng, **không làm kẹt hệ thống** |
| Tự động kết nối lại Serial nếu bị rớt | Hệ thống tự phục hồi khi dây USB bị lỏng/nhiễu, không cần khởi động lại thủ công |
| Ghi log CSV (`sort_log.csv`) mỗi lần phân loại | Theo dõi hiệu suất, tỷ lệ thành công, phục vụ báo cáo đồ án |
| Hiệu chỉnh Arduino qua lệnh Serial + lưu **EEPROM** | Chỉnh `L0/L1/L2`, offset góc, **vị trí gắp cố định**, tọa độ khay **không cần nạp lại code** mỗi lần sai số |
| `hsv_color_detector.py` hỗ trợ webcam USB, lưu thẳng vào `config.json`, gộp nhiều lần đo | Hiệu chỉnh màu nhanh hơn, không phải gõ tay số liệu vào code |

---

## 1. Kiến trúc hệ thống

```
[Băng tải chạy liên tục]
        |
        v
[Camera] --(vật đi qua, CÒN DANG DI CHUYEN)--> [PC: color_sort_vision.py]
                                                 - Nhận diện màu (HSV + CLAHE)
                                                 - Bỏ phiếu đa số nhiều khung hình
                                                 - "Khóa" màu khi đủ tin cậy
                                                 (băng tải KHÔNG dừng ở bước này)
        |
        v (băng tải vẫn chạy tiếp)
[Cảm biến IR tại VỊ TRÍ GẮP CỐ ĐỊNH] --(vật tới)--> Arduino tự dừng băng tải
                                                            |
                                                     gửi "OBJ_DETECTED"
                                                            |
                                                            v
                                    [PC: color_sort_vision.py]
                                    - Gửi luôn màu đã "khóa" từ trước
                                    - Lệnh: "PICK:<MÀU>" qua Serial
                                            |
                                            v
                            [Arduino: arduino_arm_sorter.ino]
                            - Tính động học ngược (IK) từ VỊ TRÍ GẮP CỐ ĐỊNH
                            - Điều khiển 4 servo: Base/Shoulder/Elbow/Gripper
                            - Gắp vật, di chuyển đến khay đúng màu, thả
                            - Báo "DONE", tự chạy lại băng tải
```

---

## 2. Danh sách file trong gói

| File | Mô tả |
|---|---|
| `arduino/arduino_arm_sorter.ino` | Nạp vào Arduino Mega/Uno. Điều khiển servo (IK), băng tải, cảm biến, hiệu chỉnh qua EEPROM. |
| `python/color_sort_vision.py` | Chạy trên PC. Nhận diện màu + tọa độ, gửi lệnh qua Serial, tự động hoàn toàn. |
| `python/hsv_color_detector.py` | Công cụ hiệu chỉnh khoảng màu HSV, lưu thẳng vào `config.json`. |
| `python/config.json` | **File cấu hình trung tâm** — sửa ở đây, không cần sửa code. |
| `python/sort_log.csv` | Tự động tạo khi chạy — log lịch sử phân loại (thời gian, màu, tọa độ, kết quả). |
| `docs/BOM.md` | Danh sách linh kiện cần mua + gợi ý nơi mua. |
| `README.md` | File hướng dẫn này. |

---

## 3. Cài đặt phần mềm

### 3.1 Cài Python packages (trên PC)
```bash
pip install opencv-python numpy pyserial
```

### 3.2 Cài Arduino IDE
Tải tại: https://www.arduino.cc/en/software

Trong Arduino IDE, thư viện `Servo.h` đã có sẵn (built-in), không cần cài thêm.

---

## 4. Lắp ráp phần cứng

### 4.1 Tay robot (4 servo)
| Servo | Chức năng | Chân Arduino (mặc định trong code) |
|---|---|---|
| Servo 1 | Xoay đế (Base) | D3 |
| Servo 2 | Vai (Shoulder) | D5 |
| Servo 3 | Khuỷu (Elbow) | D6 |
| Servo 4 | Kẹp gắp (Gripper) | D9 |

⚠️ **Servo công suất lớn (MG996R) nên cấp nguồn 5-6V RIÊNG** (không lấy từ chân 5V
của Arduino), chung mass (GND) với Arduino. Nếu cấp chung nguồn Arduino, servo có
thể làm sụt áp gây reset Arduino liên tục.

### 4.2 Băng tải (động cơ DC qua module L298N)
| Tín hiệu | Chân Arduino |
|---|---|
| IN1 | D22 |
| IN2 | D23 |
| ENA (PWM tốc độ) | D2 |

Nguồn động cơ DC (VMS trên L298N): cấp riêng theo điện áp động cơ băng tải của bạn
(thường 6-12V), **không dùng chung nguồn servo**.

### 4.3 Cảm biến hồng ngoại phát hiện vật (CẦN 2 CẢM BIẾN)
Code hiện tại (`PIN_SENSOR`, `PIN_START_SENSOR`) và `so_do.md` dùng **2 cảm
biến quang E18**, không phải 1:

| Cảm biến | Vị trí lắp | Chân Arduino | Vai trò |
|---|---|---|---|
| Cảm biến ĐẦU băng tải | Ngay đầu vào băng tải, nơi đặt vật lên | D25 | Phát hiện có vật vừa đặt vào → Arduino **tự bật băng tải** |
| Cảm biến CUỐI băng tải | Đúng tại **vị trí gắp cố định** (xem Bước 3, mục 5) | D24 | Phát hiện vật đã tới vị trí gắp → Arduino **tự dừng băng tải** và báo `OBJ_DETECTED` |

- Nối chân tín hiệu (OUT) của từng cảm biến đúng theo bảng trên.
- ⚠️ **Cảm biến E18-D80NK có ngõ ra NPN cực thu hở (open-collector)**, bản thân
  nó không tự tạo được mức HIGH — bắt buộc phải có điện trở kéo lên VCC thì tín
  hiệu mới ổn định (xem thêm datasheet/hướng dẫn của E18-D80NK). Code hiện tại
  đã dùng `pinMode(..., INPUT_PULLUP)` để tận dụng điện trở kéo có sẵn trong
  Arduino nên **không bắt buộc phải gắn thêm điện trở ngoài**. Nếu vẫn thấy tín
  hiệu bị nhiễu/nhảy linh tinh dù không có vật, hãy gắn thêm 1 điện trở
  4.7K~10K từ chân tín hiệu lên VCC 5V cho chắc chắn hơn.
- Cảm biến loại phổ biến ra mức LOW khi phát hiện vật (đã cấu hình sẵn trong code
  là `active LOW`). Nếu cảm biến của bạn hoạt động ngược lại, đổi điều kiện
  `digitalRead(PIN_SENSOR) == LOW` (và/hoặc `digitalRead(PIN_START_SENSOR) == LOW`)
  thành `== HIGH` trong file `.ino`.
- Vặn biến trở trên mỗi cảm biến để chỉnh khoảng cách nhận biết phù hợp với vị trí
  đặt trên băng tải.
- Nếu bạn chỉ muốn dùng 1 cảm biến (băng tải luôn chạy liên tục, không cần cảm
  biến đầu để kích hoạt), có thể bỏ qua cảm biến D25 và gọi `conveyorOn()` ngay
  trong `setup()` thay vì chờ `startObjectPresent` — nhưng khi đó cần sửa lại
  `loop()` trong file `.ino` cho phù hợp.

### 4.4 Camera
- Gắn cố định phía trên vị trí gắp trên băng tải, hướng thẳng xuống.
- Dùng webcam USB thường (đơn giản nhất) hoặc điện thoại chạy app **IP Webcam**
  (Android) nếu không có webcam.

### 4.5 Nút dừng khẩn cấp (nếu có)
⚠️ **QUAN TRỌNG VỀ AN TOÀN**: Nút dừng khẩn cấp (nút đỏ nấm) nên đấu **trực tiếp
vào đường nguồn cấp cho động cơ/servo** (ngắt điện phần cứng), KHÔNG chỉ xử lý
bằng code. Nếu Arduino hoặc PC bị treo, code sẽ không phản ứng kịp — dừng bằng
phần cứng mới đảm bảo an toàn tuyệt đối.

---

## 5. Các bước hiệu chỉnh (BẮT BUỘC trước khi chạy thật)

Đây là bước quan trọng nhất — nếu bỏ qua, tay robot sẽ gắp sai vị trí hoặc chuyển
động sai.

### Bước 1: Đo chiều dài các khâu tay robot
Dùng thước đo (đơn vị cm):
- `L0`: chiều cao từ đế đến khớp vai (shoulder)
- `L1`: chiều dài khâu vai → khuỷu (upper arm)
- `L2`: chiều dài khâu khuỷu → cổ tay/gripper (forearm)

Điền vào đầu file `arduino_arm_sorter.ino`:
```cpp
const float L0 = 9.8;
const float L1 = 10.4;
const float L2 = 15.0;
```

### Bước 2: Hiệu chỉnh offset góc servo
Cách toán học IK tính ra góc lý thuyết, nhưng servo lắp thực tế có thể lệch.

Dùng **chế độ hiệu chỉnh thủ công** ở cuối file `.ino` (đã có sẵn, xem comment
`CHE DO HIEU CHINH SERVO THU CONG`) để dò góc:
1. Copy đoạn code trong comment vào hàm `loop()`, nạp lại.
2. Mở Serial Monitor (9600 baud), gõ `<số servo> <góc>`, ví dụ `0 90`.
3. Quan sát tay robot, ghi lại độ lệch.
4. Khôi phục lại `loop()` gốc, nạp lại code.

Sau đó **điền độ lệch qua lệnh Serial** (không cần nạp lại code lần nữa nếu
sau này cần chỉnh lại):
```
SET OFFB <do_lech_base>
SET OFFS <do_lech_shoulder>
SET OFFE <do_lech_elbow>
SAVECAL
```

### Bước 3: Đặt cảm biến IR và hiệu chỉnh VỊ TRÍ GẮP CỐ ĐỊNH
Cảm biến hồng ngoại (`PIN_SENSOR`) phải được lắp **đúng tại điểm mà bạn muốn
tay robot gắp vật** — vì băng tải sẽ luôn đưa vật đến đúng điểm này rồi dừng,
và tay robot **luôn gắp tại 1 tọa độ duy nhất** đó (không tính từ ảnh camera nữa).

Đo khoảng cách thật (cm) từ gốc đế robot đến điểm gắp này, rồi hiệu chỉnh qua
Serial Monitor (9600 baud, sau khi nạp code lần đầu):
```
SET PICKX 12.5
SET PICKY 0.0
SAVECAL
```
Gõ `SHOWCAL` để xem lại giá trị vừa lưu.

### Bước 4: Đo tọa độ khay thả
Đặt thước đo tọa độ (x, y) cm của từng khay so với gốc đế robot, hiệu chỉnh
tương tự qua Serial:
```
SET BINR_X 15.0
SET BINR_Y -15.0
SET BING_X 15.0
SET BING_Y 0.0
SET BINB_X 15.0
SET BINB_Y 15.0
SET BINY_X 15.0
SET BINY_Y 25.0
SET BINX_X 15.0
SET BINX_Y -30.0
SAVECAL
```
(`BINX` = khay riêng cho "vật lạ" — mã màu không xác định được)

Gõ `SHOWCAL` để xem lại toàn bộ thông số hiện tại, `LOADCAL` để nạp lại từ
EEPROM nếu vừa sửa sai. Nếu muốn, vẫn có thể sửa trực tiếp giá trị mặc định
trong code (`BIN_POS_RED`, `PICK_POS`...) rồi nạp lại Arduino — nhưng cách
qua Serial ở trên **không cần nạp lại code mỗi lần chỉnh sai số**.

### Bước 5: Hiệu chỉnh khoảng màu HSV
Chạy:
```bash
python python/hsv_color_detector.py
```
Chọn nguồn camera (webcam USB hoặc điện thoại qua IP Webcam), đưa từng vật mẫu
vào khung hình, nhấn phím `r`/`g`/`b`/`y` rồi kéo chuột chọn vùng màu. Có thể
lặp lại nhiều lần cho cùng 1 màu (ở các điều kiện ánh sáng khác nhau) — công cụ
sẽ tự gộp khoảng màu để ổn định hơn. Nhấn `s` để **lưu thẳng vào `config.json`**
(không cần copy tay vào code nữa).

> **Lưu ý về vị trí camera:** camera nên đặt ở **phía trước** vị trí cảm biến
> IR một khoảng đủ để có thời gian nhận diện màu trong lúc vật còn di chuyển
> (thường vài chục cm tùy tốc độ băng tải). Camera **không cần** nhìn thấy
> đúng điểm gắp — nó chỉ cần nhìn thấy vật rõ ràng trong lúc vật đi qua.

Các mục khác trong `config.json` (`camera_source`, `serial_port`,
`min_area`, `vote_threshold`, `use_lighting_correction`, `lock_timeout_seconds`,
`enable_unknown_object_fallback`...) đều có thể chỉnh trực tiếp — không cần
sửa file `.py`.

---

## 6. Chạy hệ thống

1. Nạp `arduino/arduino_arm_sorter.ino` vào Arduino (Tools → Board → chọn đúng
   loại board của bạn → Upload).
2. Nối Arduino với PC qua USB, xác định đúng cổng COM (Windows) hoặc
   `/dev/ttyACM0` (Linux), sửa `SERIAL_PORT` trong `color_sort_vision.py`.
3. Chạy:
```bash
python python/color_sort_vision.py
```
4. Hệ thống sẽ tự động: chạy băng tải → phát hiện vật → dừng băng tải → chụp
   ảnh phân loại màu → gắp → thả đúng khay → chạy lại băng tải.

Nhấn `q` trong cửa sổ camera hoặc `Ctrl+C` trong terminal để dừng.

Mọi lần phân loại đều được ghi vào `python/sort_log.csv` (thời gian, mã màu,
tọa độ pixel lúc khóa màu, kết quả) — mở bằng Excel để xem thống kê hoặc
để đưa vào báo cáo đồ án.

---

## 7. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Arduino bị reset liên tục khi servo chạy | Servo hút dòng lớn làm sụt áp | Cấp nguồn riêng cho servo, chung GND |
| Tay robot gắp sai vị trí | Chưa hiệu chỉnh L0/L1/L2, offset góc, hoặc `PICKX`/`PICKY` (vị trí gắp cố định) chưa khớp với vị trí cảm biến thực tế | Gõ `SHOWCAL` qua Serial Monitor để xem giá trị hiện tại, chỉnh lại bằng `SET ...` + `SAVECAL` (mục 5, Bước 1-4) |
| Không nhận được "OBJ_DETECTED" | Cảm biến sai logic HIGH/LOW, hoặc chưa đúng khoảng cách | Kiểm tra lại loại cảm biến, chỉnh biến trở |
| Nhận diện màu sai/nhiễu | Ánh sáng môi trường thay đổi, khoảng HSV chưa chuẩn | Chạy lại `hsv_color_detector.py`; nếu ánh sáng hay thay đổi, để `use_lighting_correction: true` trong `config.json` (mặc định đã bật) |
| Hệ thống bị kẹt vì vật không xác định được màu | Vật ngoài 4 màu đã định nghĩa | Không cần xử lý gì thêm — hệ thống tự gắp vật đó vào khay "vật lạ" (`BIN_POS_UNKNOWN`). Nếu muốn tắt tính năng này, đặt `enable_unknown_object_fallback: false` trong `config.json` |
| Lỗi `findContours` không chạy | Phiên bản OpenCV khác | Đảm bảo dùng cú pháp `contours, _ = cv2.findContours(...)` (OpenCV 4.x) |
| Serial không kết nối được / bị rớt khi đang chạy | Sai cổng COM, cổng bị chiếm bởi Serial Monitor, hoặc dây USB lỏng | Đóng Serial Monitor trước khi chạy Python; chương trình sẽ **tự động thử kết nối lại** tối đa 3 lần nếu bị rớt giữa chừng |
| Đổi cấu hình nhưng không thấy hiệu lực | Sửa nhầm trong `.py` thay vì `config.json`, hoặc Arduino chưa `SAVECAL` | Với thông số phía Python: chỉ cần sửa `config.json` rồi chạy lại. Với thông số phía Arduino: phải gõ `SAVECAL` sau khi `SET` thì mới lưu vĩnh viễn vào EEPROM |

---

## 8. Nguồn tham khảo

- Repo gốc cho phần thị giác máy tính (đếm lỗ, HSV):
  https://github.com/k-karlovic/robotic-object-sorter-with-computer-vision
- Repo tham khảo cho mô hình động học ngược (IK) tay robot 3-DOF:
  https://github.com/Mohammed-El-Kassoiri/vision-robotic-arm

Xem thêm `docs/BOM.md` để biết danh sách linh kiện cần mua.
