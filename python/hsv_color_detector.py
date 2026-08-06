"""
hsv_color_detector.py  (ban nang cap)
---------------------------------------
Cong cu hieu chinh khoang mau HSV cho tung vat can phan loai, VA LUU
TRUC TIEP vao config.json (khong can copy tay so lieu vao code nua).

CACH DUNG:
  1. Chay: python hsv_color_detector.py
  2. Chon nguon anh: webcam USB (mac dinh, dung CAMERA_SOURCE trong
     config.json) hoac dien thoai qua app "IP Webcam" (nhap dia chi IP)
  3. Voi tung mau (R/G/B/Y), dua vat mau do vao khung hinh, nhan phim
     tuong ung (r/g/b/y) roi DUNG CHUOT keo mot khung quanh vung mau
     tren anh dung yen de lay mau
  4. CO THE lap lai buoc 3 nhieu lan cho CUNG 1 mau (o nhieu goc anh
     sang khac nhau) - chuong trinh se tu GOP (lay min/max chung) de
     khoang mau on dinh hon trong dieu kien anh sang thuc te
  5. Nhan 's' de LUU tat ca vao config.json, 'q' de thoat khong luu

PHIM TAT:
  r/g/b/y : chon mau dang hieu chinh (Do/Xanh la/Xanh duong/Vang)
  s       : luu vao config.json
  q       : thoat
"""

import json
import os
import cv2
import numpy as np

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

COLOR_KEYS = {
    ord('r'): ("R", "Do"),
    ord('g'): ("G", "Xanh la"),
    ord('b'): ("B", "Xanh duong"),
    ord('y'): ("Y", "Vang"),
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"color_ranges": {}}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"Da luu vao {CONFIG_PATH}")


def open_capture(cfg):
    print("Chon nguon camera:")
    print("  1 = Webcam USB (dung camera_source trong config.json)")
    print("  2 = Dien thoai qua app IP Webcam (nhap dia chi URL)")
    choice = input("Lua chon (1/2, mac dinh 1): ").strip() or "1"

    if choice == "2":
        url = input("Nhap dia chi (vd http://192.168.43.1:8080/shot.jpg): ").strip()
        return ("ip", url)
    else:
        source = cfg.get("camera_source", 0)
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Khong mo duoc webcam (source={source})")
        return ("usb", cap)


def read_frame(kind, handle):
    if kind == "usb":
        ok, frame = handle.read()
        if not ok:
            return None
        return frame
    else:
        from urllib.request import urlopen
        try:
            imgadd = urlopen(handle, timeout=3)
            imgarr = np.array(bytearray(imgadd.read()), dtype=np.uint8)
            frame = cv2.imdecode(imgarr, -1)
            return frame
        except Exception as e:
            print(f"[CANH BAO] Khong doc duoc frame tu IP Webcam: {e}")
            return None


def pick_roi(frame, window_name="Chon vung mau (keo chuot, Enter de xac nhan)"):
    """Dung ROI selector co san cua OpenCV - on dinh hon tu viet callback tay."""
    r = cv2.selectROI(window_name, frame, showCrosshair=True)
    cv2.destroyWindow(window_name)
    x, y, w, h = r
    if w == 0 or h == 0:
        return None
    return frame[y:y + h, x:x + w]


def merge_range(existing, new_lower, new_upper):
    """Gop khoang mau moi voi khoang da co (neu co) - lay min cua lower,
    max cua upper - de khoang mau bao quat nhieu dieu kien anh sang hon.

    CANH BAO VE MAU DO: kenh Hue la mot VONG TRON 0-180 trong OpenCV, mau
    do nam o CA 2 DAU vong tron (gan 0 VA gan 180). Ham nay chi gop 1 dai
    lower-upper LIEN TUC - neu ban hieu chinh mau do va cac lan do Hue ra
    ca gan 0 LAN gan 180 (VD lan 1 ra Hue~3, lan 2 ra Hue~177), gop truc
    tiep se tao ra dai qua RONG (VD 0-177, gan het vong tron Hue) va bat
    nham hau het cac mau khac. Ham se in canh bao neu thay dieu nay xay ra
    - trong truong hop do, hay SUA TAY 2 dai rieng trong config.json bang
    'lower'/'upper' (dau gan 0) VA 'lower2'/'upper2' (dau gan 180) thay vi
    dung 1 dai gop duy nhat."""
    if existing is None:
        return list(new_lower), list(new_upper)
    lower = [min(existing["lower"][i], new_lower[i]) for i in range(3)]
    upper = [max(existing["upper"][i], new_upper[i]) for i in range(3)]
    if (upper[0] - lower[0]) > 100:
        print("[CANH BAO] Dai Hue sau khi gop qua rong (co the do mau do "
              "nam o 2 dau vong tron Hue bi gop nham thanh 1 dai lien tuc). "
              "Kiem tra lai va can nhac sua tay 'lower'/'upper' + "
              "'lower2'/'upper2' trong config.json thay vi dung dai gop nay.")
    return lower, upper


def main():
    cfg = load_config()
    if "color_ranges" not in cfg:
        cfg["color_ranges"] = {}

    kind, handle = open_capture(cfg)

    print("\nDua vat can hieu chinh vao khung hinh.")
    print("Nhan phim mau (r/g/b/y) de bat dau chon vung mau do cho mau tuong ung.")
    print("Nhan 's' de luu vao config.json, 'q' de thoat.\n")

    try:
        while True:
            frame = read_frame(kind, handle)
            if frame is None:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            preview = frame.copy()
            cv2.putText(preview, "r/g/b/y: chon mau | s: luu | q: thoat",
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow("HSV Calibrator", preview)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            elif key == ord('s'):
                save_config(cfg)

            elif key in COLOR_KEYS:
                code, default_name = COLOR_KEYS[key]
                roi = pick_roi(frame)
                if roi is None or roi.size == 0:
                    print("Khong chon duoc vung hop le, bo qua.")
                    continue

                hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                new_lower = [int(hsv_roi[:, :, i].min()) for i in range(3)]
                new_upper = [int(hsv_roi[:, :, i].max()) for i in range(3)]

                existing = cfg["color_ranges"].get(code)
                lower, upper = merge_range(existing, new_lower, new_upper)
                name = existing["name"] if existing else default_name

                cfg["color_ranges"][code] = {"lower": lower, "upper": upper, "name": name}

                print(f"[{code} - {name}] lower={lower} upper={upper} "
                      f"(da gop voi lan hieu chinh truoc do neu co)")

                # Xem thu mask ket qua tren toan khung hinh de kiem tra nhanh
                hsv_full = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv_full, np.array(lower), np.array(upper))
                cv2.imshow("Xem thu mask", mask)
                cv2.waitKey(500)
                cv2.destroyWindow("Xem thu mask")

    finally:
        if kind == "usb":
            handle.release()
        cv2.destroyAllWindows()

    print("\nKet qua cuoi cung (chua chac da luu, nho nhan 's' truoc khi thoat neu can):")
    for code, val in cfg["color_ranges"].items():
        print(f"  {code} ({val['name']}): lower={val['lower']} upper={val['upper']}")


if __name__ == "__main__":
    main()
