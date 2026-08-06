/*
  arduino_arm_sorter.ino  (ban NANG CAP - IK + Bang tai + Cam bien)
  ----------------------------------------------------------------
  He thong day du gom:
   1) Tay gap 4 servo (Base/Shoulder/Elbow/Gripper) dieu khien bang
      dong hoc nguoc (Inverse Kinematics) 3-DOF
   2) Bang tai chay bang dong co DC qua mach cau H (L298N)
   3) 2 CAM BIEN hong ngoai:
      - Cam bien DAU bang tai (PIN_START_SENSOR, chan 25): phat hien vat
        vua duoc dat vao -> tu dong BAT bang tai.
      - Cam bien CUOI bang tai, dat DUNG TAI VI TRI GAP CO DINH (PICK_POS)
        (PIN_SENSOR, chan 24): phat hien vat toi noi -> tu dong DUNG bang
        tai va bao cho Python qua Serial. Camera (ben Python) da nhan dien
        mau TU TRUOC, trong luc vat con dang di chuyen tren bang tai (chua
        can dung bang tai de nhin), nen ngay khi bang tai dung la robot
        gap duoc luon.
   4) Khay rieng cho "VAT LA" (mau khong xac dinh duoc) -> he thong
      khong bi ket khi gap vat ngoai 4 mau da dinh nghia
   5. Hieu chinh thong so (L0/L1/L2, offset goc, vi tri gap co dinh,
      toa do khay) qua lenh Serial va LUU VAO EEPROM -> khong can nap
      lai code moi lan chinh sai so vi tri

  GIAO TIEP VOI PYTHON (color_sort_vision.py):
    Arduino -> Python:
      "READY"          : Arduino da khoi dong xong
      "OBJ_DETECTED"   : vat da toi DUNG VI TRI GAP CO DINH, bang tai
                          da tu dung - Python gui ngay mau da nhan dien
                          truoc do (luc vat con dang di chuyen)
      "DONE"           : da gap-tha xong, san sang chay bang tai tiep
      "CONV_TIMEOUT_NO_OBJECT" : bang tai da CHAY QUA LAU (>CONVEYOR_TIMEOUT_MS)
                          ma khong thay vat toi vi tri gap - Arduino TU DUNG
                          bang tai (an toan, tranh chay vo han). Python nen
                          huy "khoa" mau dang cho (neu co) va quay lai theo doi.

    Python -> Arduino:
      "PICK:<MAU>\n"    : lenh gap vat mau gi TAI VI TRI GAP CO DINH da
                          hieu chinh san (khong con gui toa do nua, vi
                          camera chi con nhiem vu XAC DINH MAU trong luc
                          vat con dang di chuyen, KHONG con dung de tinh
                          vi tri gap). Vi du: "PICK:R". Mau "X" = vat la
      "CONV:ON\n" / "CONV:OFF\n" : bat/tat bang tai thu cong (debug)

  LENH HIEU CHINH (go qua Serial Monitor 9600 baud hoac tu script Python):
      "SHOWCAL"                  : in toan bo thong so hieu chinh hien tai
      "SET <TEN> <GIA_TRI>"      : sua 1 thong so, vi du "SET L0 9.8"
                                    Ten hop le: L0 L1 L2 OFFB OFFS OFFE
                                    PICKX PICKY (vi tri gap CO DINH)
                                    BINR_X BINR_Y BING_X BING_Y BINB_X BINB_Y
                                    BINY_X BINY_Y BINX_X BINX_Y
      "SAVECAL"                  : luu toan bo thong so hien tai vao EEPROM
                                    (giu nguyen sau khi tat nguon/nap lai code)
      "LOADCAL"                  : nap lai thong so tu EEPROM (bo thay doi
                                    chua luu)

  Tham khao mo hinh IK: Mohammed-El-Kassoiri/vision-robotic-arm
  https://github.com/Mohammed-El-Kassoiri/vision-robotic-arm

  ==== LAN DAU TIEN, HIEU CHINH CAC THONG SO SAU CHO DUNG MO HINH THAT ====
  (co the sua truc tiep trong code o duoi ROI DUNG LENH "SAVECAL" DE LUU,
  hoac hieu chinh hoan toan qua Serial ma khong can sua code/nap lai)
  - Chieu dai cac khau L0, L1, L2 (do bang thuoc, don vi cm)
  - Vi tri goc servo tren thuc te co the LECH so voi cong thuc toan hoc
    (do cach gan servo/canh tay vat ly), can bu tru trong ANGLE_OFFSET_*
  - Toa do khay tha (BIN_POS_*) phai do dac tren mo hinh that
  - Chan dieu khien L298N va cam bien phai khop voi day noi thuc te
*/

#include <Servo.h>
#include <math.h>
#include <EEPROM.h>

// ================== BANG TAI (L298N) ==================
// IN1/IN2 dieu khien chieu quay, ENA dieu khien toc do (PWM)
const int PIN_CONV_IN1 = 22;
const int PIN_CONV_IN2 = 23;
const int PIN_CONV_ENA = 2;   // phai la chan ho tro PWM tren Mega (2,3,4,5,6,7...)
const int CONV_SPEED   = 180; // 0-255, chinh toc do bang tai

// AN TOAN: neu bang tai chay LIEN TUC qua lau (vd vat roi khoi bang tai
// giua chung, bi ket, cam bien CUOI hong...) ma cam bien CUOI (PIN_SENSOR)
// van KHONG thay vat toi noi, TU DONG DUNG bang tai thay vi chay mai mai.
// Dam bao dung nguyen tac "binh thuong bang tai phai dung khi khong co vat",
// ke ca khi PC/Python bi mat ket noi hoac dung.
const unsigned long CONVEYOR_TIMEOUT_MS = 20000UL; // 20 giay chay toi da khong co ket qua

// ================== CAM BIEN VAT CAN HONG NGOAI ==================
// Cam bien IR loai module thuong: LOW = phat hien vat (active LOW)
const int PIN_SENSOR = 24; // Cam bien cuoi (dung bang tai de gap)
const int PIN_START_SENSOR = 25; // Cam bien dau (bat bang tai chay)

bool objectHandledThisPass = false; // tranh bao "OBJ_DETECTED" lien tuc cho cung 1 vat
bool isConveyorRunning = false; // trang thai bang tai hien tai
unsigned long conveyorStartMillis = 0; // thoi diem bang tai bat dau chay - dung de kiem tra CONVEYOR_TIMEOUT_MS

// ================== SERVO - CHINH CHAN CHO DUNG PHAN CUNG ==================
Servo servoBase;
Servo servoShoulder;
Servo servoElbow;
Servo servoGripper;

const int PIN_BASE     = 3;
const int PIN_SHOULDER = 5;
const int PIN_ELBOW    = 6;
const int PIN_GRIPPER  = 9;

const int GRIP_OPEN  = 60;
const int GRIP_CLOSE = 10;

// ================== THONG SO DONG HOC (DO THUC TE VA DIEN VAO) ==================
// Cac gia tri nay la MAC DINH ban dau. Sau khi hieu chinh qua lenh Serial
// "SET ... " va "SAVECAL", gia tri se duoc doc tu EEPROM moi khi khoi dong
// (xem loadCalibrationFromEEPROM() trong setup()).

// Chieu dai cac khau (cm) - vi du, PHAI DO LAI tren canh tay that
float L0 = 9.8;   // chieu cao truc base den vai (shoulder)
float L1 = 10.4;  // do dai khau vai - khuyu (upper arm)
float L2 = 15.0;  // do dai khau khuyu - co tay/gripper (forearm)

// Bu goc neu servo lap nguoc/lech so voi mo hinh toan (do bang cach thu servo
// ve 90 do va so sanh voi vi tri thuc te cua canh tay)
int ANGLE_OFFSET_BASE     = 0;
int ANGLE_OFFSET_SHOULDER = 0;
int ANGLE_OFFSET_ELBOW    = 0;

// Toa do (x, y) cm cua tung khay tha, tinh tu goc de robot - DO THUC TE
struct Point2D { float x; float y; };
Point2D BIN_POS_RED    = {15.0, -15.0};
Point2D BIN_POS_GREEN  = {15.0,   0.0};
Point2D BIN_POS_BLUE   = {15.0,  15.0};
Point2D BIN_POS_YELLOW = {15.0,  25.0};
Point2D BIN_POS_UNKNOWN = {15.0, -30.0}; // khay rieng cho "vat la" (mau X)

// VI TRI GAP CO DINH (cm, so voi goc de robot) - ung voi vi tri cam bien IR.
// Vat luon duoc bang tai dua toi DUNG vi tri nay truoc khi dung, nen tay
// robot LUON gap tai 1 diem duy nhat nay, khong can tinh tu anh camera nua.
// DO THUC TE va dien vao, hoac hieu chinh qua lenh "SET PICKX ..." / "SET PICKY ..."
Point2D PICK_POS = {12.5, 0.0};

// ================== HIEU CHINH QUA EEPROM ==================
const int EEPROM_MAGIC_ADDR = 0;
const byte EEPROM_MAGIC_VALUE = 0xA5; // danh dau EEPROM da tung duoc luu
const int EEPROM_DATA_ADDR = 1;

struct CalibData {
  float L0, L1, L2;
  int offB, offS, offE;
  Point2D binR, binG, binB, binY, binX;
  Point2D pickPos;
};

void saveCalibrationToEEPROM() {
  CalibData data = {
    L0, L1, L2,
    ANGLE_OFFSET_BASE, ANGLE_OFFSET_SHOULDER, ANGLE_OFFSET_ELBOW,
    BIN_POS_RED, BIN_POS_GREEN, BIN_POS_BLUE, BIN_POS_YELLOW, BIN_POS_UNKNOWN,
    PICK_POS
  };
  EEPROM.put(EEPROM_DATA_ADDR, data);
  EEPROM.write(EEPROM_MAGIC_ADDR, EEPROM_MAGIC_VALUE);
  Serial.println("CAL_SAVED");
}

bool loadCalibrationFromEEPROM() {
  if (EEPROM.read(EEPROM_MAGIC_ADDR) != EEPROM_MAGIC_VALUE) {
    return false; // chua tung luu -> giu gia tri mac dinh trong code
  }
  CalibData data;
  EEPROM.get(EEPROM_DATA_ADDR, data);
  L0 = data.L0; L1 = data.L1; L2 = data.L2;
  ANGLE_OFFSET_BASE = data.offB;
  ANGLE_OFFSET_SHOULDER = data.offS;
  ANGLE_OFFSET_ELBOW = data.offE;
  BIN_POS_RED = data.binR;
  BIN_POS_GREEN = data.binG;
  BIN_POS_BLUE = data.binB;
  BIN_POS_YELLOW = data.binY;
  BIN_POS_UNKNOWN = data.binX;
  PICK_POS = data.pickPos;
  return true;
}

void printCalibration() {
  Serial.println("---- THONG SO HIEU CHINH HIEN TAI ----");
  Serial.print("L0="); Serial.print(L0); Serial.print(" L1="); Serial.print(L1);
  Serial.print(" L2="); Serial.println(L2);
  Serial.print("OFFB="); Serial.print(ANGLE_OFFSET_BASE);
  Serial.print(" OFFS="); Serial.print(ANGLE_OFFSET_SHOULDER);
  Serial.print(" OFFE="); Serial.println(ANGLE_OFFSET_ELBOW);
  Serial.print("PICK_POS(vi tri gap co dinh)="); Serial.print(PICK_POS.x); Serial.print(","); Serial.println(PICK_POS.y);
  Serial.print("BIN_R="); Serial.print(BIN_POS_RED.x); Serial.print(","); Serial.println(BIN_POS_RED.y);
  Serial.print("BIN_G="); Serial.print(BIN_POS_GREEN.x); Serial.print(","); Serial.println(BIN_POS_GREEN.y);
  Serial.print("BIN_B="); Serial.print(BIN_POS_BLUE.x); Serial.print(","); Serial.println(BIN_POS_BLUE.y);
  Serial.print("BIN_Y="); Serial.print(BIN_POS_YELLOW.x); Serial.print(","); Serial.println(BIN_POS_YELLOW.y);
  Serial.print("BIN_X(vat la)="); Serial.print(BIN_POS_UNKNOWN.x); Serial.print(","); Serial.println(BIN_POS_UNKNOWN.y);
  Serial.println("---------------------------------------");
}

// Xu ly lenh "SET <TEN> <GIA_TRI>". Tra ve true neu nhan dien duoc ten hop le.
bool handleSetCommand(String name, float value) {
  name.toUpperCase();
  if (name == "L0") { L0 = value; }
  else if (name == "L1") { L1 = value; }
  else if (name == "L2") { L2 = value; }
  else if (name == "OFFB") { ANGLE_OFFSET_BASE = (int)value; }
  else if (name == "OFFS") { ANGLE_OFFSET_SHOULDER = (int)value; }
  else if (name == "OFFE") { ANGLE_OFFSET_ELBOW = (int)value; }
  else if (name == "PICKX") { PICK_POS.x = value; }
  else if (name == "PICKY") { PICK_POS.y = value; }
  else if (name == "BINR_X") { BIN_POS_RED.x = value; }
  else if (name == "BINR_Y") { BIN_POS_RED.y = value; }
  else if (name == "BING_X") { BIN_POS_GREEN.x = value; }
  else if (name == "BING_Y") { BIN_POS_GREEN.y = value; }
  else if (name == "BINB_X") { BIN_POS_BLUE.x = value; }
  else if (name == "BINB_Y") { BIN_POS_BLUE.y = value; }
  else if (name == "BINY_X") { BIN_POS_YELLOW.x = value; }
  else if (name == "BINY_Y") { BIN_POS_YELLOW.y = value; }
  else if (name == "BINX_X") { BIN_POS_UNKNOWN.x = value; }
  else if (name == "BINX_Y") { BIN_POS_UNKNOWN.y = value; }
  else { return false; }
  return true;
}

const int MOVE_STEP_DELAY = 15; // ms/buoc noi suy - tang de chuyen dong muot hon
const int MOVE_STEPS = 30;

// Vi tri hien tai cua tung servo (dung de noi suy muot)
int curBase = 90, curShoulder = 90, curElbow = 90, curGripper = GRIP_OPEN;


// ================== INVERSE KINEMATICS ==================
// Tinh goc base/shoulder/elbow (do) tu toa do (x, y) cm.
// Tra ve false neu diem nam ngoai tam voi cua tay (khong giai duoc IK).
bool computeIK(float x, float y, int &outBase, int &outShoulder, int &outElbow) {
  float theta1 = atan2(y, x); // goc xoay base

  float d = sqrt(x * x + y * y);
  float h = sqrt(d * d + L0 * L0);

  float cosBeta = (h * h + L1 * L1 - L2 * L2) / (2 * h * L1);
  float cosElbow = (L2 * L2 + L1 * L1 - h * h) / (2 * L2 * L1);

  // Kiem tra diem co nam trong tam voi khong (tranh loi acos ngoai [-1,1])
  if (cosBeta < -1 || cosBeta > 1 || cosElbow < -1 || cosElbow > 1) {
    return false;
  }

  float alpha = acos(L0 / h);
  float beta = acos(cosBeta);
  float theta2 = alpha + beta;      // goc vai (shoulder)
  float theta3 = acos(cosElbow);    // goc khuyu (elbow)

  outBase     = (int)(degrees(theta1)) + 90 + ANGLE_OFFSET_BASE; // quy ve thang do servo 0-180
  outShoulder = (int)(degrees(theta2)) + ANGLE_OFFSET_SHOULDER;
  outElbow    = (int)(degrees(theta3)) + ANGLE_OFFSET_ELBOW;

  // Gioi han trong khoang servo cho phep
  outBase     = constrain(outBase, 0, 180);
  outShoulder = constrain(outShoulder, 0, 180);
  outElbow    = constrain(outElbow, 0, 180);

  return true;
}


// ================== DIEU KHIEN CHUYEN DONG ==================
void moveTo(int base, int shoulder, int elbow, int gripper) {
  for (int s = 1; s <= MOVE_STEPS; s++) {
    int b = curBase + (base - curBase) * s / MOVE_STEPS;
    int sh = curShoulder + (shoulder - curShoulder) * s / MOVE_STEPS;
    int e = curElbow + (elbow - curElbow) * s / MOVE_STEPS;
    int g = curGripper + (gripper - curGripper) * s / MOVE_STEPS;

    servoBase.write(b);
    servoShoulder.write(sh);
    servoElbow.write(e);
    servoGripper.write(g);

    delay(MOVE_STEP_DELAY);
  }
  curBase = base; curShoulder = shoulder; curElbow = elbow; curGripper = gripper;
}


void goHome() {
  moveTo(90, 90, 90, GRIP_OPEN);
}


// Gap vat tai (x,y) roi tha vao vi tri khay (binX, binY)
bool pickAndPlace(float pickX, float pickY, Point2D bin) {
  int b, s, e;

  if (!computeIK(pickX, pickY, b, s, e)) {
    Serial.println("LOI: Vi tri gap ngoai tam voi cua tay!");
    return false;
  }
  moveTo(b, s, e, GRIP_OPEN);   // den vi tri gap, gripper mo
  moveTo(b, s, e, GRIP_CLOSE);  // dong gripper de gap vat
  delay(300);
  moveTo(90, 60, 90, GRIP_CLOSE); // nhac vat len, tranh va cham

  if (!computeIK(bin.x, bin.y, b, s, e)) {
    Serial.println("LOI: Vi tri khay ngoai tam voi cua tay!");
    goHome();
    return false;
  }
  moveTo(b, s, e, GRIP_CLOSE);  // den khay, van giu vat
  delay(200);
  moveTo(b, s, e, GRIP_OPEN);   // mo gripper, tha vat
  delay(300);

  goHome();
  return true;
}


// ================== NHAN LENH QUA SERIAL ==================
// Dinh dang lenh: "PICK:R\n"  (PICK : ma mau) - vi tri gap la CO DINH (PICK_POS),
// khong con nhan toa do tu Python nua.
String inputBuffer = "";

void handleCommand(String cmd) {
  cmd.trim();
  // Dinh dang: "PICK:X" trong do X la 1 ky tu mau (R/G/B/Y/X)
  int colonIdx = cmd.indexOf(':');
  if (colonIdx < 0 || cmd.length() <= (unsigned int)(colonIdx + 1)) {
    Serial.println("LOI: Sai dinh dang lenh. Vi du: PICK:R");
    return;
  }

  char colorChar = cmd.charAt(colonIdx + 1);

  Point2D bin;
  String colorName;
  switch (colorChar) {
    case 'R': bin = BIN_POS_RED;     colorName = "DO";         break;
    case 'G': bin = BIN_POS_GREEN;   colorName = "XANH LA";    break;
    case 'B': bin = BIN_POS_BLUE;    colorName = "XANH DUONG"; break;
    case 'Y': bin = BIN_POS_YELLOW;  colorName = "VANG";       break;
    case 'X': bin = BIN_POS_UNKNOWN; colorName = "VAT LA";     break;
    default:
      Serial.println("LOI: Ma mau khong hop le");
      return;
  }

  Serial.print("Gap vat mau "); Serial.print(colorName);
  Serial.print(" tai vi tri gap co dinh (");
  Serial.print(PICK_POS.x); Serial.print(", "); Serial.print(PICK_POS.y);
  Serial.println(")");

  pickAndPlace(PICK_POS.x, PICK_POS.y, bin);
}


// ================== DIEU KHIEN BANG TAI ==================
void conveyorOn() {
  digitalWrite(PIN_CONV_IN1, HIGH);
  digitalWrite(PIN_CONV_IN2, LOW);
  analogWrite(PIN_CONV_ENA, CONV_SPEED);
}

void conveyorOff() {
  digitalWrite(PIN_CONV_IN1, LOW);
  digitalWrite(PIN_CONV_IN2, LOW);
  analogWrite(PIN_CONV_ENA, 0);
}


void setup() {
  Serial.begin(9600);

  servoBase.attach(PIN_BASE);
  servoShoulder.attach(PIN_SHOULDER);
  servoElbow.attach(PIN_ELBOW);
  servoGripper.attach(PIN_GRIPPER);

  pinMode(PIN_CONV_IN1, OUTPUT);
  pinMode(PIN_CONV_IN2, OUTPUT);
  pinMode(PIN_CONV_ENA, OUTPUT);
  // QUAN TRONG: cam bien E18-D80NK co nga ra NPN cuc thu ho (open-collector),
  // KHONG tu tao muc HIGH duoc - bat buoc phai co dien tro keo len VCC (1~10K)
  // thi tin hieu moi on dinh. Dung INPUT_PULLUP de dung luon dien tro keo noi
  // san trong Arduino (~20-50K), khong can han dien tro ngoai. Neu van doc bi
  // nhieu/nhay lung tung du khong co vat, hay gan them dien tro ngoai 4.7K~10K
  // tu chan tin hieu len VCC 5V cho chac chan hon.
  pinMode(PIN_SENSOR, INPUT_PULLUP);
  pinMode(PIN_START_SENSOR, INPUT_PULLUP);

  bool loaded = loadCalibrationFromEEPROM();

  goHome();
  conveyorOff(); // ban dau bang tai tat, cho vat dat vao
  isConveyorRunning = false;

  Serial.println("READY");
  if (loaded) {
    Serial.println("Da nap thong so hieu chinh tu EEPROM.");
  } else {
    Serial.println("Chua co hieu chinh luu trong EEPROM, dung gia tri mac dinh trong code.");
  }
  Serial.println("Dinh dang lenh gap vat: PICK:<MAU>  vi du PICK:R (X = vat la). Vi tri gap la CO DINH (PICK_POS).");
  Serial.println("Lenh hieu chinh: SHOWCAL | SET <TEN> <GIA_TRI> | SAVECAL | LOADCAL");
}


void loop() {
  // --- Doc lenh tu Python qua Serial ---
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      String cmd = inputBuffer;
      inputBuffer = "";
      cmd.trim();

      if (cmd == "CONV:ON") {
        conveyorOn();
      } else if (cmd == "CONV:OFF") {
        conveyorOff();
      } else if (cmd == "SHOWCAL") {
        printCalibration();
      } else if (cmd == "SAVECAL") {
        saveCalibrationToEEPROM();
      } else if (cmd == "LOADCAL") {
        if (loadCalibrationFromEEPROM()) {
          Serial.println("CAL_LOADED");
        } else {
          Serial.println("Chua co du lieu hieu chinh trong EEPROM.");
        }
      } else if (cmd.startsWith("SET ")) {
        int firstSpace = cmd.indexOf(' ');
        int secondSpace = cmd.indexOf(' ', firstSpace + 1);
        if (secondSpace > 0) {
          String name = cmd.substring(firstSpace + 1, secondSpace);
          float value = cmd.substring(secondSpace + 1).toFloat();
          if (handleSetCommand(name, value)) {
            Serial.print("OK: "); Serial.print(name); Serial.print(" = "); Serial.println(value);
          } else {
            Serial.println("LOI: Ten thong so khong hop le. Xem danh sach trong SHOWCAL/comment dau file.");
          }
        } else {
          Serial.println("LOI: Sai cu phap. Dung: SET <TEN> <GIA_TRI>");
        }
      } else if (cmd.length() > 0) {
        handleCommand(cmd);
        // Da xoa conveyorOn() o day de he thong doi vat tiep theo
        isConveyorRunning = false;
        objectHandledThisPass = false;
        Serial.println("DONE");
      }
    } else {
      inputBuffer += c;
    }
  }

  // --- Kiem tra cam bien dau (bat bang tai) ---
  bool startObjectPresent = (digitalRead(PIN_START_SENSOR) == LOW); // active LOW
  if (startObjectPresent && !isConveyorRunning && !objectHandledThisPass) {
    conveyorOn();
    isConveyorRunning = true;
    conveyorStartMillis = millis();
    Serial.println("CONVEYOR_STARTED_BY_SENSOR"); // In ra de debug tren Serial
  }

  // --- AN TOAN: bang tai chay qua lau ma khong thay vat toi vi tri gap ---
  // (vd vat roi khoi bang tai giua chung, bi ket, cam bien CUOI hong...)
  // -> TU DONG DUNG bang tai, dung nguyen tac "binh thuong phai dung khi
  // khong co vat" thay vi de chay mai mai.
  if (isConveyorRunning && (millis() - conveyorStartMillis > CONVEYOR_TIMEOUT_MS)) {
    conveyorOff();
    isConveyorRunning = false;
    objectHandledThisPass = false;
    Serial.println("CONV_TIMEOUT_NO_OBJECT"); // bao PC: da tu dung bang tai vi qua lau khong thay vat toi noi
  }

  // --- Kiem tra cam bien cuoi (dung bang tai de gap) ---
  bool objectPresent = (digitalRead(PIN_SENSOR) == LOW); // active LOW

  if (objectPresent && !objectHandledThisPass && isConveyorRunning) {
    conveyorOff();                 // dung bang tai de gap on dinh
    isConveyorRunning = false;
    objectHandledThisPass = true;
    Serial.println("OBJ_DETECTED"); // bao Python: gui ngay mau da nhan dien tu truoc
    // Arduino se cho lenh gap tha ("PICK:<MAU>") tu Python o vong lap tren
  }

  if (!objectPresent) {
    objectHandledThisPass = false; // vat da qua khoi cam bien, san sang cho vat tiep theo
  }
}

/*
  ================== CHE DO HIEU CHINH SERVO THU CONG (CALIBRATION) ==================
  Neu can do lai offset goc hoac kiem tra servo truoc khi dung IK, tam thoi
  thay noi dung loop() bang doan duoi day, nap lai, mo Serial Monitor (9600 baud):

  void loop() {
    if (Serial.available() > 0) {
      int servoIndex = Serial.parseInt();
      int angle = Serial.parseInt();
      Servo* servos[4] = {&servoBase, &servoShoulder, &servoElbow, &servoGripper};
      if (servoIndex >= 0 && servoIndex <= 3 && angle >= 0 && angle <= 180) {
        servos[servoIndex]->write(angle);
        Serial.print("Servo "); Serial.print(servoIndex);
        Serial.print(" -> "); Serial.println(angle);
      }
    }
  }
  // Go: "0 90" de servo base ve 90 do, v.v. (0=base,1=shoulder,2=elbow,3=gripper)
  ======================================================================================
*/
