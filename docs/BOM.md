# Danh Sách Linh Kiện (BOM) - Tay Robot 3 Bậc + Băng Tải

⚠️ Giá và tồn kho **đã được kiểm tra lại qua tìm kiếm trực tuyến** tại thời điểm
cập nhật tài liệu này (08/2026), chủ yếu tại Hshop.vn (269/20 Lý Thường Kiệt,
P.15, Q.11, TP.HCM — gần ĐH Bách Khoa). Giá có thể đổi theo thời gian/khuyến
mãi, hãy bấm vào link kiểm tra lại tình trạng hàng trước khi đặt mua. Ngoài
Hshop.vn còn có thể tìm ở Nshop, Shopee, Lazada, Linh Kiện Điện Tử, DIYtech...

## Bộ điều khiển

| Linh kiện | Thông số gợi ý | Số lượng | Giá tham khảo | Link |
|---|---|---|---|---|
| Arduino Mega 2560 (bản CH340, tương thích) | Nhiều chân I/O hơn Uno, phù hợp nhiều servo + động cơ + cảm biến | 1 | ~140.000₫ | https://hshop.vn/products/arduino-mega-2560r3 |
| (Tùy chọn) Arduino Mega 2560 chính hãng (Original, Made in Italy) | Nếu cần hàng chính hãng có tem chống giả, đắt hơn bản CH340 | 1 | Xem giá tại link | https://hshop.vn/products/arduino-mega-2560-chinh-hang-original-made-in-italy |
| **Module L298N rời (KHÔNG phải Motor Shield)** | Board rời có chân IN1-IN4/ENA/ENB/OUT1-OUT4, đấu dây jumper tự do — đúng loại code & `so_do.md` đang dùng (chân D22/D23/D2 tùy chỉnh). Dòng tối đa 2A/kênh | 1 | 45.000₫ | https://hshop.vn/products/mach-dieu-khien-dong-co-dc-l298 |

⚠️ **Lưu ý quan trọng:** bản BOM cũ từng trỏ tới "Arduino Motor Shield L298"
(dạng shield cắm chồng lên Arduino, chân điều khiển CỐ ĐỊNH là D10/D11/D12/D13,
không đổi được) — **KHÔNG dùng loại này**, vì code hiện tại dùng các chân tùy
chỉnh D2/D22/D23 nối bằng dây jumper tới module L298N rời như trên.

## Tay robot (servo)

| Linh kiện | Thông số gợi ý | Số lượng | Giá tham khảo | Link |
|---|---|---|---|---|
| Servo TowerPro MG996R chính hãng (Genuine, bánh răng kim loại) | Lực kéo ~11kg/cm ở 6V, góc quay 0-180° | 4 (base, shoulder, elbow, gripper) | 240.000₫/cái | https://hshop.vn/dong-co-rc-servo-towerpro-mg996-chinh-hang-genuine |
| Nguồn tổ ong 5V riêng cho servo (**khuyến nghị ≥6A**, xem ghi chú an toàn điện trong `so_do.md`) | Cấp riêng, tránh sụt áp Arduino, chung GND với Arduino. MG996R có dòng khởi động (stall) tới ~2.5A/con khi bị kẹt, 4 servo cùng lúc có thể đỉnh tới ~10A dù hiếm khi xảy ra — nguồn 4A là mức TỐI THIỂU, nên ưu tiên 6-10A nếu ngân sách cho phép | 1 | Xem giá tại link | https://nshopvn.com/product/nguon-to-ong-5v-4a/ |

> Lưu ý: MG996R hàng "không chính hãng" giá rẻ hơn (bánh răng nhựa) nhưng độ bền
> và độ chính xác kém hơn — với đồ án cần độ chính xác vị trí (IK), nên ưu tiên
> bản bánh răng kim loại chính hãng.

## Băng tải

| Linh kiện | Thông số gợi ý | Số lượng | Giá tham khảo | Link |
|---|---|---|---|---|
| Động cơ DC giảm tốc JGB37-550 12VDC (kim loại) | Nhiều tỉ số truyền để chọn giữa lực kéo/tốc độ, phù hợp kéo băng tải mini | 1 | 195.000₫ | https://hshop.vn/dong-co-dc-giam-toc-ga37-125rpm-1 |
| Kit băng tải mini DIY (dây băng + con lăn + khung + động cơ DC 12-24V có điều tốc) | Nếu không muốn tự chế khung, mua nguyên kit lắp sẵn | 1 bộ | Xem giá tại link | https://shopee.vn/B%C4%83ng-t%E1%BA%A3i-mini-gi%C3%A1-r%E1%BA%BB-c%C3%B3-%C4%91i%E1%BB%81u-t%E1%BB%91c-nhanh-ch%E1%BA%ADm-%C4%91%E1%BB%99ng-c%C6%A1-DC12-24V-i.142343169.28808437523 |
| Nguồn tổ ong 12V (dòng theo công suất động cơ băng tải) | Cấp riêng cho VMS trên L298N, KHÔNG dùng chung nguồn servo | 1 | Xem giá tại link | https://nshopvn.com/product/nguon-to-ong-12v-5a/ |

> Nếu tự chế khung: dùng nhôm định hình (phổ biến 20x40/30x30), dây băng PVC
> dày ~2mm, con lăn ở 2 đầu — tìm "khung nhôm định hình băng tải mini" hoặc
> "con lăn băng tải mini" trên Shopee nếu cần mua lẻ từng phần.

## Cảm biến (CẦN 2 CÁI — xem `so_do.md`)

| Linh kiện | Thông số gợi ý | Số lượng | Giá tham khảo | Link |
|---|---|---|---|---|
| Cảm biến quang hồng ngoại **E18-D80NK** (thân trụ, chỉnh khoảng cách 3-80cm bằng biến trở) | Ngõ ra NPN cực thu hở (open-collector) — cần `INPUT_PULLUP` hoặc điện trở kéo ngoài 1-10K (đã xử lý trong code), 3 dây: Nâu=VCC 5V, Xanh dương=GND, Đen=Tín hiệu | 2 (1 đặt ở đầu băng tải → D25, 1 đặt tại vị trí gắp → D24) | 105.000₫/cái | https://hshop.vn/cam-bien-vat-can-hong-ngoai-e18-d80nk-4 |

⚠️ Đây **không phải** loại module cảm biến vật cản hồng ngoại nhỏ dạng PCB xanh
lá thường thấy trong các kit robot dò line (loại đó có mạch so sánh onboard,
ngõ ra khác) — `so_do.md` yêu cầu đúng loại **E18-D80NK thân kim loại/nhựa
hình trụ** như trên để khớp với ghi chú màu dây trong sơ đồ.

## Camera

| Linh kiện | Thông số gợi ý | Số lượng | Link |
|---|---|---|---|
| Webcam USB (720p trở lên) | Gắn cố định phía trên vị trí camera nhìn thấy vật, không cần thấy đúng điểm gắp | 1 | Bất kỳ webcam USB phổ thông (Logitech C270, C310...) |
| (Thay thế) Điện thoại + app IP Webcam | Nếu không có webcam rời | - | App "IP Webcam" trên CH Play |

## An toàn & phụ kiện

| Linh kiện | Thông số gợi ý | Số lượng | Giá tham khảo | Link |
|---|---|---|---|---|
| Cầu chì tự phục hồi (PTC resettable fuse) ~5A cho đường 5V, ~3A cho đường 12V | Lắp ngay sau nguồn tổ ong trên dây (+), bảo vệ quá dòng khi lỡ chập dây | 2 | Xem giá tại link | https://dientu360.com/cau-chi-tu-phuc-hoi-5a |
| Tụ hóa 1000-2200µF/16V | Gắn gần điểm đấu chung VCC 4 servo, giảm sụt áp khi servo khởi động/đổi hướng đột ngột | 1-2 | Vài nghìn đồng/cái | Bất kỳ shop linh kiện điện tử |
| Nút dừng khẩn cấp LA38-11ZS phi 22mm (đầu nấm, tự giữ, 1NO+1NC) | Đấu trực tiếp vào đường nguồn động cơ/servo (ngắt phần cứng), KHÔNG chỉ xử lý bằng code | 1 | Xem giá tại link | https://linhkienvietnam.vn/nut-dung-khan-cap-stop-la38-11zs-phi-22mm-stop-emergency-button |
| Rơ-le/contactor cách ly nguồn | Dùng cùng nút dừng khẩn cấp để cắt điện phần động lực | 1 | Tùy công suất hệ thống | Tìm "relay/contactor cách ly nguồn 220V" theo dòng tải thực tế |
| Dây jumper (đực-đực, đực-cái, cái-cái) | Đấu nối mạch điều khiển, cảm biến, L298N | 1 bộ | Xem giá tại link | https://hshop.vn/day-cam-breadboard-connector |
| Nguồn tổ ong 5V/12V | Đã liệt kê ở mục Servo/Băng tải phía trên | 2 | — | (xem 2 link nguồn tổ ong ở trên) |

---

## Gợi ý tổng chi phí (tham khảo, KHÔNG bao gồm khung cơ khí/băng tải tự chế)

- Arduino Mega (CH340): ~140.000đ
- 4x Servo MG996R chính hãng: 240.000đ x 4 = 960.000đ (bản không chính hãng rẻ hơn nhiều, ~80.000đ x 4)
- Module L298N rời: 45.000đ
- Động cơ DC giảm tốc JGB37-550: 195.000đ
- Cảm biến E18-D80NK (2 cái): 105.000đ x 2 = 210.000đ
- Nguồn tổ ong 5V + 12V: tham khảo giá tại 2 link ở mục Servo/Băng tải
- Nút dừng khẩn cấp: tham khảo giá tại link

→ Tổng phần điện tử (không tính nguồn, khung, dây jumper): dao động khoảng
1.550.000đ trở lên tùy servo chính hãng hay không — nên cân nhắc theo ngân
sách đồ án và kiểm tra lại giá thực tế trước khi mua vì có thể thay đổi.
