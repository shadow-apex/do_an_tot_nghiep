# Danh Sách Linh Kiện (BOM) - Tay Robot 3 Bậc + Băng Tải

⚠️ Giá và tồn kho có thể thay đổi theo thời gian, đây là link tham khảo tại thời
điểm soạn tài liệu (2026). Hãy kiểm tra lại giá/tình trạng hàng trước khi đặt mua.
Ngoài Hshop.vn còn có thể tìm ở Shopee, Lazada, Linh Kiện Điện Tử, Nshop, DIYtech...

## Bộ điều khiển

| Linh kiện | Thông số gợi ý | Số lượng | Tham khảo |
|---|---|---|---|
| Arduino Mega 2560 | Nhiều chân I/O hơn Uno, phù hợp nhiều servo + động cơ + cảm biến | 1 | https://hshop.vn/products/arduino-mega-2560r3 |
| Mạch cầu H L298N | Điều khiển động cơ DC băng tải, dòng tối đa 2A/kênh | 1 | https://hshop.vn/products/arduino-motor-shield-l298 |

## Tay robot (servo)

| Linh kiện | Thông số gợi ý | Số lượng | Tham khảo |
|---|---|---|---|
| Servo TowerPro MG996R (chính hãng, bánh răng kim loại) | Lực kéo ~11kg/cm ở 6V, góc quay 180° | 4 (base, shoulder, elbow, gripper) | https://hshop.vn/dong-co-rc-servo-towerpro-mg996-chinh-hang-genuine |
| Nguồn 5-6V riêng cho servo (dòng ≥3A) | Cấp riêng, tránh sụt áp Arduino | 1 | Tùy chọn theo tổng dòng tiêu thụ |

> Lưu ý: MG996R hàng "không chính hãng" giá rẻ hơn (bánh răng nhựa) nhưng độ bền
> và độ chính xác kém hơn — với đồ án cần độ chính xác vị trí (IK), nên ưu tiên
> bản bánh răng kim loại.

## Băng tải

| Linh kiện | Thông số gợi ý | Số lượng | Tham khảo |
|---|---|---|---|
| Động cơ DC giảm tốc (kèm bánh răng) | Tùy tải trọng băng tải, 6-12V | 1 | Tìm "động cơ DC giảm tốc băng tải mini" trên Shopee/Hshop |
| Dây băng tải + con lăn + khung | Mua bộ kit hoặc tự chế bằng nhôm định hình | 1 bộ | Tìm "kit băng tải mini DIY" |

## Cảm biến

| Linh kiện | Thông số gợi ý | Số lượng | Tham khảo |
|---|---|---|---|
| Cảm biến hồng ngoại vật cản (IR Obstacle / quang E18) | Ngõ ra digital, có biến trở chỉnh khoảng cách | 2 (1 ở đầu băng tải để tự bật băng tải - D25, 1 ở vị trí gắp để tự dừng băng tải - D24) | https://hshop.vn/products/cam-bien-vat-can-hong-ngoai-v1-2 |

## Camera

| Linh kiện | Thông số gợi ý | Số lượng | Tham khảo |
|---|---|---|---|
| Webcam USB (720p trở lên) | Gắn cố định phía trên vị trí gắp | 1 | Bất kỳ webcam USB phổ thông |
| (Thay thế) Điện thoại + app IP Webcam | Nếu không có webcam rời | - | App "IP Webcam" trên CH Play |

## An toàn & phụ kiện

| Linh kiện | Thông số gợi ý | Số lượng | Tham khảo |
|---|---|---|---|
| Nút dừng khẩn cấp (nút nấm đỏ, tự giữ) | Đấu trực tiếp vào nguồn động cơ/servo | 1 | Tìm "nút dừng khẩn cấp emergency stop 22mm" |
| Rơ-le/contactor cách ly nguồn | Dùng cùng nút dừng khẩn cấp để cắt điện phần động lực | 1 | Tùy công suất hệ thống |
| Dây jumper, breadboard/board đồng | Đấu nối mạch điều khiển | 1 bộ | Bất kỳ shop linh kiện điện tử |
| Nguồn tổ ong 5V/12V (tùy nhu cầu) | Cấp nguồn động cơ, servo | 1-2 | Tìm "nguồn tổ ong Meanwell" |

---

## Gợi ý tổng chi phí (tham khảo, KHÔNG bao gồm khung cơ khí/băng tải tự chế)

- Arduino Mega: ~150.000 - 250.000đ
- 4x Servo MG996R chính hãng: ~240.000đ x 4 ≈ 960.000đ (bản không chính hãng rẻ hơn nhiều, ~80.000đ x 4)
- L298N: ~30.000 - 50.000đ
- Cảm biến IR (2 cái): ~15.000 - 30.000đ x 2 ≈ 30.000 - 60.000đ
- Nguồn tổ ong: ~150.000 - 300.000đ

→ Chi phí phần điện tử dao động khá nhiều tùy bạn chọn servo chính hãng hay không,
nên cân nhắc theo ngân sách đồ án.
