"""
color_sort_vision.py  (ban sua luong hoat dong cho dung yeu cau)
-------------------------------------------------------------------
Chuong trinh dieu khien phia PC cho he thong tay gap + bang tai + camera.
Chay HOAN TOAN TU DONG.

LUONG HOAT DONG (DA SUA LAI CHO DUNG YEU CAU):
  1. Bang tai TU BAT khi cam bien DAU bang tai (D25, ben Arduino) phat hien
     vat vua duoc dat vao, roi CHAY LIEN TUC (khong dung-chup-dung) cho toi
     khi vat den vi tri gap.
  2. Khi vat di chuyen vao vung camera nhin thay (vat VAN DANG DI CHUYEN,
     bang tai CHUA dung), Python lien tuc chup khung hinh va phan loai
     mau bang bo phieu da so -> khi du tin cay se "KHOA" lai mau da nhan
     dien duoc cho vat nay (khong can bang tai dung lai moi phan loai duoc).
  3. Bang tai VAN TIEP TUC CHAY cho toi khi vat den DUNG VI TRI GAP da lap
     trinh san (vi tri co dinh, xac dinh boi cam bien IR gan o do) ->
     Arduino TU DONG dung bang tai va bao "OBJ_DETECTED".
  4. Python nhan tin hieu "OBJ_DETECTED", gui NGAY mau da khoa tu buoc 2
     cho Arduino (khong can tinh toa do tu anh nua vi vi tri gap la CO
     DINH, da hieu chinh san trong Arduino) -> tay robot gap tai vi tri
     co dinh do va tha vao khay theo mau.
  5. Bang tai tu chay lai, he thong quay ve buoc 2 cho vat tiep theo.

  Neu vi ly do nao do (anh sang qua kem, vat di qua nhanh...) ma chua
  kip khoa duoc mau truoc khi vat den vi tri gap, chuong trinh se thu
  phan loai nhanh 1 lan nua ngay luc do; neu van khong duoc se tu dong
  xep vat vao khay "vat la" thay vi lam ket he thong.

NANG CAP:
  1. Doc toan bo tham so hieu chinh tu config.json (khong can sua code)
  2. Bu sang (CLAHE) giup nhan dien mau on dinh hon khi anh sang thay doi
  3. Loc bo vat the cham vien khung hinh (dang di chuyen vao/ra, chua on dinh)
  4. Bo phieu da so (majority vote) tren nhieu khung hinh de chong nhieu
  5. Vat KHONG thuoc 4 mau da biet -> tu dong xep vao khay "vat la" (rieng)
  6. Tu dong ket noi lai Serial neu bi rot ket noi giua chung
  7. Ghi log CSV moi lan phan loai (thoi gian, mau, toa do pixel, ket qua)
  8. KHONG can hieu chuan pixel->cm nua: vi tri gap la CO DINH, hieu chinh
     truc tiep tren Arduino qua lenh Serial (xem README, muc "PICK_X/PICK_Y")

CAI DAT:
  pip install opencv-python numpy pyserial
"""

import cv2
import numpy as np
import serial
import time
import json
import os
import csv
from collections import deque, Counter

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


# ============ NAP CAU HINH TU config.json ============

def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Khong tim thay file cau hinh: {path}\n"
            f"Hay dam bao file config.json nam cung thu muc voi color_sort_vision.py."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


CFG = load_config()

CAMERA_SOURCE = CFG["camera_source"]
SERIAL_PORT = CFG["serial_port"]
BAUD_RATE = CFG["baud_rate"]

MIN_AREA = CFG["min_area"]
MAX_AREA = CFG.get("max_area", 100000)
HISTORY_WINDOW = CFG.get("history_window", 10)
VOTE_THRESHOLD = CFG.get("vote_threshold", 7)
IGNORE_EDGE = CFG.get("ignore_edge_touching_objects", True)
USE_LIGHTING_CORRECTION = CFG.get("use_lighting_correction", True)

ENABLE_UNKNOWN_FALLBACK = CFG.get("enable_unknown_object_fallback", True)
UNKNOWN_MIN_AREA = CFG.get("unknown_object_min_area", 900)
UNKNOWN_SAT_THRESH = CFG.get("unknown_object_saturation_thresh", 40)

# Neu vat "khoa" mau roi nhung qua lau (giay) ma Arduino van chua bao
# OBJ_DETECTED (vd vat roi khoi bang tai, ket, hoac cam bien loi) thi
# tu huy khoa de khong bi "dinh" mau cu mai cho vat sau.
LOCK_TIMEOUT_S = CFG.get("lock_timeout_seconds", 25.0)

COLOR_RANGES = {
    key: {
        "lower": tuple(val["lower"]),
        "upper": tuple(val["upper"]),
        # lower2/upper2: dai mau PHU (tuy chon) - dung cho mau DO, vi Hue
        # cua mau do nam o 2 dau vong tron Hue trong OpenCV (gan 0 VA gan
        # 180). Neu chi dung 1 dai lower/upper duy nhat se BO SOT mau do
        # roi vao dau con lai. Xem "_note_red_wraparound" trong config.json.
        "lower2": tuple(val["lower2"]) if "lower2" in val else None,
        "upper2": tuple(val["upper2"]) if "upper2" in val else None,
        "name": val["name"],
    }
    for key, val in CFG["color_ranges"].items()
}

LOG_ENABLED = CFG.get("log_enabled", True)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), CFG.get("log_file", "sort_log.csv"))

# Ma mau gui cho Arduino khi khong xac dinh duoc mau -> khay "vat la"
UNKNOWN_COLOR_CODE = "X"


# ============ GHI LOG ============

def init_log():
    if not LOG_ENABLED:
        return
    is_new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["timestamp", "color_code", "color_name",
                              "pixel_x_luc_khoa", "pixel_y_luc_khoa", "result"])


def log_event(color_code, color_name, center, result):
    if not LOG_ENABLED:
        return
    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                color_code, color_name,
                center[0] if center else "",
                center[1] if center else "",
                result,
            ])
    except Exception as e:
        print(f"[CANH BAO] Khong ghi duoc log: {e}")


# ============ CAC HAM XU LY ANH ============

def open_camera(source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Khong mo duoc camera: {source}")
    return cap


def open_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=0)  # non-blocking read
        time.sleep(2)  # cho Arduino reset xong sau khi mo cong serial
        print(f"Da ket noi Serial: {port}")
        return ser
    except Exception as e:
        print(f"[CANH BAO] Khong mo duoc Serial ({port}): {e}")
        return None


def reconnect_serial(port, baud, retries=3, delay_s=2.0):
    """Thu ket noi lai Serial khi bi rot ket noi giua chung (VD rut/cam lai day USB)."""
    for i in range(retries):
        print(f"Dang thu ket noi lai Serial ({i+1}/{retries})...")
        ser = open_serial(port, baud)
        if ser is not None:
            return ser
        time.sleep(delay_s)
    return None


def read_serial_line_nonblocking(ser):
    """Doc 1 dong Serial neu co san, khong cho (non-blocking).
    Tra ve None neu chua co du lieu."""
    if ser is None:
        return None
    if ser.in_waiting <= 0:
        return None
    try:
        raw = ser.readline()
    except Exception:
        raise
    if not raw:
        return None
    line = raw.decode(errors="ignore").strip()
    return line if line else None


def wait_for_arduino_message(ser, expected, timeout_s=30.0):
    """Cho Arduino gui 1 dong tin nhan cu the (dung cho luc gui lenh gap-tha,
    can biet chac chan robot da lam xong truoc khi tiep tuc)."""
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            line = read_serial_line_nonblocking(ser)
        except Exception:
            return False
        if line:
            print(f"[Arduino] {line}")
            if line == expected:
                return True
        else:
            time.sleep(0.03)
    return False


def apply_lighting_correction(bgr_frame):
    """Can bang sang bang CLAHE tren kenh L (Lab) - giup nhan dien mau
    on dinh hon khi anh sang moi truong thay doi (VD may co bong den, cua so)."""
    if not USE_LIGHTING_CORRECTION:
        return bgr_frame
    lab = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def touches_edge(contour, frame_shape, margin=4):
    """True neu vat the dang cham vien khung hinh - dang di chuyen vao/ra,
    vi tri/hinh dang chua on dinh, khong nen dung de phan loai."""
    x, y, w, h = cv2.boundingRect(contour)
    fh, fw = frame_shape[:2]
    return x <= margin or y <= margin or (x + w) >= (fw - margin) or (y + h) >= (fh - margin)


def detect_color_and_position(hsv_frame, frame_shape):
    """Tra ve (ma_mau, dien_tich, (px, py) tam vat) cua mau co dien tich lon nhat
    trong so cac vat KHONG cham vien khung hinh."""
    best_key, best_area, best_center = None, 0, None

    for key, cfg in COLOR_RANGES.items():
        mask = cv2.inRange(hsv_frame, np.array(cfg["lower"]), np.array(cfg["upper"]))
        if cfg.get("lower2") is not None and cfg.get("upper2") is not None:
            # Gop them dai mau phu (VD: do o dau con lai cua vong tron Hue)
            mask2 = cv2.inRange(hsv_frame, np.array(cfg["lower2"]), np.array(cfg["upper2"]))
            mask = cv2.bitwise_or(mask, mask2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        for c in contours:
            area = cv2.contourArea(c)
            if area < MIN_AREA or area > MAX_AREA:
                continue
            if IGNORE_EDGE and touches_edge(c, frame_shape):
                continue
            if area > best_area:
                M = cv2.moments(c)
                if M["m00"] == 0:
                    continue
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                best_key, best_area, best_center = key, area, (cx, cy)

    return best_key, best_area, best_center


def detect_unknown_object(hsv_frame, frame_shape):
    """Neu khong khop mau nao da biet, thu tim VAT THE bat ky (khac nen bang
    tai) bang kenh Saturation, de van xep vat vao khay "vat la" thay vi
    bo qua vo han lan. Gia dinh bang tai la mau trung tinh (trang/xam/den).
    NEU BANG TAI CO MAU KHAC, chinh UNKNOWN_SAT_THRESH trong config.json."""
    if not ENABLE_UNKNOWN_FALLBACK:
        return None

    s_channel = hsv_frame[:, :, 1]
    _, mask = cv2.threshold(s_channel, UNKNOWN_SAT_THRESH, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < UNKNOWN_MIN_AREA or area > MAX_AREA:
        return None
    if IGNORE_EDGE and touches_edge(c, frame_shape):
        return None

    M = cv2.moments(c)
    if M["m00"] == 0:
        return None
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)


def detect_frame(hsv_frame, frame_shape):
    """Ket hop nhan dien 4 mau da biet + fallback vat la, tra ve
    (ma_mau_hoac_None, (px,py)_hoac_None)."""
    color_key, area, center = detect_color_and_position(hsv_frame, frame_shape)
    if color_key is not None:
        return color_key, center

    unknown_center = detect_unknown_object(hsv_frame, frame_shape)
    if unknown_center is not None:
        return UNKNOWN_COLOR_CODE, unknown_center

    return None, None


def get_color_name(color_key):
    if color_key == UNKNOWN_COLOR_CODE:
        return "VAT LA (khong xac dinh mau)"
    return COLOR_RANGES.get(color_key, {}).get("name", color_key)


def quick_classify_once(cap):
    """Phan loai nhanh CHI 1 khung hinh hien tai - dung lam phuong an du
    phong khi vat da toi vi tri gap ma van chua kip 'khoa' mau luc dang
    di chuyen (VD anh sang qua kem, vat di qua nhanh)."""
    ok, frame = cap.read()
    if not ok:
        return UNKNOWN_COLOR_CODE, None
    corrected = apply_lighting_correction(frame)
    blurred = cv2.GaussianBlur(corrected, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    color_key, center = detect_frame(hsv, frame.shape)
    if color_key is None:
        return UNKNOWN_COLOR_CODE, None
    return color_key, center


def main():
    cap = open_camera(CAMERA_SOURCE)
    ser = open_serial(SERIAL_PORT, BAUD_RATE)
    init_log()

    if ser is None:
        print("Khong co Serial - chi chay o che do XEM TRUOC camera, khong dieu khien duoc Arduino.")

    print("He thong chay TU DONG. Camera se nhan dien mau NGAY KHI vat con")
    print("dang di chuyen tren bang tai (chua can dung). Bang tai chi dung")
    print("khi vat toi dung vi tri gap da lap trinh san.")
    print("Nhan 'q' trong cua so anh hoac Ctrl+C trong terminal de thoat.\n")

    history = deque(maxlen=HISTORY_WINDOW)
    pending_color = None      # mau da "khoa" cho vat dang tien toi vi tri gap
    pending_center = None     # vi tri pixel luc khoa mau (chi de ghi log)
    lock_time = None

    try:
        while True:
            # ---- 1) Kiem tra tin hieu tu Arduino (khong chan luong) ----
            if ser is not None:
                try:
                    line = read_serial_line_nonblocking(ser)
                except serial.SerialException:
                    print("[CANH BAO] Mat ket noi Serial, dang thu noi lai...")
                    ser = reconnect_serial(SERIAL_PORT, BAUD_RATE)
                    line = None

                if line:
                    print(f"[Arduino] {line}")

                    if line == "OBJ_DETECTED":
                        # Vat da toi DUNG VI TRI GAP co dinh - bang tai da tu dung.
                        color_to_send = pending_color

                        if color_to_send is None:
                            # Chua kip khoa mau luc di chuyen -> thu phan loai
                            # nhanh 1 lan nua ngay luc nay de khong bo lo vat.
                            print("Chua kip nhan dien mau luc di chuyen, thu phan loai nhanh...")
                            color_to_send, _ = quick_classify_once(cap)

                        color_name = get_color_name(color_to_send)
                        print(f">> Gap vat mau {color_name} tai vi tri gap co dinh")

                        try:
                            ser.write(f"PICK:{color_to_send}\n".encode())
                        except serial.SerialException:
                            print("[CANH BAO] Mat ket noi Serial khi gui lenh, dang thu noi lai...")
                            ser = reconnect_serial(SERIAL_PORT, BAUD_RATE)
                            log_event(color_to_send, color_name, pending_center, "loi_serial")
                        else:
                            done = wait_for_arduino_message(ser, "DONE", timeout_s=20.0)
                            log_event(color_to_send, color_name, pending_center,
                                      "thanh_cong" if done else "het_thoi_gian_cho")

                        # San sang cho vat tiep theo
                        pending_color = None
                        pending_center = None
                        lock_time = None
                        history.clear()

                    elif line == "CONV_TIMEOUT_NO_OBJECT":
                        # Arduino tu dung bang tai vi chay qua lau ma khong
                        # thay vat toi vi tri gap (vat roi khoi bang tai,
                        # ket, cam bien hong...). Huy khoa mau ngay (neu co)
                        # thay vi phai cho het LOCK_TIMEOUT_S moi tu huy.
                        print("[CANH BAO] Bang tai da tu dung vi qua lau khong "
                              "thay vat toi vi tri gap - huy khoa, cho vat tiep theo.")
                        if pending_color is not None:
                            log_event(pending_color, get_color_name(pending_color),
                                      pending_center, "bang_tai_tu_dung_khong_vat")
                        pending_color = None
                        pending_center = None
                        lock_time = None
                        history.clear()

            # ---- 2) Vat het khoa qua lau ma Arduino chua bao toi noi ----
            if pending_color is not None and lock_time is not None:
                if time.time() - lock_time > LOCK_TIMEOUT_S:
                    print("[CANH BAO] Da khoa mau nhung qua lau khong thay bao toi vi tri gap "
                          "(vat co the da roi khoi bang tai) - huy khoa, quay lai theo doi.")
                    pending_color = None
                    pending_center = None
                    lock_time = None
                    history.clear()

            # ---- 3) Doc khung hinh camera va hien thi lien tuc ----
            ok, frame = cap.read()
            if not ok:
                continue

            display = frame.copy()

            if pending_color is None:
                # Dang theo doi bang tai de tim + phan loai vat MOI (vat con
                # dang di chuyen, bang tai KHONG can dung).
                corrected = apply_lighting_correction(frame)
                blurred = cv2.GaussianBlur(corrected, (11, 11), 0)
                hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

                color_key, center = detect_frame(hsv, frame.shape)
                history.append(color_key)

                if center is not None:
                    cv2.circle(display, center, 6, (0, 255, 0), -1)
                    cv2.putText(display, get_color_name(color_key), (center[0] - 20, center[1] - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                counts = Counter(history)
                if history:
                    top_color, top_count = counts.most_common(1)[0]
                    if top_color is not None and top_count >= VOTE_THRESHOLD:
                        pending_color = top_color
                        pending_center = center
                        lock_time = time.time()
                        print(f"Da nhan dien on dinh: {get_color_name(pending_color)} "
                              f"- cho bang tai dua toi vi tri gap...")
                        history.clear()

                status_text = "DANG THEO DOI / PHAN LOAI..."
            else:
                status_text = f"DA KHOA MAU: {get_color_name(pending_color)} - cho toi vi tri gap"

            cv2.putText(display, status_text, (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
            cv2.imshow("Color Sorter", display)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("Dung chuong trinh theo yeu cau.")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if ser is not None:
            ser.close()


if __name__ == "__main__":
    main()
