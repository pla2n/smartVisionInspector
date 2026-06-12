import serial
import time
import cv2
import os
import collections
from datetime import datetime
from ultralytics import YOLO
import requests
import threading

ARDUINO_PORT = '/dev/cu.usbmodem1101'
BAUD_RATE = 9600

IMAGE_DIR = "captured_imgs"
os.makedirs(IMAGE_DIR, exist_ok=True)

from dotenv import load_dotenv

load_dotenv()
SERVER_IP = os.getenv("SERVER_IP", "YOUR_SERVER_IP")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")
AUTH_HEADER = {"X-API-Key": API_SECRET_KEY}

API_URL = f"http://{SERVER_IP}:8000/api/settings"
SERVER_URL = f"http://{SERVER_IP}:8000/predict"
LOGS_URL = f"http://{SERVER_IP}:8000/api/logs"
CONFIDENCE_THRESHOLD = 0.3
IS_RUNNING = True
latest_frame = None
frame_buffer = collections.deque(maxlen=90)

YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
defect_classes_raw = os.getenv("DEFECT_CLASSES", "pizza,toilet,chair,person,bed")
DEFECT_CLASSES = [c.strip() for c in defect_classes_raw.split(",") if c.strip()]

print(f"YOLO모델({YOLO_MODEL_PATH}) 로딩중...")
model = YOLO(YOLO_MODEL_PATH)
model_lock = threading.Lock()
print(f"불량 감지 대상 클래스 목록: {DEFECT_CLASSES}")
print(f"불량 감지 임계값: {CONFIDENCE_THRESHOLD}")

def sync_settings():
    global CONFIDENCE_THRESHOLD, IS_RUNNING
    try:
        resp = requests.get(API_URL, headers=AUTH_HEADER).json()
        CONFIDENCE_THRESHOLD = resp['confidence']
        IS_RUNNING = bool(resp['is_running'])
    except Exception:
        pass
    threading.Timer(2.0, sync_settings).start()

def camera_streaming_loop():
    global latest_frame
    cap = cv2.VideoCapture(0)
    print("카메라 구동 시작 (Edge-Push 스트리밍 스레드)")

    upload_url = f"http://{SERVER_IP}:8000/api/upload_frame"

    def upload_frame(buf):
        try:
            requests.post(upload_url, data=buf, headers={**AUTH_HEADER, 'Content-Type': 'image/jpeg'}, timeout=0.5)
        except requests.exceptions.RequestException:
            pass

    try:
        while True:
            ret, frame = cap.read()
            if ret:
                latest_frame = frame.copy()
                frame_buffer.append((time.time(), frame.copy()))

                if model_lock.acquire(blocking=False):
                    try:
                        results = model(frame, verbose=False)
                        annotated = results[0].plot()
                    finally:
                        model_lock.release()
                else:
                    annotated = frame

                ret_encode, buffer = cv2.imencode('.jpg', annotated)
                if ret_encode:
                    threading.Thread(target=upload_frame, args=(buffer.tobytes(),), daemon=True).start()

            time.sleep(0.03)
    finally:
        cap.release()
        print("카메라 스트리밍 종료")

def ai_inference_loop():
    global latest_frame
    print(f"엣지 디바이스({ARDUINO_PORT}) 연결 시도 중...")
    
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print("엣지 통신 완료. 스마트 팩토리 관제 시작!")
        
        while True:
            if not IS_RUNNING:
                time.sleep(0.1)
                continue
                
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()
                
                if raw_data == "DETECTED" and latest_frame is not None:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    detect_time = time.time()
                    print(f"[알림] {now} | 물체 감지! 2초 전 6장 + 1초 전 6장 + 현재 6장 분석 시작")

                    frames_2s = [
                        f for ts, f in frame_buffer
                        if 1.7 <= detect_time - ts <= 2.3
                    ][-6:]

                    frames_1s = [
                        f for ts, f in frame_buffer
                        if 0.7 <= detect_time - ts <= 1.3
                    ][-6:]

                    now_frames = []
                    collect_start = time.time()
                    while time.time() - collect_start < 0.3:
                        if latest_frame is not None:
                            now_frames.append(latest_frame.copy())
                        time.sleep(0.05)
                    now_frames = now_frames[:6]

                    burst_frames = frames_2s + frames_1s + now_frames
                    if not burst_frames:
                        burst_frames = [latest_frame.copy()]

                    print(f"  → 2초 전 {len(frames_2s)}장 + 1초 전 {len(frames_1s)}장 + 현재 {len(now_frames)}장 = 총 {len(burst_frames)}장 YOLO 분석 중...")



                    is_defective = False
                    detected_items = []
                    defect_class = "Unknown"
                    defect_conf = 0.0
                    frame_to_analyze = burst_frames[0]
                    all_detected_with_conf = []

                    for frame in burst_frames:
                        with model_lock:
                            results = model(frame, verbose=False)

                        for r in results:
                            for box in r.boxes:
                                class_name = model.names[int(box.cls[0])]
                                confidence = float(box.conf[0])
                                all_detected_with_conf.append((class_name, round(confidence, 2)))
                                if class_name not in detected_items:
                                    detected_items.append(class_name)

                                if class_name in DEFECT_CLASSES and confidence > CONFIDENCE_THRESHOLD:
                                    if confidence > defect_conf:
                                        is_defective = True
                                        defect_class = class_name
                                        defect_conf = confidence
                                        frame_to_analyze = frame

                    detected_with_conf = all_detected_with_conf
                    print(f"탐지 결과 (멀티프레임): {detected_with_conf}")
                    
                    img_filename = "-"
                    if is_defective:
                        print(f"불량 발견({defect_class})! 컨베이어 일시 정지 후 불량품 제거 시도")
                        ser.write(b"RED\n")
                        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                        img_filename = f"error_{current_time}.jpg"
                        img_filepath = os.path.join(IMAGE_DIR, img_filename)
                        
                        cv2.imwrite(img_filepath, frame_to_analyze)

                        threading.Thread(target=send_defect_to_server, args=(defect_class, defect_conf, img_filepath), daemon=True).start()
                        
                        status = "RED_DETECTED"
                    else:
                        print("정상 제품. 통과")
                        ser.write(b"PASS\n")
                        status = "PASS"
                        
                    log_payload = {
                        "timestamp": now,
                        "status": status,
                        "sensor_data": f"YOLO: {str(detected_items)}",
                        "img_filename": img_filename
                    }
                    
                    def send_log_async(payload):
                        try:
                            requests.post(LOGS_URL, json=payload, headers=AUTH_HEADER,timeout=1.0)
                        except Exception:
                            pass
                            
                    threading.Thread(target=send_log_async, args=(log_payload,), daemon=True).start()
                        
            time.sleep(0.01)

    except serial.SerialException:
        print(f"장애 발생! {ARDUINO_PORT} 포트를 찾을 수 없습니다.")
    except KeyboardInterrupt:
        print("서버를 안전하게 종료합니다.")

def send_defect_to_server(defect_type, confidence, image_path):
    print(f"{defect_type} 불량 감지! 서버 전송 시작")

    try:
        payload = {
            "defect_type": defect_type,
            "confidence": confidence
        }

        with open(image_path, "rb") as f:
            files = {"file": f}

            response = requests.post(SERVER_URL, data=payload, files=files, headers=AUTH_HEADER)

        if response.status_code == 200:
            print("서버 전송 성공! 서버 응답:", response.json())
        else:
            print(f"전송 실패 {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("에러 : 서버 연결 불가.")

if __name__ == "__main__":
    sync_settings()
    threading.Thread(target=camera_streaming_loop, daemon=True).start()
    
    ai_inference_loop()